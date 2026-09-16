# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Breadboard Admin Application Package Initialization
# =============================================================================
# Description:
#   Инициализация пакета микроприложения ai_breadboard_admin. Экспорт роутера
#   FastAPI, менеджеров конфигураций, системных инструкций и TUI интерфейса.
#
# Examples:
#   >>> from apps.ai_breadboard_admin import init_router, run_admin_tui
#
# File: __init__.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет микроприложения администратора AI Breadboard."""

from .router import init_router, router
from .src import (
    AdminConfigManager,
    InstructionsManager,
    SourcesManager,
    UserAdminService,
)
from .tui import run_admin_tui

__all__ = [
    "init_router",
    "router",
    "AdminConfigManager",
    "InstructionsManager",
    "SourcesManager",
    "UserAdminService",
    "run_admin_tui",
]
