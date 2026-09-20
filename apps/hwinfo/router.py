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
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/hwinfo", tags=["hwinfo"])
_service = HwinfoService()
_csv_logger = AppCsvLogger("hwinfo")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка статуса HWiNFO и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("hwinfo")
    running = _service.is_running()
    available = _service.is_binary_available()
    _csv_logger.log_poll(
        poll_type="status_poll",
        metric_name="is_running",
        value=running,
        unit="bool",
        status="RUNNING" if running else "STOPPED",
        details={"binary_available": available, "binary_path": _service.binary_path},
        filename="hwinfo_status_polls.csv",
    )
    return {
        "is_running": running,
        "is_binary_available": available,
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/sensors")
async def get_sensors() -> Dict[str, Any]:
    """Получение сенсоров HWiNFO."""
    sensors = _service.get_live_sensors()
    _csv_logger.log_poll(
        poll_type="sensors_poll",
        metric_name="sensor_count",
        value=len(sensors),
        unit="count",
        status="OK",
        details={"sensors_preview": sensors[:5] if sensors else []},
        filename="hwinfo_sensor_polls.csv",
    )
    return {"sensors": sensors, "count": len(sensors)}


@router.get("/inventory")
async def get_inventory() -> Dict[str, Any]:
    """Получение полного отчета оборудования через HWiNFO CLI."""
    report = _service.generate_json_report()
    _csv_logger.log_event(
        event_type="inventory_report_generated",
        status="SUCCESS",
        details={"report_keys": list(report.keys()) if isinstance(report, dict) else len(report)},
        filename="hwinfo_inventory_events.csv",
    )
    return {"report": report}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router

