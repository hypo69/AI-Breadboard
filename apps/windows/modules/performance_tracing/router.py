# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Performance_Tracing - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.performance_tracing.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.performance_tracing
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from logger import logger
from apps.windows.modules.performance_tracing.core.manager import PerformanceTracingManager
from apps.windows.modules.performance_tracing.core.models import (
    CollectorActionRequest,
    DataCollectorSet,
    PerformanceCounterSample,
    PerformanceTracingReport,
)

router = APIRouter(prefix='/api/performance-tracing', tags=['Performance & Tracing Manager'])
_manager = PerformanceTracingManager()


@router.get('/summary', response_model=PerformanceTracingReport)
@router.get('/report', response_model=PerformanceTracingReport)
async def get_performance_report() -> PerformanceTracingReport:
    """Сводный отчет о загрузке процессора, памяти, диска и сборщиках ETW."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/counters', response_model=List[PerformanceCounterSample])
async def get_counters() -> List[PerformanceCounterSample]:
    """Моментальные значения ключевых счетчиков производительности."""
    return await asyncio.to_thread(_manager.get_counter_samples)


@router.get('/collectors', response_model=List[DataCollectorSet])
async def list_collectors() -> List[DataCollectorSet]:
    """Список наборов сборщиков данных ETW."""
    return await asyncio.to_thread(_manager.list_collectors)


@router.post('/action')
@router.post('/collectors/actions')
async def execute_collector_action(payload: CollectorActionRequest) -> Dict[str, Any]:
    """Запуск, остановка или изменение сборщика трассировки."""
    return await _manager.execute_collector_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
