# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: HWiNFO FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для HWiNFO Diagnostic App (/api/v1/hwinfo).
#
# File: router.py
# Project: ai-breadboard
# Package: apps.hwinfo
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для HWiNFO."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from apps.hwinfo.core.hwinfo_service import HwinfoService

router = APIRouter(prefix="/api/v1/hwinfo", tags=["hwinfo"])
_service = HwinfoService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка статуса HWiNFO и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("hwinfo")
    return {
        "is_running": _service.is_running(),
        "is_binary_available": _service.is_binary_available(),
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Получение сенсоров HWiNFO."""
    sensors = _service.get_live_sensors()
    return {"sensors": sensors, "count": len(sensors)}


@router.get("/inventory")
async def get_inventory() -> Dict[str, Any]:
    """Получение полного отчета оборудования через HWiNFO CLI."""
    report = _service.generate_json_report()
    return {"report": report}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router
