# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager
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
from apps.windows.modules.storage_manager.core.manager import StorageManager
from apps.windows.modules.storage_manager.core.models import (
    DiskCloneRequest,
    DiskDetailedInfo,
    DiskHashRequest,
    DiskHashResponse,
    DiskImageCreateRequest,
    DiskImageRestoreRequest,
    DiskInfo,
    DiskOperationRequest,
    DiskVerifyRequest,
    FsFeaturesInfo,
    SectorReadRequest,
    SectorReadResponse,
    SectorWriteRequest,
    SectorWriteResponse,
    StorageReport,
    StorageTaskStatus,
    VolumeInfo,
)

router = APIRouter(tags=['Storage Manager & Raw Cloner'])
_manager = StorageManager()


# -----------------------------------------------------------------------------
# REST API v1 Спецификация (/api/v1/storage)
# -----------------------------------------------------------------------------

@router.get('/api/v1/storage/disks', response_model=List[DiskInfo])
@router.get('/api/storage-manager/disks', response_model=List[DiskInfo])
async def list_disks() -> List[DiskInfo]:
    """disk.list: Список всех физических блочных дисков хоста."""
    return await asyncio.to_thread(_manager.get_disks)


@router.get('/api/v1/storage/disks/{disk_id}', response_model=DiskDetailedInfo)
async def get_disk_info(disk_id: int) -> DiskDetailedInfo:
    """disk.info: Детальная информация о диске (геометрия, SMART, разметка MBR/GPT)."""
    return await asyncio.to_thread(_manager.get_disk_detailed, disk_id)


@router.post('/api/v1/storage/disks/{disk_id}/read', response_model=SectorReadResponse)
async def read_disk_sector(disk_id: int, payload: SectorReadRequest) -> SectorReadResponse:
    """disk.read: Прямое низкоуровневое чтение секторов через WinAPI."""
    payload.disk_id = disk_id
    try:
        return await asyncio.to_thread(_manager.read_sectors, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/disks/{disk_id}/write', response_model=SectorWriteResponse)
async def write_disk_sector(disk_id: int, payload: SectorWriteRequest) -> SectorWriteResponse:
    """disk.write: Прямая низкоуровневая запись в сектора накопителя с защитой SafeOps."""
    payload.disk_id = disk_id
    try:
        return await asyncio.to_thread(_manager.write_sectors, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/disks/{source_disk_id}/clone', response_model=StorageTaskStatus)
async def clone_disk(source_disk_id: int, payload: DiskCloneRequest) -> StorageTaskStatus:
    """disk.clone: Запуск посекторного клонирования (disk A -> disk B) в режиме 'raw' или 'smart'."""
    payload.source_disk_id = source_disk_id
    try:
        return await _manager.start_clone(payload)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/disks/{disk_id}/image', response_model=StorageTaskStatus)
async def create_disk_image(disk_id: int, payload: DiskImageCreateRequest) -> StorageTaskStatus:
    """disk.image.create: Создание raw-образа диска (.img/.raw)."""
    payload.disk_id = disk_id
    try:
        return await _manager.start_image_create(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/disks/{disk_id}/restore', response_model=StorageTaskStatus)
async def restore_disk_image(disk_id: int, payload: DiskImageRestoreRequest) -> StorageTaskStatus:
    """disk.image.restore: Восстановление физического диска из raw-образа."""
    payload.disk_id = disk_id
    try:
        return await _manager.start_image_restore(payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/disks/{disk_id}/verify')
async def verify_disk(disk_id: int, payload: DiskVerifyRequest) -> Dict[str, Any]:
    """disk.verify: Посекторная верификация целостности диска."""
    payload.source_disk_id = disk_id
    try:
        return await _manager.verify_integrity(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/disks/{disk_id}/hash', response_model=DiskHashResponse)
async def calculate_disk_hash(disk_id: int, payload: DiskHashRequest) -> DiskHashResponse:
    """disk.hash: Посекторное вычисление SHA-256 хеша диска."""
    payload.disk_id = disk_id
    try:
        return await asyncio.to_thread(_manager.compute_hash, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get('/api/v1/storage/tasks', response_model=List[StorageTaskStatus])
async def list_storage_tasks() -> List[StorageTaskStatus]:
    """Список всех фоновых задач клонирования и создания образов."""
    return _manager.list_tasks()


@router.get('/api/v1/storage/tasks/{task_id}', response_model=StorageTaskStatus)
async def get_storage_task(task_id: str) -> StorageTaskStatus:
    """Получение прогресса и статуса фоновой задачи."""
    task = _manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Задача '{task_id}' не найдена")
    return task


@router.delete('/api/v1/storage/tasks/{task_id}')
async def cancel_storage_task(task_id: str) -> Dict[str, Any]:
    """Отмена выполняющейся фоновой задачи."""
    cancelled = _manager.cancel_task(task_id)
    return {'task_id': task_id, 'cancelled': cancelled}


# -----------------------------------------------------------------------------
# Совместимость со Storage Manager / Volumes
# -----------------------------------------------------------------------------

@router.get('/api/storage-manager/summary', response_model=StorageReport)
@router.get('/api/storage-manager/report', response_model=StorageReport)
@router.get('/api/v1/storage/report', response_model=StorageReport)
async def get_storage_report() -> StorageReport:
    """Сводный отчет о физических дисках, логических томах и ФС."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/api/storage-manager/volumes', response_model=List[VolumeInfo])
@router.get('/api/v1/storage/volumes', response_model=List[VolumeInfo])
async def list_volumes() -> List[VolumeInfo]:
    """Список логических томов Windows."""
    return await asyncio.to_thread(_manager.get_volumes)


@router.get('/api/storage-manager/fs/features', response_model=FsFeaturesInfo)
@router.get('/api/v1/storage/fs/features', response_model=FsFeaturesInfo)
async def get_fs_features() -> FsFeaturesInfo:
    """Параметры файловой системы (TRIM, 8.3 имена, сжатие)."""
    return await asyncio.to_thread(_manager.get_fs_features)


@router.post('/api/storage-manager/action')
@router.post('/api/storage-manager/operations')
@router.post('/api/v1/storage/operations')
async def execute_operation(payload: DiskOperationRequest) -> Dict[str, Any]:
    """Выполнение или симуляция стандартной дисковой операции."""
    return await _manager.execute_disk_operation(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
