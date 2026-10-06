# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router GPU Load
# =============================================================================
# Description:
#   GET /api/v1/panel/gpu-load — метрики графического ускорителя (GPU):
#   загрузка GPU Core, подсистем (Memory Controller, Video Engine, Bus, D3D),
#   температуры (Core, Hot Spot), видеопамять VRAM и частоты из LHM и telemetry.db.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_gpu_load import init_router
#     app.include_router(init_router())
#
# File: router_gpu_load.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-05 23:40:00
# =============================================================================

from __future__ import annotations
"""Роутер панели «Загрузка GPU»: детальные метрики видеокарты из LibreHardwareMonitor и telemetry.db."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.modules.hardware.lhm_service import LhmService
from apps.windows.telemetry.sqlite import TelemetryStorage

_TEMP_CATEGORIES = ("temperature", "temperatures")
_LOAD_CATEGORIES = ("load", "loads")
_DATA_CATEGORIES = ("data", "memory")
_CLOCK_CATEGORIES = ("clock", "clocks")


class GpuEngineMetric(BaseModel):
    """Метрика отдельного движка/блока GPU."""
    name: str = Field(..., description="Название движка (Core, Memory Controller, Video Engine, etc.)")
    load_percent: Optional[float] = Field(default=None, description="Загрузка движка, %")
    temperature_c: Optional[float] = Field(default=None, description="Температура, связанная с блоком, °C")


class GpuMemoryMetric(BaseModel):
    """Метрики видеопамяти (VRAM)."""
    total_mb: Optional[float] = Field(default=None, description="Всего видеопамяти, MB")
    used_mb: Optional[float] = Field(default=None, description="Занято видеопамяти, MB")
    free_mb: Optional[float] = Field(default=None, description="Свободно видеопамяти, MB")
    used_percent: Optional[float] = Field(default=None, description="Процент занятой видеопамяти, %")


class GpuClocksMetric(BaseModel):
    """Частоты работы GPU."""
    core_mhz: Optional[float] = Field(default=None, description="Частота графического ядра, MHz")
    memory_mhz: Optional[float] = Field(default=None, description="Частота видеопамяти, MHz")


class GpuLoadResponse(BaseModel):
    """Ответ GET /api/v1/panel/gpu-load."""
    status: str = Field(default="ok", description="Статус ответа")
    name: str = Field(default="GPU", description="Модель видеокарты")
    core_load_percent: float = Field(default=0.0, description="Загрузка графического ядра, %")
    core_temperature_c: Optional[float] = Field(default=None, description="Температура GPU Core, °C")
    hotspot_temperature_c: Optional[float] = Field(default=None, description="Температура Hot Spot, °C")
    memory_temperature_c: Optional[float] = Field(default=None, description="Температура VRAM, °C")
    fan_speed_rpm: Optional[float] = Field(default=None, description="Скорость вентилятора, RPM")
    fan_percent: Optional[float] = Field(default=None, description="Обороты вентилятора, %")
    memory: GpuMemoryMetric = Field(default_factory=GpuMemoryMetric, description="Состояние видеопамяти")
    clocks: GpuClocksMetric = Field(default_factory=GpuClocksMetric, description="Частоты GPU")
    engines: List[GpuEngineMetric] = Field(default_factory=list, description="Метрики блоков/движков GPU")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные запроса")


def build_gpu_load(sensors: List[Dict[str, Any]]) -> GpuLoadResponse:
    """Собирает структурированные метрики GPU из списка показаний сенсоров.

    Args:
        sensors: Список словарей сенсоров.

    Returns:
        GpuLoadResponse: Полная информация по загрузке, температуре, памяти и частотам GPU.
    """
    gpu_name = "GPU"
    core_load: Optional[float] = None
    core_temp: Optional[float] = None
    hotspot_temp: Optional[float] = None
    mem_temp: Optional[float] = None
    fan_rpm: Optional[float] = None
    fan_pct: Optional[float] = None

    vram_total: Optional[float] = None
    vram_used: Optional[float] = None
    vram_free: Optional[float] = None
    vram_pct: Optional[float] = None

    clock_core: Optional[float] = None
    clock_mem: Optional[float] = None

    engines_dict: Dict[str, GpuEngineMetric] = {}

    for s in sensors:
        hw_type = str(s.get("hardware_type") or "").lower()
        hw_name = str(s.get("hardware_name") or "")
        s_name = str(s.get("sensor_name") or s.get("name") or "")
        s_cat = str(s.get("sensor_category") or s.get("category") or "").lower()

        # Фильтруем сенсоры GPU
        is_gpu = "gpu" in hw_type or "gpu" in hw_name.lower() or "nvidia" in hw_name.lower() or "radeon" in hw_name.lower()
        if not is_gpu:
            continue

        if hw_name and gpu_name == "GPU":
            gpu_name = hw_name

        # Значение
        val = s.get("value_num")
        if val is None:
            val = s.get("value_numeric")
        if val is None:
            raw = s.get("value_raw") or s.get("value")
            if isinstance(raw, (int, float)):
                val = float(raw)
            elif isinstance(raw, str):
                cleaned = raw.replace("%", "").replace("°C", "").replace("MHz", "").replace("MB", "").replace("RPM", "").strip()
                try:
                    val = float(cleaned)
                except ValueError:
                    val = None

        if val is None:
            continue

        s_name_lower = s_name.lower()

        # 1. Температуры
        if any(cat in s_cat for cat in _TEMP_CATEGORIES):
            if "hot spot" in s_name_lower or "hotspot" in s_name_lower:
                hotspot_temp = val
            elif "memory" in s_name_lower or "vram" in s_name_lower:
                mem_temp = val
            elif "core" in s_name_lower or core_temp is None:
                core_temp = val

        # 2. Нагрузка движков / подсистем
        elif any(cat in s_cat for cat in _LOAD_CATEGORIES):
            if s_name_lower in ("gpu core", "core", "gpu"):
                core_load = val
                engines_dict["GPU Core"] = GpuEngineMetric(name="GPU Core", load_percent=val, temperature_c=core_temp)
            elif "memory controller" in s_name_lower:
                engines_dict["Memory Controller"] = GpuEngineMetric(name="Memory Controller", load_percent=val)
            elif "video engine" in s_name_lower or "video decode" in s_name_lower:
                if "Video Engine" not in engines_dict or val > (engines_dict["Video Engine"].load_percent or 0):
                    engines_dict["Video Engine"] = GpuEngineMetric(name="Video Engine", load_percent=val)
            elif "bus" in s_name_lower:
                engines_dict["GPU Bus"] = GpuEngineMetric(name="GPU Bus", load_percent=val)
            elif "memory" in s_name_lower:
                vram_pct = val
                engines_dict["GPU Memory"] = GpuEngineMetric(name="GPU Memory", load_percent=val)
            elif "3d" in s_name_lower:
                engines_dict["D3D 3D"] = GpuEngineMetric(name="D3D 3D", load_percent=val)
            elif "compute" in s_name_lower:
                eng_name = s_name.strip()
                engines_dict[eng_name] = GpuEngineMetric(name=eng_name, load_percent=val)
            else:
                engines_dict[s_name] = GpuEngineMetric(name=s_name, load_percent=val)

        # 3. Видеопамять (VRAM)
        elif any(cat in s_cat for cat in _DATA_CATEGORIES):
            if "total" in s_name_lower:
                vram_total = val
            elif "used" in s_name_lower:
                if "dedicated" in s_name_lower:
                    if vram_used is None:
                        vram_used = val
                else:
                    vram_used = val
            elif "free" in s_name_lower:
                vram_free = val

        # 4. Частоты
        elif any(cat in s_cat for cat in _CLOCK_CATEGORIES):
            if "core" in s_name_lower:
                clock_core = val
            elif "memory" in s_name_lower:
                clock_mem = val

        # 5. Обороты вентилятора
        elif "fan" in s_cat or "fan" in s_name_lower:
            if "rpm" in str(s.get("unit", "")).lower() or val > 100:
                fan_rpm = val
            else:
                fan_pct = val

    # Синхронизируем температуру для GPU Core в engines
    if "GPU Core" in engines_dict and core_temp is not None:
        engines_dict["GPU Core"].temperature_c = core_temp

    # Вычисляем процент занятой памяти, если не пришёл явно
    if vram_pct is None and vram_total and vram_used is not None and vram_total > 0:
        vram_pct = round((vram_used / vram_total) * 100, 1)

    # Упорядочиваем список движков
    ordered_keys = ["GPU Core", "Memory Controller", "Video Engine", "GPU Memory", "GPU Bus", "D3D 3D"]
    engines_list: List[GpuEngineMetric] = []
    for k in ordered_keys:
        if k in engines_dict:
            engines_list.append(engines_dict.pop(k))
    # Добавляем остальные
    engines_list.extend(engines_dict.values())

    return GpuLoadResponse(
        status="ok",
        name=gpu_name,
        core_load_percent=core_load if core_load is not None else 0.0,
        core_temperature_c=core_temp,
        hotspot_temperature_c=hotspot_temp,
        memory_temperature_c=mem_temp,
        fan_speed_rpm=fan_rpm,
        fan_percent=fan_pct,
        memory=GpuMemoryMetric(
            total_mb=vram_total,
            used_mb=vram_used,
            free_mb=vram_free,
            used_percent=vram_pct,
        ),
        clocks=GpuClocksMetric(
            core_mhz=clock_core,
            memory_mhz=clock_mem,
        ),
        engines=engines_list,
        meta={"source": "lhm_live", "engines_count": len(engines_list)},
    )


def init_router(storage: Optional[TelemetryStorage] = None, lhm_service: Optional[LhmService] = None) -> APIRouter:
    """Инициализация роутера GET /api/v1/panel/gpu-load.

    Args:
        storage: Опциональное хранилище TelemetryStorage.
        lhm_service: Опциональный сервис LhmService.

    Returns:
        APIRouter: Настроенный роутер FastAPI.
    """
    router = APIRouter(prefix="/api/v1/panel", tags=["GPU Panel"])

    @router.get("/gpu-load", response_model=GpuLoadResponse, summary="Загрузка, температура и метрики GPU")
    async def get_gpu_load() -> GpuLoadResponse:
        """Возвращает детальную загрузку, температуру, VRAM и частоты GPU."""
        # 1. Пробуем получить живые данные LHM
        lhm = lhm_service or LhmService()
        if lhm.is_running():
            try:
                sensors = lhm.get_flattened_sensors()
                gpu_sensors = [
                    s for s in sensors
                    if "gpu" in str(s.get("hardware_type", "")).lower()
                    or "gpu" in str(s.get("hardware_name", "")).lower()
                    or "nvidia" in str(s.get("hardware_name", "")).lower()
                    or "radeon" in str(s.get("hardware_name", "")).lower()
                ]
                if gpu_sensors:
                    resp = build_gpu_load(gpu_sensors)
                    resp.meta = {"source": "lhm_live", "engines_count": len(resp.engines)}
                    return resp
            except Exception as exc:
                logger.warning(f"[router_gpu_load] Ошибка опроса живого LHM: {exc}")

        # 2. Fallback: Опрос из telemetry.db
        st = storage or TelemetryStorage.get_instance(read_only=True)
        try:
            db_sensors = st.get_latest_sensors()
            if db_sensors:
                gpu_sensors = [
                    s for s in db_sensors
                    if "gpu" in str(s.get("hardware_type", "")).lower()
                    or "gpu" in str(s.get("hardware_name", "")).lower()
                    or "nvidia" in str(s.get("hardware_name", "")).lower()
                ]
                if gpu_sensors:
                    resp = build_gpu_load(gpu_sensors)
                    resp.meta = {"source": "telemetry_db", "engines_count": len(resp.engines)}
                    return resp
        except Exception as exc:
            logger.error(f"[router_gpu_load] Ошибка чтения метрик GPU из БД: {exc}", exc_info=True)

        return GpuLoadResponse(
            status="ok",
            name="GPU",
            core_load_percent=0.0,
            engines=[],
            meta={"source": "none", "engines_count": 0},
        )

    return router
