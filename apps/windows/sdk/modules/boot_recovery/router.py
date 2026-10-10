# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Boot_Recovery - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.boot_recovery.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.boot_recovery
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
from apps.windows.sdk.modules.boot_recovery.core.manager import BootRecoveryManager
from apps.windows.sdk.modules.boot_recovery.core.models import (
    BcdEntry,
    BootActionRequest,
    BootReport,
    WinReStatus,
)

router = APIRouter(prefix='/api/boot-recovery', tags=['Boot & Recovery Manager'])
_manager = BootRecoveryManager()


@router.get('/summary', response_model=BootReport)
@router.get('/report', response_model=BootReport)
async def get_boot_report() -> BootReport:
    """Сводный отчет конфигурации загрузки и WinRE."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/entries', response_model=List[BcdEntry])
async def list_bcd_entries() -> List[BcdEntry]:
    """Список всех загрузочных записей BCD."""
    return await asyncio.to_thread(_manager.get_bcd_entries)


@router.get('/winre', response_model=WinReStatus)
async def get_winre_status() -> WinReStatus:
    """Статус и конфигурация среды аварийного восстановления WinRE."""
    return await asyncio.to_thread(_manager.get_winre_status)


@router.post('/action')
@router.post('/actions')
async def execute_boot_action(payload: BootActionRequest) -> Dict[str, Any]:
    """Выполнение или симуляция действия с загрузчиком."""
    return await _manager.execute_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
