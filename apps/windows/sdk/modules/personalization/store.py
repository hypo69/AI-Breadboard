# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Personalization - Store
# =============================================================================
# Description:
#   SQLite-хранилище персонализации в telemetry.db: снимки конфигурации
#   (personalization_snapshots) и журнал изменений (personalization_change_history).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.personalization.store import PersonalizationStore
#
#     store = PersonalizationStore(db_path)
#     store.record_change('CURSOR', 'cursor_size', 32, 48)
#
# File: store.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.personalization
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:20:00
# =============================================================================

from __future__ import annotations
"""SQLite-хранилище снимков и аудита персонализации."""

import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_SCHEMA = """
CREATE TABLE IF NOT EXISTS personalization_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cursor_size INTEGER NOT NULL DEFAULT 32,
    cursor_type TEXT NOT NULL DEFAULT 'white',
    cursor_color_hex TEXT,
    cursor_shadow_enabled INTEGER NOT NULL DEFAULT 1,
    cursor_trails_length INTEGER NOT NULL DEFAULT 0,
    cursor_speed INTEGER NOT NULL DEFAULT 10,
    apps_use_light_theme INTEGER NOT NULL DEFAULT 0,
    system_use_light_theme INTEGER NOT NULL DEFAULT 0,
    dwm_accent_color_hex TEXT NOT NULL DEFAULT '#0078D4',
    wallpaper_path TEXT,
    wallpaper_fit_mode TEXT NOT NULL DEFAULT 'Fill',
    taskbar_alignment TEXT NOT NULL DEFAULT 'center',
    captured_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS personalization_change_history (
    change_id TEXT PRIMARY KEY,
    parameter_group TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL DEFAULT 'USER_UI',
    restore_point_created INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_SNAPSHOT_COLUMNS = frozenset({
    'cursor_size', 'cursor_type', 'cursor_color_hex', 'cursor_shadow_enabled', 'cursor_trails_length',
    'cursor_speed', 'apps_use_light_theme', 'system_use_light_theme', 'dwm_accent_color_hex',
    'wallpaper_path', 'wallpaper_fit_mode', 'taskbar_alignment',
})


class PersonalizationStore:
    """Запись и чтение снимков и журнала изменений персонализации."""

    def __init__(self, db_path: Union[str, Path]) -> None:
        """Args:
            db_path: Путь к telemetry.db.
        """
        self.db_path = Path(db_path)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def add_snapshot(self, values: Dict[str, Any]) -> int:
        """Сохраняет снимок конфигурации; неуказанные поля получают значения схемы.

        Raises:
            ValueError: Передан неизвестный столбец.
        """
        unknown = set(values) - _SNAPSHOT_COLUMNS
        if unknown:
            raise ValueError(f'Неизвестные поля снимка: {sorted(unknown)}')
        cols = list(values)
        sql = f"INSERT INTO personalization_snapshots ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})" if cols \
            else 'INSERT INTO personalization_snapshots DEFAULT VALUES'
        with self._connect() as conn:
            return conn.execute(sql, [values[c] for c in cols]).lastrowid

    def latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Последний снимок или ``None``, если снимков еще нет (допустимо: первичный запуск)."""
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM personalization_snapshots ORDER BY snapshot_id DESC LIMIT 1').fetchone()
        return dict(row) if row else None

    def record_change(
        self,
        group: str,
        name: str,
        old: Any,
        new: Any,
        changed_by: str = 'USER_UI',
        restore_point_created: bool = False,
    ) -> str:
        """Добавляет запись в журнал; возвращает ``change_id``."""
        change_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO personalization_change_history (change_id, parameter_group, parameter_name, '
                'old_value, new_value, changed_by, restore_point_created) VALUES (?,?,?,?,?,?,?)',
                (change_id, group, name, None if old is None else str(old), None if new is None else str(new),
                 changed_by, int(restore_point_created)),
            )
        return change_id

    def history(self, limit: int = 100, group: Optional[str] = None) -> List[Dict[str, Any]]:
        """Журнал изменений от новых к старым (опционально по группе)."""
        sql = 'SELECT * FROM personalization_change_history'
        args: List[Any] = []
        if group:
            sql += ' WHERE parameter_group = ?'
            args.append(group)
        sql += ' ORDER BY rowid DESC LIMIT ?'
        args.append(limit)
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(sql, args).fetchall()]
