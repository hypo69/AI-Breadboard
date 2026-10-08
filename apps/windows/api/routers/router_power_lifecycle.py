# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Power Lifecycle
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для управления, анализа и мониторинга жизненного цикла
#   питания Windows, истории перезагрузок (User32 1074, Kernel-Power 41, EventLog 6008/6005/6006)
#   и реконструированных сессий питания (Power Sessions).
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_power_lifecycle import init_router
#
#     router = init_router()
#
# File: router_power_lifecycle.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:51:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST эндпоинты для анализа жизненного цикла питания и сессий Windows."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.telemetry.models import (
    PowerEventRecord,
    PowerSessionRecord,
    PowerLifecycleSummary,
)
from apps.windows.telemetry.power_lifecycle import PowerLifecycleEngine
from apps.windows.telemetry.sqlite import TelemetryStorage


def init_router(prefix: str = "/api/v1/power", **kwargs: Any) -> APIRouter:
    """Инициализирует и возвращает FastAPI APIRouter для подсистемы питания.

    Args:
        prefix: Префикс REST маршрутов API.

    Returns:
        APIRouter: Сконфигурированный роутер FastAPI.
    """
    router = APIRouter(prefix=prefix, tags=["Power Lifecycle & Boot History"])
    engine = PowerLifecycleEngine()

    @router.get("/summary", response_model=PowerLifecycleSummary)
    async def get_power_summary() -> PowerLifecycleSummary:
        """Получить сводную статистику по сессиям питания, аптайму и перезагрузкам."""
        try:
            # Если в БД ещё нет записей, выполняем первичное быстрое сканирование
            summary = engine.get_summary()
            if summary.total_sessions_count == 0:
                summary = engine.scan_and_reconstruct(hours=720)
            return summary
        except Exception as exc:
            logger.error(f"[RouterPowerLifecycle] Ошибка получения сводки: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/sessions", response_model=List[PowerSessionRecord])
    async def get_power_sessions(
        limit: int = Query(50, ge=1, le=500, description="Лимит записей"),
        offset: int = Query(0, ge=0, description="Смещение"),
        shutdown_type: Optional[str] = Query(None, description="Фильтр по типу: Restart, Shutdown, Unexpected, Active"),
        unexpected_only: bool = Query(False, description="Только внезапные завершения"),
    ) -> List[PowerSessionRecord]:
        """Получить список реконструированных сессий питания Windows."""
        try:
            sessions = engine.get_sessions(
                limit=limit,
                offset=offset,
                shutdown_type=shutdown_type,
                unexpected_only=unexpected_only,
            )
            if not sessions and offset == 0:
                # Первоначальный сбор при пустой базе
                engine.scan_and_reconstruct(hours=720)
                sessions = engine.get_sessions(
                    limit=limit,
                    offset=offset,
                    shutdown_type=shutdown_type,
                    unexpected_only=unexpected_only,
                )
            return sessions
        except Exception as exc:
            logger.error(f"[RouterPowerLifecycle] Ошибка получения сессий: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get("/sessions/{session_id}", response_model=PowerSessionRecord)
    async def get_power_session_by_id(session_id: str) -> PowerSessionRecord:
        """Получить детальную информацию по конкретной сессии питания."""
        item = engine.storage.get_power_session_by_id(session_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Сессия питания {session_id} не найдена")
        return PowerSessionRecord(**item)

    @router.get("/events", response_model=List[PowerEventRecord])
    async def get_power_events(
        limit: int = Query(100, ge=1, le=1000, description="Лимит событий"),
        offset: int = Query(0, ge=0, description="Смещение"),
        event_id: Optional[int] = Query(None, description="Фильтр по Event ID (1074, 41, 6008, 12, 13, etc.)"),
    ) -> List[PowerEventRecord]:
        """Получить список нормализованных системных событий питания."""
        try:
            return engine.get_events(limit=limit, offset=offset, event_id=event_id)
        except Exception as exc:
            logger.error(f"[RouterPowerLifecycle] Ошибка получения событий: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post("/rebuild", response_model=PowerLifecycleSummary)
    async def rebuild_power_lifecycle(
        hours: int = Query(720, ge=1, le=8760, description="Глубина сканирования журналов в часах")
    ) -> PowerLifecycleSummary:
        """Принудительно пересканировать Event Log и перестроить сессии питания."""
        try:
            summary = engine.scan_and_reconstruct(hours=hours, force=True)
            return summary
        except Exception as exc:
            logger.error(f"[RouterPowerLifecycle] Ошибка пересборки: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    return router


__all__ = ["init_router"]
