"""Коннектор Teams для Enterprise Knowledge Platform."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.connectors.base import BaseConnector


class TeamsConnector(BaseConnector):
    """Коннектор для интеграции с Microsoft Teams (сообщения, звонки)."""

    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить изменения из Teams."""
        # TODO: Реализовать подключение к Teams API
        return []

    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать элемент Teams в унифицированный формат."""
        # TODO: Реализовать нормализацию
        return item
