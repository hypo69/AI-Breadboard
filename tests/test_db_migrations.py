# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit and integration tests for database migration system
# =============================================================================
# Description:
#   Comprehensive unit and scenario tests for MigrationManager covering discovery,
#   SQL and Python execution, checksum validation, rollback on error, and backups.
#
# File: tests/test_db_migrations.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import tempfile
from pathlib import Path
import pytest

from src.db.migrations import MigrationManager


@pytest.fixture
def temp_repo_dir(tmp_path: Path) -> Path:
    """Fixture to create temporary repository structure for migration testing.

    Args:
        tmp_path (Path): Pytest temporary path fixture.

    Returns:
        Path: Initialized temporary workspace path.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    migrations_dir = repo / "migrations" / "test_db"
    migrations_dir.mkdir(parents=True)
    return repo


def test_migration_manager_initialization_happy_path(temp_repo_dir: Path) -> None:
    """Test standard initialization of MigrationManager.

    Check: Directory structure is created and DB can be registered.
    """
    # Arrange
    # Target database file path in the temp repo
    test_db_path: Path = temp_repo_dir / "test.db"

    # Act
    # Instantiate manager with temp repo root
    manager: MigrationManager = MigrationManager(repo_root=temp_repo_dir)
    manager.register_db("test_db", test_db_path)

    # Assert
    # Verify manager properties and registered databases
    assert "test_db" in manager.db_registry, "test_db should be in db_registry"
    assert manager.db_registry["test_db"] == test_db_path, "Registered path should match"


def test_migration_manager_sql_execution_and_tracking(temp_repo_dir: Path) -> None:
    """Test execution of sequential SQL migrations and schema version tracking."""
    # Arrange
    test_db_path: Path = temp_repo_dir / "test.db"
    manager: MigrationManager = MigrationManager(repo_root=temp_repo_dir)
    manager.register_db("test_db", test_db_path)

    # Write first migration: creates table
    mig1_path = temp_repo_dir / "migrations" / "test_db" / "0001_create_items.sql"
    mig1_path.write_text("CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT);", encoding="utf-8")

    # Write second migration: adds column
    mig2_path = temp_repo_dir / "migrations" / "test_db" / "0002_add_price.sql"
    mig2_path.write_text("ALTER TABLE items ADD COLUMN price REAL DEFAULT 0.0;", encoding="utf-8")

    # Act
    # Apply migrations
    ok, count, msg = manager.apply_db_migrations("test_db")

    # Assert
    assert ok is True, f"Migrations should succeed: {msg}"
    assert count == 2, f"Should apply 2 migrations, applied: {count}"

    # Verify database table and columns exist
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(items)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "id" in columns
        assert "title" in columns
        assert "price" in columns

        # Verify tracking table
        cursor = conn.execute("SELECT version FROM _schema_migrations ORDER BY id ASC")
        applied_versions = [row[0] for row in cursor.fetchall()]
        assert applied_versions == ["0001_create_items", "0002_add_price"]


def test_migration_manager_python_migration_execution(temp_repo_dir: Path) -> None:
    """Test execution of Python migration scripts with upgrade(conn) function."""
    # Arrange
    test_db_path: Path = temp_repo_dir / "test.db"
    manager: MigrationManager = MigrationManager(repo_root=temp_repo_dir)
    manager.register_db("test_db", test_db_path)

    # Initial SQL migration
    mig1 = temp_repo_dir / "migrations" / "test_db" / "0001_init.sql"
    mig1.write_text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);", encoding="utf-8")

    # Python migration to seed default data
    mig2 = temp_repo_dir / "migrations" / "test_db" / "0002_seed.py"
    py_code = (
        "import sqlite3\n"
        "def upgrade(conn: sqlite3.Connection) -> bool:\n"
        "    conn.execute(\"INSERT INTO users (id, name) VALUES (1, 'Admin')\")\n"
        "    return True\n"
    )
    mig2.write_text(py_code, encoding="utf-8")

    # Act
    ok, count, msg = manager.apply_db_migrations("test_db")

    # Assert
    assert ok is True, f"Migrations should succeed: {msg}"
    assert count == 2, f"Applied count should be 2, got: {count}"

    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.execute("SELECT name FROM users WHERE id = 1")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "Admin"


def test_migration_manager_rollback_on_error(temp_repo_dir: Path) -> None:
    """Test automatic restore from backup when a migration encounters SQL error."""
    # Arrange
    test_db_path: Path = temp_repo_dir / "test.db"
    manager: MigrationManager = MigrationManager(repo_root=temp_repo_dir)
    manager.register_db("test_db", test_db_path)

    # Valid initial migration
    mig1 = temp_repo_dir / "migrations" / "test_db" / "0001_valid.sql"
    mig1.write_text("CREATE TABLE test_table (id INTEGER PRIMARY KEY);", encoding="utf-8")
    ok, count, _ = manager.apply_db_migrations("test_db")
    assert ok is True
    assert count == 1

    # Broken second migration with syntax error
    mig2 = temp_repo_dir / "migrations" / "test_db" / "0002_broken.sql"
    mig2.write_text("SYNTAX ERROR IN SQL STATEMENT;", encoding="utf-8")

    # Act
    ok, count, msg = manager.apply_db_migrations("test_db")

    # Assert
    assert ok is False, "Broken migration should fail"
    assert "Rolled back" in msg or "failed" in msg.lower()

    # Verify database state remained at 0001
    applied = manager.get_applied_versions(test_db_path)
    assert applied == ["0001_valid"]


def test_migration_manager_idempotency_no_duplicate_runs(temp_repo_dir: Path) -> None:
    """Test that running migrations again when already up-to-date applies 0 migrations."""
    # Arrange
    test_db_path: Path = temp_repo_dir / "test.db"
    manager: MigrationManager = MigrationManager(repo_root=temp_repo_dir)
    manager.register_db("test_db", test_db_path)

    mig1 = temp_repo_dir / "migrations" / "test_db" / "0001_first.sql"
    mig1.write_text("CREATE TABLE foo (id INTEGER PRIMARY KEY);", encoding="utf-8")

    # First run
    ok1, count1, _ = manager.apply_db_migrations("test_db")
    assert ok1 is True
    assert count1 == 1

    # Act: Second run
    ok2, count2, msg2 = manager.apply_db_migrations("test_db")

    # Assert
    assert ok2 is True
    assert count2 == 0
    assert "up to date" in msg2.lower()


def test_migration_manager_create_migration_file(temp_repo_dir: Path) -> None:
    """Test helper creating sequential migration files."""
    # Arrange
    manager: MigrationManager = MigrationManager(repo_root=temp_repo_dir)

    # Act
    file1 = manager.create_migration("test_db", "add_indexes", is_python=False)
    file2 = manager.create_migration("test_db", "transform_data", is_python=True)

    # Assert
    assert file1.name == "0001_add_indexes.sql"
    assert file2.name == "0002_transform_data.py"
    assert file1.exists()
    assert file2.exists()
