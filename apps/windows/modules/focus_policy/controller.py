# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy - Controller
# =============================================================================
# Description:
#   WindowsFocusController: профили в SQLite, жизненный цикл фокус-сессий,
#   подавление и архивация уведомлений, итог сессии. Состояние сессии хранится
#   в БД, поэтому корректно разделяется между API и процессом Task Scheduler.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.focus_policy.controller import WindowsFocusController
#
#     ctrl = WindowsFocusController()
#     ctrl.start_session('prof-work-default', 'UI_MANUAL')
#
# File: controller.py
# Project: ai-breadboard
# Package: apps.windows.modules.focus_policy
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""Ядро Focus Policy Engine."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Union

from logger import logger
from apps.windows.modules.focus_policy.listener import WinRtNotificationListener
from apps.windows.modules.focus_policy.models import (
    FocusProfile,
    FocusStatus,
    SessionSummary,
    SuppressedNotification,
)
from apps.windows.modules.focus_policy.scheduler import FocusTaskRegistrar
from apps.windows.modules.window_control_plane.history import get_default_telemetry_db_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS focus_profiles (
    profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active_profile INTEGER NOT NULL DEFAULT 0,
    schedule_days TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS suppressed_notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    app_user_model_id TEXT,
    app_display_name TEXT NOT NULL,
    title TEXT,
    message_text TEXT,
    received_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_read INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS focus_session_logs (
    session_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    suppressed_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    details_json TEXT
);
"""


def _default_applier(profile: Optional[FocusProfile]) -> None:
    """Применяет (или снимает при ``None``) системные параметры через реестр.

    Переиспользует ``FocusSessionManager`` из router_focus (бейджи, мигание, DND).
    """
    from apps.windows.api.routers.router_focus import FocusSessionManager

    mgr = FocusSessionManager()
    if profile is None:
        mgr._apply_focus_state(dnd=False, hide_badges=False, hide_flashing=False)
    else:
        mgr._apply_focus_state(
            dnd=profile.display.suppress_toast_banners,
            hide_badges=profile.taskbar.suppress_badges,
            hide_flashing=profile.taskbar.suppress_flashing,
        )


class WindowsFocusController:
    """Политика фокусировки: профили, сессии, подавление уведомлений."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        registrar: Optional[FocusTaskRegistrar] = None,
        listener: Optional[Any] = None,
        applier: Optional[Callable[[Optional[FocusProfile]], None]] = None,
    ) -> None:
        """Все зависимости внедряются явно (DI); по умолчанию — боевые реализации."""
        self.db_path = Path(db_path) if db_path else get_default_telemetry_db_path()
        self.registrar = registrar or FocusTaskRegistrar()
        self.listener = listener or WinRtNotificationListener()
        self.applier = applier or _default_applier
        self.listener_status = 'Unspecified'
        self._seen: Set[int] = set()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Профили ------------------------------------------------------------
    def save_profile(self, profile: FocusProfile) -> FocusProfile:
        """Создает/обновляет профиль и перерегистрирует задачи Task Scheduler."""
        sch = profile.schedule
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO focus_profiles (profile_id, name, schedule_days, start_time, end_time, is_enabled, profile_json) '
                'VALUES (?,?,?,?,?,?,?) ON CONFLICT(profile_id) DO UPDATE SET name=excluded.name, '
                "schedule_days=excluded.schedule_days, start_time=excluded.start_time, end_time=excluded.end_time, "
                "is_enabled=excluded.is_enabled, profile_json=excluded.profile_json, updated_at=datetime('now')",
                (profile.profile_id, profile.name, ','.join(sch.days), sch.start_time, sch.end_time,
                 int(sch.auto_start), profile.model_dump_json()),
            )
        self.registrar.register(profile)
        return profile

    def get_profile(self, profile_id: str) -> FocusProfile:
        """Возвращает профиль или бросает ``KeyError``."""
        with self._connect() as conn:
            row = conn.execute('SELECT profile_json FROM focus_profiles WHERE profile_id = ?', (profile_id,)).fetchone()
        if row is None:
            raise KeyError(f'Профиль {profile_id} не найден')
        return FocusProfile.model_validate_json(row['profile_json'])

    def list_profiles(self) -> List[FocusProfile]:
        """Список всех профилей."""
        with self._connect() as conn:
            rows = conn.execute('SELECT profile_json FROM focus_profiles ORDER BY name').fetchall()
        return [FocusProfile.model_validate_json(r['profile_json']) for r in rows]

    # --- Сессии -------------------------------------------------------------
    def _active_row(self, conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
        return conn.execute(
            "SELECT * FROM focus_session_logs WHERE event_type = 'SESSION_START' ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()

    def start_session(self, profile_id: str, triggered_by: str = 'UI_MANUAL') -> str:
        """Запускает сессию профиля.

        Raises:
            KeyError: Профиль не найден.
            RuntimeError: Сессия уже активна.
        """
        profile = self.get_profile(profile_id)
        with self._connect() as conn:
            if self._active_row(conn) is not None:
                raise RuntimeError('Сессия фокусировки уже активна')
            session_id = 'sess-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
            conn.execute(
                "INSERT INTO focus_session_logs (session_id, profile_id, event_type, triggered_by) VALUES (?,?,'SESSION_START',?)",
                (session_id, profile_id, triggered_by),
            )
            conn.execute('UPDATE focus_profiles SET is_active_profile = (profile_id = ?)', (profile_id,))
        self._seen.clear()
        self.applier(profile)
        logger.info(f'[FocusController] Сессия {session_id} ({profile_id}) запущена: {triggered_by}')
        return session_id

    def stop_session(self, triggered_by: Optional[str] = None) -> SessionSummary:
        """Завершает активную сессию, снимает ограничения и возвращает итог.

        Raises:
            RuntimeError: Нет активной сессии.
        """
        with self._connect() as conn:
            row = self._active_row(conn)
            if row is None:
                raise RuntimeError('Нет активной сессии фокусировки')
            summary = self._summary(conn, row['session_id'], row['profile_id'])
            conn.execute(
                "UPDATE focus_session_logs SET event_type='SESSION_END', suppressed_count=?, timestamp=datetime('now'), "
                "triggered_by=COALESCE(?, triggered_by) WHERE session_id=?",
                (summary.total_suppressed, triggered_by, row['session_id']),
            )
            conn.execute('UPDATE focus_profiles SET is_active_profile = 0')
        self.applier(None)
        logger.info(f'[FocusController] Сессия {summary.session_id} завершена, подавлено: {summary.total_suppressed}')
        return summary

    @staticmethod
    def _summary(conn: sqlite3.Connection, session_id: str, profile_id: str) -> SessionSummary:
        rows = conn.execute(
            'SELECT app_display_name, COUNT(*) AS c FROM suppressed_notifications WHERE session_id = ? '
            'GROUP BY app_display_name ORDER BY c DESC', (session_id,)
        ).fetchall()
        by_app = {r['app_display_name']: r['c'] for r in rows}
        return SessionSummary(session_id=session_id, profile_id=profile_id, total_suppressed=sum(by_app.values()), by_app=by_app)

    def status(self) -> FocusStatus:
        """Текущее состояние контроллера."""
        with self._connect() as conn:
            row = self._active_row(conn)
            if row is None:
                return FocusStatus(listener_access_status=self.listener_status)
            profile = self.get_profile(row['profile_id'])
            count = conn.execute('SELECT COUNT(*) FROM suppressed_notifications WHERE session_id = ?', (row['session_id'],)).fetchone()[0]
        return FocusStatus(
            is_focus_active=True,
            active_profile_id=profile.profile_id,
            active_profile_name=profile.name,
            session_id=row['session_id'],
            session_started_at=row['timestamp'],
            scheduled_end_at=profile.schedule.end_time,
            suppressed_notifications_count=count,
            listener_access_status=self.listener_status,
        )

    # --- Уведомления --------------------------------------------------------
    def request_listener_access(self) -> str:
        """Запрашивает права UserNotificationListener и запоминает статус."""
        self.listener_status = self.listener.request_access()
        return self.listener_status

    def poll_notifications(self) -> int:
        """Подавляет и архивирует новые Toast; возвращает число подавленных.

        В режиме без прав (``Denied``/``Unspecified``) перехват не выполняется.
        """
        if self.listener_status == 'Unspecified':
            self.request_listener_access()
        if self.listener_status != 'Allowed':
            return 0
        with self._connect() as conn:
            row = self._active_row(conn)
            if row is None:
                return 0
            profile = self.get_profile(row['profile_id'])
            count = 0
            for n in self.listener.get_toasts():
                if n.id in self._seen or n.app_user_model_id in profile.notifications.allow_priority_apps:
                    continue
                self._seen.add(n.id)
                self.listener.remove(n.id)
                if profile.notifications.store_suppressed:
                    conn.execute(
                        'INSERT INTO suppressed_notifications (session_id, profile_id, app_user_model_id, '
                        'app_display_name, title, message_text) VALUES (?,?,?,?,?,?)',
                        (row['session_id'], row['profile_id'], n.app_user_model_id, n.app_display_name, n.title, n.text),
                    )
                count += 1
        return count

    def list_suppressed(self, session_id: Optional[str] = None) -> List[SuppressedNotification]:
        """Архив подавленных уведомлений (по умолчанию — активной/последней сессии)."""
        with self._connect() as conn:
            if session_id is None:
                last = conn.execute('SELECT session_id FROM focus_session_logs ORDER BY timestamp DESC LIMIT 1').fetchone()
                if last is None:
                    return []
                session_id = last['session_id']
            rows = conn.execute(
                'SELECT * FROM suppressed_notifications WHERE session_id = ? ORDER BY notification_id', (session_id,)
            ).fetchall()
        return [
            SuppressedNotification(
                id=r['notification_id'], notification_id=r['notification_id'], session_id=r['session_id'],
                profile_id=r['profile_id'], app_user_model_id=r['app_user_model_id'], app_display_name=r['app_display_name'],
                title=r['title'], text=r['message_text'], received_at=r['received_at'], is_read=bool(r['is_read']),
            )
            for r in rows
        ]
