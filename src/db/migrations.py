# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SQLite Database Migration Manager
# =============================================================================
# Description:
#   Manages SQLite schema versioning, transaction-wrapped migrations,
#   automatic pre-migration backups and rollbacks.
#
# File: migrations.py
# Project: ai-breadboard
# Package: src.db
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления миграциями SQLite баз данных."""

import hashlib
import importlib.util
from pathlib import Path
import shutil
import sqlite3
import time
from typing import Dict, List, Tuple

from logger import logger


class MigrationManager:
    """Менеджер версионирования и миграций баз данных SQLite."""

    def __init__(self, repo_root: Path | None = None) -> None:
        """Инициализация менеджера миграций.

        Args:
            repo_root (Path | None): Корневая директория репозитория.
        """
        if repo_root is None:
            self.repo_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.repo_root = Path(repo_root)

        self.migrations_root = self.repo_root / "migrations"
        self.migrations_root.mkdir(parents=True, exist_ok=True)
        self.db_registry: Dict[str, Path] = {}

    def register_db(self, db_name: str, db_path: Path | str) -> None:
        """Регистрация базы данных для управления миграциями.

        Args:
            db_name (str): Имя базы данных (соответствует папке в migrations/).
            db_path (Path | str): Путь к файлу SQLite базы данных.
        """
        self.db_registry[db_name] = Path(db_path)

    def _ensure_tracking_table(self, conn: sqlite3.Connection) -> None:
        """Создает служебную таблицу _schema_migrations при её отсутствии.

        Args:
            conn (sqlite3.Connection): Соединение с базой данных.
        """
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()

    def get_applied_versions(self, db_path: Path) -> List[str]:
        """Возвращает список примененных версий миграций.

        Args:
            db_path (Path): Путь к базе данных.

        Returns:
            List[str]: Список версий.
        """
        if not db_path.exists():
            return []

        with sqlite3.connect(db_path) as conn:
            self._ensure_tracking_table(conn)
            cursor = conn.execute("SELECT version FROM _schema_migrations ORDER BY id ASC")
            return [row[0] for row in cursor.fetchall()]

    def create_migration(self, db_name: str, name: str, is_python: bool = False) -> Path:
        """Создает новый файл миграции с инкрементным номером.

        Args:
            db_name (str): Имя базы данных.
            name (str): Описание миграции.
            is_python (bool): True если создается Python-миграция (.py), иначе SQL (.sql).

        Returns:
            Path: Путь к созданному файлу миграции.
        """
        target_dir = self.migrations_root / db_name
        target_dir.mkdir(parents=True, exist_ok=True)

        existing_files = sorted(
            [f for f in target_dir.iterdir() if f.suffix in (".sql", ".py")]
        )
        next_num = len(existing_files) + 1
        prefix = f"{next_num:04d}"
        ext = ".py" if is_python else ".sql"
        filename = f"{prefix}_{name}{ext}"
        file_path = target_dir / filename

        if is_python:
            template = (
                "# -*- coding: utf-8 -*-\n"
                "import sqlite3\n\n\n"
                "def upgrade(conn: sqlite3.Connection) -> bool:\n"
                '    """Выполнение миграции."""\n'
                "    return True\n"
            )
            file_path.write_text(template, encoding="utf-8")
        else:
            file_path.write_text("-- Миграция базы данных\n", encoding="utf-8")

        return file_path

    def apply_db_migrations(self, db_name: str) -> Tuple[bool, int, str]:
        """Применяет ожидающие миграции к целевой базе данных.

        Args:
            db_name (str): Имя зарегистрированной БД.

        Returns:
            Tuple[bool, int, str]: (Успех, количество примененных миграций, сообщение).
        """
        if db_name not in self.db_registry:
            return False, 0, f"Database '{db_name}' is not registered."

        db_path = self.db_registry[db_name]
        mig_dir = self.migrations_root / db_name
        if not mig_dir.exists():
            return True, 0, f"No migrations folder found for '{db_name}'."

        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Pre-migration backup
        backup_path: Path | None = None
        if db_path.exists():
            backup_path = db_path.with_name(f"{db_path.name}.backup_{int(time.time() * 1000)}")
            shutil.copy2(db_path, backup_path)

        try:
            with sqlite3.connect(db_path) as conn:
                self._ensure_tracking_table(conn)
                cursor = conn.execute("SELECT version FROM _schema_migrations ORDER BY id ASC")
                applied = set(row[0] for row in cursor.fetchall())

                migration_files = sorted(
                    [f for f in mig_dir.iterdir() if f.suffix in (".sql", ".py")]
                )
                pending = [f for f in migration_files if f.stem not in applied]

                if not pending:
                    if backup_path and backup_path.exists():
                        backup_path.unlink()
                    return True, 0, f"Database '{db_name}' schema is up to date."

                applied_count = 0
                for mig_file in pending:
                    version = mig_file.stem
                    raw_content = mig_file.read_bytes()
                    checksum = hashlib.sha256(raw_content).hexdigest()

                    if mig_file.suffix == ".sql":
                        sql_text = raw_content.decode("utf-8")
                        conn.executescript(sql_text)
                    elif mig_file.suffix == ".py":
                        spec = importlib.util.spec_from_file_location(f"mig_{version}", mig_file)
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            if hasattr(mod, "upgrade"):
                                res = mod.upgrade(conn)
                                if res is False:
                                    raise RuntimeError(f"Python migration {mig_file.name} upgrade() returned False")

                    conn.execute(
                        "INSERT INTO _schema_migrations (version, filename, checksum) VALUES (?, ?, ?)",
                        (version, mig_file.name, checksum),
                    )
                    conn.commit()
                    applied_count += 1

                if backup_path and backup_path.exists():
                    backup_path.unlink()

                return True, applied_count, f"Successfully applied {applied_count} migrations to '{db_name}'."

        except Exception as err:
            logger.error(f"Migration error on '{db_name}': {err}")
            # Restore from backup on error
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, db_path)
                backup_path.unlink()
            return False, 0, f"Migration failed on '{db_name}': {err}. Rolled back to backup."
