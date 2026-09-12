# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SQLite Database Schema Migration Manager
# =============================================================================
# Description:
#   Automatic schema discovery, backup creation, version tracking, and transactional
#   execution of SQL and Python migration scripts across project SQLite databases.
#
# Examples:
#   >>> from src.db.migrations import MigrationManager
#   >>> manager = MigrationManager()
#   >>> manager.apply_all_pending()
#
# File: migrations.py
# Project: ai-breadboard
# Package: src.db
# Module: Core
# Class: MigrationManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from header import __root__
from src.logger import logger


class MigrationManager:
    """Manages SQLite database schema migrations and automatic upgrades.

    Handles tracking applied versions, creating pre-migration database backups,
    discovering pending migration scripts (.sql and .py), and executing migrations
    within transactional boundaries.

    Attributes:
        repo_root (Path): Root directory of the repository.
        migrations_dir (Path): Base directory containing migration subdirectories per DB.
        db_registry (Dict[str, Path]): Mapping of logical DB names to file paths.
    """

    def __init__(self, repo_root: Optional[Path] = Path('')) -> None:
        """Initialize migration manager with repository paths and DB registry.

        Args:
            repo_root (Optional[Path]): Root directory path. Defaults to __root__.
        """
        self.repo_root: Path = repo_root if (repo_root and str(repo_root) != '') else __root__
        self.migrations_dir: Path = self.repo_root / 'migrations'
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.db_registry: Dict[str, Path] = {
            'users': self.repo_root / 'src' / 'user_manager' / 'users.db',
        }

    def register_db(self, name: str, path: Path) -> None:
        """Register a database to be managed by the migration manager.

        Args:
            name (str): Logical identifier for the database.
            path (Path): Path to the SQLite database file.
        """
        self.db_registry[name] = path

    def _ensure_migrations_table(self, conn: sqlite3.Connection) -> None:
        """Ensure tracking table exists in the target SQLite database.

        Args:
            conn (sqlite3.Connection): Open SQLite database connection.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for a migration file.

        Args:
            file_path (Path): Path to the migration script.

        Returns:
            str: Hexadecimal SHA256 checksum string.
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_applied_versions(self, db_path: Path) -> List[str]:
        """Retrieve list of migration versions already applied to the database.

        Args:
            db_path (Path): Path to the SQLite database file.

        Returns:
            List[str]: List of applied migration version identifiers.
        """
        if not db_path.exists():
            return []

        try:
            with sqlite3.connect(db_path) as conn:
                self._ensure_migrations_table(conn)
                cursor = conn.execute("SELECT version FROM _schema_migrations ORDER BY id ASC")
                return [row[0] for row in cursor.fetchall()]
        except Exception as ex:
            logger.error(f"Failed to read applied migrations from {db_path}: {ex}")
            return []

    def get_available_migrations(self, db_name: str) -> List[Path]:
        """Get sorted list of available migration files for a given database.

        Args:
            db_name (str): Logical database name corresponding to migrations subfolder.

        Returns:
            List[Path]: Sorted list of migration file paths.
        """
        db_migrations_dir = self.migrations_dir / db_name
        if not db_migrations_dir.exists():
            return []

        files = [
            p for p in db_migrations_dir.iterdir()
            if p.is_file() and (p.suffix in ('.sql', '.py')) and not p.name.startswith(('.', '_'))
        ]
        return sorted(files, key=lambda x: x.name)

    def create_backup(self, db_path: Path) -> Optional[Path]:
        """Create timestamped backup copy of a database before migration.

        Args:
            db_path (Path): Path to the SQLite database file.

        Returns:
            Optional[Path]: Path to the created backup file, or None if DB does not exist.
        """
        if not db_path.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_path = db_path.parent / f"{db_path.name}.backup_{timestamp}"
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as ex:
            logger.error(f"Failed to create database backup for {db_path}: {ex}")
            return None

    def restore_backup(self, db_path: Path, backup_path: Path) -> bool:
        """Restore database file from backup in case of migration failure.

        Args:
            db_path (Path): Target database file path.
            backup_path (Path): Path to backup file.

        Returns:
            bool: True if restored successfully, False otherwise.
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file does not exist: {backup_path}")
                return False
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database {db_path} restored from backup {backup_path}")
            return True
        except Exception as ex:
            logger.error(f"Failed to restore database from backup {backup_path}: {ex}")
            return False

    def _execute_sql_migration(self, conn: sqlite3.Connection, file_path: Path) -> bool:
        """Execute plain SQL migration script.

        Args:
            conn (sqlite3.Connection): Open SQLite connection.
            file_path (Path): Path to SQL script.

        Returns:
            bool: True if executed successfully, False otherwise.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        conn.executescript(sql_content)
        return True

    def _execute_py_migration(self, conn: sqlite3.Connection, file_path: Path) -> bool:
        """Execute Python migration script with an upgrade(conn) function.

        Args:
            conn (sqlite3.Connection): Open SQLite connection.
            file_path (Path): Path to Python script.

        Returns:
            bool: True if upgrade succeeded, False otherwise.
        """
        module_name = f"migration_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            logger.error(f"Could not load python migration module: {file_path}")
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, 'upgrade'):
            logger.error(f"Migration script {file_path} lacks required 'upgrade(conn)' function")
            return False

        upgrade_fn = getattr(module, 'upgrade')
        result = upgrade_fn(conn)
        return result is not False

    def apply_migration_file(self, db_path: Path, file_path: Path) -> bool:
        """Apply a single migration file to the specified database.

        Args:
            db_path (Path): Path to SQLite database.
            file_path (Path): Path to migration script.

        Returns:
            bool: True on success, False on error.
        """
        version = file_path.stem
        checksum = self._calculate_checksum(file_path)

        db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(db_path) as conn:
            self._ensure_migrations_table(conn)
            cursor = conn.execute("SELECT 1 FROM _schema_migrations WHERE version = ?", (version,))
            if cursor.fetchone():
                logger.debug(f"Migration {version} already applied to {db_path.name}")
                return True

            try:
                conn.execute("BEGIN TRANSACTION")
                if file_path.suffix == '.sql':
                    self._execute_sql_migration(conn, file_path)
                elif file_path.suffix == '.py':
                    self._execute_py_migration(conn, file_path)
                else:
                    logger.warning(f"Unsupported migration file format: {file_path.suffix}")
                    conn.rollback()
                    return False

                conn.execute(
                    "INSERT INTO _schema_migrations (version, filename, checksum) VALUES (?, ?, ?)",
                    (version, file_path.name, checksum)
                )
                conn.commit()
                logger.info(f"Successfully applied migration {file_path.name} to {db_path.name}")
                return True
            except Exception as ex:
                conn.rollback()
                logger.error(f"Failed to apply migration {file_path.name} to {db_path.name}: {ex}")
                return False

    def apply_db_migrations(self, db_name: str) -> Tuple[bool, int, str]:
        """Apply all pending migrations for a specific registered database.

        Args:
            db_name (str): Logical name of database.

        Returns:
            Tuple[bool, int, str]: (Success status, number of applied migrations, status message).
        """
        if db_name not in self.db_registry:
            msg = f"Database '{db_name}' not registered"
            logger.warning(msg)
            return False, 0, msg

        db_path = self.db_registry[db_name]
        available = self.get_available_migrations(db_name)
        applied = set(self.get_applied_versions(db_path))

        pending = [p for p in available if p.stem not in applied]
        if not pending:
            return True, 0, f"Database '{db_name}' is up to date"

        logger.info(f"Found {len(pending)} pending migrations for '{db_name}'")
        backup_path = self.create_backup(db_path)

        applied_count = 0
        for migration_file in pending:
            success = self.apply_migration_file(db_path, migration_file)
            if not success:
                if backup_path:
                    self.restore_backup(db_path, backup_path)
                msg = f"Migration failed on {migration_file.name}. Rolled back."
                logger.error(msg)
                return False, applied_count, msg
            applied_count += 1

        return True, applied_count, f"Successfully applied {applied_count} migrations to '{db_name}'"

    def apply_all_pending(self) -> Dict[str, Any]:
        """Apply all pending migrations across all registered databases.

        Returns:
            Dict[str, Any]: Summary dictionary of migration results per database.
        """
        results: Dict[str, Any] = {
            "success": True,
            "applied_total": 0,
            "databases": {}
        }

        for db_name in self.db_registry:
            ok, count, msg = self.apply_db_migrations(db_name)
            results["databases"][db_name] = {
                "success": ok,
                "applied_count": count,
                "message": msg
            }
            results["applied_total"] += count
            if not ok:
                results["success"] = False

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get current migration status for all registered databases.

        Returns:
            Dict[str, Any]: Detailed status report of available vs applied migrations.
        """
        status: Dict[str, Any] = {}
        for db_name, db_path in self.db_registry.items():
            available = self.get_available_migrations(db_name)
            applied = self.get_applied_versions(db_path)
            applied_set = set(applied)
            pending = [p.name for p in available if p.stem not in applied_set]

            status[db_name] = {
                "db_path": str(db_path),
                "db_exists": db_path.exists(),
                "applied_count": len(applied),
                "available_count": len(available),
                "pending_count": len(pending),
                "pending_migrations": pending,
                "is_up_to_date": len(pending) == 0
            }
        return status

    def create_migration(self, db_name: str, name: str, is_python: bool = False) -> Path:
        """Generate a new migration template file.

        Args:
            db_name (str): Logical database name.
            name (str): Short description of migration.
            is_python (bool): If True, creates .py migration instead of .sql.

        Returns:
            Path: Path to created migration file.
        """
        db_migrations_dir = self.migrations_dir / db_name
        db_migrations_dir.mkdir(parents=True, exist_ok=True)

        existing = self.get_available_migrations(db_name)
        next_seq = 1
        if existing:
            last_name = existing[-1].stem
            prefix = last_name.split('_')[0]
            if prefix.isdigit():
                next_seq = int(prefix) + 1

        clean_name = "".join(c if c.isalnum() or c == '_' else '_' for c in name.lower().strip())
        file_name = f"{next_seq:04d}_{clean_name}" + ('.py' if is_python else '.sql')
        target_path = db_migrations_dir / file_name

        if is_python:
            template = (
                "# -*- coding: utf-8 -*-\n"
                "import sqlite3\n\n"
                "def upgrade(conn: sqlite3.Connection) -> bool:\n"
                "    \"\"\"Execute migration operations.\n\n"
                "    Args:\n"
                "        conn: Active SQLite connection within transaction.\n\n"
                "    Returns:\n"
                "        bool: True on success.\n"
                "    \"\"\"\n"
                "    # conn.execute(\"ALTER TABLE ...\")\n"
                "    return True\n"
            )
        else:
            template = (
                "-- Migration: " + file_name + "\n"
                "-- Created: " + datetime.now().isoformat() + "\n\n"
                "-- Write your SQL statements below:\n"
            )

        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(template)

        logger.info(f"Created new migration file: {target_path}")
        return target_path


_global_migration_manager: Optional[MigrationManager] = None


def get_migration_manager(repo_root: Optional[Path] = Path('')) -> MigrationManager:
    """Obtain singleton instance of MigrationManager.

    Args:
        repo_root (Optional[Path]): Root directory path.

    Returns:
        MigrationManager: Shared migration manager instance.
    """
    global _global_migration_manager
    if _global_migration_manager is None:
        _global_migration_manager = MigrationManager(repo_root)
    return _global_migration_manager


def main() -> int:
    """CLI entry point for running database migrations."""
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    parser.add_argument('--apply', action='store_true', help="Apply all pending migrations")
    parser.add_argument('--status', action='store_true', help="Check migration status")
    parser.add_argument('--create', type=str, help="Create a new migration for a DB")
    parser.add_argument('--db', type=str, default='users', help="Target database name")
    parser.add_argument('--py', action='store_true', help="Create python migration instead of SQL")

    args = parser.parse_args()
    mgr = get_migration_manager()

    if args.create:
        path = mgr.create_migration(args.db, args.create, is_python=args.py)
        print(f"Created migration: {path}")
        return 0

    if args.status or not args.apply:
        status = mgr.get_status()
        print("\n--- DATABASE MIGRATION STATUS ---")
        for db, info in status.items():
            print(f"[{db}] Up-to-date: {info['is_up_to_date']} | Applied: {info['applied_count']} | Pending: {info['pending_count']}")
            if info['pending_migrations']:
                print(f"  Pending: {', '.join(info['pending_migrations'])}")
        print("---------------------------------\n")
        if not args.apply:
            return 0

    if args.apply:
        print("Applying pending database migrations...")
        result = mgr.apply_all_pending()
        for db, res in result['databases'].items():
            status_tag = "[OK]" if res['success'] else "[ERROR]"
            print(f"  {status_tag} {db}: {res['message']} ({res['applied_count']} applied)")
        return 0 if result['success'] else 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
