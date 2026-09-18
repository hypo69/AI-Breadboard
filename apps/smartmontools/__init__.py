# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: smartmontools App Package Init
# =============================================================================
# Description:
#   Пакетная инициализация приложения smartmontools.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.smartmontools
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""smartmontools Diagnostic App Standalone Package."""

from apps.smartmontools.router import init_router

__all__ = ["init_router"]
