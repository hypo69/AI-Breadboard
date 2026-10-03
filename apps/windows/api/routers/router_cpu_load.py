# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router CPU Load
# =============================================================================
# Description:
#   GET /api/v1/panel/cpu-load — загрузка и температура каждого ядра CPU
#   из таблицы sensor_polls базы telemetry.db.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_cpu_load import init_router
#     app.include_router(init_router())
#
# File: router_cpu_load.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 01:30:00
# =============================================================================

from __future__ import annotations
"""Роутер панели «Загрузка CPU»: метрики по ядрам из telemetry.db."""

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage

_CORE_RE = re.compile(r"core[\s_#]*(\d+)", re.IGNORECASE)
_TEMP_CATEGORIES = ("temperature", "temperatures")


class CpuCoreMetric(BaseModel):
    """Метрики одного ядра CPU."""
    index: int = Field(..., description="Индекс ядра")
    name: str = Field(default="", description="Имя ядра")
    load_percent: Optional[float] = Field(default=None, description="Загрузка ядра, %")
    temperature_c: Optional[float] = Field(default=None, description="Температура ядра, °C")
    timestamp: str = Field(default="", description="Время последнего замера")


class CpuLoadResponse(BaseModel):
    """Ответ GET /api/v1/panel/cpu-load."""
    status: str = Field(default="ok", description="Статус ответа")
    total_percent: float = Field(default=0.0, description="Суммарная загрузка CPU, %")
    package_temperature_c: Optional[float] = Field(default=None, description="Температура корпуса CPU (Package), °C")
    cores: List[CpuCoreMetric] = Field(default_factory=list, description="Метрики по ядрам")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные запроса")


def _core_index(row: Dict[str, Any]) -> Optional[int]:
    """Определяет индекс ядра по sensor_id или sensor_name; None — сенсор не относится к ядру."""
    for text in (row.get("sensor_id") or "", row.get("sensor_name") or ""):
        match = _CORE_RE.search(str(text))
        if match:
            return int(match.group(1))
    return None


def build_cpu_load(sensors: List[Dict[str, Any]]) -> CpuLoadResponse:
    """Собирает ответ из последних значений сенсоров CPU.

    Args:
        sensors: Последние показания сенсоров (строки sensor_polls).

    Returns:
        CpuLoadResponse: Загрузка и температура по ядрам.
    """
    cores: Dict[int, CpuCoreMetric] = {}
    total = 0.0
    package_temp: Optional[float] = None

    for row in sensors:
        if str(row.get("hardware_type") or "").lower() != "cpu":
            continue
        category = str(row.get("sensor_category") or "").lower()
        value = row.get("value")
        if value is None:
            continue
        is_temp = category in _TEMP_CATEGORIES
        idx = _core_index(row)

        if idx is None:
            if row.get("sensor_id") == "cpu_util_total":
                total = round(float(value), 1)
            elif is_temp and package_temp is None:
                package_temp = round(float(value), 1)
            continue

        core = cores.setdefault(idx, CpuCoreMetric(index=idx, name=f"Core #{idx}"))
        if is_temp:
            core.temperature_c = round(float(value), 1)
        elif category == "load":
            core.load_percent = round(float(value), 1)
        core.timestamp = max(core.timestamp, str(row.get("timestamp") or ""))

    ordered = [cores[i] for i in sorted(cores)]
    if not total and ordered:
        loads = [c.load_percent for c in ordered if c.load_percent is not None]
        total = round(sum(loads) / len(loads), 1) if loads else 0.0
    return CpuLoadResponse(
        total_percent=total,
        package_temperature_c=package_temp,
        cores=ordered,
        meta={"source": "telemetry.db", "table": "sensor_polls", "cores_count": len(ordered)},
    )


def init_router(storage: Optional[TelemetryStorage] = None) -> APIRouter:
    """Создаёт роутер /api/v1/panel/cpu-load.

    Args:
        storage: Хранилище телеметрии (по умолчанию — синглтон).

    Returns:
        APIRouter: Роутер с эндпоинтом GET /api/v1/panel/cpu-load.
    """
    router = APIRouter(tags=["CPU Load Panel"])
    store = storage or TelemetryStorage.get_instance()

    @router.get("/api/v1/panel/cpu-load", response_model=CpuLoadResponse)
    async def get_panel_cpu_load() -> CpuLoadResponse:
        """Возвращает последние значения загрузки и температуры каждого ядра из БД."""
        try:
            return build_cpu_load(store.get_latest_sensors())
        except Exception as exc:
            logger.error(f"[router_cpu_load] Ошибка чтения метрик ядер: {exc}", exc_info=True)
            return CpuLoadResponse(status="error", meta={"source": "telemetry.db", "error": str(exc)})

    return router


__all__ = ["init_router", "build_cpu_load", "CpuLoadResponse", "CpuCoreMetric"]
