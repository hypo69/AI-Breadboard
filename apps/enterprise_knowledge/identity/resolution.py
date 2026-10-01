# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge Identity - Resolution
# =============================================================================
# Description:
#   Модуль разрешения идентичности сотрудников.
#
# Usage Examples:
#   Python API:
#     from apps.enterprise_knowledge.identity.resolution import IdentityResolver
#
#     service = IdentityResolver()
#
# File: resolution.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge.identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль разрешения идентичности сотрудников."""

from typing import Any
from apps.enterprise_knowledge.storage import KnowledgeStore

class IdentityResolver:
    """Разрешение идентификаторов сотрудников по различным стратегиям."""

    def __init__(self, store: KnowledgeStore, strategies: list[str] | None=None) -> None:
        self.store = store
        self.strategies = strategies or ['email', 'alias', 'employee_id']

    def resolve(self, identity: str) -> str | None:
        """Разрешить идентификатор в employee_id."""
        return self.store.resolve_employee(identity)

    def batch_resolve(self, identities: list[str]) -> dict[str, str | None]:
        """Пакетное разрешение идентификаторов."""
        return {identity: self.resolve(identity) for identity in identities}