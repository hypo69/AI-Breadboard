# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Resolvers - Fingerprint
# =============================================================================
# Description:
#   Резолвер сопоставления по структурным шаблонам и отпечаткам (fingerprints).
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.resolvers.fingerprint import FingerprintResolver
#
#     service = FingerprintResolver()
#
# File: fingerprint.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.resolvers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Резолвер сопоставления по структурным шаблонам и отпечаткам (fingerprints)."""

from typing import Optional
from ..models import ArtifactInput, KnowledgeEntity, LookupLevel
from ..normalizer import CanonicalKeyNormalizer
from ..storage import WikiStorage
from .base import BaseResolver


class FingerprintResolver(BaseResolver):
    """Резолвер сопоставления по отпечаткам сообщений и провайдеров Level 2."""

    def __init__(self, storage: WikiStorage) -> None:
        """Инициализирует FingerprintResolver.

        Args:
            storage: Экземпляр хранилища WikiStorage.
        """
        super().__init__(level=LookupLevel.FINGERPRINT, name="FingerprintTemplateResolver")
        self.storage = storage

    async def resolve(self, artifact: ArtifactInput) -> Optional[KnowledgeEntity]:
        """Ищет сущность по вычисленному структурному отпечатку.

        Args:
            artifact: Входной артефакт.

        Returns:
            KnowledgeEntity при шаблонном совпадении или None.
        """
        fingerprint = CanonicalKeyNormalizer.compute_fingerprint(artifact)
        if not fingerprint:
            return None

        return self.storage.find_by_fingerprint(fingerprint)
