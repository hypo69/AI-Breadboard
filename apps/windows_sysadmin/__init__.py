# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator Application Module Initialization
# =============================================================================
# Description:
#   Root package initialization for the Windows System Administrator application.
#   Provides system administration utilities, Active Directory management,
#   user account lifecycle, group policies, and security monitoring.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Windows System Administrator application package."""

from .router import init_router
from .tui import run_sysadmin_dashboard

__all__ = [
    "init_router",
    "run_sysadmin_dashboard",
]
