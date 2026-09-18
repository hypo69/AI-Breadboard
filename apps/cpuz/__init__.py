# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CPU-Z App Package Init
# =============================================================================
# Description:
#   Пакетная инициализация приложения CPU-Z.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.cpuz
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CPU-Z Diagnostic App Standalone Package."""

from apps.cpuz.router import init_router

__all__ = ["init_router"]
