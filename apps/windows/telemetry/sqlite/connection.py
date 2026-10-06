# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Connection
# =============================================================================
# Description:
#   Менеджер подключений к SQLite базе данных с поддержкой режима только чтение.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.connection import TelemetryConnectionManager
#
#     cm = TelemetryConnectionManager(db_path=Path("logs/telemetry.db"), read_only=True)
#     with cm.get_connection() as conn:
#         ...
#
# File: connection.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-05 23:35:00
# =============================================================================

from __future__ import annotations

"""Управление подключениями к базе данных SQLite с поддержкой режимов Read-Only и WAL."""

import sqlite3
import threading
from pathlib import Path
from typing import Optional, Union

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class TelemetryConnectionManager:
    """Менеджер создания и настройки соединений к SQLite базе данных телеметрии."""

    def __init__(
        self,
        db_path: Union[str, Path],
        read_only: bool = False,
        timeout: float = 15.0,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        """Инициализирует менеджер соединений.

        Args:
            db_path: Путь к файлу SQLite базы данных.
            read_only: Флаг строгого режима только чтения (блокирует запись).
            timeout: Таймаут ожидания освобождения базы данных в секундах.
            lock: Разделяемый RLock (опционально).
        """
        self.db_path = Path(db_path)
        self.read_only = bool(read_only)
        self.timeout = float(timeout)
        self._lock = lock or threading.RLock()

        if not self.read_only:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def lock(self) -> threading.RLock:
        """Возвращает разделяемый поток-безопасный лок."""
        return self._lock

    def get_connection(self) -> sqlite3.Connection:
        """Создает и настраивает соединение SQLite с необходимыми PRAGMA директивами.

        Returns:
            sqlite3.Connection: Настроенное соединение.
        """
        if self.read_only:
            db_uri = f"file:{self.db_path.as_posix()}?mode=ro"
            try:
                conn = sqlite3.connect(db_uri, uri=True, timeout=self.timeout, check_same_thread=False)
            except sqlite3.OperationalError:
                conn = sqlite3.connect(str(self.db_path), timeout=self.timeout, check_same_thread=False)
                try:
                    conn.execute('PRAGMA query_only = ON;')
                except Exception:
                    pass
        else:
            conn = sqlite3.connect(str(self.db_path), timeout=self.timeout, check_same_thread=False)
            conn.execute('PRAGMA journal_mode = WAL;')
            conn.execute('PRAGMA synchronous = NORMAL;')
            conn.execute('PRAGMA foreign_keys = ON;')

        conn.row_factory = sqlite3.Row
        return conn
