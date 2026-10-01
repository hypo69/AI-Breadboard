# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Telemetry Module
# =============================================================================
# Description:
#   Экспортировать роутер телеметрии.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.tc.telemetry.router_telemetry import init_router
#
#     res = init_router()
#     print(res)
#
# File: router_telemetry.py
# Project: ai-breadboard
# Package: src.api.routers.tc.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Экспортировать роутер телеметрии."""

from fastapi import APIRouter

router = APIRouter()

def init_router() -> APIRouter:
    """Экспортировать роутер телеметрии."""
    return router

__all__ = ["init_router", "router"]
