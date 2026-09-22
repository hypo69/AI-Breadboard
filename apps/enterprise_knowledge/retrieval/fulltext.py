"""Полнотекстовый поиск."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore


class FullTextSearch:
    """Полнотекстовый поиск по исходным текстам."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Поиск по полнотекстовому индексу."""
        # TODO: Реализовать полнотекстовый поиск
        return []
