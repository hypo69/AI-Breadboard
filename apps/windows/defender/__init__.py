# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Security Center App Package
# =============================================================================
# Description:
#   Пакетная инициализация приложения Windows Defender & AI Security Diagnostic Center.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.defender
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Windows Defender & AI Security Diagnostic Center Standalone App."""

from apps.windows.defender.router import init_router

__all__ = ["init_router"]
