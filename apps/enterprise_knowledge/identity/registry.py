# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge Identity - Registry
# =============================================================================
# Description:
#   Регистр идентичности сотрудников.
#
# Usage Examples:
#   Python API:
#     from apps.enterprise_knowledge.identity.registry import IdentityRegistry
#
#     service = IdentityRegistry()
#
# File: registry.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge.identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Регистр идентичности сотрудников."""

from typing import Any
from apps.enterprise_knowledge.storage import KnowledgeStore

class IdentityRegistry:
    """Регистр идентичности сотрудников с поддержкой алиасов."""

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def register(self, employee: dict[str, Any]) -> dict[str, Any]:
        """Зарегистрировать сотрудника и алиасы."""
        return self.store.add_employee(employee)

    def resolve(self, identity: str) -> str | None:
        """Разрешить идентификатор в employee_id."""
        return self.store.resolve_employee(identity)

    def get_profile(self, employee_id: str) -> dict[str, Any] | None:
        """Получить профиль сотрудника."""
        return self.store.get_employee(employee_id)