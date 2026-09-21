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
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/aida64", tags=["aida64"])
_service = Aida64Service()
_csv_logger = AppCsvLogger("aida64")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка статуса AIDA64 и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("aida64")
    running = _service.is_running()
    available = _service.is_binary_available()
    _csv_logger.log_poll(
        poll_type="status_poll",
        metric_name="is_running",
        value=running,
        unit="bool",
        status="RUNNING" if running else "STOPPED",
        details={"binary_available": available, "binary_path": _service.binary_path},
        filename="aida64_status_polls.csv",
    )
    return {
        "is_running": running,
        "is_binary_available": available,
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Получение показаний сенсоров реального времени из Shared Memory."""
    sensors = _service.get_live_sensors()
    _csv_logger.log_poll(
        poll_type="sensors_poll",
        metric_name="sensor_count",
        value=len(sensors),
        unit="count",
        status="OK",
        details={"sensors_preview": sensors[:5] if sensors else []},
        filename="aida64_sensor_polls.csv",
    )
    return {
        "count": len(sensors),
        "sensors": sensors,
    }


@router.post("/report")
async def generate_report(report_type: str = "HW") -> Dict[str, Any]:
    """Запуск генерации отчета AIDA64 через CLI."""
    report = _service.generate_report(report_type=report_type)
    _csv_logger.log_event(
        event_type="report_generated",
        status="SUCCESS",
        details={"report_type": report_type, "length": len(report) if report else 0},
        filename="aida64_report_events.csv",
    )
    return {"report": report}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router

