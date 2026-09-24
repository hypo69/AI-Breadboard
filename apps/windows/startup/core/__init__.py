# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor Core Package Init
# =============================================================================
# Description:
#   Экспорт основных классов и моделей ядра аудитора автозапуска Windows.
#
# Examples:
#   >>> from apps.windows.startup.core import StartupAuditor, StartupScanner
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.startup.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет ядра сканирования и аудита автозапуска Windows."""

from apps.windows.startup.core.models import (
    AuditReport,
    AuditSummary,
    ItemCategory,
    LocationInfo,
    RiskLevel,
    StartupEntry,
    StartupLocationType,
    ToggleRequest,
    ToggleResponse,
)
from apps.windows.startup.core.scanner import StartupScanner
from apps.windows.startup.core.auditor import StartupAuditor
from apps.windows.startup.core.manager import StartupManager

__all__ = [
    "AuditReport",
    "AuditSummary",
    "ItemCategory",
    "LocationInfo",
    "RiskLevel",
    "StartupEntry",
    "StartupLocationType",
    "ToggleRequest",
    "ToggleResponse",
    "StartupScanner",
    "StartupAuditor",
    "StartupManager",
]
