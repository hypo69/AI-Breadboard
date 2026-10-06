# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs - Router
# =============================================================================
# Description:
#   FastAPI роутер для управления системными журналами Windows и Log Intelligence API.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.event_logs.router import init_router
#
#     router = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.event_logs
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:28:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер для управления системными журналами Windows и Log Intelligence API."""

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
    IntelligenceProcessResponse,
    IntelligenceSearchRequest,
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


@router.get('/events', response_model=List[EventLogEntry])
async def get_channel_events(
    channel: str = Query('System', description='Имя журнала событий'),
    limit: int = Query(50, ge=1, le=500, description='Количество записей'),
    level: str = Query('', description='Фильтр по уровню важности'),
    hours: int = Query(24, ge=1, le=720, description='Глубина выборки в часах'),
) -> List[EventLogEntry]:
    """Получение нормализованного списка событий из канала."""
    return await asyncio.to_thread(_manager.get_events, channel, limit, level, hours)


@router.get('/errors', response_model=List[EventLogEntry])
async def get_recent_errors(limit: int = Query(10, ge=1, le=100)) -> List[EventLogEntry]:
    """Список последних критических событий и ошибок."""
    return await asyncio.to_thread(_manager.get_recent_errors, limit)


@router.post('/action')
@router.post('/actions')
async def execute_event_log_action(payload: EventLogActionRequest) -> Dict[str, Any]:
    """Очистка или экспорт журнала событий."""
    return await _manager.execute_channel_action(payload)


@router.get('/intelligence/profile')
@router.post('/intelligence/process')
async def process_log_intelligence(
    channel: str = Query('System', description='Имя канала для анализа'),
    hours: int = Query(24, ge=1, le=720, description='Глубина выборки в часах'),
    limit: int = Query(100, ge=10, le=1000, description='Лимит выборки событий'),
) -> Dict[str, Any]:
    """Запуск полного цикла Log Intelligence (EDA профайлинг -> Decision Gate -> Adaptive RAG)."""
    return await asyncio.to_thread(_manager.process_intelligence, channel, hours, limit)


@router.post('/intelligence/search')
@router.get('/intelligence/search')
async def search_log_intelligence_rag(
    query: str = Query('', description='Поисковый запрос'),
    top_k: int = Query(5, ge=1, le=50, description='Лимит результатов'),
    channel: str = Query('', description='Канал для фильтрации'),
) -> List[Dict[str, Any]]:
    """Семантический и ключевой поиск по адаптивному RAG-хранилищу логов."""
    if not query:
        return []
    return await asyncio.to_thread(_manager.search_rag, query, top_k, channel)


@router.get('/intelligence/audit')
async def get_log_intelligence_audit(
    channel: str = Query('System', description='Имя канала'),
    hours: int = Query(24, ge=1, le=720, description='Глубина выборки в часах'),
    limit: int = Query(200, ge=10, le=1000, description='Лимит выборки'),
) -> Dict[str, Any]:
    """Многоуровневый статистический аудит канала: дедупликация, шаблоны, аномалии, всплески."""
    return await asyncio.to_thread(_manager.audit_channel, channel, hours, limit)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
