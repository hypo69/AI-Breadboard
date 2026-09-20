# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: smartmontools FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для smartmontools Diagnostic App (/api/v1/smartmontools).
#
# File: router.py
# Project: ai-breadboard
# Package: apps.smartmontools
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для smartmontools."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from apps.smartmontools.core.smartctl_service import SmartctlService
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/smartmontools", tags=["smartmontools"])
_service = SmartctlService()
_csv_logger = AppCsvLogger("smartmontools")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности smartctl и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("smartmontools")
    available = _service.is_available()
    _csv_logger.log_poll(
        poll_type="status_poll",
        metric_name="is_available",
        value=available,
        unit="bool",
        status="AVAILABLE" if available else "MISSING",
        details={"binary_path": _service.binary_path},
        filename="smartmontools_status_polls.csv",
    )
    return {
        "is_available": available,
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/devices")
async def get_devices() -> Dict[str, Any]:
    """Список всех обнаруженных накопителей."""
    devices = _service.scan_devices()
    _csv_logger.log_poll(
        poll_type="devices_scan",
        metric_name="device_count",
        value=len(devices),
        unit="count",
        status="OK",
        details={"devices": devices},
        filename="smartmontools_disk_health_polls.csv",
    )
    return {"devices": devices, "count": len(devices)}


@router.get("/device/{device_name}")
async def get_device_info(device_name: str) -> Dict[str, Any]:
    """Полная SMART телеметрия выбранного накопителя."""
    info = _service.get_device_health(device_name)
    _csv_logger.log_poll(
        poll_type="device_health_poll",
        metric_name=device_name,
        value="PASSED" if info.get("smart_status", {}).get("passed", True) else "FAILED",
        unit="status",
        status="OK",
        details={"model": info.get("model_name"), "temp": info.get("temperature")},
        filename="smartmontools_disk_health_polls.csv",
    )
    return {"device": device_name, "info": info}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router

