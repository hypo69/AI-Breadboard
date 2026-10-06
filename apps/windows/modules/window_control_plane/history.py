# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Management Telemetry DB History
# =============================================================================
# Description:
#   Менеджер фиксации всех изменений Window Management Control Plane в SQLite
#   базе данных telemetry.db. Обеспечивает персистентный аудит параметров,
#   транзакционную историю и надежный откат (Rollback) параметров ОС.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.window_control_plane.history import get_window_history_manager
#
#     history_mgr = get_window_history_manager()
#     history_mgr.record_change(...)
#     history = history_mgr.get_history(limit=50)
#
# File: history.py
# Project: ai-breadboard
# Package: apps.windows.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:20:00
# =============================================================================

from __future__ import annotations
"""Менеджер истории изменений и отката Window Management в telemetry.db."""

from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union
import uuid

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("window_management_history")


def get_default_telemetry_db_path() -> Path:
    """Возвращает стандартный путь к файлу базы данных telemetry.db с fallback-путями."""
    programdata = os.environ.get("ProgramData") or os.environ.get("ALLUSERSPROFILE")
    if programdata and os.path.exists(programdata):
        primary = Path(programdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs" / "telemetry.db"
    else:
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home() / ".config")
        primary = Path(appdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs" / "telemetry.db"

    if not primary.parent.exists():
        try:
            primary.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            primary = Path(__file__).resolve().parents[2] / "telemetry" / "logs" / "telemetry.db"
            primary.parent.mkdir(parents=True, exist_ok=True)

    return primary


class WindowManagementHistoryManager:
    """Управление аудитом изменений Window Control Plane в базе telemetry.db."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        """Инициализация менеджера и создание схемы таблицы при отсутствии."""
        self.db_path = Path(db_path) if db_path else get_default_telemetry_db_path()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Создает соединение с базой данных SQLite с включенным timeout и row_factory."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Создает таблицу истории изменений окон и диспетчера в telemetry.db."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS window_management_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        change_id TEXT UNIQUE NOT NULL,
                        timestamp TEXT NOT NULL,
                        setting_id TEXT NOT NULL,
                        setting_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        backend_type TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        operator TEXT,
                        reason TEXT,
                        restore_point_id TEXT,
                        status TEXT NOT NULL,
                        requires_restart INTEGER DEFAULT 0,
                        is_rolled_back INTEGER DEFAULT 0,
                        rolled_back_at TEXT,
                        rolled_back_by TEXT,
                        rolled_back_change_id TEXT,
                        details_json TEXT,
                        error TEXT
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_wm_hist_timestamp 
                    ON window_management_history(timestamp DESC);
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_wm_hist_setting 
                    ON window_management_history(setting_id);
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_wm_hist_change_id 
                    ON window_management_history(change_id);
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_wm_hist_category 
                    ON window_management_history(category);
                """)
                conn.commit()
        except Exception as exc:
            logger.error(f"[WindowManagementHistoryManager] Ошибка инициализации таблицы в telemetry.db: {exc}")

    def record_change(
        self,
        change_id: str,
        setting_id: str,
        setting_name: str,
        category: str,
        backend_type: str,
        scope: str,
        risk_level: str,
        old_value: Any,
        new_value: Any,
        action_type: str = "APPLY",
        operator: Optional[str] = "User",
        reason: Optional[str] = None,
        restore_point_id: Optional[str] = None,
        status: str = "SUCCESS",
        requires_restart: bool = False,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        rolled_back_change_id: Optional[str] = None,
    ) -> int:
        """Записывает изменение в таблицу window_management_history базы telemetry.db.

        Args:
            change_id: Уникальный UUID изменения.
            setting_id: Идентификатор настройки (например focus_activation_001).
            setting_name: Название параметра.
            category: Категория параметра.
            backend_type: Тип бэкенда (spi, winreg, dwm, display, policy).
            scope: Область действия (user, machine, session).
            risk_level: Уровень риска (safe, caution, critical).
            old_value: Предыдущее значение.
            new_value: Новое значение.
            action_type: Тип действия ('APPLY' | 'BATCH_APPLY' | 'ROLLBACK').
            operator: Инициатор изменения.
            reason: Причина или комментарий.
            restore_point_id: Идентификатор точки восстановления Windows (если создана).
            status: Статус выполнения ('SUCCESS' | 'FAILED').
            requires_restart: Требуется ли перезагрузка.
            details: Дополнительные метаданные.
            error: Текст ошибки при сбое.
            rolled_back_change_id: Ссылка на откатываемое изменение (при action_type='ROLLBACK').

        Returns:
            int: Первичный ключ созданной записи (id).
        """
        now_ts = datetime.now().isoformat()
        old_val_str = json.dumps(old_value, ensure_ascii=False) if old_value is not None else None
        new_val_str = json.dumps(new_value, ensure_ascii=False) if new_value is not None else None
        details_str = json.dumps(details or {}, ensure_ascii=False)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO window_management_history (
                        change_id, timestamp, setting_id, setting_name, category,
                        action_type, backend_type, scope, risk_level,
                        old_value, new_value, operator, reason, restore_point_id,
                        status, requires_restart, is_rolled_back, details_json, error,
                        rolled_back_change_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?);
                    """,
                    (
                        change_id,
                        now_ts,
                        setting_id,
                        setting_name,
                        category,
                        action_type,
                        backend_type,
                        scope,
                        risk_level,
                        old_val_str,
                        new_val_str,
                        operator,
                        reason,
                        restore_point_id,
                        status,
                        1 if requires_restart else 0,
                        details_str,
                        error,
                        rolled_back_change_id,
                    ),
                )
                conn.commit()
                row_id = cursor.lastrowid or 0
                logger.info(
                    f"📝 [telemetry.db] Зафиксировано изменение #{row_id} [{setting_id}] "
                    f"'{setting_name}' ({old_val_str} -> {new_val_str})"
                )
                return row_id
        except Exception as exc:
            logger.error(f"[WindowManagementHistoryManager] Ошибка записи в telemetry.db: {exc}")
            return -1

    def get_history(
        self,
        limit: int = 100,
        offset: int = 0,
        setting_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        unrolled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Получает историю зафиксированных изменений из telemetry.db.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение выборки.
            setting_id: Фильтр по ID параметра.
            category: Фильтр по категории.
            status: Фильтр по статусу (SUCCESS/FAILED).
            unrolled_only: Только неоткаченные изменения.

        Returns:
            List[Dict[str, Any]]: Список записей истории изменений.
        """
        query = "SELECT * FROM window_management_history WHERE 1=1"
        params: List[Any] = []

        if setting_id:
            query += " AND setting_id = ?"
            params.append(setting_id)

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        if unrolled_only:
            query += " AND is_rolled_back = 0 AND action_type != 'ROLLBACK'"

        query += " ORDER BY id DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                result: List[Dict[str, Any]] = []
                for row in rows:
                    item = dict(row)
                    # Десериализация JSON значений
                    try:
                        item["old_value"] = json.loads(item["old_value"]) if item["old_value"] is not None else None
                    except Exception:
                        pass
                    try:
                        item["new_value"] = json.loads(item["new_value"]) if item["new_value"] is not None else None
                    except Exception:
                        pass
                    try:
                        item["details"] = json.loads(item["details_json"]) if item.get("details_json") else {}
                    except Exception:
                        item["details"] = {}

                    item["requires_restart"] = bool(item.get("requires_restart", 0))
                    item["is_rolled_back"] = bool(item.get("is_rolled_back", 0))
                    item["rolled_back"] = bool(item.get("is_rolled_back", 0))
                    item["success"] = item.get("status") == "SUCCESS"
                    result.append(item)

                return result
        except Exception as exc:
            logger.error(f"[WindowManagementHistoryManager] Ошибка чтения истории из telemetry.db: {exc}")
            return []

    def get_by_change_id(self, change_id: str) -> Optional[Dict[str, Any]]:
        """Получает запись истории по уникальному change_id."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM window_management_history WHERE change_id = ? LIMIT 1;", (change_id,))
                row = cursor.fetchone()
                if not row:
                    return None

                item = dict(row)
                try:
                    item["old_value"] = json.loads(item["old_value"]) if item["old_value"] is not None else None
                except Exception:
                    pass
                try:
                    item["new_value"] = json.loads(item["new_value"]) if item["new_value"] is not None else None
                except Exception:
                    pass
                try:
                    item["details"] = json.loads(item["details_json"]) if item.get("details_json") else {}
                except Exception:
                    item["details"] = {}

                item["requires_restart"] = bool(item.get("requires_restart", 0))
                item["is_rolled_back"] = bool(item.get("is_rolled_back", 0))
                item["rolled_back"] = bool(item.get("is_rolled_back", 0))
                item["success"] = item.get("status") == "SUCCESS"
                return item
        except Exception as exc:
            logger.error(f"[WindowManagementHistoryManager] Ошибка поиска change_id '{change_id}': {exc}")
            return None

    def mark_as_rolled_back(self, change_id: str, rolled_back_by: Optional[str] = "User") -> bool:
        """Помечает транзакцию как откаченную в telemetry.db."""
        now_ts = datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE window_management_history
                    SET is_rolled_back = 1, rolled_back_at = ?, rolled_back_by = ?
                    WHERE change_id = ?;
                    """,
                    (now_ts, rolled_back_by, change_id),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as exc:
            logger.error(f"[WindowManagementHistoryManager] Ошибка пометки отката в telemetry.db: {exc}")
            return False

    def get_last_action(self) -> Optional[Dict[str, Any]]:
        """Получает последнее неоткаченное успешное действие для быстрого отката."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM window_management_history
                    WHERE status = 'SUCCESS' AND is_rolled_back = 0 AND action_type != 'ROLLBACK'
                    ORDER BY id DESC LIMIT 1;
                    """
                )
                row = cursor.fetchone()
                if not row:
                    return None

                item = dict(row)
                try:
                    item["old_value"] = json.loads(item["old_value"]) if item["old_value"] is not None else None
                except Exception:
                    pass
                try:
                    item["new_value"] = json.loads(item["new_value"]) if item["new_value"] is not None else None
                except Exception:
                    pass
                item["requires_restart"] = bool(item.get("requires_restart", 0))
                item["is_rolled_back"] = bool(item.get("is_rolled_back", 0))
                item["success"] = True
                return item
        except Exception as exc:
            logger.error(f"[WindowManagementHistoryManager] Ошибка получения последнего действия: {exc}")
            return None


_history_manager_instance: Optional[WindowManagementHistoryManager] = None


def get_window_history_manager(db_path: Optional[Union[str, Path]] = None) -> WindowManagementHistoryManager:
    """Синглтон фабрика менеджера истории telemetry.db."""
    global _history_manager_instance
    if _history_manager_instance is None or db_path is not None:
        _history_manager_instance = WindowManagementHistoryManager(db_path=db_path)
    return _history_manager_instance
