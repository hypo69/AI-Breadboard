# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Resolvers - Semantic
# =============================================================================
# Description:
#   Резолвер семантического и полнотекстового поиска (FTS5). Выполняет поиск по смыслу,
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.resolvers.semantic import SemanticResolver
#
#     service = SemanticResolver()
#
# File: semantic.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.resolvers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Резолвер семантического и полнотекстового поиска (FTS5). Выполняет поиск по смыслу,"""

from typing import Optional
from ..models import ArtifactInput, KnowledgeEntity, LookupLevel
from ..storage import WikiStorage
from .base import BaseResolver


class SemanticResolver(BaseResolver):
    """Резолвер семантического сопоставления и полнотекстового поиска FTS5."""

    def __init__(self, storage: WikiStorage) -> None:
        """Инициализирует SemanticResolver.

        Args:
            storage: Экземпляр хранилища WikiStorage.
        """
        super().__init__(level=LookupLevel.SEMANTIC, name="SemanticFTSResolver")
        self.storage = storage

    async def resolve(self, artifact: ArtifactInput) -> Optional[KnowledgeEntity]:
        """Выполняет полнотекстовый поиск по сообщению или описанию симптома.

        Args:
            artifact: Входной артефакт.

        Returns:
            KnowledgeEntity с наивысшим рангом релевантности или None.
        """
        search_query = artifact.message or artifact.raw_query or ""
        if not search_query or len(search_query.strip()) < 3:
            return None

        candidates = self.storage.search_fts(search_query, limit=1)
        if candidates:
            return candidates[0]

        return None
