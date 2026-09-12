# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator FastAPI Router Re-export
# =============================================================================
# Description:
#   FastAPI endpoint re-exports for Windows system administration,
#   Active Directory operations, user account management, group policies,
#   and security event monitoring.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows_sysadmin.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows_sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router integration for Windows System Administrator."""

from src.fastapi.router_windows_admin import init_router

__all__ = [
    "init_router",
]
