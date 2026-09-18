# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Backup, Libraries & File History Manager App Package
# =============================================================================
# Description:
#   Пакетная инициализация приложения Windows Backup Manager.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows_backup_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Windows Backup, Libraries & File History Management Standalone App."""

from apps.windows_backup_manager.router import init_router

__all__ = ["init_router"]