# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для LibreHardwareMonitor App (/api/v1/lhm).
#
# File: router.py
# Project: ai-breadboard
# Package: apps.librehardwaremonitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для LibreHardwareMonitor."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter

from apps.librehardwaremonitor.core.lhm_service import LhmService
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/lhm", tags=["librehardwaremonitor"])
_service = LhmService()
_csv_logger = AppCsvLogger("librehardwaremonitor")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности LHM и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("librehardwaremonitor")
    running = _service.is_running()
    available = _service.is_binary_available()
    _csv_logger.log_poll(
        poll_type="status_poll",
        metric_name="is_running",
        value=running,
        unit="bool",
        status="RUNNING" if running else "STOPPED",
        details={"binary_available": available, "endpoint": _service.endpoint_url},
        filename="lhm_status_polls.csv",
    )
    return {
        "is_running": running,
        "is_binary_available": available,
        "binary_path": _service.binary_path,
        "endpoint_url": _service.endpoint_url,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Получение полного дерева сенсоров."""
    data = _service.get_sensor_tree()
    _csv_logger.log_poll(
        poll_type="sensor_tree_poll",
        metric_name="has_tree",
        value=bool(data),
        unit="bool",
        status="OK" if data else "EMPTY",
        details={"root_id": data.get("id") if isinstance(data, dict) else None},
        filename="lhm_sensor_polls.csv",
    )
    return {"sensors_tree": data}


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Получение плоского списка всех сенсоров с нормализованными числовыми значениями."""
    items = _service.get_flattened_sensors()
    _csv_logger.log_poll(
        poll_type="metrics_poll",
        metric_name="sensor_count",
        value=len(items),
        unit="count",
        status="OK",
        details={"metrics_preview": items[:5] if items else []},
        filename="lhm_sensor_polls.csv",
    )
    return {
        "count": len(items),
        "sensors": items,
    }


@router.get("/summary")
async def get_summary() -> Dict[str, Any]:
    """Получение краткой системной сводки (CPU/GPU/RAM)."""
    summary = _service.get_system_summary()
    _csv_logger.log_poll(
        poll_type="summary_poll",
        metric_name="summary_status",
        value="available" if summary else "empty",
        unit="string",
        status="OK",
        details=summary,
        filename="lhm_sensor_polls.csv",
    )
    return summary


@router.post("/launch")
async def launch_lhm() -> Dict[str, Any]:
    """Запуск исполняемого файла LibreHardwareMonitor в фоновом режиме."""
    started = _service.start_process()
    _csv_logger.log_event(
        event_type="launch_lhm_process",
        status="SUCCESS" if started else "FAILED",
        details={"binary_path": _service.binary_path},
        filename="lhm_service_events.csv",
    )
    return {
        "success": started,
        "is_running": _service.is_running(),
        "binary_path": _service.binary_path,
    }


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router


