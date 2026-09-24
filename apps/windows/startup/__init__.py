# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor Application Init
# =============================================================================
# Description:
#   Экспорт основных компонентов приложения Windows Startup Auditor.
#
# Examples:
#   >>> from apps.windows.startup import init_router, StartupAuditor
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.startup
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Приложение Windows Startup & Autorun Auditor."""

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
from apps.windows.startup.router import init_router
from apps.windows.startup.tui import StartupAuditorTUI

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
