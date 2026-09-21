# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU-Z FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для GPU-Z Graphics Diagnostic App (/api/v1/gpuz).
#
# File: router.py
# Project: ai-breadboard
# Package: apps.gpuz
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для GPU-Z."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from apps.gpuz.core.gpuz_service import GpuzService
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/gpuz", tags=["gpuz"])
_service = GpuzService()
_csv_logger = AppCsvLogger("gpuz")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности GPU-Z и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("gpuz")
    available = _service.is_available()
    _csv_logger.log_poll(
        poll_type="status_poll",
        metric_name="is_available",
        value=available,
        unit="bool",
        status="AVAILABLE" if available else "MISSING",
        details={"binary_path": _service.binary_path},
        filename="gpuz_sensor_polls.csv",
    )
    return {
        "is_available": available,
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Чтение последних сенсоров из лога GPU-Z."""
    data = _service.parse_sensor_log()
    _csv_logger.log_poll(
        poll_type="sensors_poll",
        metric_name="gpu_sensors_read",
        value=bool(data),
        unit="bool",
        status="OK" if data else "NO_DATA",
        details={"sensors": data},
        filename="gpuz_sensor_polls.csv",
    )
    return {"sensors": data}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router

