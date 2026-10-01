# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge Connectors - Base
# =============================================================================
# Description:
#   Базовый интерфейс коннекторов для Enterprise Knowledge Platform.
#
# Usage Examples:
#   Python API:
#     from apps.enterprise_knowledge.connectors.base import BaseConnector
#
#     service = BaseConnector()
#
# File: base.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge.connectors
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Базовый интерфейс коннекторов для Enterprise Knowledge Platform."""

from abc import ABC, abstractmethod
from typing import Any

class BaseConnector(ABC):
    """Базовый класс для всех коннекторов источников данных."""

    def __init__(self, config: dict[str, Any] | None=None) -> None:
        self.config = config or {}

    @abstractmethod
    async def fetch_changes(self, since: str | None=None) -> list[dict[str, Any]]:
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