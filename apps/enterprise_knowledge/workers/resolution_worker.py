"""Рабочий процесс разрешения идентичности."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore
from apps.enterprise_knowledge.identity.resolution import IdentityResolver


class ResolutionWorker:
    """Рабочий процесс для разрешения идентичности сотрудников."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store
        self.resolver = IdentityResolver(store)

    async def resolve_batch(self, identities: list[str]) -> dict[str, str | None]:
        """Пакетное разрешение идентификаторов."""
        return self.resolver.batch_resolve(identities)

    async def find_duplicates(self) -> list[dict[str, Any]]:
        """Найти потенциальные дубликаты сотрудников."""
        # TODO: Реализовать поиск дубликатов
        return []
