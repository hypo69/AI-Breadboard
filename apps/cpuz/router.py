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

router = APIRouter(prefix="/api/v1/cpuz", tags=["cpuz"])
_service = CpuzService()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Проверка доступности CPU-Z и руководство по установке portable-версии."""
    from apps.common.discovery import UtilityDiscovery
    guide = UtilityDiscovery().get_portable_guide("cpuz")
    return {
        "is_available": _service.is_available(),
        "binary_path": _service.binary_path,
        "portable_guide": guide.to_dict(),
    }


@router.get("/report")
async def get_report() -> Dict[str, Any]:
    """Получение детального отчета CPU-Z."""
    report = _service.generate_report()
    return {"report": report}


def init_router() -> APIRouter:
    """Инициализация роутера."""
    return router
