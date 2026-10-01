# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Google_User_Desktop Routers -   Init  
# =============================================================================
# Description:
#   FastAPI роутер пакет приложения Google User Desktop.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.google_user_desktop.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""FastAPI роутер пакет приложения Google User Desktop."""

from .router import get_state, init_router, router

__all__ = ['router', 'init_router', 'get_state']
