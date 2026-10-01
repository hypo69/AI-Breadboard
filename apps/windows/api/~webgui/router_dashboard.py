# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api ~Webgui - Router Dashboard
# =============================================================================
# Description:
#   router_dashboard.py
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.~webgui.router_dashboard import get_dashboard_snapshot
#
#     res = get_dashboard_snapshot()
#
# File: router_dashboard.py
# Project: ai-breadboard
# Package: apps.windows.api.~webgui
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""router_dashboard.py"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from apps.windows.telemetry.sqlite import TelemetryStorage
from logger import logger

router = APIRouter(prefix='/api/windows/dashboard', tags=['dashboard'])


def _storage() -> TelemetryStorage:
    """Возвращает синглтон TelemetryStorage.

    Returns:
        TelemetryStorage: Экземпляр хранилища телеметрии.
    """
    return TelemetryStorage.get_instance()


# ---------------------------------------------------------------------------
# GET /snapshot — последний системный снепшот (CPU, RAM, GPU, диски)
# ---------------------------------------------------------------------------

@router.get('/snapshot')
def get_dashboard_snapshot() -> Dict[str, Any]:
    """Последний системный снепшот из таблицы system_snapshots.

    Возвращает агрегированные метрики CPU, RAM, GPU и дисков из самой
    последней записи базы данных telemetry.db. Если raw_json содержит
    полный снепшот, он разбирается и возвращается структура, совместимая
    с форматом live-API /api/windows/hardware/monitor.

    Returns:
        Dict[str, Any]: Структурированный снепшот системных метрик.
    """
    storage = _storage()
    rows = storage.get_snapshots(limit=1)
    if not rows:
        logger.warning('[Dashboard] system_snapshots пуста — телеметрия ещё не собиралась')
        return {
            'cpu': {'total_percent': 0, 'model': '', 'cores_logical': 0},
            'ram': {'percent_used': 0, 'used_gb': 0, 'total_gb': 0},
            'gpus': [],
            'disks': [],
            'timestamp': None,
            'source': 'telemetry.db',
        }

    row = rows[0]

    # Попытка распарсить полный снепшот из raw_json
    raw: Dict[str, Any] = {}
    try:
        raw = json.loads(row.get('raw_json') or '{}')
    except Exception:
        pass

    # Формируем совместимую структуру
    cpu = raw.get('cpu') or {
        'total_percent': row.get('cpu_total_percent', 0),
        'frequency_mhz': row.get('cpu_frequency_mhz', 0),
        'model': '',
        'cores_logical': 0,
        'cores_physical': 0,
    }
    ram_raw = raw.get('memory') or raw.get('ram') or {}
    ram = {
        'percent_used': ram_raw.get('percent', row.get('memory_percent', 0)),
        'used_gb': ram_raw.get('used_gb', row.get('memory_used_gb', 0)),
        'total_gb': ram_raw.get('total_gb', row.get('memory_total_gb', 0)),
        'swap_percent': ram_raw.get('swap_percent', row.get('swap_percent', 0)),
    }
    gpus = raw.get('gpus') or []
    if not gpus and (row.get('gpu_load_percent') or row.get('gpu_temp_c')):
        gpus = [{
            'name': 'GPU',
            'load_percent': row.get('gpu_load_percent', 0),
            'temp_c': row.get('gpu_temp_c', 0),
            'memory_used_mb': 0,
            'memory_total_mb': 0,
        }]

    disks = raw.get('disks') or []

    return {
        'cpu': cpu,
        'ram': ram,
        'gpus': gpus,
        'disks': disks,
        'hostname': row.get('hostname', ''),
        'uptime_seconds': row.get('uptime_seconds', 0),
        'timestamp': row.get('timestamp'),
        'snapshot_id': row.get('id'),
        'source': 'telemetry.db',
    }


# ---------------------------------------------------------------------------
# GET /sensors — последние значения всех датчиков
# ---------------------------------------------------------------------------

@router.get('/sensors')
def get_dashboard_sensors() -> Dict[str, Any]:
    """Последние значения всех аппаратных датчиков из таблицы sensor_polls.

    Использует метод get_latest_sensors(), который возвращает последнее
    измерение для каждого уникального sensor_id.

    Returns:
        Dict[str, Any]: Список сенсоров и их счётчик.
    """
    storage = _storage()
    sensors = storage.get_latest_sensors()
    return {'sensors': sensors, 'count': len(sensors), 'source': 'telemetry.db'}


# ---------------------------------------------------------------------------
# GET /processes — процессы из последнего снепшота
# ---------------------------------------------------------------------------

@router.get('/processes')
def get_dashboard_processes(
    limit: int = Query(50, ge=1, le=500, description='Максимальное число процессов'),
    sort_by: str = Query('cpu', description='Сортировка: cpu | memory | handles'),
) -> Dict[str, Any]:
    """Список процессов из самого последнего снепшота process_snapshots.

    Args:
        limit: Максимальное количество возвращаемых процессов.
        sort_by: Поле сортировки ('cpu', 'memory', 'handles').

    Returns:
        Dict[str, Any]: Список процессов и метаданные.
    """
    storage = _storage()
    processes = storage.get_latest_processes(limit=limit, sort_by=sort_by)
    return {
        'processes': processes,
        'count': len(processes),
        'sort_by': sort_by,
        'source': 'telemetry.db',
    }


# ---------------------------------------------------------------------------
# GET /history — история системных снепшотов
# ---------------------------------------------------------------------------

@router.get('/history')
def get_dashboard_history(
    limit: int = Query(60, ge=1, le=1000, description='Количество снепшотов'),
    since: Optional[float] = Query(None, description='Фильтр: Unix-эпоха начала периода'),
) -> Dict[str, Any]:
    """История системных срезов из таблицы system_snapshots.

    Args:
        limit: Максимальное число возвращаемых записей.
        since: Unix timestamp начала периода (опционально).

    Returns:
        Dict[str, Any]: Список снепшотов и счётчик.
    """
    storage = _storage()
    snapshots = storage.get_snapshots(limit=limit, since_epoch=since)
    return {
        'snapshots': snapshots,
        'count': len(snapshots),
        'source': 'telemetry.db',
    }


# ---------------------------------------------------------------------------
# GET /sensor-history — история показаний датчика
# ---------------------------------------------------------------------------

@router.get('/sensor-history')
def get_dashboard_sensor_history(
    sensor_id: Optional[str] = Query(None, description='ID сенсора'),
    category: Optional[str] = Query(None, description='Категория: Temperatures | Load | Clocks | Fans'),
    limit: int = Query(100, ge=1, le=2000, description='Лимит записей'),
) -> Dict[str, Any]:
    """История измерений датчиков из таблицы sensor_polls.

    Args:
        sensor_id: Идентификатор конкретного сенсора (опционально).
        category: Категория сенсора для фильтрации (опционально).
        limit: Лимит возвращаемых записей.

    Returns:
        Dict[str, Any]: История показаний и счётчик.
    """
    storage = _storage()
    readings = storage.get_sensor_history(
        sensor_id=sensor_id,
        category=category,
        limit=limit,
    )
    return {
        'readings': readings,
        'count': len(readings),
        'sensor_id': sensor_id,
        'category': category,
        'source': 'telemetry.db',
    }


# ---------------------------------------------------------------------------
# GET /events — события телеметрии
# ---------------------------------------------------------------------------

@router.get('/events')
def get_dashboard_events(
    event_type: Optional[str] = Query(None, description='Тип события для фильтрации'),
    limit: int = Query(100, ge=1, le=1000, description='Лимит записей'),
) -> Dict[str, Any]:
    """События телеметрии из таблицы telemetry_events.

    Args:
        event_type: Тип события для фильтрации (опционально).
        limit: Лимит возвращаемых записей.

    Returns:
        Dict[str, Any]: Список событий и счётчик.
    """
    storage = _storage()
    events = storage.get_events(event_type=event_type, limit=limit)
    return {
        'events': events,
        'count': len(events),
        'event_type': event_type,
        'source': 'telemetry.db',
    }


# ---------------------------------------------------------------------------
# GET /process-stats — агрегированная статистика процессов
# ---------------------------------------------------------------------------

@router.get('/process-stats')
def get_dashboard_process_stats(
    name: Optional[str] = Query(None, description='Фильтр по имени процесса (подстрока)'),
    limit: int = Query(50, ge=1, le=500, description='Лимит записей'),
) -> Dict[str, Any]:
    """Агрегированная статистика процессов: роллапы и выбросы.

    Возвращает данные из таблиц process_rollups_2min, process_rollups_daily
    и process_outliers через метод get_process_stats().

    Args:
        name: Подстрока имени процесса для фильтрации (опционально).
        limit: Лимит записей на каждую группу.

    Returns:
        Dict[str, Any]: Словарь с роллапами, суточной статистикой и выбросами.
    """
    storage = _storage()
    stats = storage.get_process_stats(name=name, limit=limit)
    stats['source'] = 'telemetry.db'
    return stats


def init_router() -> APIRouter:
    """Экспортировать роутер дашборда.

    Returns:
        APIRouter: Настроенный роутер FastAPI.
    """
    return router


__all__ = ['init_router', 'router']
