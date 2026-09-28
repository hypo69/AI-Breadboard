"""Модуль хранилища Dead Letter Queue (DLQ) на базе SQLite."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# Динамическое определение пути к базе данных DLQ от текущего файла
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "dlq_store.db"


class DLQStorage:
    """Класс для управления локальной базой данных тупиковой очереди (DLQ)."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Инициализация подключения и структуры таблицы DLQ.

        Args:
            db_path: Кастомный путь к файлу SQLite базы данных.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Создать новое соединение с SQLite БД."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Создание таблицы dlq_messages и индексов при их отсутствии."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dlq_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'PENDING'
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dlq_status ON dlq_messages(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dlq_source ON dlq_messages(source);")

    def push(
        self,
        source: str,
        error_message: str,
        payload: Dict[str, Any] | str | None = None,
        status: str = "PENDING",
    ) -> int:
        """Добавить новое ошибочное сообщение или задачу в DLQ.

        Args:
            source: Источник возникновения ошибки (например, 'gemini-cli', 'subagent-research').
            error_message: Текст или стек ошибки.
            payload: Данные запроса или контекст задачи.
            status: Начальный статус (по умолчанию 'PENDING').

        Returns:
            int: Идентификатор созданной записи в DLQ.
        """
        if not source or not source.strip():
            raise ValueError("Параметр 'source' не может быть пустым.")
        if not error_message or not error_message.strip():
            raise ValueError("Параметр 'error_message' не может быть пустым.")

        if isinstance(payload, dict):
            payload_str = json.dumps(payload, ensure_ascii=False)
        elif isinstance(payload, str):
            payload_str = payload
        else:
            payload_str = json.dumps({}, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dlq_messages (source, error_message, payload, status)
                VALUES (?, ?, ?, ?)
                """,
                (source.strip(), error_message.strip(), payload_str, status.upper()),
            )
            return cursor.lastrowid or 0

    def list_all(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Получить список сообщений DLQ с возможностью фильтрации.

        Args:
            status: Фильтр по статусу ('PENDING', 'RETRYING', 'RESOLVED', 'FAILED').
            source: Фильтр по источнику.
            limit: Максимальное количество возвращаемых записей.

        Returns:
            List[Dict[str, Any]]: Список записей DLQ.
        """
        query = "SELECT * FROM dlq_messages WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status.upper())
        if source:
            query += " AND source = ?"
            params.append(source.strip())

        query += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, limit))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, msg_id: int) -> Optional[Dict[str, Any]]:
        """Получить одну запись DLQ по идентификатору.

        Args:
            msg_id: Идентификатор записи.

        Returns:
            Optional[Dict[str, Any]]: Запись DLQ или None, если запись не найдена.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dlq_messages WHERE id = ?", (msg_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_status(self, msg_id: int, status: str) -> bool:
        """Обновить статус записи в DLQ.

        Args:
            msg_id: Идентификатор записи.
            status: Новый статус ('PENDING', 'RETRYING', 'RESOLVED', 'FAILED').

        Returns:
            bool: True, если запись была обновлена.
        """
        valid_statuses = {"PENDING", "RETRYING", "RESOLVED", "FAILED"}
        new_status = status.upper()
        if new_status not in valid_statuses:
            raise ValueError(f"Недопустимый статус '{status}'. Допустимые: {valid_statuses}")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE dlq_messages
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_status, msg_id),
            )
            return cursor.rowcount > 0

    def increment_retry(self, msg_id: int) -> bool:
        """Увеличить счетчик попыток повтора (retry_count) на 1."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE dlq_messages
                SET retry_count = retry_count + 1,
                    status = 'RETRYING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (msg_id,),
            )
            return cursor.rowcount > 0

    def purge(self, status: Optional[str] = None) -> int:
        """Очистить записи DLQ.

        Args:
            status: Опциональный фильтр по статусу (например, 'RESOLVED'). Если None — удаляются все.

        Returns:
            int: Количество удаленных записей.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("DELETE FROM dlq_messages WHERE status = ?", (status.upper(),))
            else:
                cursor.execute("DELETE FROM dlq_messages")
            return cursor.rowcount

    def get_stats(self) -> Dict[str, int]:
        """Получить статистику сообщений по статусам."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as cnt
                FROM dlq_messages
                GROUP BY status
            """)
            stats = {row["status"]: row["cnt"] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) as total FROM dlq_messages")
            stats["TOTAL"] = cursor.fetchone()["total"]
            return stats
