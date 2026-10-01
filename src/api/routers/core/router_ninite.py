# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Ninite Module
# =============================================================================
# Description:
#   Минимальная реализация роутера router_ninite.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_ninite import NiniteScheduleRequest
#
#     service = NiniteScheduleRequest()
#
# File: router_ninite.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Минимальная реализация роутера router_ninite."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

router = APIRouter(prefix="/api/ninite", tags=["router_ninite"])

# Константа имени задачи
TASK_NAME = "ninite_schedule"

class NiniteScheduleRequest(BaseModel):
    """Запрос на планирование задания Ninite.

    Поля могут быть расширены в будущем.
    """
    schedule: str = Field(..., description="Cron-выражение для расписания задания")
    enabled: bool = Field(..., description="Флаг включения/выключения задания")
    task_name: Literal["ninite_schedule"] = TASK_NAME

@router.get('/ping', tags=['router_ninite'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

@router.post('/schedule', tags=['router_ninite'])
async def schedule_ninite(request: NiniteScheduleRequest) -> dict:
    """Обрабатывает запрос на планирование Ninite задачи.
    В реальном приложении здесь будет логика планировщика.
    """
    # Здесь могла бы быть интеграция с системой планирования
    return {'status': 'scheduled', 'task': request.task_name, 'schedule': request.schedule, 'enabled': request.enabled}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера для FastAPI приложения."""
    return router

__all__ = ["init_router", "router", "TASK_NAME", "NiniteScheduleRequest"]
