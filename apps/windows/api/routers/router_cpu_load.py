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
# Updated: 2026-10-04 08:05:00
# =============================================================================

from __future__ import annotations
"""Роутер панели «Загрузка CPU»: метрики по ядрам и температура из telemetry.db и LibreHardwareMonitor."""

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.modules.hardware.lhm_service import LhmService
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
    name: str = Field(default="CPU", description="Модель процессора")
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
    """Собирает ответ из показаний сенсоров CPU (LHM или telemetry.db).

    Args:
        sensors: Список словарей сенсоров.

    Returns:
        CpuLoadResponse: Загрузка и температура по ядрам.
    """
    cores: Dict[int, CpuCoreMetric] = {}
    temp_by_core: Dict[int, float] = {}
    total = 0.0
    package_temp: Optional[float] = None
    cpu_name = "CPU"

    for row in sensors:
        if str(row.get("hardware_type") or "").lower() != "cpu":
            continue
        hw_name = str(row.get("hardware_name") or "").strip()
        if hw_name and hw_name.lower() != "cpu" and cpu_name == "CPU":
            cpu_name = hw_name

        category = str(row.get("sensor_category") or "").lower()
        value = row.get("value") if row.get("value") is not None else row.get("value_num")
        if value is None:
            continue

        name = str(row.get("sensor_name") or row.get("sensor_id") or "")
        if "tjmax" in name.lower():
            continue

        is_temp = category in _TEMP_CATEGORIES

        if name in ("CPU Total", "cpu_util_total") or row.get("sensor_id") == "cpu_util_total":
            total = round(float(value), 1)
            continue
        if ("package" in name.lower() or row.get("sensor_id") == "cpu_package_temp") and is_temp:
            package_temp = round(float(value), 1)
            continue

        idx = _core_index(row)
        if idx is None:
            continue

        core = cores.setdefault(idx, CpuCoreMetric(index=idx, name=f"Core #{idx}"))
        if is_temp:
            val_f = round(float(value), 1)
            core.temperature_c = val_f
            temp_by_core[idx] = val_f
        elif category == "load":
            core.load_percent = round(float(value), 1)
        core.timestamp = max(core.timestamp, str(row.get("timestamp") or ""))

    # Маппинг температур для Hyper-Threading потоков (когда потоков вдвое больше, чем ядер с термодатчиками)
    if len(temp_by_core) > 0 and len(cores) >= 4 and len(cores) == len(temp_by_core) * 2:
        for core in cores.values():
            core.temperature_c = temp_by_core.get(core.index // 2)

    ordered = [cores[i] for i in sorted(cores)]
    if not total and ordered:
        loads = [c.load_percent for c in ordered if c.load_percent is not None]
        total = round(sum(loads) / len(loads), 1) if loads else 0.0

    return CpuLoadResponse(
        name=cpu_name,
        total_percent=total,
        package_temperature_c=package_temp,
        cores=ordered,
        meta={"source": "telemetry.db/lhm", "cores_count": len(ordered)},
    )


def init_router(storage: Optional[TelemetryStorage] = None, lhm_service: Optional[LhmService] = None) -> APIRouter:
    """Создаёт роутер /api/v1/panel/cpu-load.

    Args:
        storage: Хранилище телеметрии (по умолчанию — синглтон).
        lhm_service: Сервис LibreHardwareMonitor (по умолчанию создается при пустом storage).

    Returns:
        APIRouter: Роутер с эндпоинтом GET /api/v1/panel/cpu-load.
    """
    router = APIRouter(tags=["CPU Load Panel"])
    store = storage or TelemetryStorage.get_instance()
    lhm = lhm_service if lhm_service is not None else (LhmService() if storage is None else None)

    @router.get("/api/v1/panel/cpu-load", response_model=CpuLoadResponse)
    async def get_panel_cpu_load() -> CpuLoadResponse:
        """Возвращает последние значения загрузки и температуры каждого ядра из LHM или БД."""
        try:
            # 1. Прямой опрос работающего LibreHardwareMonitor (если активен)
            if lhm and lhm.is_running():
                lhm_sensors = lhm.get_flattened_sensors()
                if lhm_sensors:
                    resp = build_cpu_load(lhm_sensors)
                    resp.meta = {"source": "lhm_live", "table": "http://127.0.0.1:8085", "cores_count": len(resp.cores)}
                    if resp.cores or resp.total_percent > 0.0:
                        return resp

            # 2. Опрос последних сенсоров из SQLite БД (sensor_polls)
            res = build_cpu_load(store.get_latest_sensors())
            if res.cores or res.total_percent > 0.0:
                res.meta = {"source": "telemetry.db", "table": "sensor_polls", "cores_count": len(res.cores)}
                return res

            # 3. Fallback: извлечение из системных снимков (system_snapshots)
            snaps = store.get_snapshots(limit=1)
            if snaps:
                snap_dict = dict(snaps[0])
                raw_str = snap_dict.get("raw_json")
                total_p = float(snap_dict.get("cpu_total_percent") or 0.0)
                cores_list: List[CpuCoreMetric] = []
                pkg_temp: Optional[float] = None
                cpu_name = "CPU"
                if raw_str:
                    try:
                        raw_data = json.loads(raw_str)
                        cpu_info = raw_data.get("cpu", {})
                        cpu_name = cpu_info.get("model") or cpu_name
                        total_p = float(cpu_info.get("total_percent") or total_p)
                        cores_raw = cpu_info.get("cores_usage") or []
                        for idx, c_val in enumerate(cores_raw):
                            cores_list.append(CpuCoreMetric(index=idx, name=f"Core #{idx}", load_percent=float(c_val)))
                    except Exception:
                        pass
                res = CpuLoadResponse(
                    name=cpu_name,
                    total_percent=round(total_p, 1),
                    package_temperature_c=pkg_temp,
                    cores=cores_list,
                    meta={"source": "telemetry.db", "table": "system_snapshots", "cores_count": len(cores_list)},
                )
            return res
        except Exception as exc:
            logger.error(f"[router_cpu_load] Ошибка чтения метрик ядер: {exc}", exc_info=True)
            return CpuLoadResponse(status="error", meta={"source": "telemetry.db", "error": str(exc)})

    return router


__all__ = ["init_router", "build_cpu_load", "CpuLoadResponse", "CpuCoreMetric"]
