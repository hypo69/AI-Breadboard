# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AIDA64 FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для приложения AIDA64 Diagnostic App (/api/v1/aida64).
#
# File: router.py
# Project: ai-breadboard
# Package: apps.aida64
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для AIDA64."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter

from apps.aida64.core.aida64_service import Aida64Service

router = APIRouter(prefix="/api/v1/aida64", tags=["aida64"])
_service = Aida64Service()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка статуса AIDA64 и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("aida64")
    return {
        "is_running": _service.is_running(),
        "is_binary_available": _service.is_binary_available(),
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Получение показаний сенсоров реального времени из Shared Memory."""
    sensors = _service.get_live_sensors()
    return {
        "count": len(sensors),
        "sensors": sensors,
    }


@router.post("/report")
async def generate_report(report_type: str = "HW") -> Dict[str, Any]:
    """Запуск генерации отчета AIDA64 через CLI."""
    report = _service.generate_report(report_type=report_type)
    return {"report": report}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router
