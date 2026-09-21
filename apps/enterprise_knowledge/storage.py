"""Локальное SQLite-хранилище для накопительной базы знаний."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("data/enterprise_knowledge/knowledge.db")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeStore:
    """Хранит исходные события, сущности, факты и полнотекстовый индекс."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        configured_path = db_path or os.getenv("ENTERPRISE_KNOWLEDGE_DB")
        self.db_path = Path(configured_path or DEFAULT_DB_PATH)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT,
                    email TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS employee_aliases (
                    alias TEXT NOT NULL,
                    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
                    confidence REAL NOT NULL DEFAULT 1.0,
                    verified INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(alias, employee_id)
                );
                CREATE TABLE IF NOT EXISTS ingestion_events (
                    event_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    external_id TEXT,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'processed',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL REFERENCES ingestion_events(event_id),
                    source_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS facts (
                    fact_id TEXT PRIMARY KEY,
                    employee_id TEXT REFERENCES employees(employee_id),
                    predicate TEXT NOT NULL,
                    object_value TEXT NOT NULL,
                    valid_from TEXT,
                    valid_to TEXT,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS processing_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    error TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_facts_employee ON facts(employee_id);
                CREATE INDEX IF NOT EXISTS idx_facts_status ON facts(status);
                CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(
                    source_id UNINDEXED, content, metadata
                );
                """
            )

    def add_employee(self, employee: dict[str, Any]) -> dict[str, Any]:
        employee_id = employee["employee_id"]
        now = utc_now()
        aliases = {employee.get("name", ""), *employee.get("aliases", [])}
        if employee.get("email"):
            aliases.add(employee["email"])
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO employees(employee_id, name, department, email, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(employee_id) DO UPDATE SET name=excluded.name,
                   department=excluded.department, email=excluded.email""",
                (employee_id, employee["name"], employee.get("department"), employee.get("email"), now),
            )
            for alias in aliases:
                if alias:
                    connection.execute(
                        """INSERT INTO employee_aliases(alias, employee_id, confidence, verified)
                           VALUES (?, ?, ?, ?)
                           ON CONFLICT(alias, employee_id) DO UPDATE SET confidence=excluded.confidence,
                           verified=excluded.verified""",
                        (alias.casefold(), employee_id, employee.get("confidence", 1.0), int(employee.get("verified", False))),
                    )
        return self.get_employee(employee_id) or {}

    def resolve_employee(self, identity: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT employee_id FROM employee_aliases WHERE alias = ? ORDER BY verified DESC, confidence DESC LIMIT 1",
                (identity.casefold(),),
            ).fetchone()
        return row["employee_id"] if row else None

    def get_employee(self, employee_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            employee = connection.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)).fetchone()
            if not employee:
                return None
            facts = connection.execute(
                "SELECT * FROM facts WHERE employee_id = ? ORDER BY valid_from DESC, created_at DESC", (employee_id,)
            ).fetchall()
        result = dict(employee)
        result["facts"] = [dict(fact) for fact in facts]
        return result

    def ingest(self, event: dict[str, Any]) -> dict[str, Any]:
        event_id = event["event_id"]
        source = event.get("source", {})
        source_type = source.get("type", "manual")
        occurred_at = event.get("occurred_at", utc_now())
        content = event.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else str(content)
        source_id = f"SRC-{source_type}-{source.get('external_id') or event_id}-{event_id}"
        with self._connect() as connection:
            existing = connection.execute("SELECT status FROM ingestion_events WHERE event_id = ?", (event_id,)).fetchone()
            if existing:
                return {"event_id": event_id, "status": "duplicate", "source_id": source_id, "facts_created": 0}
            now = utc_now()
            connection.execute(
                "INSERT INTO ingestion_events VALUES (?, ?, ?, ?, ?, 'processed', ?)",
                (event_id, source_type, source.get("external_id"), occurred_at, json.dumps(event, ensure_ascii=False), now),
            )
            connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?)",
                (source_id, event_id, source_type, text, json.dumps(event.get("metadata", {}), ensure_ascii=False), now),
            )
            connection.execute("INSERT INTO source_fts(source_id, content, metadata) VALUES (?, ?, ?)", (source_id, text, json.dumps(event.get("metadata", {}), ensure_ascii=False)))
            facts_created = 0
            for fact in event.get("facts", []):
                employee_id = fact.get("employee_id")
                if not employee_id and fact.get("subject"):
                    employee_id = self.resolve_employee(str(fact["subject"]))
                fact_id = fact.get("fact_id") or self._fact_id(event_id, fact)
                connection.execute(
                    """INSERT OR IGNORE INTO facts(fact_id, employee_id, predicate, object_value,
                       valid_from, valid_to, status, source_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (fact_id, employee_id, fact["predicate"], str(fact["object"]), fact.get("valid_from", occurred_at), fact.get("valid_to"), fact.get("status", "proposed"), source_id, now),
                )
                facts_created += connection.execute("SELECT changes()").fetchone()[0]
        return {"event_id": event_id, "status": "processed", "source_id": source_id, "facts_created": facts_created}

    @staticmethod
    def _fact_id(event_id: str, fact: dict[str, Any]) -> str:
        value = f"{event_id}:{fact.get('subject')}:{fact['predicate']}:{fact['object']}"
        return "FACT-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    def search(self, query: str, employee_id: str | None = None, status: str | None = None, limit: int = 20) -> dict[str, Any]:
        fact_parameters: list[Any] = [f"%{query}%", f"%{query}%"]
        filters = ""
        if employee_id:
            filters += " AND f.employee_id = ?"
            fact_parameters.append(employee_id)
        if status:
            filters += " AND f.status = ?"
            fact_parameters.append(status)
        with self._connect() as connection:
            sources = connection.execute(
                "SELECT source_id, content, metadata FROM source_fts WHERE source_fts MATCH ? LIMIT ?", (query, limit)
            ).fetchall()
            facts = connection.execute(
                f"""SELECT f.*, e.name AS employee_name FROM facts f LEFT JOIN employees e ON e.employee_id=f.employee_id
                    WHERE (f.predicate LIKE ? OR f.object_value LIKE ?) {filters}
                    ORDER BY f.valid_from DESC LIMIT ?""",
                [*fact_parameters, limit],
            ).fetchall()
        return {"query": query, "facts": [dict(row) for row in facts], "sources": [dict(row) for row in sources]}
