# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Services_Manager - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.services_manager.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.services_manager
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
from apps.windows.modules.services_manager.core.manager import ServicesManager
from apps.windows.modules.services_manager.core.models import (
    ServiceActionRequest,
    ServiceItem,
    ServicesReport,
)

router = APIRouter(prefix='/api/services-manager', tags=['Services Manager'])
_manager = ServicesManager()


@router.get('/summary', response_model=ServicesReport)
@router.get('/report', response_model=ServicesReport)
async def get_services_report() -> ServicesReport:
    """Сводный отчет о службах хоста."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/list', response_model=List[ServiceItem])
async def list_services(status: Optional[str] = Query(None, description='RUNNING или STOPPED')) -> List[ServiceItem]:
    """Список всех служб с фильтрацией по статусу."""
    services = await asyncio.to_thread(_manager.list_services)
    if status:
        st_upper = status.upper()
        services = [s for s in services if s.status == st_upper]
    return services


@router.post('/action')
@router.post('/actions')
async def execute_service_action(payload: ServiceActionRequest) -> Dict[str, Any]:
    """Запуск, остановка или изменение типа автозапуска службы."""
    return await _manager.execute_service_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
