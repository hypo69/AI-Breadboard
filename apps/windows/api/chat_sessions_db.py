# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Chat Sessions DB
# =============================================================================
# Description:
#   SQLite хранилище сессий чата для Windows API.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.chat_sessions_db import get_db_connection, list_sessions
#
# File: chat_sessions_db.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:41:00
# =============================================================================

from __future__ import annotations
"""SQLite хранилище сессий чата для Windows API."""

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Dict, Optional
import os
from logger import logger

appdata_root = Path(os.getenv('APPDATA', str(Path.home() / 'AppData' / 'Roaming')))
DB_PATH: Path = appdata_root / 'AI-Breadboard' / 'chat_sessions' / 'chat_sessions.db'


def get_db_connection() -> sqlite3.Connection:
    """Получение подключения к SQLite БД в режиме WAL."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA foreign_keys=ON;')
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Контекстный менеджер транзакционного подключения."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f'Chat sessions DB transaction failed: {e}')
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Инициализация таблиц базы данных сессий чата."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT DEFAULT '',
                title TEXT NOT NULL DEFAULT 'New Chat',
                is_custom_title INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                messages_json TEXT NOT NULL DEFAULT '[]',
                chat_history_json TEXT NOT NULL DEFAULT '[]'
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated
            ON chat_sessions (user_id, updated_at DESC);
        """)


def format_row(row: sqlite3.Row) -> dict[str, Any]:
    """Форматирование строки SQLite в словарь сессии."""
    try:
        messages = json.loads(row['messages_json']) if row['messages_json'] else []
    except Exception:
        messages = []
    try:
        chat_history = json.loads(row['chat_history_json']) if row['chat_history_json'] else []
    except Exception:
        chat_history = []
    return {
        'id': row['id'],
        'userId': row['user_id'] or '',
        'title': row['title'] or 'New Chat',
        'isCustomTitle': bool(row['is_custom_title']),
        'createdAt': row['created_at'],
        'updatedAt': row['updated_at'],
        'messages': messages,
        'chatHistory': chat_history
    }


def list_sessions(user_id: str = '') -> list[dict[str, Any]]:
    """Получение всех сессий пользователя."""
    init_db()
    with get_db() as conn:
        if user_id:
            cur = conn.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
        else:
            cur = conn.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC")
        return [format_row(row) for row in cur.fetchall()]


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    """Получение одной сессии по ID."""
    init_db()
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        return format_row(row) if row else None


def save_session(session: dict[str, Any]) -> None:
    """Сохранение или обновление сессии."""
    init_db()
    s_id = session.get('id', '')
    user_id = session.get('userId', '')
    title = session.get('title', 'New Chat')
    is_custom = 1 if session.get('isCustomTitle') else 0
    now_ms = int(time.time() * 1000)
    created_at = session.get('createdAt') or now_ms
    updated_at = session.get('updatedAt') or now_ms
    messages_json = json.dumps(session.get('messages', []), ensure_ascii=False)
    chat_history_json = json.dumps(session.get('chatHistory', []), ensure_ascii=False)

    with get_db() as conn:
        conn.execute("""
            INSERT INTO chat_sessions (id, user_id, title, is_custom_title, created_at, updated_at, messages_json, chat_history_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                title = excluded.title,
                is_custom_title = excluded.is_custom_title,
                updated_at = excluded.updated_at,
                messages_json = excluded.messages_json,
                chat_history_json = excluded.chat_history_json;
        """, (s_id, user_id, title, is_custom, created_at, updated_at, messages_json, chat_history_json))


def delete_session(session_id: str) -> bool:
    """Удаление сессии по ID."""
    init_db()
    with get_db() as conn:
        cur = conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0


__all__ = [
    'get_db_connection',
    'get_db',
    'init_db',
    'format_row',
    'list_sessions',
    'get_session',
    'save_session',
    'delete_session',
]
