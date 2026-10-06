# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - History & Telemetry Manager
# =============================================================================
# Description:
#   Фиксация всех изменений Taskbar и Desktop Window Control Plane в SQLite базе
#   telemetry.db с возможностью аудита и безопасного отката (Rollback).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.core.history_manager import TaskbarHistoryManager
#
#     history_mgr = TaskbarHistoryManager()
#     record_id = history_mgr.record_action(...)
#     history_mgr.rollback(record_id, controller)
#
# File: history_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:58:00
# =============================================================================

from __future__ import annotations
"""Менеджер истории изменений и отката в базе данных telemetry.db."""

from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union

from logger import logger


def get_telemetry_db_path() -> Path:
    """Определяет стандартный путь к базе данных telemetry.db с fallback-путями."""
    programdata = os.environ.get("ProgramData") or os.environ.get("ALLUSERSPROFILE")
    if programdata and os.path.exists(programdata):
        primary = Path(programdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs" / "telemetry.db"
    else:
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home() / ".config")
        primary = Path(appdata) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs" / "telemetry.db"

    # Если родительский каталог не существует, используем локальный fallback
    if not primary.parent.exists():
        try:
            primary.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            primary = Path(__file__).resolve().parents[3] / "telemetry" / "logs" / "telemetry.db"
            primary.parent.mkdir(parents=True, exist_ok=True)

    return primary


class TaskbarHistoryManager:
    """Управление аудитом изменений в telemetry.db и поддержкой истории/отката."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        """Инициализирует менеджер истории и создает схему таблицы при отсутствии."""
        self.db_path = Path(db_path) if db_path else get_telemetry_db_path()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Создает соединение с базой данных SQLite."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Создает таблицу истории операций панели задач и окон."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS taskbar_action_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        command_id TEXT NOT NULL,
                        category TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        target_hwnd INTEGER,
                        previous_state TEXT,
                        new_state TEXT,
                        details TEXT,
                        status TEXT NOT NULL,
                        is_rolled_back INTEGER DEFAULT 0,
                        rolled_back_at TEXT
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tb_hist_timestamp 
                    ON taskbar_action_history(timestamp DESC);
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tb_hist_cmd 
                    ON taskbar_action_history(command_id);
                """)
                conn.commit()
        except Exception as exc:
            logger.error(f"[TaskbarHistoryManager] Ошибка инициализации таблицы в telemetry.db: {exc}")

    def record_action(
        self,
        command_id: str,
        category: str,
        action_type: str,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        target_hwnd: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
    ) -> int:
        """
        Записывает выполненное действие в telemetry.db.
        
        Returns:
            int: Идентификатор созданной записи истории.
        """
        now_iso = datetime.now().isoformat()
        prev_json = json.dumps(previous_state, ensure_ascii=False) if previous_state else None
        new_json = json.dumps(new_state, ensure_ascii=False) if new_state else None
        det_json = json.dumps(details, ensure_ascii=False) if details else None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO taskbar_action_history (
                        timestamp, command_id, category, action_type, target_hwnd,
                        previous_state, new_state, details, status, is_rolled_back
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    now_iso, command_id, category, action_type, target_hwnd,
                    prev_json, new_json, det_json, status
                ))
                conn.commit()
                rec_id = cursor.lastrowid or 0
                logger.debug(f"[TaskbarHistory] Зафиксировано действие {command_id} [ID: {rec_id}] в telemetry.db")
                return rec_id
        except Exception as exc:
            logger.error(f"[TaskbarHistoryManager] Не удалось записать действие в telemetry.db: {exc}")
            return 0

    def get_history(self, limit: int = 50, command_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Возвращает историю изменений из telemetry.db."""
        result: List[Dict[str, Any]] = []
        query = "SELECT * FROM taskbar_action_history"
        params: List[Any] = []

        if command_id:
            query += " WHERE command_id = ?"
            params.append(command_id)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                for row in rows:
                    item = dict(row)
                    if item.get("previous_state"):
                        try:
                            item["previous_state"] = json.loads(item["previous_state"])
                        except Exception:
                            pass
                    if item.get("new_state"):
                        try:
                            item["new_state"] = json.loads(item["new_state"])
                        except Exception:
                            pass
                    if item.get("details"):
                        try:
                            item["details"] = json.loads(item["details"])
                        except Exception:
                            pass
                    result.append(item)
        except Exception as exc:
            logger.error(f"[TaskbarHistoryManager] Ошибка чтения истории из telemetry.db: {exc}")

        return result

    def get_record_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """Получает запись истории по ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM taskbar_action_history WHERE id = ?", (history_id,))
                row = cursor.fetchone()
                if row:
                    item = dict(row)
                    if item.get("previous_state"):
                        item["previous_state"] = json.loads(item["previous_state"])
                    if item.get("new_state"):
                        item["new_state"] = json.loads(item["new_state"])
                    if item.get("details"):
                        item["details"] = json.loads(item["details"])
                    return item
        except Exception as exc:
            logger.error(f"[TaskbarHistoryManager] Ошибка получения записи ID {history_id}: {exc}")
        return None

    def rollback(self, history_id: int, controller: Any) -> Dict[str, Any]:
        """
        Выполняет откат операции по ее идентификатору в telemetry.db.
        
        Args:
            history_id: ID записи истории.
            controller: Экземпляр TaskbarController.
        """
        rec = self.get_record_by_id(history_id)
        if not rec:
            return {"status": "ERROR", "message": f"Запись истории ID {history_id} не найдена"}

        if rec.get("is_rolled_back"):
            return {"status": "ERROR", "message": f"Запись ID {history_id} уже была откачена ранее"}

        prev = rec.get("previous_state")
        if not prev:
            return {"status": "ERROR", "message": f"Запись ID {history_id} не содержит предыдущего состояния для отката"}

        cmd = rec.get("command_id", "").upper()
        cat = rec.get("category", "")
        rollback_ok = False
        rollback_details = {}

        try:
            # 1. Откат настроек панели задач
            if cat == "taskbar" or "SETTINGS" in cmd or "ALIGNMENT" in cmd or "AUTOHIDE" in cmd or "WIDGETS" in cmd:
                from apps.windows.modules.taskbar.core.models import TaskbarSettingsUpdate
                update_payload = TaskbarSettingsUpdate(**prev)
                res = controller.update_settings(update_payload, record_telemetry=False)
                rollback_ok = (res.get("status") == "SUCCESS")
                rollback_details = res

            # 2. Откат перемещения / масштабирования окна
            elif cmd == "WINDOW.MOVE" or cmd == "WINDOW.RESIZE":
                hwnd = rec.get("target_hwnd") or prev.get("hwnd")
                if hwnd and "x" in prev and "y" in prev:
                    from apps.windows.modules.taskbar.core.models import WindowMoveRequest
                    m_req = WindowMoveRequest(
                        x=prev["x"],
                        y=prev["y"],
                        width=prev.get("width", 800),
                        height=prev.get("height", 600),
                    )
                    res = controller.move_window(hwnd, m_req, record_telemetry=False)
                    rollback_ok = (res.get("status") == "SUCCESS")
                    rollback_details = res

            # 3. Откат минимизации / максимизации
            elif cmd in ("WINDOW.MINIMIZE", "WINDOW.MAXIMIZE", "WINDOW.RESTORE"):
                hwnd = rec.get("target_hwnd")
                if hwnd:
                    if prev.get("is_minimized"):
                        res = controller.minimize_window(hwnd, record_telemetry=False)
                    elif prev.get("is_maximized"):
                        res = controller.maximize_window(hwnd, record_telemetry=False)
                    else:
                        res = controller.restore_window(hwnd, record_telemetry=False)
                    rollback_ok = (res.get("status") == "SUCCESS")
                    rollback_details = res

            else:
                return {
                    "status": "ERROR",
                    "message": f"Откат для команды '{cmd}' не поддерживается или не применим",
                }

            if rollback_ok:
                now_iso = datetime.now().isoformat()
                with self._get_connection() as conn:
                    conn.execute("""
                        UPDATE taskbar_action_history
                        SET is_rolled_back = 1, rolled_back_at = ?
                        WHERE id = ?
                    """, (now_iso, history_id))
                    conn.commit()

                logger.info(f"[TaskbarHistory] Успешный откат записи ID {history_id} ({cmd})")
                return {
                    "status": "SUCCESS",
                    "history_id": history_id,
                    "command_id": cmd,
                    "message": f"Откат действия ID {history_id} успешно выполнен",
                    "details": rollback_details,
                }
            else:
                return {
                    "status": "ERROR",
                    "history_id": history_id,
                    "message": f"Не удалось применить откат: {rollback_details}",
                }

        except Exception as exc:
            logger.error(f"[TaskbarHistoryManager] Ошибка при откате ID {history_id}: {exc}")
            return {"status": "ERROR", "message": str(exc)}

    def rollback_last(self, controller: Any) -> Dict[str, Any]:
        """Откатывает последнее обратимое действие."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM taskbar_action_history
                    WHERE is_rolled_back = 0 AND previous_state IS NOT NULL
                    ORDER BY id DESC LIMIT 1
                """)
                row = cursor.fetchone()
                if not row:
                    return {"status": "ERROR", "message": "Нет доступных действий для отката"}
                last_id = row[0]
                return self.rollback(last_id, controller)
        except Exception as exc:
            logger.error(f"[TaskbarHistoryManager] Ошибка отката последнего действия: {exc}")
            return {"status": "ERROR", "message": str(exc)}
