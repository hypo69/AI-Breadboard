# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AIDA64 App Package Init
# =============================================================================
# Description:
#   Пакетная инициализация приложения AIDA64.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.aida64
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AIDA64 Diagnostic App Standalone Package."""

from apps.aida64.router import init_router

__all__ = ["init_router"]
