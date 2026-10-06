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
# Package: apps.windows.modules.startup
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 14:05:00
# =============================================================================

"""Приложение Windows Startup & Autorun Auditor."""

from apps.windows.modules.startup.core.models import (
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
from apps.windows.modules.startup.core.scanner import StartupScanner
from apps.windows.modules.startup.core.auditor import StartupAuditor
from apps.windows.modules.startup.core.manager import StartupManager
from apps.windows.modules.startup.router import init_router
from apps.windows.modules.startup.tui import StartupAuditorTUI

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