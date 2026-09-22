"""Гибридный поиск."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore

from apps.enterprise_knowledge.retrieval.structured import StructuredSearch
from apps.enterprise_knowledge.retrieval.fulltext import FullTextSearch
from apps.enterprise_knowledge.retrieval.vector import VectorSearch
from apps.enterprise_knowledge.retrieval.graph import GraphSearch


class HybridSearch:
    """Гибридный поиск, объединяющий несколько стратегий."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store
        self.structured = StructuredSearch(store)
        self.fulltext = FullTextSearch(store)
        self.vector = VectorSearch(store)
        self.graph = GraphSearch(store)

    def search(self, query: str, employee_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Гибридный поиск с объединением результатов."""
        # TODO: Реализовать гибридный поиск
        structured_results = self.structured.search({"employee_id": employee_id} if employee_id else {}, limit)
        fulltext_results = self.fulltext.search(query, limit)
        
        return {
            "query": query,
            "structured": structured_results,
            "fulltext": fulltext_results,
            "vector": [],
            "graph": []
        }
