# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Features - Package Init
# =============================================================================
# Description:
#   Инициализация пакета Windows Features. Экспортирует основные функции менеджера.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.features
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 11:20:00
# =============================================================================

"""Пакет для управления Windows Optional Features через FastAPI.

Содержит менеджер, который использует PowerShell/DISM для получения, включения
и отключения компонентов Windows. Экспортируются функции:
- get_windows_features
- enable_windows_feature
- disable_windows_feature
"""

from .manager import get_windows_features, enable_windows_feature, disable_windows_feature

__all__ = [
    "get_windows_features",
    "enable_windows_feature",
    "disable_windows_feature",
]
