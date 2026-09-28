from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from header import __root__
from logger import logger
DB_PATH: Path = __root__ / 'data' / 'helpdesk.db'

def get_db_connection() -> sqlite3.Connection:
    """Acquire a SQLite database connection configured with Row factory and WAL mode.

    Returns:
        sqlite3.Connection: Initialized SQLite connection.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA foreign_keys=ON;')
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
        logger.error(f'Helpdesk DB transaction failed: {e}')
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Initialize database tables and indexes for helpdesk tickets, messages, and operators."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("\n                CREATE TABLE IF NOT EXISTS helpdesk_tickets (\n                    id TEXT PRIMARY KEY,\n                    ticket_number INTEGER UNIQUE,\n                    user_id TEXT NOT NULL,\n                    user_name TEXT NOT NULL,\n                    user_email TEXT,\n                    subject TEXT NOT NULL,\n                    category TEXT DEFAULT 'general',\n                    status TEXT NOT NULL DEFAULT 'open',\n                    priority TEXT NOT NULL DEFAULT 'normal',\n                    assigned_to TEXT,\n                    assigned_name TEXT,\n                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    closed_at DATETIME\n                );\n            ")
            cursor.execute("\n                CREATE TABLE IF NOT EXISTS helpdesk_messages (\n                    id TEXT PRIMARY KEY,\n                    ticket_id TEXT NOT NULL,\n                    sender_id TEXT NOT NULL,\n                    sender_name TEXT NOT NULL,\n                    sender_type TEXT NOT NULL DEFAULT 'user',\n                    message_type TEXT NOT NULL DEFAULT 'text',\n                    content TEXT NOT NULL,\n                    is_internal_note INTEGER DEFAULT 0,\n                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    FOREIGN KEY (ticket_id) REFERENCES helpdesk_tickets (id) ON DELETE CASCADE\n                );\n            ")
            cursor.execute("\n                CREATE TABLE IF NOT EXISTS helpdesk_operators (\n                    id TEXT PRIMARY KEY,\n                    user_id TEXT UNIQUE NOT NULL,\n                    display_name TEXT NOT NULL,\n                    role TEXT DEFAULT 'operator',\n                    is_online INTEGER DEFAULT 0,\n                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP\n                );\n            ")
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hd_tickets_status ON helpdesk_tickets(status);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hd_tickets_user ON helpdesk_tickets(user_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hd_tickets_assigned ON helpdesk_tickets(assigned_to);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hd_messages_ticket ON helpdesk_messages(ticket_id);')
            cursor.execute('\n                CREATE TABLE IF NOT EXISTS helpdesk_sequences (\n                    name TEXT PRIMARY KEY,\n                    current_value INTEGER DEFAULT 1000\n                );\n            ')
            cursor.execute("\n                INSERT OR IGNORE INTO helpdesk_sequences (name, current_value)\n                VALUES ('ticket_number', 1000);\n            ")
        logger.info('Helpdesk database initialized successfully.')
    except Exception as e:
        logger.error(f'Failed to initialize Helpdesk database: {e}')
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
            return int(row['current_value'])
        return 1001