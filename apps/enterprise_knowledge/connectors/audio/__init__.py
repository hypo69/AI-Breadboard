"""Коннектор аудио для Enterprise Knowledge Platform."""

from __future__ import annotations

from typing import Any

from apps.enterprise_knowledge.connectors.base import BaseConnector


class AudioConnector(BaseConnector):
    """Коннектор для обработки аудиозаписей (транскрипция, диаризация)."""

    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить аудиофайлы для обработки."""
        # TODO: Реализовать подключение к источнику аудио
        return []

    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать аудио элемент в унифицированный формат."""
        # TODO: Реализовать нормализацию
        return item
