# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API Routers - Telemetry
# =============================================================================
# Description:
#   Слой 7: Высокопроизводительный REST API роутер попроцессной телеметрии
#   и файловой активности (Per-PID Resource & Activity Telemetry Engine).
#
# Usage Examples:
#   GET /api/v1/telemetry/processes/1234
#   GET /api/v1/telemetry/processes/1234/file-activity?limit=50
#   POST /api/v1/telemetry/tracked-directories {"action": "add", "directory_path": "C:\\Projects"}
#
# File: router_telemetry.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 13:31:00
# =============================================================================

from __future__ import annotations

"""FastAPI роутер попроцессной телеметрии ресурсов, активности и отслеживания каталогов."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
import psutil

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.telemetry.directory_watcher import DirectoryWatchEngine
from apps.windows.telemetry.models import (
    CpuDetail,
    GpuDetail,
    IoDetail,
    MemoryDetail,
    NetworkDetail,
    ProcessFileEventItem,
    ProcessTelemetryResponse,
    TrackedDirectoryRequest,
    TrackedDirectoryResponse,
)
from apps.windows.telemetry.sqlite import TelemetryStorage

router = APIRouter(prefix='/api/v1/telemetry', tags=['Per-PID Telemetry'])


@router.get('/processes/{pid}', response_model=ProcessTelemetryResponse)
async def get_process_telemetry(pid: int) -> ProcessTelemetryResponse:
    """Возвращает детальные метрики потребления ресурсов процессом по его PID (< 5 мс).

    Args:
        pid: Идентификатор процесса Windows.

    Returns:
        ProcessTelemetryResponse: Полный профиль потребления ресурсов (CPU, RAM, GPU, IO, Net).
    """
    storage = TelemetryStorage.get_instance(read_only=True)
    row = storage.get_process_pid_snapshot(pid=pid)

    if row:
        working_set_mb = round(float(row.get('working_set_bytes', 0)) / (1024 * 1024), 2)
        private_bytes_mb = round(float(row.get('private_bytes', 0)) / (1024 * 1024), 2)
        vram_mb = round(float(row.get('gpu_vram_bytes', 0)) / (1024 * 1024), 2)

        return ProcessTelemetryResponse(
            pid=int(row['pid']),
            process_name=str(row['process_name']),
            executable_path=row.get('executable_path'),
            cpu=CpuDetail(
                percent=float(row.get('cpu_percent', 0.0)),
                user_time_ms=int(row.get('user_time_ms', 0)),
                kernel_time_ms=int(row.get('kernel_time_ms', 0)),
                thread_count=int(row.get('thread_count', 1)),
            ),
            memory=MemoryDetail(
                working_set_mb=working_set_mb,
                private_bytes_mb=private_bytes_mb,
                page_faults=int(row.get('page_faults_count', 0)),
            ),
            gpu=GpuDetail(
                vram_dedicated_mb=vram_mb,
                utilization_percent=float(row.get('gpu_utilization', 0.0)),
            ),
            io=IoDetail(
                read_bytes_sec=int(row.get('read_bytes_total', 0)),
                write_bytes_sec=int(row.get('write_bytes_total', 0)),
                handles_count=int(row.get('handle_count', 0)),
                read_ops_total=int(row.get('read_ops_total', 0)),
                write_ops_total=int(row.get('write_ops_total', 0)),
            ),
            network=NetworkDetail(
                bytes_sent_sec=int(row.get('net_bytes_sent_total', 0)),
                bytes_recv_sec=int(row.get('net_bytes_recv_total', 0)),
                active_sockets=0,
            ),
            timestamp=str(row.get('timestamp') or datetime.now(timezone.utc).isoformat()),
        )

    # Fallback на оперативный сбор через psutil для активных процессов
    try:
        proc = psutil.Process(pid)
        mem_info = proc.memory_info()
        cpu_times = proc.cpu_times()
        io_cnt = proc.io_counters() if hasattr(proc, 'io_counters') else None
        num_h = proc.num_handles() if os.name == 'nt' and hasattr(proc, 'num_handles') else 0

        working_set_mb = round(float(getattr(mem_info, 'rss', 0)) / (1024 * 1024), 2)
        private_bytes_mb = round(float(getattr(mem_info, 'vms', 0) or getattr(mem_info, 'private', 0) or 0) / (1024 * 1024), 2)

        return ProcessTelemetryResponse(
            pid=pid,
            process_name=proc.name(),
            executable_path=proc.exe() if hasattr(proc, 'exe') else None,
            cpu=CpuDetail(
                percent=proc.cpu_percent(interval=None),
                user_time_ms=int(cpu_times.user * 1000) if cpu_times else 0,
                kernel_time_ms=int(cpu_times.system * 1000) if cpu_times else 0,
                thread_count=proc.num_threads(),
            ),
            memory=MemoryDetail(
                working_set_mb=working_set_mb,
                private_bytes_mb=private_bytes_mb,
                page_faults=int(getattr(mem_info, 'num_page_faults', 0)),
            ),
            gpu=GpuDetail(
                vram_dedicated_mb=0.0,
                utilization_percent=0.0,
            ),
            io=IoDetail(
                read_bytes_sec=int(getattr(io_cnt, 'read_bytes', 0)) if io_cnt else 0,
                write_bytes_sec=int(getattr(io_cnt, 'write_bytes', 0)) if io_cnt else 0,
                handles_count=num_h,
                read_ops_total=int(getattr(io_cnt, 'read_count', 0)) if io_cnt else 0,
                write_ops_total=int(getattr(io_cnt, 'write_count', 0)) if io_cnt else 0,
            ),
            network=NetworkDetail(
                bytes_sent_sec=0,
                bytes_recv_sec=0,
                active_sockets=len(proc.net_connections()) if hasattr(proc, 'net_connections') else 0,
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        raise HTTPException(
            status_code=404,
            detail=f'Процесс с PID {pid} не найден или завершил выполнение'
        )


@router.get('/processes/{pid}/file-activity', response_model=List[ProcessFileEventItem])
async def get_process_file_activity(
    pid: int,
    directory: Optional[str] = Query(None, description='Фильтр по целевой директории'),
    limit: int = Query(50, ge=1, le=500, description='Максимальное число событий')
) -> List[ProcessFileEventItem]:
    """Возвращает историю файловых операций, инициированных указанным PID.

    Args:
        pid: Идентификатор процесса.
        directory: Опциональный фильтр директории.
        limit: Лимит записей.

    Returns:
        List[ProcessFileEventItem]: Список файловых событий процесса из базы данных.
    """
    storage = TelemetryStorage.get_instance(read_only=True)
    events = storage.get_process_file_events(pid=pid, directory=directory, limit=limit)
    result: List[ProcessFileEventItem] = []
    for ev in events:
        result.append(ProcessFileEventItem(
            event_id=int(ev.get('event_id', ev.get('id', 0))),
            pid=int(ev.get('pid', pid)),
            process_name=str(ev.get('process_name', '')),
            action_type=str(ev.get('action_type', ev.get('action', 'MODIFY'))),
            target_directory=str(ev.get('target_directory', ev.get('target_folder', ''))),
            file_path=str(ev.get('file_path', '')),
            bytes_affected=int(ev.get('bytes_affected', ev.get('bytes_count', 0)) or 0),
            timestamp=str(ev.get('timestamp') or datetime.now(timezone.utc).isoformat()),
        ))
    return result


@router.post('/tracked-directories', response_model=TrackedDirectoryResponse)
async def manage_tracked_directories(request: TrackedDirectoryRequest) -> TrackedDirectoryResponse:
    """Управление списком отслеживаемых контролируемых директорий.

    Args:
        request: Запрос на добавление ('add') или удаление ('remove') директории.

    Returns:
        TrackedDirectoryResponse: Статус операции и обновленный список директорий.
    """
    engine = DirectoryWatchEngine.get_instance()
    action = request.action.lower().strip()
    path = request.directory_path.strip()

    if action == 'add':
        engine.add_directory(path)
    elif action == 'remove':
        engine.remove_directory(path)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимое действие '{request.action}'. Используйте 'add' или 'remove'."
        )

    return TrackedDirectoryResponse(
        status='ok',
        action=action,
        directory_path=path,
        tracked_directories=engine.get_tracked_directories()
    )


@router.get('/tracked-directories')
async def list_tracked_directories() -> Dict[str, Any]:
    """Возвращает список всех зарегистрированных отслеживаемых директорий."""
    engine = DirectoryWatchEngine.get_instance()
    return {
        'status': 'ok',
        'tracked_directories': engine.get_tracked_directories()
    }


@router.get('/time-ranges')
async def get_telemetry_time_ranges() -> Dict[str, Any]:
    """Возвращает доступные временные интервалы (секунды, минуты, часы, дни, недели, месяцы, все) на основе возраста данных в БД."""
    try:
        storage = TelemetryStorage.get_instance(read_only=True)
        return storage.get_telemetry_time_ranges()
    except Exception as exc:
        logger.error(f"[router_telemetry] Ошибка вычисления доступных диапазонов времени: {exc}", exc_info=True)
        return {
            'status': 'error',
            'error': str(exc),
            'intervals': [
                {'id': 'seconds', 'label': 'Секунды', 'seconds': 120, 'is_available': True},
                {'id': 'all', 'label': 'Все', 'seconds': None, 'is_available': True},
            ],
            'available_ids': ['seconds', 'all']
        }


@router.get('/history')
async def get_telemetry_history(
    interval: str = Query('seconds', description="Временной интервал: seconds, minutes, hours, days, weeks, months, all"),
    metric: str = Query('all', description="Категория метрики: all, cpu, gpu, ram, net, storage"),
    limit: int = Query(120, ge=10, le=500, description="Максимальное количество точек")
) -> Dict[str, Any]:
    """Возвращает агрегированную историю метрик под выбранный временной интервал."""
    try:
        storage = TelemetryStorage.get_instance(read_only=True)
        rows = storage.get_history_by_interval(interval=interval, metric=metric, limit=limit)
        return {
            'status': 'ok',
            'interval': interval,
            'metric': metric,
            'count': len(rows),
            'history': rows
        }
    except Exception as exc:
        logger.error(f"[router_telemetry] Ошибка чтения истории телеметрии: {exc}", exc_info=True)
        return {
            'status': 'error',
            'interval': interval,
            'metric': metric,
            'error': str(exc),
            'history': []
        }


def init_router() -> APIRouter:
    """Возвращает сконфигурированный FastAPI APIRouter для Auto-Discovery."""
    return router

