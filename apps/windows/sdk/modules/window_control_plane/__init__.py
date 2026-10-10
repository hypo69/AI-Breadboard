# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Management Control Plane
# =============================================================================
# Description:
#   Пакет Windows Window Management Control Plane: унифицированный каталог из 295 параметров
#   управления окнами, DWM, панелью задач, экранным окружением и политиками Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.window_control_plane import (
#         WindowManagementControlPlane, get_window_control_plane, get_window_catalog
#     )
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:25:00
# =============================================================================

from __future__ import annotations
"""Пакет управления окнами и системной оболочкой Windows Window Management Control Plane."""

from apps.windows.sdk.modules.window_control_plane.catalog import (
    WindowControlPlaneCatalog,
    get_window_catalog,
)
from apps.windows.sdk.modules.window_control_plane.history import (
    WindowManagementHistoryManager,
    get_window_history_manager,
)
from apps.windows.sdk.modules.window_control_plane.manager import (
    WindowManagementControlPlane,
    get_window_control_plane,
)
from apps.windows.sdk.modules.window_control_plane.models import (
    BackendResolverSpec,
    BackendType,
    DocStatus,
    RiskLevel,
    SettingCategory,
    SettingScope,
    SettingValueType,
    SupportStatus,
    WindowSettingDefinition,
)
from apps.windows.sdk.modules.window_control_plane.resolver import WindowBackendResolver
from apps.windows.sdk.modules.window_control_plane.router import init_router

__all__ = [
    "WindowControlPlaneCatalog",
    "get_window_catalog",
    "WindowManagementControlPlane",
    "get_window_control_plane",
    "WindowManagementHistoryManager",
    "get_window_history_manager",
    "WindowBackendResolver",
    "init_router",
    "WindowSettingDefinition",
    "SettingCategory",
    "SettingScope",
    "SettingValueType",
    "BackendType",
    "SupportStatus",
    "DocStatus",
    "RiskLevel",
    "BackendResolverSpec",
]
