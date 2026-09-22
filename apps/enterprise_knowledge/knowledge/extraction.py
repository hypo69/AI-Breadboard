"""Извлечение фактов из текстов."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore


class FactExtractor:
    """Извлечение фактов из неструктурированных данных."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def extract(self, text: str, employee_id: str | None = None) -> list[dict[str, Any]]:
        """Извлечь факты из текста."""
        # TODO: Реализовать извлечение фактов с помощью LLM
        return []

    def extract_from_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Извлечь факты из события."""
        text = event.get("content", {}).get("text", "")
        return self.extract(text, event.get("employee_id"))
