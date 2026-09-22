"""Рабочий процесс ингестии данных."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore
from apps.enterprise_knowledge.connectors.base import BaseConnector


class IngestionWorker:
    """Рабочий процесс для ингестии данных из коннекторов."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    async def process_connector(self, connector: BaseConnector, batch_size: int = 100) -> dict[str, Any]:
        """Обработать изменения от коннектора."""
        # TODO: Реализовать обработку коннектора
        return {"processed": 0, "errors": []}

    async def run_batch(self, connectors: list[BaseConnector]) -> dict[str, Any]:
        """Запустить пакетную обработку."""
        # TODO: Реализовать пакетную обработку
        return {}
