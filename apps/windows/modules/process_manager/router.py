# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.process_manager.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.process_manager
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
from apps.windows.modules.process_manager.core.manager import ProcessManager
from apps.windows.modules.process_manager.core.models import (
    ProcessItem,
    ProcessKillRequest,
    ProcessReport,
)

router = APIRouter(prefix='/api/process-manager', tags=['Process Manager'])
_manager = ProcessManager()


@router.get('/summary', response_model=ProcessReport)
@router.get('/report', response_model=ProcessReport)
async def get_processes_report() -> ProcessReport:
    """Сводный отчет о процессах, нагрузке на CPU и памяти."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/list', response_model=List[ProcessItem])
async def list_processes(name: Optional[str] = Query(None, description='Фильтр по имени процесса')) -> List[ProcessItem]:
    """Список всех активных процессов."""
    processes = await asyncio.to_thread(_manager.list_processes)
    if name:
        n_lower = name.lower()
        processes = [p for p in processes if n_lower in p.name.lower()]
    return processes


@router.post('/action')
@router.post('/kill')
async def kill_process(payload: ProcessKillRequest) -> Dict[str, Any]:
    """Завершение процесса по PID."""
    return await _manager.kill_process(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
