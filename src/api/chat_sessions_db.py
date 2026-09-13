# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Chat Sessions Database Manager and Persistence Provider
# =============================================================================
# Description:
#   Manages SQLite storage, querying, bulk synchronization, and lifecycle
#   operations for conversational sessions and user message history.
#
# File: chat_sessions_db.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Dict

from header import __root__
from src.logger import logger

DB_PATH: Path = __root__ / 'src' / 'fastapi' / 'chat_sessions.db'


def get_db_connection() -> sqlite3.Connection:
    """Acquire a SQLite database connection configured with Row factory and WAL mode.

    Returns:
        sqlite3.Connection: Initialized SQLite connection.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager providing transactional SQLite database connection.

    Yields:
        sqlite3.Connection: Active database connection.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Chat sessions DB transaction failed: {e}")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables for chat sessions if not existing."""
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
    """Format a SQLite Row into a dictionary matching frontend session structure.

    Args:
        row (sqlite3.Row): Database row.

    Returns:
        dict[str, Any]: Formatted session dictionary.
    """
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
    """Retrieve all chat sessions for a specific user or global session list.

    Args:
        user_id (str): User identifier filter. Defaults to ''.

    Returns:
        list[dict[str, Any]]: List of session dictionaries ordered by updated_at descending.
    """
    init_db()
    with get_db() as conn:
        if user_id:
            cursor = conn.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC;",
                (user_id,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM chat_sessions ORDER BY updated_at DESC;"
            )
        rows = cursor.fetchall()
        return [format_row(r) for r in rows]


def get_session(session_id: str, user_id: str = '') -> dict[str, Any]:
    """Retrieve a single chat session by ID.

    Args:
        session_id (str): Target session identifier.
        user_id (str): Optional user identifier filter. Defaults to ''.

    Returns:
        dict[str, Any]: Session dictionary, or empty dict if not found.
    """
    if not session_id:
        return {}
    init_db()
    with get_db() as conn:
        if user_id:
            cursor = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?;",
                (session_id, user_id)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ?;",
                (session_id,)
            )
        row = cursor.fetchone()
        if not row:
            return {}
        return format_row(row)


def save_session(session_data: dict[str, Any], user_id: str = '') -> dict[str, Any]:
    """Create or update a chat session in the database.

    Args:
        session_data (dict[str, Any]): Session payload dictionary.
        user_id (str): Optional user identifier. Defaults to ''.

    Returns:
        dict[str, Any]: The saved session dictionary.
    """
    if not session_data or not isinstance(session_data, dict):
        return {}

    session_id = str(session_data.get('id') or f"session_{int(time.time() * 1000)}")
    title = str(session_data.get('title') or 'New Chat')
    is_custom_title = 1 if session_data.get('isCustomTitle') else 0
    now_ms = int(time.time() * 1000)
    created_at = int(session_data.get('createdAt') or now_ms)
    updated_at = int(session_data.get('updatedAt') or now_ms)
    messages = session_data.get('messages', [])
    chat_history = session_data.get('chatHistory', [])

    messages_json = json.dumps(messages, ensure_ascii=False)
    chat_history_json = json.dumps(chat_history, ensure_ascii=False)
    effective_user_id = user_id or str(session_data.get('userId') or '')

    init_db()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO chat_sessions (
                id, user_id, title, is_custom_title, created_at, updated_at, messages_json, chat_history_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                title = excluded.title,
                is_custom_title = excluded.is_custom_title,
                updated_at = excluded.updated_at,
                messages_json = excluded.messages_json,
                chat_history_json = excluded.chat_history_json;
        """, (
            session_id,
            effective_user_id,
            title,
            is_custom_title,
            created_at,
            updated_at,
            messages_json,
            chat_history_json
        ))

    return {
        'id': session_id,
        'userId': effective_user_id,
        'title': title,
        'isCustomTitle': bool(is_custom_title),
        'createdAt': created_at,
        'updatedAt': updated_at,
        'messages': messages,
        'chatHistory': chat_history
    }


def bulk_sync_sessions(sessions: list[dict[str, Any]], user_id: str = '') -> list[dict[str, Any]]:
    """Synchronize multiple sessions from a client, merging with server data.

    Args:
        sessions (list[dict[str, Any]]): List of client session dictionaries.
        user_id (str): Optional user identifier. Defaults to ''.

    Returns:
        list[dict[str, Any]]: The complete up-to-date list of sessions.
    """
    if not isinstance(sessions, list):
        return list_sessions(user_id=user_id)

    init_db()
    for s in sessions:
        if isinstance(s, dict) and s.get('id'):
            # Check if server has newer or existing session
            existing = get_session(str(s['id']), user_id=user_id)
            if not existing or int(s.get('updatedAt', 0)) >= int(existing.get('updatedAt', 0)):
                save_session(s, user_id=user_id)

    return list_sessions(user_id=user_id)


def delete_session(session_id: str, user_id: str = '') -> bool:
    """Delete a chat session by ID.

    Args:
        session_id (str): Session identifier to delete.
        user_id (str): Optional user identifier filter. Defaults to ''.

    Returns:
        bool: True if deletion was executed.
    """
    if not session_id:
        return False
    init_db()
    with get_db() as conn:
        if user_id:
            conn.execute(
                "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?;",
                (session_id, user_id)
            )
        else:
            conn.execute(
                "DELETE FROM chat_sessions WHERE id = ?;",
                (session_id,)
            )
    return True


def clear_sessions(user_id: str = '') -> bool:
    """Delete all chat sessions.

    Args:
        user_id (str): Optional user identifier filter. Defaults to ''.

    Returns:
        bool: True if cleared.
    """
    init_db()
    with get_db() as conn:
        if user_id:
            conn.execute("DELETE FROM chat_sessions WHERE user_id = ?;", (user_id,))
        else:
            conn.execute("DELETE FROM chat_sessions;")
    return True
