# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - System Inspector Router
# =============================================================================
# Description:
#   Реэкспорт эндпоинтов системного инспектора, перенесенных в состав /api/v1/tc
#
# Usage Examples:
#   Python API:
#     import apps.windows.system_inspector_router as system_inspector_router
#
# File: system_inspector_router.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Реэкспорт эндпоинтов системного инспектора, перенесенных в состав /api/v1/tc"""

from apps.windows.api.routers.router_tc import (
    get_collector,
    get_diagnostician,
    init_router,
)

router = init_router()

__all__ = ["get_collector", "get_diagnostician", "init_router", "router"]