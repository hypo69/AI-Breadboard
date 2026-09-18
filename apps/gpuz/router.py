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

router = APIRouter(prefix="/api/v1/gpuz", tags=["gpuz"])
_service = GpuzService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности GPU-Z и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("gpuz")
    return {
        "is_available": _service.is_available(),
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Чтение последних сенсоров из лога GPU-Z."""
    data = _service.parse_sensor_log()
    return {"sensors": data}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router
