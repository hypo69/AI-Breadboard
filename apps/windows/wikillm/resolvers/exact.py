# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Resolvers - Exact
# =============================================================================
# Description:
#   Резолвер точного совпадения по каноническому ключу (canonical_key) в SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.resolvers.exact import ExactResolver
#
#     service = ExactResolver()
#
# File: exact.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.resolvers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Резолвер точного совпадения по каноническому ключу (canonical_key) в SQLite."""

from typing import Optional
from ..models import ArtifactInput, KnowledgeEntity, LookupLevel
from ..normalizer import CanonicalKeyNormalizer
from ..storage import WikiStorage
from .base import BaseResolver


class ExactResolver(BaseResolver):
    """Резолвер точного соответствия Level 1 (O(1) SQLite lookup)."""

    def __init__(self, storage: WikiStorage) -> None:
        """Инициализирует ExactResolver.

        Args:
            storage: Экземпляр хранилища WikiStorage.
        """
        super().__init__(level=LookupLevel.EXACT, name="ExactMatchResolver")
        self.storage = storage

    async def resolve(self, artifact: ArtifactInput) -> Optional[KnowledgeEntity]:
        """Ищет запись в базе данных по canonical_key.

        Args:
            artifact: Входной артефакт.

        Returns:
            KnowledgeEntity при точном совпадении или None.
        """
        canonical_key = CanonicalKeyNormalizer.compute_canonical_key(artifact)
        if not canonical_key or canonical_key == "unknown:unspecified":
            return None

        return self.storage.get_entity(canonical_key)
