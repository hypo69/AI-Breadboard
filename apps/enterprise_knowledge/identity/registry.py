"""Регистр идентичности сотрудников."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.storage import KnowledgeStore


class IdentityRegistry:
    """Регистр идентичности сотрудников с поддержкой алиасов."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def register(self, employee: dict[str, Any]) -> dict[str, Any]:
        """Зарегистрировать сотрудника и алиасы."""
        return self.store.add_employee(employee)

    def resolve(self, identity: str) -> str | None:
        """Разрешить идентификатор в employee_id."""
        return self.store.resolve_employee(identity)

    def get_profile(self, employee_id: str) -> dict[str, Any] | None:
        """Получить профиль сотрудника."""
        return self.store.get_employee(employee_id)
