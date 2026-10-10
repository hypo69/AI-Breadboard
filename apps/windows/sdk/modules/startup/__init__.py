# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Startup -   Init  
# =============================================================================
# Description:
#   Приложение Windows Startup & Autorun Auditor.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.startup
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 14:05:00
# =============================================================================

"""Приложение Windows Startup & Autorun Auditor."""

from apps.windows.sdk.modules.startup.core.models import (
    AuditReport,
    AuditSummary,
    ItemCategory,
    LocationInfo,
    RiskLevel,
    StartupArchiveEntry,
    StartupChangeItem,
    StartupEntry,
    StartupLocationType,
    StartupRefreshResponse,
    ToggleRequest,
    ToggleResponse,
)
from apps.windows.sdk.modules.startup.core.scanner import StartupScanner
from apps.windows.sdk.modules.startup.core.auditor import StartupAuditor
from apps.windows.sdk.modules.startup.core.manager import StartupManager
from apps.windows.sdk.modules.startup.tui import StartupAuditorTUI


def init_router(*args, **kwargs):
    """Ленивая инициализация FastAPI роутера Startup Auditor."""
    from apps.windows.sdk.modules.startup.router import init_router as _init
    return _init(*args, **kwargs)

__all__ = [
    'init_router',
    'StartupAuditor',
    'StartupScanner',
    'StartupManager',
    'StartupAuditorTUI',
    'StartupEntry',
    'StartupLocationType',
    'RiskLevel',
    'ItemCategory',
    'LocationInfo',
    'AuditSummary',
    'AuditReport',
    'StartupChangeItem',
    'StartupArchiveEntry',
    'StartupRefreshResponse',
    'ToggleRequest',
    'ToggleResponse',
]