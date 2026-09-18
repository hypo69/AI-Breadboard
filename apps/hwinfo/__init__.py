# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HWiNFO App Package Init
# =============================================================================
# Description:
#   Пакетная инициализация приложения HWiNFO.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.hwinfo
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""HWiNFO Diagnostic App Standalone Package."""

from apps.hwinfo.router import init_router

__all__ = ["init_router"]
