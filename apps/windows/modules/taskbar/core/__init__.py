# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - Core Init
# =============================================================================
# Description:
#   Инициализация ядра модуля управления панелью задач.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.core import TaskbarController
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:32:00
# =============================================================================

from __future__ import annotations
"""Пакет ядра подсистемы Taskbar & Windows Management."""

from apps.windows.modules.taskbar.core.app_manager import TaskbarAppManager
from apps.windows.modules.taskbar.core.command_registry import (
    TaskbarCommandMetadata,
    get_taskbar_command_catalog,
)
from apps.windows.modules.taskbar.core.manager import TaskbarController
from apps.windows.modules.taskbar.core.models import (
    AppLaunchRequest,
    AppPinRequest,
    PinnedAppItem,
    TaskbarOverlayRequest,
    TaskbarProgressRequest,
    TaskbarSettings,
    TaskbarSettingsUpdate,
    TaskbarSummaryReport,
    WindowBatchActionRequest,
    WindowItem,
    WindowMoveRequest,
    WindowRect,
)
from apps.windows.modules.taskbar.core.settings_manager import TaskbarSettingsManager
from apps.windows.modules.taskbar.core.taskbar_list_com import (
    TaskbarList3Wrapper,
    TaskbarProgressFlag,
)
from apps.windows.modules.taskbar.core.window_manager import WindowManager

__all__ = [
    "TaskbarController",
    "TaskbarSettingsManager",
    "WindowManager",
    "TaskbarAppManager",
    "TaskbarList3Wrapper",
    "TaskbarProgressFlag",
    "TaskbarSettings",
    "TaskbarSettingsUpdate",
    "TaskbarSummaryReport",
    "TaskbarProgressRequest",
    "TaskbarOverlayRequest",
    "WindowItem",
    "WindowRect",
    "WindowMoveRequest",
    "WindowBatchActionRequest",
    "AppLaunchRequest",
    "AppPinRequest",
    "PinnedAppItem",
    "TaskbarCommandMetadata",
    "get_taskbar_command_catalog",
]
