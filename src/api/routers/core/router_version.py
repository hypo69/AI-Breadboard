# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Version Module
# =============================================================================
# Description:
#   Минимальная реализация роутера router_version.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_version import init_router
#
#     res = init_router()
#     print(res)
#
# File: router_version.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Минимальная реализация роутера router_version."""

from fastapi import APIRouter
router = APIRouter()

@router.get('/router_version/ping', tags=['router_version'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router