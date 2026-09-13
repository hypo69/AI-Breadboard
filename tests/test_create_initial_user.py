# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for initial user creation script
# =============================================================================
# Description:
#   Validates user creation logic, PBKDF2 password hashing, fallback direct
#   SQLite provisioning, and non-interactive execution.
#
# File: tests/test_create_initial_user.py
# Project: AI Breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.create_initial_user import InitialUserManager
from src.user_manager import user_manager


class TestInitialUserManager:
    """Test suite for InitialUserManager class."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary SQLite database for testing user provisioning."""
        db_file = tmp_path / "test_users.db"
        return db_file

    def test_hash_password(self):
        """Test password hashing using PBKDF2."""
        raw_pw = "secret123"
        hashed = InitialUserManager.hash_password(raw_pw)
        assert "$" in hashed
        salt, pw_hash = hashed.split("$", 1)
        assert len(salt) == 32
        assert len(pw_hash) == 64

    def test_provision_admin_user_custom(self, temp_db):
        """Test creating custom administrator user."""
        manager = InitialUserManager(db_path=temp_db)
        res = manager.provision_admin_user(
            email="custom_admin@test.com",
            name="Custom Administrator",
            password="my_secure_pass"
        )
        assert res["status"] == "ok"
        assert res["email"] == "custom_admin@test.com"

        # Verify DB content
        with sqlite3.connect(temp_db) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE email = ?", ("custom_admin@test.com",)).fetchone()
            assert row is not None
            assert row["name"] == "Custom Administrator"
            assert row["is_admin"] == 1
            assert row["role"] == "admin"
            assert row["is_email_verified"] == 1
            assert row["password_hash"] != ""

    def test_provision_admin_user_default(self, temp_db):
        """Test creating default administrator user."""
        manager = InitialUserManager(db_path=temp_db)
        res = manager.provision_admin_user()
        assert res["status"] == "ok"
        assert res["email"] == "admin@localhost"
        assert res["name"] == "Admin"

        with sqlite3.connect(temp_db) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE email = 'admin@localhost'").fetchone()
            assert row is not None
            assert row["is_admin"] == 1
            assert row["is_active"] == 1

    def test_update_existing_admin_password(self, temp_db):
        """Test updating password of existing user."""
        manager = InitialUserManager(db_path=temp_db)
        manager.provision_admin_user(email="admin@localhost", password="first_pass")
        res2 = manager.provision_admin_user(email="admin@localhost", password="new_pass")
        assert res2["status"] == "ok"

        with sqlite3.connect(temp_db) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE email = 'admin@localhost'").fetchone()
            assert row is not None
            # Verify new password with user_manager
            assert user_manager.verify_password("new_pass", row["password_hash"])
            assert not user_manager.verify_password("first_pass", row["password_hash"])

    def test_cli_execution_non_interactive(self, tmp_path):
        """Test executing create_initial_user.py script via CLI."""
        db_file = tmp_path / "cli_users.db"
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "create_initial_user.py"

        cmd = [
            sys.executable,
            str(script_path),
            "--email", "cli_admin@test.com",
            "--name", "CLI Admin",
            "--password", "cli_pass_123",
            "--db-path", str(db_file),
            "--non-interactive"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0
        assert "successfully configured" in result.stdout or "provisioned" in result.stdout
