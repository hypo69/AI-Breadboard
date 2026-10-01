# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Rag Module
# =============================================================================
# Description:
#   Минимальная реализация роутера router_rag.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_rag import init_router
#
#     res = init_router()
#     print(res)
#
# File: router_rag.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Минимальная реализация роутера router_rag."""

from fastapi import APIRouter
router = APIRouter()

@router.get('/router_rag/ping', tags=['router_rag'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router