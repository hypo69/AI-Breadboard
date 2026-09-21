"""Сценарии платформы корпоративных знаний."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore


class EnterpriseKnowledgeEngine:
    """Координирует identity resolution, ingestion и hybrid retrieval."""

    def __init__(self, db_path: str | None = None) -> None:
        self.store = KnowledgeStore(db_path)

    def register_employee(self, employee: dict[str, Any]) -> dict[str, Any]:
        return self.store.add_employee(employee)

    def ingest(self, event: dict[str, Any]) -> dict[str, Any]:
        return self.store.ingest(event)

    def query(self, query: str, employee_id: str | None = None, status: str | None = None, limit: int = 20) -> dict[str, Any]:
        return self.store.search(query, employee_id=employee_id, status=status, limit=limit)

    def employee(self, employee_id: str) -> dict[str, Any] | None:
        return self.store.get_employee(employee_id)