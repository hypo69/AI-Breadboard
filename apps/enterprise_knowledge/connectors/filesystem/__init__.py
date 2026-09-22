"""Коннектор файловой системы для Enterprise Knowledge Platform."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.enterprise_knowledge.connectors.base import BaseConnector


class FilesystemConnector(BaseConnector):
    """Коннектор для интеграции с файловой системой."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.base_path = Path(config.get("base_path", "data/enterprise_knowledge/files"))

    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить изменения в файловой системе."""
        # TODO: Реализовать мониторинг изменений файлов
        return []

    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать элемент файловой системы в унифицированный формат."""
        # TODO: Реализовать нормализацию
        return item
