"""Базовый интерфейс коннекторов для Enterprise Knowledge Platform."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Базовый класс для всех коннекторов источников данных."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def fetch_changes(self, since: str | None = None) -> list[dict[str, Any]]:
        """Получить изменения с последней синхронизации."""
        raise NotImplementedError

    @abstractmethod
    async def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Нормализовать элемент в унифицированный формат."""
        raise NotImplementedError

    async def connect(self) -> bool:
        """Установить соединение с источником."""
        return True

    async def disconnect(self) -> bool:
        """Разорвать соединение с источником."""
        return True
