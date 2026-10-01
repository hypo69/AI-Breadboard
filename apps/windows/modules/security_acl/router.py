# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Security_Acl - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.security_acl.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.security_acl
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
from apps.windows.modules.security_acl.core.manager import SecurityAclManager
from apps.windows.modules.security_acl.core.models import (
    AclEntry,
    AclModifyRequest,
    BitLockerVolumeStatus,
    SecurityAclReport,
)

router = APIRouter(prefix='/api/security-acl', tags=['Security & ACL Manager'])
_manager = SecurityAclManager()


@router.get('/summary', response_model=SecurityAclReport)
@router.get('/report', response_model=SecurityAclReport)
async def get_security_report() -> SecurityAclReport:
    """Сводный отчет о безопасности ACL, UAC и BitLocker."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/bitlocker', response_model=List[BitLockerVolumeStatus])
async def get_bitlocker_status() -> List[BitLockerVolumeStatus]:
    """Статус шифрования BitLocker для накопителей."""
    return await asyncio.to_thread(_manager.get_bitlocker_status)


@router.get('/acl', response_model=List[AclEntry])
async def get_path_acl(path: str = Query(..., description='Путь к файлу или папке')) -> List[AclEntry]:
    """Получение списков контроля доступа ACL для объекта."""
    return await asyncio.to_thread(_manager.get_path_acl, path)


@router.post('/action')
@router.post('/acl/modify')
async def modify_acl(payload: AclModifyRequest) -> Dict[str, Any]:
    """Модификация или симуляция изменения прав ACL."""
    return await _manager.execute_acl_modification(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
