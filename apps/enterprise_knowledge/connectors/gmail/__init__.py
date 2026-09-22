"""Коннектор Gmail для Enterprise Knowledge Platform."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.connectors.base import BaseConnector


class GmailConnector(BaseConnector):
    """Коннектор для интеграции с Gmail."""

    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить изменения из Gmail."""
        # TODO: Реализовать подключение к Gmail API
        return []

    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать элемент Gmail в унифицированный формат."""
        # TODO: Реализовать нормализацию
        return item
