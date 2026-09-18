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

router = APIRouter(prefix="/api/v1/lhm", tags=["librehardwaremonitor"])
_service = LhmService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности LHM и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("librehardwaremonitor")
    return {
        "is_running": _service.is_running(),
        "is_binary_available": _service.is_binary_available(),
        "binary_path": _service.binary_path,
        "endpoint_url": _service.endpoint_url,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Получение полного дерева сенсоров."""
    data = _service.get_sensor_tree()
    return {"sensors_tree": data}


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Получение плоского списка всех сенсоров с нормализованными числовыми значениями."""
    items = _service.get_flattened_sensors()
    return {
        "count": len(items),
        "sensors": items,
    }


@router.get("/summary")
async def get_summary() -> Dict[str, Any]:
    """Получение краткой системной сводки (CPU/GPU/RAM)."""
    summary = _service.get_system_summary()
    return summary


@router.post("/launch")
async def launch_lhm() -> Dict[str, Any]:
    """Запуск исполняемого файла LibreHardwareMonitor в фоновом режиме."""
    started = _service.start_process()
    return {
        "success": started,
        "is_running": _service.is_running(),
        "binary_path": _service.binary_path,
    }


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router

