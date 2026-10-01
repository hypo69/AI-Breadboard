# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins User-Plugins Ifttt Routers - Router
# =============================================================================
# Description:
#   Маршрутизатор FastAPI для плагина IFTTT.
#
# Usage Examples:
#   Python API:
#     import plugins.user-plugins.ifttt.routers.router as router
#
# File: router.py
# Project: ai-breadboard
# Package: plugins.user-plugins.ifttt.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

"""Маршрутизатор FastAPI для плагина IFTTT.

Экспортирует объект ``router`` (APIRouter), который будет автоматически обнаружен
модулем ``router_loader`` и включён в приложение."""

from fastapi import APIRouter

router = APIRouter(prefix="/ifttt", tags=["IFTTT"])

@router.get("/status")
async def status() -> dict:
    """Возвращает простую информацию о состоянии плагина.

    Returns:
        dict: ``{"status": "ok"}`` – статус плагина IFTTT.
    """
    return {"status": "ok"}
