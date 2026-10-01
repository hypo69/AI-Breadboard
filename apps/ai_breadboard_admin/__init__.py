# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Ai_Breadboard_Admin -   Init  
# =============================================================================
# Description:
#   Пакет микроприложения администратора AI Breadboard.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.ai_breadboard_admin
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет микроприложения администратора AI Breadboard."""

from .router import init_router, router
from .src import AdminConfigManager, InstructionsManager, SourcesManager, UserAdminService
from .tui import run_admin_tui
__all__ = ['init_router', 'router', 'AdminConfigManager', 'InstructionsManager', 'SourcesManager', 'UserAdminService', 'run_admin_tui']