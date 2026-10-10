# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Models
# =============================================================================
# Description:
#   Модели данных аудита, диагностики и безопасного выполнения (Фасад contracts).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.models import RiskLevel, AuditFinding, FullAuditReport
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:37:00
# =============================================================================

from __future__ import annotations
"""Модели данных аудита, диагностики и безопасного выполнения для Windows."""

from apps.windows.contracts.enums import RiskLevel, ActionType
from apps.windows.contracts.audit import (
    RemediationAction,
    AuditFinding,
    DomainAuditResult,
    HealthScoreSummary,
    FullAuditReport,
    InvestigationReport,
)

__all__ = [
    "RiskLevel",
    "ActionType",
    "RemediationAction",
    "AuditFinding",
    "DomainAuditResult",
    "HealthScoreSummary",
    "FullAuditReport",
    "InvestigationReport",
]