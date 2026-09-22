"""Коннектор CRM для Enterprise Knowledge Platform."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.connectors.base import BaseConnector


class CRMConnector(BaseConnector):
    """Коннектор для интеграции с CRM системами."""

    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить изменения из CRM."""
        # TODO: Реализовать подключение к CRM API
        return []

    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать элемент CRM в унифицированный формат."""
        # TODO: Реализовать нормализацию
        return item
