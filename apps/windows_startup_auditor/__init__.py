# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor Application Init
# =============================================================================
# Description:
#   Экспорт основных компонентов приложения Windows Startup Auditor.
#
# Examples:
#   >>> from apps.windows_startup_auditor import init_router, StartupAuditor
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows_startup_auditor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Приложение Windows Startup & Autorun Auditor."""

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
from apps.windows_startup_auditor.router import init_router
from apps.windows_startup_auditor.tui import StartupAuditorTUI

__all__ = [
    "init_router",
    "StartupAuditor",
    "StartupScanner",
    "StartupManager",
    "StartupAuditorTUI",
    "StartupEntry",
    "StartupLocationType",
    "RiskLevel",
    "ItemCategory",
    "LocationInfo",
    "AuditSummary",
    "AuditReport",
    "ToggleRequest",
    "ToggleResponse",
]
