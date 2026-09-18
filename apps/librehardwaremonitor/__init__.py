# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor App Package Init
# =============================================================================
# Description:
#   Пакетная инициализация приложения LibreHardwareMonitor.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.librehardwaremonitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""LibreHardwareMonitor Standalone App Package."""

from apps.librehardwaremonitor.router import init_router

__all__ = ["init_router"]
