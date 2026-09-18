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

router = APIRouter(prefix="/api/v1/smartmontools", tags=["smartmontools"])
_service = SmartctlService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности smartctl и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("smartmontools")
    return {
        "is_available": _service.is_available(),
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/devices")
async def get_devices() -> Dict[str, Any]:
    """Список всех обнаруженных накопителей."""
    devices = _service.scan_devices()
    return {"devices": devices, "count": len(devices)}


@router.get("/device/{device_name}")
async def get_device_info(device_name: str) -> Dict[str, Any]:
    """Полная SMART телеметрия выбранного накопителя."""
    info = _service.get_device_health(device_name)
    return {"device": device_name, "info": info}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router
