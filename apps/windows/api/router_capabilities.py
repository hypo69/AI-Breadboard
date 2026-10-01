# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api - Router Capabilities
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.router_capabilities import init_router
#
#     res = init_router()
#
# File: router_capabilities.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from logger import logger
from apps.windows.core.atomic_capabilities import get_atomic_registry
from apps.windows.core.atomic_models import (
    AtomicOperationExecutionRequest,
    AtomicOperationExecutionResult,
    CapabilityCategory,
    PrivilegeLevel,
    RiskLevel,
)

router = APIRouter(prefix='/api/v1', tags=['Windows Atomic Operations & Capabilities'])
_registry = get_atomic_registry()


@router.get('/capabilities/catalog')
async def get_capabilities_catalog(
    category: Optional[str] = Query(None, description='Фильтр по категории (storage_fs, boot_recovery, etc.)'),
    utility: Optional[str] = Query(None, description='Фильтр по утилите (diskpart, fsutil, etc.)'),
    risk_level: Optional[str] = Query(None, description='Фильтр по уровню риска (READ_ONLY, LOW, MEDIUM, HIGH, CRITICAL)'),
    query: Optional[str] = Query(None, description='Поисковый запрос по названию или описанию')
) -> Dict[str, Any]:
    """Получение плоского каталога всех атомарных операций Windows с фильтрацией."""
    ops = _registry.get_all_operations()
    if category:
        ops = [o for o in ops if o.category.value == category or category in o.category.value]
    if utility:
        u_clean = utility.lower().replace('.exe', '').replace('.com', '')
        ops = [o for o in ops if u_clean in o.utility.lower()]
    if risk_level:
        ops = [o for o in ops if o.risk_level.value == risk_level]
    if query:
        q_lower = query.lower()
        ops = [
            o for o in ops
            if q_lower in o.name_ru.lower() or q_lower in o.description.lower() or q_lower in o.id.lower()
        ]

    return {
        'total': len(ops),
        'operations': [o.to_dict() for o in ops]
    }


@router.get('/capabilities/tree')
async def get_capabilities_tree(group_by: str = Query('utility', description='Группировка: utility или category')) -> Dict[str, Any]:
    """Иерархическое дерево возможностей Windows («утилита -> список атомарных операций»)."""
    if group_by == 'category':
        return {'tree': _registry.get_categories_tree(), 'grouped_by': 'category'}
    return {'tree': _registry.get_tree(), 'grouped_by': 'utility'}


@router.get('/capabilities/categories')
async def get_categories_list() -> Dict[str, Any]:
    """Список всех 17 системных категорий с количеством операций."""
    categories_info = []
    for cat in CapabilityCategory:
        ops = _registry.get_operations_by_category(cat)
        categories_info.append({
            'category_id': cat.value,
            'name': cat.name,
            'operations_count': len(ops),
            'utilities': list(set(o.utility for o in ops))
        })
    return {'categories': categories_info, 'total': len(categories_info)}


@router.get('/capabilities/utilities')
async def get_utilities_list() -> Dict[str, Any]:
    """Список всех CLI утилит с количеством доступных атомарных операций."""
    tree = _registry.get_tree()
    utils = []
    for u_name, ops_list in tree.items():
        utils.append({
            'utility': u_name,
            'operations_count': len(ops_list),
            'categories': list(set(o.get('category') for o in ops_list)),
            'max_risk': max([o.get('risk_level') for o in ops_list], default='READ_ONLY')
        })
    return {'utilities': utils, 'total': len(utils)}


@router.get('/capabilities/utilities/{utility_name}')
async def get_utility_operations(utility_name: str) -> Dict[str, Any]:
    """Получение всех атомарных операций конкретной CLI утилиты."""
    ops = _registry.get_operations_by_utility(utility_name)
    if not ops:
        raise HTTPException(status_code=404, detail=f"Утилита '{utility_name}' не найдена в каталоге")
    return {'utility': utility_name, 'operations': [o.to_dict() for o in ops], 'total': len(ops)}


@router.get('/capabilities/operations/{operation_id}')
async def get_operation_detail(operation_id: str) -> Dict[str, Any]:
    """Получение детальной спецификации атомарной операции по её ID."""
    op = _registry.get_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail=f"Операция '{operation_id}' не найдена в каталоге")
    return op.to_dict()


@router.post('/capabilities/execute')
async def execute_operation(payload: AtomicOperationExecutionRequest) -> AtomicOperationExecutionResult:
    """Исполнение или симуляция (Dry-Run) выбранной атомарной операции."""
    return await _registry.execute_operation(payload)


# =============================================================================
# REST эндпоинты категорий
# =============================================================================

@router.get('/storage/disks')
async def list_storage_disks() -> Dict[str, Any]:
    """Перечисление физических дисков хоста."""
    try:
        from apps.windows.telemetry.windows_storage_sensor import WindowsStorageSensor
        sensor = WindowsStorageSensor(timeout_sec=15)
        disks = await asyncio.to_thread(sensor.get_physical_disks)
        return {'disks': [d.to_dict() for d in disks], 'total': len(disks)}
    except Exception as exc:
        logger.warning(f"Ошибка получения дисков: {exc}")
        return {'disks': [], 'total': 0, 'error': str(exc)}


@router.get('/storage/fs/trim')
async def get_fs_trim_status() -> Dict[str, Any]:
    """Запрос глобального статуса TRIM для SSD."""
    res = await _registry.execute_operation(
        AtomicOperationExecutionRequest(operation_id='fsutil.fs.trim_query', dry_run=False, confirmed_by_user=True)
    )
    return {'trim_status': res.data, 'message': res.message}


@router.get('/boot/entries')
async def list_boot_entries() -> Dict[str, Any]:
    """Чтение записей диспетчера загрузки BCD."""
    res = await _registry.execute_operation(
        AtomicOperationExecutionRequest(operation_id='bcdedit.boot.list', dry_run=False, confirmed_by_user=True)
    )
    return {'boot_entries': res.data, 'message': res.message}


@router.get('/recovery/winre/info')
async def get_winre_info() -> Dict[str, Any]:
    """Состояние среды аварийного восстановления WinRE."""
    res = await _registry.execute_operation(
        AtomicOperationExecutionRequest(operation_id='reagentc.winre.info', dry_run=False, confirmed_by_user=True)
    )
    return {'winre_status': res.data, 'message': res.message}


@router.get('/hardware/devices/problems')
async def get_problem_devices() -> Dict[str, Any]:
    """Список устройств с аппаратными сбоями или ошибками драйверов (Code 10/43)."""
    res = await _registry.execute_operation(
        AtomicOperationExecutionRequest(operation_id='pnputil.device.problems', dry_run=False, confirmed_by_user=True)
    )
    return {'problem_devices': res.data, 'message': res.message}


@router.get('/power/requests')
async def get_power_sleep_requests() -> Dict[str, Any]:
    """Список блокировок спящего режима (Sleep Troubleshooter)."""
    res = await _registry.execute_operation(
        AtomicOperationExecutionRequest(operation_id='powercfg.requests', dry_run=False, confirmed_by_user=True)
    )
    return {'sleep_blocks': res.data, 'message': res.message}


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер возможностей."""
    return router


__all__ = ['router', 'init_router']
