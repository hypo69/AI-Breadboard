# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor Core Package Init
# =============================================================================
# Description:
#   Экспорт основных классов и моделей ядра аудитора автозапуска Windows.
#
# Examples:
#   >>> from apps.windows_startup_auditor.core import StartupAuditor, StartupScanner
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows_startup_auditor.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет ядра сканирования и аудита автозапуска Windows."""

from apps.windows_startup_auditor.core.models import (
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
from apps.windows_startup_auditor.core.scanner import StartupScanner
from apps.windows_startup_auditor.core.auditor import StartupAuditor
from apps.windows_startup_auditor.core.manager import StartupManager

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
