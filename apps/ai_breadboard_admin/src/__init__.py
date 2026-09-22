# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Breadboard Admin Core Package Initialization
# =============================================================================
# Description:
#   Инициализация пакета ядра приложения администратора: экспорт сервисов
#   управления конфигурациями, системными инструкциями, источниками и пользователями.
#
# Examples:
#   >>> from apps.ai_breadboard_admin.src import AdminConfigManager, InstructionsManager
#
# File: __init__.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .config_manager import AdminConfigManager
from .instructions_manager import InstructionsManager
from .sources_manager import SourcesManager
from .user_admin_service import UserAdminService
from .windows_user_manager import WindowsUserManager

__all__ = [
    "AdminConfigManager",
    "InstructionsManager",
    "SourcesManager",
    "UserAdminService",
    "WindowsUserManager",
]
