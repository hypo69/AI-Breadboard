"""Модуль разрешения идентичности сотрудников."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore


class IdentityResolver:
    """Разрешение идентификаторов сотрудников по различным стратегиям."""

    def __init__(self, store: KnowledgeStore, strategies: list[str] | None = None) -> None:
        self.store = store
        self.strategies = strategies or ["email", "alias", "employee_id"]

    def resolve(self, identity: str) -> str | None:
        """Разрешить идентификатор в employee_id."""
        # TODO: Реализовать стратегии разрешения
        return self.store.resolve_employee(identity)

    def batch_resolve(self, identities: list[str]) -> dict[str, str | None]:
        """Пакетное разрешение идентификаторов."""
        return {identity: self.resolve(identity) for identity in identities}
