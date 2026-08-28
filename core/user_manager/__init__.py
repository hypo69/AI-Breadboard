# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Управление авторизованными пользователями
# =============================================================================
# Описание:
#   Модуль обеспечивает управление авторизованными пользователями системы.
#   Реализует хранение пользовательских данных, управление сессиями, проверку
#   прав доступа, логирование активности и аудит важных операций. Поддерживает
#   email и Telegram авторизацию, системы ролей и разрешений.
#
# File: user_manager.py
# Project: ai-breadboard
# Package: src.user_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
from pathlib import Path
from typing import Dict, List

from core.logger import logger


# =============================================================================
# Класс управления пользователями
# =============================================================================


class UserManager:
    """Управление авторизованными пользователями.

    Хранение пользовательских данных, управление сессиями,
    проверка прав доступа и логирование активности.

    Attributes:
        db_path (Path): Путь к файлу базы данных.
    """

    def __init__(self, db_path: Path) -> None:
        """Инициализация менеджера пользователей.

        Args:
            db_path (Path): Путь к файлу SQLite базы данных.
        """
        self.db_path: Path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Инициализация схемы таблиц управления пользователями."""
        with sqlite3.connect(self.db_path) as conn:
            # Создание таблицы users для управления авторизованными пользователями
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

            # Добавляем новые колонки для телеграма
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

            # Добавляем новые колонки для email авторизации
            try:
                conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE users ADD COLUMN is_email_verified INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            # Создание таблицы настроек пользователя
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


            # Создание таблицы временных токенов линковки Telegram
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telegram_link_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Создание таблицы токенов Google OAuth
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

            # Создание таблицы кодов подтверждения email
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_verification_tokens (
                    email TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            # Создание индекса для быстрого поиска по email
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """)

            # Создание таблицы session_tokens для управления активными сессиями
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

            # Создание индекса для поиска по хешу токена
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_token_hash ON session_tokens(token_hash)
            """)

            # Создание таблицы user_activity_log для логирования активности
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

            # Создание индекса для быстрого поиска по пользователю и времени
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_user_time ON user_activity_log(user_id, timestamp)
            """)

            # Создание таблицы roles для управления ролями и правами
            conn.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    permissions TEXT
                )
            """)

            # Создание таблицы user_roles для связи пользователь-роль
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
            """)

            # Создание таблицы permission_grants для грантов прав
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

            # Создание индекса для быстрого поиска по grantee
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_permission_grants_grantee ON permission_grants(grantee_id)
            """)

            # Создание таблицы audit_log для аудита важных операций
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

            # Создание индекса для быстрого поиска по времени
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)
            """)

            # Создание таблицы permissions для хранения разрешений
            conn.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    category TEXT
                )
            """)

            # Вставка ролей по умолчанию
            initial_roles = [
                ('admin', 'Администратор системы', '{"all": true}'),
                ('user', 'Обычный пользователь', '{"read": true, "chat": true, "media": true}'),
                ('guest', 'Гость', '{"read": true, "chat": false, "media": false}')
            ]
            for role_name, role_desc, role_perms in initial_roles:
                conn.execute(
                    'INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?, ?, ?)',
                    (role_name, role_desc, role_perms)
                )

            # Вставка разрешений по умолчанию
            initial_permissions = [
                ('read', 'Чтение данных', 'basic'),
                ('write', 'Запись данных', 'basic'),
                ('delete', 'Удаление данных', 'admin'),
                ('admin', 'Администрирование', 'admin'),
                ('chat', 'Доступ к чату', 'chat'),
                ('media', 'Доступ к медиа', 'media'),
                ('qbt', 'Доступ к qBittorrent', 'tools'),
                ('media_organizer', 'Доступ к медиа-организатору', 'tools')
            ]
            for perm_name, perm_desc, perm_cat in initial_permissions:
                conn.execute(
                    'INSERT OR IGNORE INTO permissions (name, description, category) VALUES (?, ?, ?)',
                    (perm_name, perm_desc, perm_cat)
                )

            # Вставка администратора по умолчанию (ID: 1) для локального обхода
            conn.execute("""
                INSERT OR IGNORE INTO users (id, email, name, is_admin, role)
                VALUES (1, 'admin@localhost', 'Admin', 1, 'admin')
            """)


    def _get_connection(self) -> sqlite3.Connection:
        """Получение подключения к базе данных.

        Returns:
            sqlite3.Connection: Подключение к SQLite.
        """
        return sqlite3.connect(self.db_path)

    def add_user(self, email: str, name: str, picture: str = '', role: str = 'user') -> int:
        """Добавление нового пользователя.

        Args:
            email (str): Email пользователя (уникальный).
            name (str): Имя пользователя.
            picture (str): URL аватара пользователя.
            role (str): Роль пользователя ('admin', 'user', 'guest').

        Returns:
            int: ID добавленного пользователя или 0 при ошибке.
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
                logger.info(f'Добавлен новый пользователь: {email} (ID: {cursor.lastrowid})')
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.error(f'Пользователь с email {email} уже существует')
                return 0

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Обновление данных пользователя.

        Args:
            user_id (int): ID пользователя.
            **kwargs: Поля для обновления (name, picture, role, is_active, is_admin, email, is_email_verified, password_hash, telegram_id, telegram_username).

        Returns:
            bool: True при успехе, False при ошибке.
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
                logger.error(f'Ошибка обновления пользователя {user_id}:', e, False)
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
        """Создание пользователя администратором.

        Args:
            email (str): Email пользователя.
            name (str): Имя пользователя.
            password (str): Пароль (опционально).
            role (str): Роль ('admin', 'user', 'guest').
            is_admin (int): Флаг администратора (0 или 1).
            is_active (int): Флаг активности (0 или 1).
            is_email_verified (int): Флаг подтверждения email (0 или 1).

        Returns:
            int: ID созданного пользователя или 0 при ошибке.
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
                logger.info(f'Создан новый пользователь: {email_clean} (ID: {user_id})')
                return user_id
            except sqlite3.IntegrityError:
                logger.error(f'Пользователь с email {email_clean} уже существует')
                return 0
            except Exception as e:
                logger.error(f'Ошибка создания пользователя {email_clean}:', e, False)
                return 0

    def set_user_password(self, user_id: int, password: str) -> bool:
        """Установка нового пароля пользователю.

        Args:
            user_id (int): ID пользователя.
            password (str): Новый пароль в открытом виде.

        Returns:
            bool: True при успехе, False при ошибке.
        """
        if not password:
            return False
        pw_hash = self.hash_password(password)
        return self.update_user(user_id, password_hash=pw_hash)

    def get_user_by_id(self, user_id: int) -> Dict:
        """Получение пользователя по ID.

        Args:
            user_id (int): ID пользователя.

        Returns:
            Dict: Данные пользователя или пустой словарь.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM users WHERE id = ? LIMIT 1',
                (user_id,)
            ).fetchone()
            return dict(row) if row else {}

    def get_user_by_email(self, email: str) -> Dict:
        """Получение пользователя по email.

        Args:
            email (str): Email пользователя.

        Returns:
            Dict: Данные пользователя или пустой словарь.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM users WHERE email = ? LIMIT 1',
                (email,)
            ).fetchone()
            return dict(row) if row else {}

    def get_all_users(self, active_only: bool = True) -> List[Dict]:
        """Получение всех пользователей.

        Args:
            active_only (bool): Фильтровать только активных пользователей.

        Returns:
            List[Dict]: Список пользователей.
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
        """Удаление пользователя.

        Args:
            user_id (int): ID пользователя.

        Returns:
            bool: True при успехе, False при ошибке.
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
                logger.error(f'Ошибка у��аления пользователя {user_id}:', e, False)
                return False

    def user_exists(self, email: str) -> bool:
        """Проверка существования пользователя.

        Args:
            email (str): Email пользователя.

        Returns:
            bool: True если пользователь существует.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT 1 FROM users WHERE email = ?',
                (email,)
            ).fetchone()
            return row is not None

    def is_user_active(self, user_id: int) -> bool:
        """Проверка активности пользователя.

        Args:
            user_id (int): ID пользователя.

        Returns:
            bool: True если пользователь активен.
        """
        user = self.get_user_by_id(user_id)
        return bool(user.get('is_active', 0))

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора.

        Args:
            user_id (int): ID пользователя.

        Returns:
            bool: True если пользователь администратор.
        """
        user = self.get_user_by_id(user_id)
        return bool(user.get('is_admin', 0))

    def get_user_role(self, user_id: int) -> str:
        """Получение роли пользователя.

        Args:
            user_id (int): ID пользователя.

        Returns:
            str: Название роли или 'user' по умолчанию.
        """
        user = self.get_user_by_id(user_id)
        return user.get('role', 'user')

    def set_user_role(self, user_id: int, role: str) -> bool:
        """Установка роли пользователя.

        Args:
            user_id (int): ID пользователя.
            role (str): Название роли ('admin', 'user', 'guest').

        Returns:
            bool: True при успехе.
        """
        return self.update_user(user_id, role=role)

    def revoke_session(self, token_hash: str) -> bool:
        """Отзыв сессии по хешу токена.

        Args:
            token_hash (str): Хеш токена для отзыва.

        Returns:
            bool: True при успехе.
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
                logger.error('Ошибка отзыва сессии:', e, False)
                return False

    def create_session_token(self, user_id: int, token_hash: str, expires_at: str, ip_address: str = '', user_agent: str = '') -> bool:
        """Создание новой сессии.

        Args:
            user_id (int): ID пользователя.
            token_hash (str): Хеш токена.
            expires_at (str): Дата истечения срока действия.
            ip_address (str): IP адрес пользователя.
            user_agent (str): User-Agent браузера.

        Returns:
            bool: True при успехе.
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
                logger.error('Ошибка создания сессии:', e, False)
                return False

    def is_session_valid(self, token_hash: str) -> bool:
        """Проверка валидности сессии.

        Args:
            token_hash (str): Хеш токена.

        Returns:
            bool: True если сессия валидна.
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
        """Логирование активности пользователя.

        Args:
            user_id (int): ID пользователя.
            action (str): Действие (login, logout, api_call, etc).
            ip_address (str): IP адрес.
            user_agent (str): User-Agent.
            details (str): Дополнительные детали.

        Returns:
            bool: True при успехе.
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
                logger.error('Ошибка логирования активности:', e, False)
                return False

    def log_audit(self, user_id: int, action: str, target_type: str = '', target_id: int = 0, old_values: str = '', new_values: str = '', ip_address: str = '') -> bool:
        """Логирование аудита важных операций.

        Args:
            user_id (int): ID пользователя.
            action (str): Действие.
            target_type (str): Тип целевого объекта.
            target_id (int): ID целевого объекта.
            old_values (str): Старые значения (JSON).
            new_values (str): Новые значения (JSON).
            ip_address (str): IP адрес.

        Returns:
            bool: True при успехе.
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
                logger.error('Ошибка аудита:', e, False)
                return False

    def has_permission(self, user_id: int, permission: str) -> bool:
        """Проверка наличия разрешения у пользователя.

        Args:
            user_id (int): ID пользователя.
            permission (str): Имя разрешения.

        Returns:
            bool: True если пользователь имеет разрешение.
        """
        # Администраторы имеют все разрешения
        if self.is_admin(user_id):
            return True

        with self._get_connection() as conn:
            # Проверка через permission_grants
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

            # Проверка через роли
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
        """Получение списка разрешений пользователя.

        Args:
            user_id (int): ID пользователя.

        Returns:
            List[str]: Список разрешений.
        """
        permissions = []

        # Администраторы имеют все разрешения
        if self.is_admin(user_id):
            with self._get_connection() as conn:
                rows = conn.execute('SELECT name FROM permissions').fetchall()
                return [r['name'] for r in rows]

        with self._get_connection() as conn:
            # Получение разрешений через permission_grants
            rows = conn.execute(
                'SELECT permission FROM permission_grants WHERE grantee_id = ? AND grant_type = ?',
                (user_id, 'user')
            ).fetchall()
            permissions.extend([r['permission'] for r in rows])

            # Получение разрешений через роли
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
        """Получение пользователя по telegram_id."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM users WHERE telegram_id = ? LIMIT 1',
                (telegram_id,)
            ).fetchone()
            return dict(row) if row else {}

    def get_user_settings(self, user_id: int) -> Dict:
        """Получение настроек пользователя."""
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
                    logger.error(f'Ошибка вставки настроек по умолчанию для {user_id}:', e, False)
                row = conn.execute(
                    'SELECT * FROM user_settings WHERE user_id = ? LIMIT 1',
                    (user_id,)
                ).fetchone()
            return dict(row) if row else {'user_id': user_id, 'theme': 'dark', 'language': 'ru', 'tts_enabled': 1, 'system_instruction': None, 'model': None, 'tts_system': 'edge-tts', 'tts_voice': 'ru-RU-DmitryNeural'}

    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Обновление настроек пользователя."""
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
                logger.error(f'Ошибка обновления настроек {user_id}:', e, False)
                return False

    def generate_link_token(self, user_id: int) -> str:
        """Генерация временного токена линковки Telegram."""
        import secrets
        from datetime import datetime, timedelta
        token = secrets.token_hex(4).upper()  # 8-символьный код, например AB12CD34
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO telegram_link_tokens (token, user_id, expires_at) VALUES (?, ?, ?)',
                (token, user_id, expires_at)
            )
            conn.commit()
        return token

    def link_telegram_account(self, token: str, telegram_id: int, telegram_username: str) -> bool:
        """Связывание Telegram-аккаунта по токену."""
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
                # Удаляем временного telegram-пользователя, если он был автоматически создан
                conn.execute(
                    'DELETE FROM users WHERE telegram_id = ? AND email = ?',
                    (telegram_id, f"tg_{telegram_id}@telegram.bot")
                )
                # Очищаем telegram_id у любых других записей, если они есть
                conn.execute(
                    'UPDATE users SET telegram_id = NULL, telegram_username = NULL WHERE telegram_id = ?',
                    (telegram_id,)
                )
                # Привязываем telegram_id к целевому пользователю
                conn.execute(
                    'UPDATE users SET telegram_id = ?, telegram_username = ? WHERE id = ?',
                    (telegram_id, telegram_username, user_id)
                )
                conn.execute('DELETE FROM telegram_link_tokens WHERE token = ?', (token,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f'Ошибка линковки аккаунта {user_id}:', e, False)
                return False

    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля с использованием PBKDF2."""
        import hashlib
        import os
        salt = os.urandom(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + '$' + pw_hash.hex()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Проверка пароля по его хешу."""
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
        """Регистрация нового пользователя с email/паролем.
        Если пользователь уже существует (например, создан через Google),
        мы обновляем ему пароль и имя, но не меняем его email_verified,
        если он не подтвержден.
        """
        email = email.lower().strip()
        pw_hash = self.hash_password(password)
        db_user = self.get_user_by_email(email)
        
        with self._get_connection() as conn:
            if db_user:
                # Обновляем существующий аккаунт
                try:
                    conn.execute(
                        'UPDATE users SET name = ?, password_hash = ? WHERE id = ?',
                        (name, pw_hash, db_user['id'])
                    )
                    conn.commit()
                    return db_user['id']
                except Exception as e:
                    logger.error(f'Ошибка обновления при регистрации {email}:', e, False)
                    return 0
            else:
                # Создаем новый аккаунт (unverified)
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
        """Создание 6-значного кода подтверждения email."""
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
        """Проверка кода подтверждения email."""
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
            
            # Подтверждаем пользователя
            conn.execute(
                'UPDATE users SET is_email_verified = 1 WHERE email = ?',
                (email,)
            )
            # Удаляем использованный токен
            conn.execute(
                'DELETE FROM email_verification_tokens WHERE email = ?',
                (email,)
            )
            conn.commit()
            return True

    def save_google_tokens(self, user_id: int, access_token: str, refresh_token: str = '', expires_in: int = 3600, scope: str = '') -> bool:
        """Сохранение или обновление токенов Google OAuth.

        Args:
            user_id: Идентификатор пользователя.
            access_token: Токен доступа Google.
            refresh_token: Токен обновления Google.
            expires_in: Время жизни токена в секундах.
            scope: Список разрешений (scopes).

        Returns:
            bool: True в случае успешного сохранения.
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
                logger.info(f'Токены Google OAuth сохранены для пользователя ID={user_id}')
                return True
            except Exception as e:
                logger.error(f'Ошибка сохранения токенов Google OAuth для user_id={user_id}:', e, False)
                return False

    def get_google_tokens(self, user_id: int) -> dict:
        """Получение токенов Google OAuth пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            dict: Словарь с данными токенов или пустой словарь.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM google_oauth_tokens WHERE user_id = ? LIMIT 1',
                (user_id,)
            ).fetchone()
            return dict(row) if row else {}

    def has_google_auth(self, user_id: int) -> bool:
        """Проверка наличия токенов Google OAuth у пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            bool: True если у пользователя есть токен Google.
        """
        tokens = self.get_google_tokens(user_id)
        return bool(tokens and tokens.get('access_token'))



from header import __root__
db_path = __root__ / 'core' / 'user_manager' / 'users.db'
user_manager = UserManager(db_path)
