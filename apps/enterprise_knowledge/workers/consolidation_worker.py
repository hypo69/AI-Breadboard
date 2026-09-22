"""Рабочий процесс консолидации знаний."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore
from apps.enterprise_knowledge.knowledge.consolidation import KnowledgeConsolidator


class ConsolidationWorker:
    """Рабочий процесс для консолидации знаний и проверки противоречий."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store
        self.consolidator = KnowledgeConsolidator(store)

    async def run_consolidation(self) -> dict[str, Any]:
        """Запустить консолидацию всех новых фактов."""
        return self.consolidator.run_batch_consolidation()
