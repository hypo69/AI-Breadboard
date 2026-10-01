# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Sysadmin -   Init  
# =============================================================================
# Description:
#   Windows System Administrator application package.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Windows System Administrator application package."""

from .router import init_router
from .src.state import SystemAdminState, UserSession, SecurityEvent
from .tui import run_sysadmin_dashboard
__all__ = ['init_router', 'SystemAdminState', 'UserSession', 'SecurityEvent', 'run_sysadmin_dashboard']