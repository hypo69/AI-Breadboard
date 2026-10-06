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
# Updated: 2026-10-06 17:43:00
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage
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
async def list_processes(
    name: Optional[str] = Query(None, description='Фильтр по имени процесса'),
    sort_by: str = Query('cpu_percent', description='Поле сортировки: cpu_percent, memory_mb, name, pid'),
    limit: int = Query(0, description='Лимит возвращаемых процессов (0 = все)')
) -> List[ProcessItem]:
    """Список всех активных процессов из SQLite (< 5 мс)."""
    try:
        storage = TelemetryStorage.get_instance(read_only=True)
        raw_list = storage.get_latest_processes(limit=limit, sort_by=sort_by)
        if raw_list:
            items: List[ProcessItem] = []
            for p in raw_list:
                mem_b = p.get('memory_rss_bytes') or 0
                mem_mb = round(mem_b / (1024 * 1024), 2) if mem_b else float(p.get('memory_mb') or 0.0)
                items.append(
                    ProcessItem(
                        pid=int(p.get('pid', 0)),
                        name=str(p.get('name') or 'unknown'),
                        username=p.get('username'),
                        cpu_percent=float(p.get('cpu_percent') or 0.0),
                        memory_mb=mem_mb,
                        num_threads=int(p.get('num_threads') or 1),
                        create_time=str(p.get('created_at') or ''),
                        exe_path=p.get('exe_path'),
                        command_line=p.get('cmdline') or p.get('command_line'),
                    )
                )
            if name:
                n_lower = name.lower()
                items = [p for p in items if n_lower in p.name.lower()]
            return items
    except Exception as ex:
        logger.debug(f'Ошибка извлечения процессов из SQLite: {ex}')

    # Cold Start Fallback
    processes = await asyncio.to_thread(_manager.list_processes)
    if name:
        n_lower = name.lower()
        processes = [p for p in processes if n_lower in p.name.lower()]
    return processes


@router.post('/action')
@router.post('/kill')
async def kill_process(payload: ProcessKillRequest) -> Dict[str, Any]:
    """Завершение процесса по PID с точечной валидацией."""
    return await _manager.kill_process(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
