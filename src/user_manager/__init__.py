# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User management and authorization system
# =============================================================================
# Description:
#   User account management, role-based access control, permission handling,
#   session management, and comprehensive audit logging for system security.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.user_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
from pathlib import Path
from typing import Dict, List

from src.logger import logger

# =============================================================================
# User management class
# =============================================================================

class UserManager:
    """User management and authorization system.

    Storage of user data, session management,
    access rights verification and activity logging.

    Attributes:
        db_path (Path): Path to database file.
    """

    def __init__(self, db_path: Path) -> None:
        """Initialization of user manager.

        Args:
            db_path (Path): Path to SQLite database file.
        """
        self.db_path: Path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialization of user management table schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Create users table for authorized user management
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
                    role TEXT DEFAULT 'user'
                )
            """)

            # Add new columns for Telegram
            try:
                conn.execute("ALTER TABLE users ADD COLUMN telegram_id INTEGER")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE users ADD COLUMN telegram_username TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id) WHERE telegram_id IS NOT NULL")
            except sqlite3.OperationalError:
                pass

            # Add new columns for email authorization
            try:
                conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE users ADD COLUMN is_email_verified INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            # Create user settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'dark',
                    language TEXT DEFAULT 'ru',
                    tts_enabled INTEGER DEFAULT 1,
                    system_instruction TEXT,
                    tts_system TEXT DEFAULT 'edge-tts',
                    tts_voice TEXT DEFAULT 'ru-RU-DmitryNeural',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            try:
                conn.execute("ALTER TABLE user_settings ADD COLUMN model TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE user_settings ADD COLUMN tts_system TEXT DEFAULT 'edge-tts'")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE user_settings ADD COLUMN tts_voice TEXT DEFAULT 'ru-RU-DmitryNeural'")
            except sqlite3.OperationalError:
                pass

            # Create temporary tokens table for Telegram linking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telegram_link_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create Google OAuth tokens table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS google_oauth_tokens (
                    user_id INTEGER PRIMARY KEY,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at TEXT,
                    scope TEXT,
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create email verification codes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_verification_tokens (
                    email TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            # Create index for fast email lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """)

            # Create session tokens table for active session management
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT DEFAULT (datetime('now')),
                    expires_at TEXT NOT NULL,
                    is_revoked INTEGER DEFAULT 0,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create index for token hash lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_token_hash ON session_tokens(token_hash)
            """)

            # Create user activity log table for activity logging
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TEXT DEFAULT (datetime('now')),
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create index for fast user and time lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_user_time ON user_activity_log(user_id, timestamp)
            """)

            # Create roles table for role and permission management
            conn.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    permissions TEXT
                )
            """)

            # Create user-role association table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
            """)

            # Create permission grants table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS permission_grants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grantee_id INTEGER NOT NULL,
                    grant_type TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id INTEGER,
                    permission TEXT NOT NULL,
                    granted_at TEXT DEFAULT (datetime('now')),
                    granted_by INTEGER,
                    FOREIGN KEY (grantee_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (granted_by) REFERENCES users(id)
                )
            """)

            # Create index for fast grantee lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_permission_grants_grantee ON permission_grants(grantee_id)
            """)

            # Create audit log table for important operations audit
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    ip_address TEXT,
                    timestamp TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create index for fast timestamp lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)
            """)

            # Create permissions table for storing available permissions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    category TEXT
                )
            """)

            # Insert default roles
            initial_roles = [
                ('admin', 'System Administrator', '{"all": true}'),
                ('user', 'Regular User', '{"read": true, "chat": true, "media": true}'),
                ('guest', 'Guest', '{"read": true, "chat": false, "media": false}')
            ]
            for role_name, role_desc, role_perms in initial_roles:
                conn.execute(
                    'INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?, ?, ?)',
                    (role_name, role_desc, role_perms)
                )

            # Insert default permissions
            initial_permissions = [
                ('read', 'Data read access', 'basic'),
                ('write', 'Data write access', 'basic'),
                ('delete', 'Data deletion access', 'admin'),
                ('admin', 'System administration', 'admin'),
                ('chat', 'Chat access', 'chat'),
                ('media', 'Media access', 'media'),
                ('qbt', 'qBittorrent access', 'tools'),
                ('media_organizer', 'Media organizer access', 'tools')
            ]
            for perm_name, perm_desc, perm_cat in initial_permissions:
                conn.execute(
                    'INSERT OR IGNORE INTO permissions (name, description, category) VALUES (?, ?, ?)',
                    (perm_name, perm_desc, perm_cat)
                )

            # Insert default administrator (ID: 1) for local bypass
            conn.execute("""
                INSERT OR IGNORE INTO users (id, email, name, is_admin, role)
                VALUES (1, 'admin@localhost', 'Admin', 1, 'admin')
            """)

    def _get_connection(self) -> sqlite3.Connection:
        """Obtaining database connection.

        Returns:
            sqlite3.Connection: Connection to SQLite.
        """
        return sqlite3.connect(self.db_path)

    def add_user(self, email: str, name: str, picture: str = '', role: str = 'user') -> int:
        """Adding a new user.

        Args:
            email (str): User email (unique).
            name (str): User name.
            picture (str): User avatar URL.
            role (str): User role ('admin', 'user', 'guest').

        Returns:
            int: Added user ID or 0 on error.
        """
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    '''
                    INSERT INTO users (email, name, picture, role)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (email, name, picture, role)
                )
                conn.commit()
                logger.info(f'New user added: {email} (ID: {cursor.lastrowid})')
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.error(f'User with email {email} already exists')
                return 0

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user data.

        Args:
            user_id (int): User ID.
            **kwargs: Fields to update (name, picture, role, is_active, is_admin, email, is_email_verified, password_hash, telegram_id, telegram_username).

        Returns:
            bool: True on success, False on error.
        """
        allowed_fields = {
            'name', 'picture', 'role', 'is_active', 'is_admin',
            'last_login', 'email', 'is_email_verified', 'password_hash',
            'telegram_id', 'telegram_username'
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ', '.join(f'{k} = ?' for k in updates.keys())
        values = list(updates.values()) + [user_id]

        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    f'UPDATE users SET {set_clause} WHERE id = ?',
                    values
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f'Error updating user {user_id}:', e, False)
                return False

    def create_user_admin(
        self,
        email: str,
        name: str,
        password: str = '',
        role: str = 'user',
        is_admin: int = 0,
        is_active: int = 1,
        is_email_verified: int = 1
    ) -> int:
        """Creating user by administrator.

        Args:
            email (str): User email.
            name (str): User name.
            password (str): Password (optional).
            role (str): Role ('admin', 'user', 'guest').
            is_admin (int): Administrator flag (0 or 1).
            is_active (int): Activity flag (0 or 1).
            is_email_verified (int): Email verification flag (0 or 1).

        Returns:
            int: Created user ID or 0 on error.
        """
        email_clean = email.lower().strip()
        pw_hash = self.hash_password(password) if password else ''
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    '''
                    INSERT INTO users (email, name, password_hash, role, is_admin, is_active, is_email_verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (email_clean, name, pw_hash, role, is_admin, is_active, is_email_verified)
                )
                conn.commit()
                user_id = cursor.lastrowid or 0
                logger.info(f'New user created: {email_clean} (ID: {user_id})')
                return user_id
            except sqlite3.IntegrityError:
                logger.error(f'User with email {email_clean} already exists')
                return 0
            except Exception as e:
                logger.error(f'Error creating user {email_clean}:', e, False)
                return 0

    def set_user_password(self, user_id: int, password: str) -> bool:
        """Setting new password for user.

        Args:
            user_id (int): User ID.
            password (str): New password in plain text.

        Returns:
            bool: True on success, False on error.
        """
        if not password:
            return False
        pw_hash = self.hash_password(password)
        return self.update_user(user_id, password_hash=pw_hash)

    def get_user_by_id(self, user_id: int) -> Dict:
        """Getting user by ID.

        Args:
            user_id (int): User ID.

        Returns:
            Dict: User data or empty dictionary.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM users WHERE id = ? LIMIT 1',
                (user_id,)
            ).fetchone()
            return dict(row) if row else {}

    def get_user_by_email(self, email: str) -> Dict:
        """Getting user by email.

        Args:
            email (str): User email.

        Returns:
            Dict: User data or empty dictionary.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM users WHERE email = ? LIMIT 1',
                (email,)
            ).fetchone()
            return dict(row) if row else {}

    def get_all_users(self, active_only: bool = True) -> List[Dict]:
        """Getting all users.

        Args:
            active_only (bool): Filter only active users.

        Returns:
            List[Dict]: List of users.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            if active_only:
                rows = conn.execute(
                    'SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC'
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT * FROM users ORDER BY created_at DESC'
                ).fetchall()
            return [dict(r) for r in rows]

    def delete_user(self, user_id: int) -> bool:
        """Deleting user.

        Args:
            user_id (int): User ID.

        Returns:
            bool: True on success, False on error.
        """
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    'DELETE FROM users WHERE id = ?',
                    (user_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f'Error deleting user {user_id}:', e, False)
                return False

    def user_exists(self, email: str) -> bool:
        """Checking user existence.

        Args:
            email (str): User email.

        Returns:
            bool: True if user exists.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT 1 FROM users WHERE email = ?',
                (email,)
            ).fetchone()
            return row is not None

    def is_user_active(self, user_id: int) -> bool:
        """Checking user activity.

        Args:
            user_id (int): User ID.

        Returns:
            bool: True if user is active.
        """
        user = self.get_user_by_id(user_id)
        return bool(user.get('is_active', 0))

    def is_admin(self, user_id: int) -> bool:
        """Checking administrator rights.

        Args:
            user_id (int): User ID.

        Returns:
            bool: True if user is administrator.
        """
        user = self.get_user_by_id(user_id)
        return bool(user.get('is_admin', 0))

    def get_user_role(self, user_id: int) -> str:
        """Getting user role.

        Args:
            user_id (int): User ID.

        Returns:
            str: Role name or 'user' by default.
        """
        user = self.get_user_by_id(user_id)
        return user.get('role', 'user')

    def set_user_role(self, user_id: int, role: str) -> bool:
        """Setting user role.

        Args:
            user_id (int): User ID.
            role (str): Role name ('admin', 'user', 'guest').

        Returns:
            bool: True on success.
        """
        return self.update_user(user_id, role=role)

    def revoke_session(self, token_hash: str) -> bool:
        """Revoking session by token hash.

        Args:
            token_hash (str): Token hash to revoke.

        Returns:
            bool: True on success.
        """
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    'UPDATE session_tokens SET is_revoked = 1 WHERE token_hash = ?',
                    (token_hash,)
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error('Error revoking session:', e, False)
                return False

    def create_session_token(self, user_id: int, token_hash: str, expires_at: str, ip_address: str = '', user_agent: str = '') -> bool:
        """Creating new session.

        Args:
            user_id (int): User ID.
            token_hash (str): Token hash.
            expires_at (str): Expiration date.
            ip_address (str): User IP address.
            user_agent (str): Browser User-Agent.

        Returns:
            bool: True on success.
        """
        with self._get_connection() as conn:
            try:
                conn.execute(
                    '''
                    INSERT INTO session_tokens (user_id, token_hash, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (user_id, token_hash, expires_at, ip_address, user_agent)
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error('Error creating session:', e, False)
                return False

    def is_session_valid(self, token_hash: str) -> bool:
        """Checking session validity.

        Args:
            token_hash (str): Token hash.

        Returns:
            bool: True if session is valid.
        """
        with self._get_connection() as conn:
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            row = conn.execute(
                '''
                SELECT 1 FROM session_tokens
                WHERE token_hash = ?
                  AND is_revoked = 0
                  AND expires_at > ?
                ''',
                (token_hash, now)
            ).fetchone()
            return row is not None

    def log_user_activity(self, user_id: int, action: str, ip_address: str = '', user_agent: str = '', details: str = '') -> bool:
        """Logging user activity.

        Args:
            user_id (int): User ID.
            action (str): Action (login, logout, api_call, etc).
            ip_address (str): IP address.
            user_agent (str): User-Agent.
            details (str): Additional details.

        Returns:
            bool: True on success.
        """
        with self._get_connection() as conn:
            try:
                conn.execute(
                    '''
                    INSERT INTO user_activity_log (user_id, action, ip_address, user_agent, details)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (user_id, action, ip_address, user_agent, details)
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error('Error logging activity:', e, False)
                return False

    def log_audit(self, user_id: int, action: str, target_type: str = '', target_id: int = 0, old_values: str = '', new_values: str = '', ip_address: str = '') -> bool:
        """Logging audit of important operations.

        Args:
            user_id (int): User ID.
            action (str): Action.
            target_type (str): Target object type.
            target_id (int): Target object ID.
            old_values (str): Old values (JSON).
            new_values (str): New values (JSON).
            ip_address (str): IP address.

        Returns:
            bool: True on success.
        """
        with self._get_connection() as conn:
            try:
                conn.execute(
                    '''
                    INSERT INTO audit_log (user_id, action, target_type, target_id, old_values, new_values, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (user_id, action, target_type, target_id, old_values, new_values, ip_address)
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error('Error auditing:', e, False)
                return False

    def has_permission(self, user_id: int, permission: str) -> bool:
        """Checking permission presence for user.

        Args:
            user_id (int): User ID.
            permission (str): Permission name.

        Returns:
            bool: True if user has permission.
        """
        # Administrators have all permissions
        if self.is_admin(user_id):
            return True

        with self._get_connection() as conn:
            # Check through permission_grants
            row = conn.execute(
                '''
                SELECT 1 FROM permission_grants
                WHERE grantee_id = ?
                  AND grant_type = 'user'
                  AND permission = ?
                ''',
                (user_id, permission)
            ).fetchone()
            if row:
                return True

            # Check through roles
            row = conn.execute(
                '''
                SELECT r.permissions FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
                  AND r.permissions IS NOT NULL
                ''',
                (user_id,)
            ).fetchone()
            if row:
                try:
                    import json
                    perms = json.loads(row[0])
                    return perms.get(permission, False)
                except json.JSONDecodeError:
                    pass

            return False

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Getting list of user permissions.

        Args:
            user_id (int): User ID.

        Returns:
            List[str]: List of permissions.
        """
        permissions = []

        # Administrators have all permissions
        if self.is_admin(user_id):
            with self._get_connection() as conn:
                rows = conn.execute('SELECT name FROM permissions').fetchall()
                return [r['name'] for r in rows]

        with self._get_connection() as conn:
            # Getting permissions through permission_grants
            rows = conn.execute(
                'SELECT permission FROM permission_grants WHERE grantee_id = ? AND grant_type = ?',
                (user_id, 'user')
            ).fetchall()
            permissions.extend([r['permission'] for r in rows])

            # Getting permissions through roles
            rows = conn.execute(
                '''
                SELECT r.permissions FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
                ''',
                (user_id,)
            ).fetchall()
            for row in rows:
                try:
                    import json
                    perms = json.loads(row[0])
                    permissions.extend(perms.keys())
                except json.JSONDecodeError:
                    pass

        return list(set(permissions))

    def get_user_by_telegram_id(self, telegram_id: int) -> Dict:
        """Getting user by telegram_id."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM users WHERE telegram_id = ? LIMIT 1',
                (telegram_id,)
            ).fetchone()
            return dict(row) if row else {}

    def get_user_settings(self, user_id: int) -> Dict:
        """Getting user settings."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM user_settings WHERE user_id = ? LIMIT 1',
                (user_id,)
            ).fetchone()
            if not row:
                try:
                    conn.execute(
                        'INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)',
                        (user_id,)
                    )
                    conn.commit()
                except Exception as e:
                    logger.error(f'Error inserting default settings for {user_id}:', e, False)
                row = conn.execute(
                    'SELECT * FROM user_settings WHERE user_id = ? LIMIT 1',
                    (user_id,)
                ).fetchone()
            return dict(row) if row else {'user_id': user_id, 'theme': 'dark', 'language': 'ru', 'tts_enabled': 1, 'system_instruction': None, 'model': None, 'tts_system': 'edge-tts', 'tts_voice': 'ru-RU-DmitryNeural'}

    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Update user settings."""
        allowed_fields = {'theme', 'language', 'tts_enabled', 'system_instruction', 'model', 'tts_system', 'tts_voice'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        if not updates:
            return False
        set_clause = ', '.join(f'{k} = ?' for k in updates.keys())
        values = list(updates.values()) + [user_id]
        with self._get_connection() as conn:
            try:
                conn.execute(
                    f'UPDATE user_settings SET {set_clause} WHERE user_id = ?',
                    values
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error(f'Error updating settings {user_id}:', e, False)
                return False

    def generate_link_token(self, user_id: int) -> str:
        """Generating temporary token for Telegram linking."""
        import secrets
        from datetime import datetime, timedelta
        token = secrets.token_hex(4).upper()  # 8-character code, e.g. AB12CD34
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO telegram_link_tokens (token, user_id, expires_at) VALUES (?, ?, ?)',
                (token, user_id, expires_at)
            )
            conn.commit()
        return token

    def link_telegram_account(self, token: str, telegram_id: int, telegram_username: str) -> bool:
        """Linking Telegram account by token."""
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        token = token.strip().upper()
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT user_id FROM telegram_link_tokens WHERE token = ? AND expires_at > ? LIMIT 1',
                (token, now)
            ).fetchone()
            if not row:
                return False
            user_id = row[0]
            try:
                # Delete temporary telegram user if it was auto-created
                conn.execute(
                    'DELETE FROM users WHERE telegram_id = ? AND email = ?',
                    (telegram_id, f"tg_{telegram_id}@telegram.bot")
                )
                # Clear telegram_id from any other records
                conn.execute(
                    'UPDATE users SET telegram_id = NULL, telegram_username = NULL WHERE telegram_id = ?',
                    (telegram_id,)
                )
                # Bind telegram_id to target user
                conn.execute(
                    'UPDATE users SET telegram_id = ?, telegram_username = ? WHERE id = ?',
                    (telegram_id, telegram_username, user_id)
                )
                conn.execute('DELETE FROM telegram_link_tokens WHERE token = ?', (token,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f'Error linking account {user_id}:', e, False)
                return False

    @staticmethod
    def hash_password(password: str) -> str:
        """Password hashing using PBKDF2."""
        import hashlib
        import os
        salt = os.urandom(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + '$' + pw_hash.hex()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Checking password against hash."""
        if not hashed or '$' not in hashed:
            return False
        import hashlib
        try:
            salt_hex, hash_hex = hashed.split('$', 1)
            salt = bytes.fromhex(salt_hex)
            pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return pw_hash.hex() == hash_hex
        except Exception:
            return False

    def register_email_user(self, email: str, password: str, name: str) -> int:
        """Registering new user with email/password.
        If user already exists (for example, created via Google),
        we update password and name, but don't change email_verified
        if it is not confirmed.
        """
        email = email.lower().strip()
        pw_hash = self.hash_password(password)
        db_user = self.get_user_by_email(email)
        
        with self._get_connection() as conn:
            if db_user:
                # Update existing account
                try:
                    conn.execute(
                        'UPDATE users SET name = ?, password_hash = ? WHERE id = ?',
                        (name, pw_hash, db_user['id'])
                    )
                    conn.commit()
                    return db_user['id']
                except Exception as e:
                    logger.error(f'Error updating during registration {email}:', e, False)
                    return 0
            else:
                # Create new account (unverified)
                try:
                    cursor = conn.execute(
                        '''
                        INSERT INTO users (email, name, password_hash, is_email_verified)
                        VALUES (?, ?, ?, 0)
                        ''',
                        (email, name, pw_hash)
                    )
                    conn.commit()
                    return cursor.lastrowid
                except sqlite3.IntegrityError:
                    return 0

    def create_email_verification(self, email: str) -> str:
        """Creating 6-digit email verification code."""
        import random
        from datetime import datetime, timedelta
        email = email.lower().strip()
        code = f"{random.randint(100000, 999999)}"
        expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        
        with self._get_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO email_verification_tokens (email, code, expires_at) VALUES (?, ?, ?)',
                (email, code, expires_at)
            )
            conn.commit()
        return code

    def verify_email_code(self, email: str, code: str) -> bool:
        """Checking email verification code."""
        from datetime import datetime
        email = email.lower().strip()
        code = code.strip()
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT 1 FROM email_verification_tokens WHERE email = ? AND code = ? AND expires_at > ?',
                (email, code, now)
            ).fetchone()
            if not row:
                return False
            
            # Verify user email
            conn.execute(
                'UPDATE users SET is_email_verified = 1 WHERE email = ?',
                (email,)
            )
            # Delete used token
            conn.execute(
                'DELETE FROM email_verification_tokens WHERE email = ?',
                (email,)
            )
            conn.commit()
            return True

    def save_google_tokens(self, user_id: int, access_token: str, refresh_token: str = '', expires_in: int = 3600, scope: str = '') -> bool:
        """Saving or updating Google OAuth tokens.

        Args:
            user_id: User identifier.
            access_token: Google access token.
            refresh_token: Google refresh token.
            expires_in: Token lifetime in seconds.
            scope: List of scopes.

        Returns:
            bool: True on successful save.
        """
        from datetime import datetime, timedelta
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            try:
                if not refresh_token:
                    existing = conn.execute(
                        'SELECT refresh_token FROM google_oauth_tokens WHERE user_id = ?',
                        (user_id,)
                    ).fetchone()
                    if existing and existing[0]:
                        refresh_token = existing[0]

                conn.execute(
                    '''
                    INSERT INTO google_oauth_tokens (user_id, access_token, refresh_token, expires_at, scope, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        access_token = excluded.access_token,
                        refresh_token = CASE WHEN excluded.refresh_token != '' THEN excluded.refresh_token ELSE google_oauth_tokens.refresh_token END,
                        expires_at = excluded.expires_at,
                        scope = excluded.scope,
                        updated_at = excluded.updated_at
                    ''',
                    (user_id, access_token, refresh_token, expires_at, scope, now)
                )
                conn.commit()
                logger.info(f'Google OAuth tokens saved for user ID={user_id}')
                return True
            except Exception as e:
                logger.error(f'Error saving Google OAuth tokens for user_id={user_id}:', e, False)
                return False

    def get_google_tokens(self, user_id: int) -> dict:
        """Getting user Google OAuth tokens.

        Args:
            user_id: User identifier.

        Returns:
            dict: Dictionary with token data or empty dictionary.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM google_oauth_tokens WHERE user_id = ? LIMIT 1',
                (user_id,)
            ).fetchone()
            return dict(row) if row else {}

    def has_google_auth(self, user_id: int) -> bool:
        """Checking presence of Google OAuth tokens for user.

        Args:
            user_id: User identifier.

        Returns:
            bool: True if user has Google token.
        """
        tokens = self.get_google_tokens(user_id)
        return bool(tokens and tokens.get('access_token'))

from header import __root__
db_path = __root__ / 'core' / 'user_manager' / 'users.db'
user_manager = UserManager(db_path)
