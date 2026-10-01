# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Mcp Module
# =============================================================================
# Description:
#   Минимальная реализация роутера router_mcp.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_mcp import init_router
#
#     res = init_router()
#     print(res)
#
# File: router_mcp.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Минимальная реализация роутера router_mcp."""

from fastapi import APIRouter
router = APIRouter()

@router.get('/router_mcp/ping', tags=['router_mcp'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router

def init_admin_mcp_router() -> APIRouter:
    """Инициализировать и вернуть админский MCP роутер."""
    return router

def init_user_mcp_router() -> APIRouter:
    """Инициализировать и вернуть пользовательский MCP роутер."""
    return router