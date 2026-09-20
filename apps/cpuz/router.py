# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CPU-Z FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для CPU-Z Processor Diagnostic App (/api/v1/cpuz).
#
# File: router.py
# Project: ai-breadboard
# Package: apps.cpuz
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для CPU-Z."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from apps.cpuz.core.cpuz_service import CpuzService
from apps.common.csv_logger import AppCsvLogger

router = APIRouter(prefix="/api/v1/cpuz", tags=["cpuz"])
_service = CpuzService()
_csv_logger = AppCsvLogger("cpuz")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности CPU-Z и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("cpuz")
    available = _service.is_available()
    _csv_logger.log_poll(
        poll_type="status_poll",
        metric_name="is_available",
        value=available,
        unit="bool",
        status="AVAILABLE" if available else "MISSING",
        details={"binary_path": _service.binary_path},
        filename="cpuz_hardware_polls.csv",
    )
    return {
        "is_available": available,
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/report")
async def get_report() -> Dict[str, Any]:
    """Получение детального отчета CPU-Z."""
    report = _service.generate_report()
    _csv_logger.log_event(
        event_type="cpuz_report_generated",
        status="SUCCESS",
        details={"report_length": len(report) if report else 0},
        filename="cpuz_hardware_polls.csv",
    )
    return {"report": report}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router

