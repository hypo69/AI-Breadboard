# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Resolvers - Base
# =============================================================================
# Description:
#   Базовый абстрактный интерфейс для уровней поиска и разрешения артефактов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.resolvers.base import BaseResolver
#
#     service = BaseResolver()
#
# File: base.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.resolvers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Базовый абстрактный интерфейс для уровней поиска и разрешения артефактов."""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import ArtifactInput, KnowledgeEntity, LookupLevel


class BaseResolver(ABC):
    """Абстрактный резолвер артефактов."""

    def __init__(self, level: LookupLevel, name: str) -> None:
        """Инициализирует базовый резолвер.

        Args:
            level: Уровень поиска (LookupLevel).
            name: Человекочитаемое имя резолвера.
        """
        self.level = level
        self.name = name

    @abstractmethod
    async def resolve(self, artifact: ArtifactInput) -> Optional[KnowledgeEntity]:
        """Пытается разрешить артефакт на текущем уровне.

        Args:
            artifact: Входной артефакт.

        Returns:
            Сущность KnowledgeEntity или None, если знание не найдено.
        """
        raise NotImplementedError
