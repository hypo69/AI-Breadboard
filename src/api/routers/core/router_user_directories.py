# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router User Directories Module
# =============================================================================
# Description:
#   Минимальная реализация роутера router_user_directories.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_user_directories import init_router
#
#     res = init_router()
#     print(res)
#
# File: router_user_directories.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Минимальная реализация роутера router_user_directories."""

from fastapi import APIRouter
router = APIRouter()

@router.get('/router_user_directories/ping', tags=['router_user_directories'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router