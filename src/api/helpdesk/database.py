# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Database Manager and Connection Provider
# =============================================================================
# Description:
#   Provides SQLite database connection pooling, schema initialization,
#   and transactional contexts for the centralized Helpdesk ticket system.
#
# File: database.py
# Project: ai-breadboard
# Package: src.api.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

from header import __root__
from src.logger import logger

DB_PATH: Path = __root__ / 'data' / 'helpdesk.db'


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
        logger.error(f"Helpdesk DB transaction failed: {e}")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables and indexes for helpdesk tickets, messages, and operators."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Helpdesk Tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS helpdesk_tickets (
                    id TEXT PRIMARY KEY,
                    ticket_number INTEGER UNIQUE,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    user_email TEXT,
                    subject TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    status TEXT NOT NULL DEFAULT 'open',
                    priority TEXT NOT NULL DEFAULT 'normal',
                    assigned_to TEXT,
                    assigned_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed_at DATETIME
                );
            """)

            # 2. Helpdesk Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS helpdesk_messages (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT NOT NULL,
                    sender_type TEXT NOT NULL DEFAULT 'user',
                    message_type TEXT NOT NULL DEFAULT 'text',
                    content TEXT NOT NULL,
                    is_internal_note INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES helpdesk_tickets (id) ON DELETE CASCADE
                );
            """)

            # 3. Helpdesk Operators table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS helpdesk_operators (
                    id TEXT PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT DEFAULT 'operator',
                    is_online INTEGER DEFAULT 0,
                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 4. Create helpful indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_tickets_status ON helpdesk_tickets(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_tickets_user ON helpdesk_tickets(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_tickets_assigned ON helpdesk_tickets(assigned_to);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_messages_ticket ON helpdesk_messages(ticket_id);")

            # Initialize auto-increment ticket counter if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS helpdesk_sequences (
                    name TEXT PRIMARY KEY,
                    current_value INTEGER DEFAULT 1000
                );
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO helpdesk_sequences (name, current_value)
                VALUES ('ticket_number', 1000);
            """)

        logger.info("Helpdesk database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Helpdesk database: {e}")
        raise


def get_next_ticket_number() -> int:
    """Generate the next sequential ticket number atomically.

    Returns:
        int: Next ticket sequence number.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE helpdesk_sequences SET current_value = current_value + 1 WHERE name = 'ticket_number';")
        row = cursor.execute("SELECT current_value FROM helpdesk_sequences WHERE name = 'ticket_number';").fetchone()
        if row:
            return int(row["current_value"])
        return 1001
