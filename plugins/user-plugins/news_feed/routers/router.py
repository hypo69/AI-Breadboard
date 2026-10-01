# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins News_Feed Routers - Router
# =============================================================================
# Description:
#   FastAPI‑router для плагина news_feed.
#
# Usage Examples:
#   Python API:
#     import plugins.user-plugins.news_feed.routers.router as router
#
# File: router.py
# Project: ai-breadboard
# Package: plugins.user-plugins.news_feed.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

"""FastAPI‑router для плагина news_feed.

Экспортирует объект ``router`` (APIRouter), который будет автоматически обнаружен
модулем ``router_loader`` и подключён к приложению."""

from fastapi import APIRouter

router = APIRouter(prefix="/news", tags=["News Feed"])

@router.get("/status")
async def status() -> dict:
    """Простейший эндпоинт, показывающий, что плагин подключён.
    Returns:
        dict: ``{"status": "ok"}``.
    """
    return {"status": "ok"}
