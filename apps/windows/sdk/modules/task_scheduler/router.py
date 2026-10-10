# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler - Router
# =============================================================================
# Description:
#   FastAPI маршрутизатор для управления планировщиком задач Windows (Task Scheduler).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.task_scheduler.router import init_router
#
#     router = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.task_scheduler
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:35:00
# =============================================================================

from __future__ import annotations
"""FastAPI маршрутизатор для управления планировщиком задач Windows (Task Scheduler)."""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from logger import logger
from apps.windows.sdk.modules.task_scheduler.core.manager import TaskSchedulerManager
from apps.windows.sdk.modules.task_scheduler.core.models import (
    ScheduledTaskItem,
    TaskActionRequest,
    TaskSchedulerReport,
)

router = APIRouter(prefix='/api/task-scheduler', tags=['Task Scheduler Manager'])
_manager = TaskSchedulerManager()


@router.get('/summary', response_model=TaskSchedulerReport)
@router.get('/report', response_model=TaskSchedulerReport)
async def get_scheduler_report() -> TaskSchedulerReport:
    """Сводный отчет о задачах планировщика Windows."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/tasks', response_model=List[ScheduledTaskItem])
async def list_tasks(state: Optional[str] = Query(None, description='Ready, Running, Disabled')) -> List[ScheduledTaskItem]:
    """Список запланированных заданий с фильтрацией по состоянию."""
    tasks = await asyncio.to_thread(_manager.list_tasks)
    if state:
        st_lower = state.lower()
        tasks = [t for t in tasks if t.state.lower() == st_lower]
    return tasks


@router.post('/action')
@router.post('/actions')
async def execute_task_action(payload: TaskActionRequest) -> Dict[str, Any]:
    """Запуск, остановка, включение или удаление задания."""
    return await _manager.execute_task_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
