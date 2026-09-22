# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Messenger Database Manager and Connection Provider
# =============================================================================
# Description:
#   Provides SQLite / PostgreSQL database connection pooling, table schema
#   initialization, and thread-safe session contexts for the real-time messenger.
#
# File: database.py
# Project: ai-breadboard
# Package: src.api.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Generator
from contextlib import contextmanager

from header import __root__
from logger import logger

DB_PATH: Path = __root__ / 'data' / 'messenger.db'


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
        logger.error(f"Messenger DB transaction failed: {e}")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables for messenger, rooms, attachments, and call sessions."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Messenger Users table (synced with native auth or WordPress)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messenger_users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    avatar_url TEXT,
                    source TEXT DEFAULT 'native',
                    is_online INTEGER DEFAULT 0,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Chat Rooms table (direct, group, channel, meeting)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_rooms (
                    id TEXT PRIMARY KEY,
                    room_type TEXT NOT NULL, -- 'direct', 'group', 'channel', 'meeting'
                    title TEXT,
                    description TEXT,
                    avatar_url TEXT,
                    created_by TEXT,
                    is_archived INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES messenger_users (id) ON DELETE SET NULL
                );
            """)

            # 3. Chat Room Members table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_members (
                    room_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT DEFAULT 'member', -- 'owner', 'admin', 'member'
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_read_message_id TEXT,
                    PRIMARY KEY (room_id, user_id),
                    FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES messenger_users (id) ON DELETE CASCADE
                );
            """)

            # 4. Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text', -- 'text', 'image', 'audio', 'video', 'file', 'system'
                    content TEXT,
                    reply_to_id TEXT,
                    forward_from_id TEXT,
                    status TEXT DEFAULT 'sent', -- 'sent', 'delivered', 'read'
                    is_edited INTEGER DEFAULT 0,
                    is_deleted INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                    FOREIGN KEY (sender_id) REFERENCES messenger_users (id) ON DELETE CASCADE
                );
            """)

            # 5. Message Attachments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_attachments (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    duration_sec REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES chat_messages (id) ON DELETE CASCADE
                );
            """)

            # 6. WebRTC Meeting Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_sessions (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    initiator_id TEXT NOT NULL,
                    call_type TEXT DEFAULT 'video', -- 'audio', 'video', 'screen'
                    status TEXT DEFAULT 'active', -- 'active', 'ended', 'missed'
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                    FOREIGN KEY (initiator_id) REFERENCES messenger_users (id) ON DELETE CASCADE
                );
            """)

            # Create performance indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_room_time ON chat_messages(room_id, created_at DESC);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_user ON chat_members(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_source ON messenger_users(source);")

            logger.info("Messenger database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Messenger database: {e}")
        raise
