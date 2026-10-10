# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Servicing_Integrity - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.servicing_integrity.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.servicing_integrity
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
from apps.windows.sdk.modules.servicing_integrity.core.manager import ServicingIntegrityManager
from apps.windows.sdk.modules.servicing_integrity.core.models import (
    IntegrityReport,
    ServicingActionRequest,
    WindowsFeature,
)

router = APIRouter(prefix='/api/servicing-integrity', tags=['Servicing & Integrity Manager'])
_manager = ServicingIntegrityManager()


@router.get('/summary', response_model=IntegrityReport)
@router.get('/report', response_model=IntegrityReport)
async def get_integrity_report() -> IntegrityReport:
    """Сводный отчет о целостности системных файлов и хранилища компонентов DISM."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/features', response_model=List[WindowsFeature])
async def list_windows_features() -> List[WindowsFeature]:
    """Список дополнительных компонентов Windows."""
    return await asyncio.to_thread(_manager.get_features)


@router.post('/action')
@router.post('/actions')
async def execute_servicing_action(payload: ServicingActionRequest) -> Dict[str, Any]:
    """Запуск или симуляция действий SFC / DISM."""
    return await _manager.execute_servicing_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
