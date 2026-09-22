"""Коннектор Outlook для Enterprise Knowledge Platform."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.connectors.base import BaseConnector


class OutlookConnector(BaseConnector):
    """Коннектор для интеграции с Outlook (email, календарь, контакты)."""

    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить изменения из Outlook."""
        # TODO: Реализовать подключение к Outlook API
        return []

    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать элемент Outlook в унифицированный формат."""
        # TODO: Реализовать нормализацию
        return item
