# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager - Router
# =============================================================================
# Description:
#   FastAPI роутер управления физическими дисками, томами, клонированием и бенчмарком DiskSpd.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.router import init_router
#
#     router = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 08:16:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер управления физическими дисками, томами, клонированием и бенчмарком DiskSpd."""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from logger import logger
from apps.windows.sdk.modules.storage_manager.core.benchmark import StorageBenchmarkService
from apps.windows.sdk.modules.storage_manager.core.manager import StorageManager
from apps.windows.sdk.modules.storage_manager.core.models import (
    BenchmarkHistoryItem,
    BenchmarkProfileResult,
    BenchmarkRequest,
    BenchmarkSuiteResult,
    BenchmarkTargetInfo,
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

router = APIRouter(tags=['Storage Manager, Raw Cloner & DiskSpd Benchmark'])
_manager = StorageManager()
_benchmark = StorageBenchmarkService()


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


# -----------------------------------------------------------------------------
# DiskSpd Benchmark REST API
# -----------------------------------------------------------------------------

@router.get('/api/v1/storage/benchmark/engine')
@router.get('/api/storage-manager/benchmark/engine')
async def get_benchmark_engine_status() -> Dict[str, Any]:
    """Проверка доступности и статуса исполняемого файла Microsoft DiskSpd."""
    binary_path = _benchmark.find_diskspd_binary()
    return {
        'available': binary_path is not None and binary_path.is_file(),
        'binary_path': str(binary_path) if binary_path else None,
        'engine': 'Microsoft DiskSpd (CLI)',
        'download_available': True,
    }


@router.post('/api/v1/storage/benchmark/engine/download')
@router.post('/api/storage-manager/benchmark/engine/download')
async def download_benchmark_engine() -> Dict[str, Any]:
    """Принудительная загрузка или обновление официального бинарника DiskSpd."""
    try:
        path = await asyncio.to_thread(_benchmark.ensure_diskspd_binary)
        return {'status': 'ok', 'binary_path': str(path), 'message': 'DiskSpd готов к использованию'}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Ошибка загрузки DiskSpd: {exc}')


@router.get('/api/v1/storage/benchmark/targets', response_model=List[BenchmarkTargetInfo])
@router.get('/api/storage-manager/benchmark/targets', response_model=List[BenchmarkTargetInfo])
async def list_benchmark_targets() -> List[BenchmarkTargetInfo]:
    """Список дисков и разделов, доступных для тестирования скорости."""
    return await asyncio.to_thread(_benchmark.get_available_targets)


@router.post('/api/v1/storage/benchmark/run', response_model=BenchmarkSuiteResult)
@router.post('/api/storage-manager/benchmark/run', response_model=BenchmarkSuiteResult)
async def run_benchmark_sync(payload: BenchmarkRequest) -> BenchmarkSuiteResult:
    """Синхронный запуск теста производительности диска (CrystalDiskMark стиль)."""
    try:
        return await asyncio.to_thread(_benchmark.run_suite, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post('/api/v1/storage/benchmark/start', response_model=StorageTaskStatus)
@router.post('/api/storage-manager/benchmark/start', response_model=StorageTaskStatus)
async def start_benchmark_async(payload: BenchmarkRequest) -> StorageTaskStatus:
    """Асинхронный запуск тестирования диска в фоновом режиме с отслеживанием прогресса."""
    try:
        return await _benchmark.start_async_benchmark(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get('/api/v1/storage/benchmark/status/{task_id}', response_model=StorageTaskStatus)
@router.get('/api/storage-manager/benchmark/status/{task_id}', response_model=StorageTaskStatus)
async def get_benchmark_task_status(task_id: str) -> StorageTaskStatus:
    """Получение текущего статуса и прогресса запущенного бенчмарка."""
    task = _benchmark.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Задача бенчмарка '{task_id}' не найдена")
    return task


@router.post('/api/v1/storage/benchmark/cancel/{task_id}')
@router.post('/api/storage-manager/benchmark/cancel/{task_id}')
async def cancel_benchmark_task(task_id: str) -> Dict[str, Any]:
    """Отмена выполняющегося тестирования производительности."""
    cancelled = _benchmark.cancel_task(task_id)
    return {'task_id': task_id, 'cancelled': cancelled}


@router.get('/api/v1/storage/benchmark/history', response_model=List[BenchmarkHistoryItem])
@router.get('/api/storage-manager/benchmark/history', response_model=List[BenchmarkHistoryItem])
async def get_benchmark_history(limit: int = Query(50, ge=1, le=200)) -> List[BenchmarkHistoryItem]:
    """История ранее проведенных тестов производительности."""
    return await asyncio.to_thread(_benchmark.get_history, limit)


@router.delete('/api/v1/storage/benchmark/history/{bench_id}')
@router.delete('/api/storage-manager/benchmark/history/{bench_id}')
async def delete_benchmark_history(bench_id: str) -> Dict[str, Any]:
    """Удаление записи бенчмарка из базы данных."""
    success = await asyncio.to_thread(_benchmark.delete_history_item, bench_id)
    return {'id': bench_id, 'deleted': success}


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']

