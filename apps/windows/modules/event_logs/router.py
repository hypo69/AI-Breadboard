# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.event_logs.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.event_logs
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from logger import logger
from apps.windows.modules.event_logs.core.manager import EventLogsManager
from apps.windows.modules.event_logs.core.models import (
    EventLogActionRequest,
    EventLogChannel,
    EventLogEntry,
    EventLogReport,
)

router = APIRouter(prefix='/api/event-logs', tags=['Event Logs Manager'])
_manager = EventLogsManager()


@router.get('/summary', response_model=EventLogReport)
@router.get('/report', response_model=EventLogReport)
async def get_event_logs_report() -> EventLogReport:
    """Сводный отчет о журналах событий и последних ошибках."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/channels', response_model=List[EventLogChannel])
async def list_channels() -> List[EventLogChannel]:
    """Список всех зарегистрированных каналов событий."""
    return await asyncio.to_thread(_manager.list_channels)


@router.get('/errors', response_model=List[EventLogEntry])
async def get_recent_errors(limit: int = Query(10, ge=1, le=100)) -> List[EventLogEntry]:
    """Список последних критических событий и ошибок."""
    return await asyncio.to_thread(_manager.get_recent_errors, limit)


@router.post('/action')
@router.post('/actions')
async def execute_event_log_action(payload: EventLogActionRequest) -> Dict[str, Any]:
    """Очистка или экспорт журнала событий."""
    return await _manager.execute_channel_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
