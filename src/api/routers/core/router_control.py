# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Control Module
# =============================================================================
# Description:
#   router_control
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_control import init_router
#
#     res = init_router()
#     print(res)
#
# File: router_control.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""router_control

Минимальная реализация роутера control."""

from fastapi import APIRouter
router = APIRouter()

@router.get('/router_control/ping', tags=['router_control'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера control."""
    return router