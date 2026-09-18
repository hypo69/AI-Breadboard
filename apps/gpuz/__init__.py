# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU-Z App Package Init
# =============================================================================
# Description:
#   Пакетная инициализация приложения GPU-Z.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.gpuz
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""GPU-Z Diagnostic App Standalone Package."""

from apps.gpuz.router import init_router

__all__ = ["init_router"]
