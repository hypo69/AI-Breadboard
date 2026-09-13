# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Initial Administrator User Creation Script
# =============================================================================
# Description:
#   Sets up, initializes, or updates the initial administrator user account
#   in the SQLite users database (src/user_manager/users.db). Supports both
#   interactive input and headless/non-interactive configuration.
#
# Usage Examples:
#   python scripts/create_initial_user.py
#   python scripts/create_initial_user.py --non-interactive
#   python scripts/create_initial_user.py --email admin@domain.com --name SuperAdmin --password secret
#
# File: scripts/create_initial_user.py
# Project: AI Breadboard
# Package: Scripts
# Module: Setup
# Class: InitialUserManager
# Function: main
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import getpass
import hashlib
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class InitialUserManager:
    """Manager for setting up and provisioning the initial administrator account."""

    DEFAULT_EMAIL: str = "admin@localhost"
    DEFAULT_NAME: str = "Admin"
    DEFAULT_PASSWORD: str = "onela"

    def __init__(self, db_path: Optional[Path] = Path("")) -> None:
        """Initialize user manager with database location.

        Args:
            db_path (Optional[Path]): Specific path to SQLite database.
        """
        if db_path and str(db_path):
            self.db_path: Path = Path(db_path)
        else:
            self.db_path = PROJECT_ROOT / "src" / "user_manager" / "users.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash plain text password using PBKDF2 with SHA-256 and salt.

        Args:
            password (str): Plain text password.

        Returns:
            str: Salt and hash formatted as 'salt$hash'.
        """
        salt = os.urandom(16)
        pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + "$" + pw_hash.hex()

    def provision_admin_user(
        self,
        email: str = "",
        name: str = "",
        password: str = "",
    ) -> Dict[str, Any]:
        """Provision initial administrator user in the database.

        Updates or creates the administrator account with the given credentials.

        Args:
            email (str): Administrator email address.
            name (str): Administrator full name.
            password (str): Administrator password.

        Returns:
            Dict[str, Any]: Result dictionary containing status, user_id, and message.
        """
        clean_email = (email or self.DEFAULT_EMAIL).lower().strip()
        clean_name = (name or self.DEFAULT_NAME).strip()
        clean_password = password or self.DEFAULT_PASSWORD

        pw_hash = self.hash_password(clean_password)

        try:
            from src.user_manager import UserManager, user_manager as default_mgr
            active_mgr = UserManager(self.db_path) if self.db_path else default_mgr
            db_user = active_mgr.get_user_by_email(clean_email)
            
            if not db_user:
                # Check if user with ID 1 exists
                id1_user = active_mgr.get_user_by_id(1)
                if id1_user:
                    active_mgr.update_user(
                        1,
                        email=clean_email,
                        name=clean_name,
                        password_hash=pw_hash,
                        is_admin=1,
                        is_active=1,
                        is_email_verified=1,
                        role="admin"
                    )
                    user_id = 1
                else:
                    user_id = active_mgr.create_user_admin(
                        email=clean_email,
                        name=clean_name,
                        password=clean_password,
                        role="admin",
                        is_admin=1,
                        is_active=1,
                        is_email_verified=1
                    )
            else:
                user_id = db_user.get("id", 1)
                active_mgr.update_user(
                    user_id,
                    name=clean_name,
                    password_hash=pw_hash,
                    is_admin=1,
                    is_active=1,
                    is_email_verified=1,
                    role="admin"
                )

            return {
                "status": "ok",
                "user_id": user_id,
                "email": clean_email,
                "name": clean_name,
                "message": f"Administrator user '{clean_email}' successfully configured."
            }

        except Exception:
            # Fallback directly to SQLite in case src package is running without full environment
            return self._provision_direct_sqlite(clean_email, clean_name, pw_hash)

    def _provision_direct_sqlite(self, email: str, name: str, pw_hash: str) -> Dict[str, Any]:
        """Direct SQLite fallback provisioning when application imports are unavailable.

        Args:
            email (str): User email.
            name (str): User name.
            pw_hash (str): Hashed password.

        Returns:
            Dict[str, Any]: Result dictionary.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        picture TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        last_login TEXT,
                        is_admin INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        role TEXT DEFAULT 'user',
                        telegram_id INTEGER,
                        telegram_username TEXT,
                        password_hash TEXT,
                        is_email_verified INTEGER DEFAULT 0
                    )
                """)

                cursor = conn.execute("SELECT id FROM users WHERE email = ? OR id = 1 LIMIT 1", (email,))
                row = cursor.fetchone()

                if row:
                    user_id = row[0]
                    conn.execute("""
                        UPDATE users SET
                            email = ?,
                            name = ?,
                            password_hash = ?,
                            is_admin = 1,
                            is_active = 1,
                            is_email_verified = 1,
                            role = 'admin'
                        WHERE id = ?
                    """, (email, name, pw_hash, user_id))
                else:
                    cursor = conn.execute("""
                        INSERT INTO users (id, email, name, password_hash, is_admin, is_active, is_email_verified, role)
                        VALUES (1, ?, ?, ?, 1, 1, 1, 'admin')
                    """, (email, name, pw_hash))
                    user_id = cursor.lastrowid or 1

                conn.commit()

            return {
                "status": "ok",
                "user_id": user_id,
                "email": email,
                "name": name,
                "message": f"Administrator user '{email}' provisioned via direct SQLite."
            }
        except Exception as ex:
            return {
                "status": "error",
                "user_id": 0,
                "email": email,
                "name": name,
                "message": f"Failed to provision user: {ex}"
            }


def main() -> int:
    """Main command line entry point.

    Returns:
        int: Exit status code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(description="Create or initialize the default administrator user.")
    parser.add_argument("--email", "-e", default="", help="Administrator email (default: admin@localhost)")
    parser.add_argument("--name", "-n", default="", help="Administrator name (default: Admin)")
    parser.add_argument("--password", "-p", default="", help="Administrator password (default: onela)")
    parser.add_argument("--db-path", default="", help="Path to users.db")
    parser.add_argument("--non-interactive", action="store_true", help="Skip interactive prompts and use defaults")

    args = parser.parse_args()

    email = args.email
    name = args.name
    password = args.password

    non_interactive: bool = getattr(args, "non_interactive", False)

    if not non_interactive and not (args.email and args.password):
        print("\n============================================================")
        print("  AI Breadboard — Initial Administrator Setup")
        print("============================================================")
        
        input_email = input("  Administrator Email [admin@localhost]: ").strip()
        email = input_email if input_email else (email or "admin@localhost")

        input_name = input("  Administrator Name [Admin]: ").strip()
        name = input_name if input_name else (name or "Admin")

        input_pass = getpass.getpass("  Administrator Password [Enter for default 'onela']: ").strip()
        password = input_pass if input_pass else (password or "onela")
        print("============================================================\n")

    manager = InitialUserManager(db_path=Path(args.db_path) if args.db_path else Path(""))
    result = manager.provision_admin_user(email=email, name=name, password=password)

    if result["status"] == "ok":
        print(f"✓ {result['message']}")
        print(f"  Login Email: {result['email']}")
        print(f"  Role: System Administrator (ID: {result['user_id']})")
        return 0
    else:
        print(f"✗ Error: {result['message']}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
