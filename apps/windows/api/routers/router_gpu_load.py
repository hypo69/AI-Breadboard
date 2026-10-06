# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router GPU Load
# =============================================================================
# Description:
#   GET /api/v1/panel/gpu-load — метрики графического ускорителя (GPU):
#   загрузка GPU Core, подсистем (Memory Controller, Video Engine, Bus, D3D),
#   температуры (Core, Hot Spot), видеопамять VRAM, энергопотребление,
#   паспортные данные GPU (Specs), датчики и история замеров из LHM и telemetry.db.
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
# Updated: 2026-10-06 07:25:00
# =============================================================================

from __future__ import annotations

"""Роутер панели «Загрузка GPU»: детальные метрики видеокарты, паспорт, сенсоры и история из LHM и telemetry.db."""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.modules.hardware.lhm_service import LhmService
from apps.windows.modules.hardware.gpu_prober import GpuProber
from apps.windows.telemetry.sqlite import TelemetryStorage

_TEMP_CATEGORIES = ("temperature", "temperatures")
_LOAD_CATEGORIES = ("load", "loads")
_DATA_CATEGORIES = ("data", "memory")
_CLOCK_CATEGORIES = ("clock", "clocks")
_POWER_CATEGORIES = ("power", "powers")
_VOLTAGE_CATEGORIES = ("voltage", "voltages")

_CPU_HARDWARE_KEYWORDS = (
    "cpu", "processor", "core i3", "core i5", "core i7", "core i9",
    "ryzen", "xeon", "threadripper", "pentium", "celeron", "athlon"
)

_CPU_SENSOR_BLACKLIST = (
    "cpu core", "cpu thread", "cpu total", "cpu max", "cpu package",
    "cpu cores", "cpu memory", "cpu platform", "bus speed", "core average",
    "core max", "distance to tjmax", "cpu freq", "cpu utilization",
    "core #", "thread #"
)


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


class GpuSensorMetric(BaseModel):
    """Электрический или физический сенсор графического процессора."""
    id: str = Field(..., description="Уникальный идентификатор сенсора")
    name: str = Field(..., description="Понятное название сенсора")
    category: str = Field(default="General", description="Категория (Powers, Voltages, Clocks, Fans)")
    unit: str = Field(default="", description="Единица измерения (W, V, MHz, RPM, %)")
    value: float = Field(default=0.0, description="Числовое значение")
    value_raw: str = Field(default="", description="Форматированная строка со значением")
    status: str = Field(default="normal", description="Статус: normal, warning, danger")


class GpuHistoryPoint(BaseModel):
    """Точка временного ряда истории параметров GPU."""
    timestamp: str = Field(default="", description="ISO время точки")
    time_label: str = Field(default="", description="Короткая метка времени ЧЧ:ММ:СС")
    load_percent: float = Field(default=0.0, description="Загрузка ядра GPU, %")
    temperature_c: Optional[float] = Field(default=None, description="Температура GPU Core, °C")
    power_w: Optional[float] = Field(default=None, description="Потребляемая мощность, Вт")
    vram_percent: Optional[float] = Field(default=None, description="Занятая память VRAM, %")


class GpuSpecsInfo(BaseModel):
    """Сводная спецификация и паспортные данные графического ускорителя."""
    name: str = Field(default="", description="Наименование модели видеокарты")
    vendor: str = Field(default="NVIDIA", description="Производитель (NVIDIA, AMD, Intel, Generic)")
    driver_version: str = Field(default="", description="Версия видеодрайвера")
    driver_date: str = Field(default="", description="Дата релиза видеодрайвера")
    vram_mb: Optional[float] = Field(default=None, description="Объем видеопамяти VRAM, МБ")
    vram_gb: Optional[float] = Field(default=None, description="Объем видеопамяти VRAM, ГБ")
    vram_str: str = Field(default="", description="Форматированный объем видеопамяти")
    vram_used_str: str = Field(default="", description="Форматированная занятая память с процентом")
    core_clock_mhz: Optional[float] = Field(default=None, description="Частота графического процессора, МГц")
    core_clock_str: str = Field(default="", description="Форматированная частота ядра")
    memory_clock_mhz: Optional[float] = Field(default=None, description="Частота видеопамяти, МГц")
    memory_clock_str: str = Field(default="", description="Форматированная частота памяти")
    directx: str = Field(default="DirectX 12 (FL 12_1)", description="Поддерживаемый графический API")
    pci_bus: str = Field(default="PCIe x16", description="Интерфейс подключения шины")
    cuda_cores: Optional[int] = Field(default=None, description="Количество шейдерных ядер CUDA / блоков")
    directml_supported: bool = Field(default=True, description="Поддержка DirectML ускорения")
    power_limit_w: Optional[float] = Field(default=None, description="Лимит TDP, Вт")


class GpuLoadResponse(BaseModel):
    """Ответ GET /api/v1/panel/gpu-load."""
    status: str = Field(default="ok", description="Статус ответа")
    name: str = Field(default="GPU", description="Модель видеокарты")
    vendor: str = Field(default="NVIDIA", description="Производитель GPU")
    core_load_percent: float = Field(default=0.0, description="Загрузка графического ядра, %")
    core_temperature_c: Optional[float] = Field(default=None, description="Температура GPU Core, °C")
    hotspot_temperature_c: Optional[float] = Field(default=None, description="Температура Hot Spot, °C")
    memory_temperature_c: Optional[float] = Field(default=None, description="Температура VRAM, °C")
    power_w: Optional[float] = Field(default=None, description="Энергопотребление GPU, Вт")
    fan_speed_rpm: Optional[float] = Field(default=None, description="Скорость вентилятора, RPM")
    fan_percent: Optional[float] = Field(default=None, description="Обороты вентилятора, %")
    memory: GpuMemoryMetric = Field(default_factory=GpuMemoryMetric, description="Состояние видеопамяти")
    clocks: GpuClocksMetric = Field(default_factory=GpuClocksMetric, description="Частоты GPU")
    specs: Optional[GpuSpecsInfo] = Field(default=None, description="Паспортные характеристики GPU")
    engines: List[GpuEngineMetric] = Field(default_factory=list, description="Метрики блоков/движков GPU")
    sensors: List[GpuSensorMetric] = Field(default_factory=list, description="Сенсоры электропитания, напряжения и вентиляторов GPU")
    history: List[GpuHistoryPoint] = Field(default_factory=list, description="История параметров GPU")
    available_gpus: List[Dict[str, Any]] = Field(default_factory=list, description="Список всех обнаруженных видеокарт")
    devices: List[Dict[str, Any]] = Field(default_factory=list, description="Полные метрики по каждому отдельному GPU в системе")
    current_gpu_index: int = Field(default=0, description="Индекс текущей отображаемой видеокарты")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные запроса")


def _calculate_gpu_sensor_status(category: str, value: float) -> str:
    """Определяет статус сенсора GPU по категории и значению."""
    cat = category.lower()
    if "temp" in cat:
        if value >= 83.0:
            return "danger"
        if value >= 74.0:
            return "warning"
        return "normal"
    if "load" in cat:
        if value >= 95.0:
            return "danger"
        if value >= 80.0:
            return "warning"
        return "normal"
    return "normal"


def _normalize_gpu_sensor_name(sid: str, name: str, cat: str) -> str:
    """Формирует понятное название для сенсора GPU без Unknown."""
    raw = (name or "").strip()
    if not raw or raw.lower() in ("unknown", "sensor"):
        return f"GPU Sensor #{sid}" if sid else "GPU Sensor"

    raw_l = raw.lower()
    cat_l = cat.lower()

    if raw_l == "gpu package" and "power" in cat_l:
        return "GPU Package Power"
    if raw_l == "gpu power" or (raw_l == "power" and "power" in cat_l):
        return "GPU Board Power"
    if raw_l == "gpu core" and "volt" in cat_l:
        return "GPU Core Voltage"
    if raw_l == "gpu memory" and "clock" in cat_l:
        return "GPU Memory Clock"
    if raw_l == "gpu core" and "clock" in cat_l:
        return "GPU Core Clock"
    if raw_l == "gpu fan" or (raw_l == "fan" and "fan" in cat_l):
        return "GPU Fan Speed"

    return raw


def _is_sensor_matching_gpu(sensor_hw_name: str, target_gpu_name: str, sensor_hw_type: str = "") -> bool:
    """Проверяет, принадлежит ли показание сенсора целевой видеокарте и не относится ли к CPU."""
    if sensor_hw_type and str(sensor_hw_type).lower() == "cpu":
        return False
    if not sensor_hw_name:
        return True

    s_clean_raw = str(sensor_hw_name).strip().lower()
    if any(k in s_clean_raw for k in _CPU_HARDWARE_KEYWORDS):
        return False

    if not target_gpu_name:
        return True

    t_clean_raw = str(target_gpu_name).strip().lower()

    # Прямое равенство или взаимное включение подстрок
    if s_clean_raw == t_clean_raw or s_clean_raw in t_clean_raw or t_clean_raw in s_clean_raw:
        return True

    ignore = {
        'gpu', 'graphics', 'corporation', 'corp', 'inc', 'series', 'adapter', 'video',
        'display', 'controller', 'intel', 'nvidia', 'amd', 'microsoft', 'basic'
    }
    s_clean = re.sub(r'[^a-zA-Z0-9]+', ' ', s_clean_raw)
    t_clean = re.sub(r'[^a-zA-Z0-9]+', ' ', t_clean_raw)
    s_toks = {t for t in s_clean.split() if t and t not in ignore}
    t_toks = {t for t in t_clean.split() if t and t not in ignore}

    if not s_toks or not t_toks:
        # Если остались только бренды, проверяем вендора
        s_brand = "nvidia" if "nvidia" in s_clean_raw or "geforce" in s_clean_raw else ("amd" if "amd" in s_clean_raw or "radeon" in s_clean_raw else ("intel" if "intel" in s_clean_raw else None))
        t_brand = "nvidia" if "nvidia" in t_clean_raw or "geforce" in t_clean_raw else ("amd" if "amd" in t_clean_raw or "radeon" in t_clean_raw else ("intel" if "intel" in t_clean_raw else None))
        return bool(s_brand and t_brand and s_brand == t_brand)

    return bool(s_toks & t_toks)


def build_gpu_load(
    sensors: List[Dict[str, Any]],
    inventory: Optional[Dict[str, Any]] = None,
    history_samples: Optional[List[Dict[str, Any]]] = None,
    target_gpu_name: Optional[str] = None,
    available_gpus: Optional[List[Dict[str, Any]]] = None,
    current_gpu_index: int = 0,
) -> GpuLoadResponse:
    """Собирает структурированные метрики конкретного GPU из списка сенсоров, паспорта и истории.

    Args:
        sensors: Список словарей сенсоров.
        inventory: Паспортные данные GPU из gpu_inventory / GpuProber.
        history_samples: Исторические сэмплы из gpu_telemetry_samples или снимков.
        target_gpu_name: Название целевой видеокарты для фильтрации сенсоров.
        available_gpus: Список всех видеокарт в системе.
        current_gpu_index: Индекс выбранной видеокарты.

    Returns:
        GpuLoadResponse: Полная информация по загрузке, температуре, памяти, спецификациям и истории GPU.
    """
    gpu_name = target_gpu_name or (inventory.get("name") if inventory else "GPU")
    core_load: Optional[float] = None
    core_temp: Optional[float] = None
    hotspot_temp: Optional[float] = None
    mem_temp: Optional[float] = None
    power_draw: Optional[float] = None
    fan_rpm: Optional[float] = None
    fan_pct: Optional[float] = None

    vram_total: Optional[float] = None
    vram_used: Optional[float] = None
    vram_free: Optional[float] = None
    vram_pct: Optional[float] = None

    clock_core: Optional[float] = None
    clock_mem: Optional[float] = None

    engines_dict: Dict[str, GpuEngineMetric] = {}
    general_sensors_list: List[GpuSensorMetric] = []
    seen_sensor_keys = set()

    for s in sensors:
        hw_type = str(s.get("hardware_type") or "").lower()
        hw_name = str(s.get("hardware_name") or "")
        s_id = str(s.get("sensor_id") or s.get("id") or "")
        s_name = str(s.get("sensor_name") or s.get("name") or s_id)
        s_cat = str(s.get("sensor_category") or s.get("category") or "").lower()
        s_unit = str(s.get("unit") or "")

        # 1. Строго отсекаем сенсоры CPU
        if hw_type == "cpu" or any(k in hw_name.lower() for k in _CPU_HARDWARE_KEYWORDS):
            continue

        s_name_lower = s_name.lower()
        s_id_lower = s_id.lower()
        if any(black in s_name_lower or black in s_id_lower for black in _CPU_SENSOR_BLACKLIST):
            continue

        # 2. Фильтруем сенсоры GPU
        is_gpu = (
            "gpu" in hw_type
            or "gpu" in hw_name.lower()
            or "nvidia" in hw_name.lower()
            or "radeon" in hw_name.lower()
            or "geforce" in hw_name.lower()
            or "rtx" in hw_name.lower()
            or "gtx" in hw_name.lower()
            or "uhd" in hw_name.lower()
            or "iris" in hw_name.lower()
            or "arc" in hw_name.lower()
        )
        if not is_gpu:
            continue

        # 3. Фильтруем строго под целевой GPU, если имя задано
        if target_gpu_name and hw_name and not _is_sensor_matching_gpu(hw_name, target_gpu_name, hw_type):
            continue

        if hw_name and (gpu_name == "GPU" or not target_gpu_name):
            gpu_name = hw_name

        # Значение
        val = s.get("value_num")
        if val is None:
            val = s.get("value_numeric")
        if val is None:
            val = s.get("value")
        if val is None:
            raw = s.get("value_raw")
            if isinstance(raw, (int, float)):
                val = float(raw)
            elif isinstance(raw, str):
                cleaned = raw.replace("%", "").replace("°C", "").replace("MHz", "").replace("MB", "").replace("RPM", "").replace("W", "").replace("V", "").strip()
                try:
                    val = float(cleaned)
                except ValueError:
                    val = None

        if val is None:
            continue

        # 1. Температуры
        if any(cat in s_cat for cat in _TEMP_CATEGORIES) or s_unit == "°C":
            if "hot spot" in s_name_lower or "hotspot" in s_name_lower:
                hotspot_temp = val
            elif "memory" in s_name_lower or "vram" in s_name_lower:
                mem_temp = val
            elif "core" in s_name_lower or core_temp is None:
                core_temp = val

        # 2. Нагрузка движков / подсистем
        elif any(cat in s_cat for cat in _LOAD_CATEGORIES) or (s_unit == "%" and "fan" not in s_cat):
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
            elif "memory" in s_name_lower and "controller" not in s_name_lower:
                vram_pct = val
                engines_dict["GPU Memory"] = GpuEngineMetric(name="GPU Memory", load_percent=val)
            elif "3d" in s_name_lower:
                engines_dict["D3D 3D"] = GpuEngineMetric(name="D3D 3D", load_percent=val)
            elif "copy" in s_name_lower:
                engines_dict["Copy Engine"] = GpuEngineMetric(name="Copy Engine", load_percent=val)
            elif "compute" in s_name_lower:
                eng_name = s_name.strip()
                engines_dict[eng_name] = GpuEngineMetric(name=eng_name, load_percent=val)
            else:
                engines_dict[s_name] = GpuEngineMetric(name=s_name, load_percent=val)

        # 3. Видеопамять (VRAM)
        elif any(cat in s_cat for cat in _DATA_CATEGORIES) or "mb" in s_unit.lower() or "gb" in s_unit.lower():
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
        elif any(cat in s_cat for cat in _CLOCK_CATEGORIES) or "mhz" in s_unit.lower():
            if "core" in s_name_lower:
                clock_core = val
            elif "memory" in s_name_lower:
                clock_mem = val

        # 5. Мощность (Power)
        elif any(cat in s_cat for cat in _POWER_CATEGORIES) or s_unit.lower() == "w":
            if power_draw is None or "package" in s_name_lower or "total" in s_name_lower or "board" in s_name_lower:
                power_draw = val

        # 6. Обороты вентилятора
        elif "fan" in s_cat or "fan" in s_name_lower:
            if "rpm" in s_unit.lower() or val > 100:
                fan_rpm = val
            else:
                fan_pct = val

        # Добавление в общий список электрических/физических сенсоров GPU
        if (
            any(cat in s_cat for cat in _POWER_CATEGORIES)
            or any(cat in s_cat for cat in _VOLTAGE_CATEGORIES)
            or any(cat in s_cat for cat in _CLOCK_CATEGORIES)
            or "fan" in s_cat
            or s_unit.lower() in ("w", "v", "rpm")
        ):
            norm_name = _normalize_gpu_sensor_name(s_id, s_name, s_cat)
            s_key = f"{s_cat}_{norm_name.lower()}"
            if s_key not in seen_sensor_keys:
                seen_sensor_keys.add(s_key)
                unit_str = s_unit
                if not unit_str:
                    if any(cat in s_cat for cat in _POWER_CATEGORIES): unit_str = "W"
                    elif any(cat in s_cat for cat in _VOLTAGE_CATEGORIES): unit_str = "V"
                    elif any(cat in s_cat for cat in _CLOCK_CATEGORIES): unit_str = "MHz"
                    elif "fan" in s_cat: unit_str = "RPM" if val > 100 else "%"

                val_raw_str = f"{val:.1f} {unit_str}".strip()
                if unit_str == "V":
                    val_raw_str = f"{val:.3f} V"
                elif unit_str == "MHz" and val >= 1000.0:
                    val_raw_str = f"{val / 1000.0:.2f} GHz"

                general_sensors_list.append(
                    GpuSensorMetric(
                        id=s_id or f"gpu_sensor_{len(general_sensors_list)+1}",
                        name=norm_name,
                        category=s_cat.capitalize() or "General",
                        unit=unit_str,
                        value=round(val, 2),
                        value_raw=val_raw_str,
                        status=_calculate_gpu_sensor_status(s_cat, val),
                    )
                )

    # Синхронизируем температуру для GPU Core в engines
    if "GPU Core" in engines_dict and core_temp is not None:
        engines_dict["GPU Core"].temperature_c = core_temp

    # Вычисляем процент занятой памяти, если не пришёл явно
    if vram_pct is None and vram_total and vram_used is not None and vram_total > 0:
        vram_pct = round((vram_used / vram_total) * 100, 1)

    # Упорядочиваем список движков
    ordered_keys = ["GPU Core", "Memory Controller", "Video Engine", "GPU Memory", "GPU Bus", "D3D 3D", "Copy Engine"]
    engines_list: List[GpuEngineMetric] = []
    for k in ordered_keys:
        if k in engines_dict:
            engines_list.append(engines_dict.pop(k))
    engines_list.extend(engines_dict.values())

    # Паспортные данные GPU (Specs)
    inv = inventory or {}
    inv_name = inv.get("name") or gpu_name
    inv_name_l = inv_name.lower()
    vendor = inv.get("vendor") or ("NVIDIA" if "nvidia" in inv_name_l or "geforce" in inv_name_l else ("AMD" if "amd" in inv_name_l or "radeon" in inv_name_l else ("Intel" if "intel" in inv_name_l or "arc" in inv_name_l or "uhd" in inv_name_l else "GPU")))
    driver_ver = str(inv.get("driver_version") or "")
    driver_dt = str(inv.get("driver_date") or "")
    vram_b = inv.get("vram_bytes") or 0
    vram_g = inv.get("vram_gb") or (vram_total / 1024.0 if vram_total else (vram_b / (1024**3) if vram_b else 0.0))
    if vram_total is None and vram_g > 0:
        vram_total = vram_g * 1024.0

    vram_str = f"{vram_g:.1f} GB" if vram_g >= 1.0 else (f"{vram_total:.0f} MB" if vram_total else "--")
    if vram_used is not None and vram_total:
        vram_used_gb = vram_used / 1024.0 if vram_used >= 1024 else vram_used / 1024.0
        vram_used_str = f"{vram_used_gb:.1f} / {vram_g:.1f} GB ({vram_pct or 0:.0f}%)"
    elif vram_pct is not None:
        vram_used_str = f"{vram_pct:.0f}% занято"
    else:
        vram_used_str = "--"

    core_clk_str = f"{clock_core:.0f} MHz" if clock_core else "--"
    mem_clk_str = f"{clock_mem:.0f} MHz" if clock_mem else "--"

    pci_bus_str = str(inv.get("pci_bus_id") or ("PCIe x16" if vendor in ("NVIDIA", "AMD") else "Integrated / PCIe"))
    cuda_c = inv.get("cuda_cores")
    directml = bool(inv.get("directml_supported", True))

    specs_obj = GpuSpecsInfo(
        name=inv_name,
        vendor=vendor,
        driver_version=driver_ver or "WDDM 2.7",
        driver_date=driver_dt,
        vram_mb=vram_total,
        vram_gb=round(vram_g, 2) if vram_g else None,
        vram_str=vram_str,
        vram_used_str=vram_used_str,
        core_clock_mhz=clock_core,
        core_clock_str=core_clk_str,
        memory_clock_mhz=clock_mem,
        memory_clock_str=mem_clk_str,
        directx="DirectX 12 (FL 12_1)",
        pci_bus=pci_bus_str,
        cuda_cores=cuda_c,
        directml_supported=directml,
    )

    # История параметров GPU
    history_points: List[GpuHistoryPoint] = []
    if history_samples:
        for r in history_samples:
            ts_str = str(r.get("timestamp") or "")
            t_label = ts_str.split("T")[-1][:8] if "T" in ts_str else ts_str[-8:]
            p_load = float(r.get("load_percent") or r.get("gpu_load_percent") or 0.0)
            p_temp = r.get("temperature_gpu_c") or r.get("temperature_c") or r.get("core_temperature_c")
            p_pow = r.get("power_draw_w") or r.get("power_w")
            p_mem = r.get("memory_percent") or r.get("vram_percent")

            history_points.append(
                GpuHistoryPoint(
                    timestamp=ts_str,
                    time_label=t_label or "--:--:--",
                    load_percent=round(p_load, 1),
                    temperature_c=round(float(p_temp), 1) if p_temp is not None else core_temp,
                    power_w=round(float(p_pow), 1) if p_pow is not None else power_draw,
                    vram_percent=round(float(p_mem), 1) if p_mem is not None else vram_pct,
                )
            )

    return GpuLoadResponse(
        status="ok",
        name=inv_name,
        vendor=vendor,
        core_load_percent=round(core_load if core_load is not None else 0.0, 1),
        core_temperature_c=core_temp,
        hotspot_temperature_c=hotspot_temp,
        memory_temperature_c=mem_temp,
        power_w=power_draw,
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
        specs=specs_obj,
        engines=engines_list,
        sensors=general_sensors_list,
        history=history_points,
        available_gpus=available_gpus or [],
        current_gpu_index=current_gpu_index,
        meta={
            "source": "telemetry.db",
            "engines_count": len(engines_list),
            "sensors_count": len(general_sensors_list),
        },
    )


def _discover_system_gpus(storage: Optional[TelemetryStorage] = None) -> List[Dict[str, Any]]:
    """Собирает список всех физических и интегрированных видеокарт в системе строго из БД/инвентаря.

    Returns:
        List[Dict[str, Any]]: Список словарей характеристик обнаруженных GPU.
    """
    gpus: List[Dict[str, Any]] = []

    # 1. Если передано хранилище и в нем есть инвентарь GPU
    if storage:
        try:
            db_inv = storage.get_gpu_inventory()
            if db_inv:
                for idx, item in enumerate(db_inv):
                    g_name = item.get("name", f"GPU {idx}")
                    g_name_l = g_name.lower()
                    vendor = "NVIDIA" if "nvidia" in g_name_l or "geforce" in g_name_l else ("AMD" if "amd" in g_name_l or "radeon" in g_name_l else ("Intel" if "intel" in g_name_l or "arc" in g_name_l or "uhd" in g_name_l else item.get("vendor", "Generic")))
                    gpus.append({
                        "index": item.get("gpu_id", idx),
                        "name": g_name,
                        "vendor": vendor,
                        "driver_version": item.get("driver_version", ""),
                        "driver_date": item.get("driver_date", ""),
                        "vram_gb": item.get("vram_gb", 0.0),
                        "pci_bus_id": item.get("pci_bus_id", ""),
                        "cuda_cores": item.get("cuda_cores"),
                        "directml_supported": item.get("directml_supported", True),
                    })
        except Exception as exc:
            logger.debug(f"[router_gpu_load] Ошибка чтения gpu_inventory из БД: {exc}")

        # Если инвентаря нет, но в БД есть сохраненные сенсоры GPU
        if not gpus:
            try:
                db_sensors = storage.get_latest_sensors()
                if db_sensors:
                    seen_names: Dict[str, int] = {}
                    for s in db_sensors:
                        ht = str(s.get("hardware_type", "")).lower()
                        hn = str(s.get("hardware_name", "")).strip()
                        hn_l = hn.lower()
                        if ht == "cpu" or any(k in hn_l for k in _CPU_HARDWARE_KEYWORDS):
                            continue
                        if hn and ("gpu" in ht or "gpu" in hn_l or "nvidia" in hn_l or "radeon" in hn_l or "geforce" in hn_l or "rtx" in hn_l or "gtx" in hn_l or "uhd" in hn_l or "iris" in hn_l or "arc" in hn_l):
                            if hn not in seen_names:
                                seen_names[hn] = len(seen_names)
                    for hn, idx in seen_names.items():
                        hn_l = hn.lower()
                        vendor = "NVIDIA" if "nvidia" in hn_l or "geforce" in hn_l else ("AMD" if "amd" in hn_l or "radeon" in hn_l else ("Intel" if "intel" in hn_l or "arc" in hn_l or "uhd" in hn_l else "Generic"))
                        gpus.append({
                            "index": idx,
                            "name": hn,
                            "vendor": vendor,
                            "driver_version": "",
                            "vram_gb": 0.0,
                        })
            except Exception as exc:
                logger.debug(f"[router_gpu_load] Ошибка извлечения GPU из latest_sensors: {exc}")

    # 2. Опрос через GpuProber (NVIDIA SMI + AMD SMI + WMI с дедупликацией), если хранилище пусто
    if not gpus and storage is None:
        try:
            prober = GpuProber()
            probed = prober.probe_all()
            for g in probed:
                gpus.append({
                    "index": g.index,
                    "name": g.name,
                    "vendor": g.vendor,
                    "driver_version": g.driver_version,
                    "vram_gb": round(g.memory_total_mb / 1024.0, 1) if g.memory_total_mb else 0.0,
                    "temperature_gpu_c": g.temperature_gpu_c,
                    "utilization_gpu_pct": g.utilization_gpu_pct,
                    "memory_used_mb": g.memory_used_mb,
                    "memory_total_mb": g.memory_total_mb,
                })
        except Exception as exc:
            logger.debug(f"[router_gpu_load] Ошибка GpuProber: {exc}")

    if not gpus:
        gpus.append({
            "index": 0,
            "name": "GPU",
            "vendor": "Generic",
            "driver_version": "N/A",
            "vram_gb": 0.0,
        })

    return gpus


def _fetch_single_gpu_data(
    target_idx: int,
    target_gpu: Dict[str, Any],
    available_gpus: List[Dict[str, Any]],
    store: TelemetryStorage,
    lhm: Optional[LhmService] = None,
) -> GpuLoadResponse:
    """Извлекает детальные параметры и сенсоры для конкретного GPU строго из БД телеметрии."""
    target_name = target_gpu.get("name", f"GPU {target_idx}")

    # 1. Загрузка истории сэмплов из SQLite базы данных
    try:
        db_history = store.get_gpu_telemetry_samples(gpu_id=target_idx, limit=60)
    except TypeError:
        db_history = store.get_gpu_telemetry_samples(limit=60)
    except Exception:
        db_history = []

    if not db_history:
        try:
            db_history = store.get_gpu_telemetry_samples(limit=60)
        except Exception:
            db_history = []
    db_history.reverse()

    # 2. Получение последних показаний сенсоров строго из SQLite базы данных
    try:
        db_sensors = store.get_latest_sensors()
        if db_sensors:
            gpu_sensors = [
                s for s in db_sensors
                if str(s.get("hardware_type", "")).lower() != "cpu"
                and not any(k in str(s.get("hardware_name", "")).lower() for k in _CPU_HARDWARE_KEYWORDS)
                and (
                    "gpu" in str(s.get("hardware_type", "")).lower()
                    or "gpu" in str(s.get("hardware_name", "")).lower()
                    or "nvidia" in str(s.get("hardware_name", "")).lower()
                    or "radeon" in str(s.get("hardware_name", "")).lower()
                    or "geforce" in str(s.get("hardware_name", "")).lower()
                    or "rtx" in str(s.get("hardware_name", "")).lower()
                    or "gtx" in str(s.get("hardware_name", "")).lower()
                    or "uhd" in str(s.get("hardware_name", "")).lower()
                    or "iris" in str(s.get("hardware_name", "")).lower()
                    or "arc" in str(s.get("hardware_name", "")).lower()
                )
                and _is_sensor_matching_gpu(str(s.get("hardware_name", "")), target_name, str(s.get("hardware_type", "")))
            ]
            if gpu_sensors:
                resp = build_gpu_load(
                    sensors=gpu_sensors,
                    inventory=target_gpu,
                    history_samples=db_history,
                    target_gpu_name=target_name,
                    available_gpus=available_gpus,
                    current_gpu_index=target_idx,
                )
                resp.meta["source"] = "telemetry_db"
                return resp
    except Exception as exc:
        logger.error(f"[router_gpu_load] Ошибка чтения метрик GPU из БД: {exc}", exc_info=True)

    # 3. Fallback: Живой опрос LHM, только если явно передан и доступен
    if lhm and lhm.is_running():
        try:
            sensors = lhm.get_flattened_sensors()
            gpu_sensors = [
                s for s in sensors
                if str(s.get("hardware_type", "")).lower() != "cpu"
                and not any(k in str(s.get("hardware_name", "")).lower() for k in _CPU_HARDWARE_KEYWORDS)
                and (
                    "gpu" in str(s.get("hardware_type", "")).lower()
                    or "gpu" in str(s.get("hardware_name", "")).lower()
                    or "nvidia" in str(s.get("hardware_name", "")).lower()
                    or "radeon" in str(s.get("hardware_name", "")).lower()
                    or "geforce" in str(s.get("hardware_name", "")).lower()
                    or "rtx" in str(s.get("hardware_name", "")).lower()
                    or "gtx" in str(s.get("hardware_name", "")).lower()
                    or "uhd" in str(s.get("hardware_name", "")).lower()
                    or "iris" in str(s.get("hardware_name", "")).lower()
                    or "arc" in str(s.get("hardware_name", "")).lower()
                )
                and _is_sensor_matching_gpu(str(s.get("hardware_name", "")), target_name, str(s.get("hardware_type", "")))
            ]
            if gpu_sensors:
                resp = build_gpu_load(
                    sensors=gpu_sensors,
                    inventory=target_gpu,
                    history_samples=db_history,
                    target_gpu_name=target_name,
                    available_gpus=available_gpus,
                    current_gpu_index=target_idx,
                )
                resp.meta["source"] = "lhm_live+telemetry.db"
                return resp
        except Exception as exc:
            logger.warning(f"[router_gpu_load] Ошибка опроса LHM для GPU {target_name}: {exc}")

    # 4. Fallback: Данные из сэмплов БД или инвентаря целевого GPU
    synthetic_sensors: List[Dict[str, Any]] = []
    latest_sample = db_history[-1] if db_history else {}
    sample_load = latest_sample.get("load_percent") if latest_sample else None
    if sample_load is None:
        sample_load = latest_sample.get("gpu_load_percent") if latest_sample else None
    if sample_load is None:
        sample_load = target_gpu.get("utilization_gpu_pct")

    sample_temp = latest_sample.get("temperature_gpu_c") if latest_sample else None
    if sample_temp is None:
        sample_temp = latest_sample.get("temperature_c") if latest_sample else None
    if sample_temp is None:
        sample_temp = target_gpu.get("temperature_gpu_c")

    sample_vram_used = latest_sample.get("memory_used_mb") if latest_sample else None
    if sample_vram_used is None:
        sample_vram_used = target_gpu.get("memory_used_mb")

    sample_vram_total = latest_sample.get("memory_total_mb") if latest_sample else None
    if sample_vram_total is None:
        sample_vram_total = target_gpu.get("memory_total_mb") or ((target_gpu.get("vram_gb") or 0.0) * 1024.0)

    if sample_load is not None:
        synthetic_sensors.append({"sensor_name": "GPU Core", "sensor_category": "Load", "value": float(sample_load), "hardware_name": target_name, "hardware_type": "gpu", "unit": "%"})
    if sample_temp is not None:
        synthetic_sensors.append({"sensor_name": "GPU Core Temp", "sensor_category": "Temperatures", "value": float(sample_temp), "hardware_name": target_name, "hardware_type": "gpu", "unit": "°C"})
    if sample_vram_used is not None:
        synthetic_sensors.append({"sensor_name": "GPU Memory Used", "sensor_category": "Data", "value": float(sample_vram_used), "hardware_name": target_name, "hardware_type": "gpu", "unit": "MB"})
    if sample_vram_total:
        synthetic_sensors.append({"sensor_name": "GPU Memory Total", "sensor_category": "Data", "value": float(sample_vram_total), "hardware_name": target_name, "hardware_type": "gpu", "unit": "MB"})

    if synthetic_sensors:
        resp = build_gpu_load(
            sensors=synthetic_sensors,
            inventory=target_gpu,
            history_samples=db_history,
            target_gpu_name=target_name,
            available_gpus=available_gpus,
            current_gpu_index=target_idx,
        )
        resp.meta["source"] = "telemetry_db_samples"
        return resp

    # История параметров GPU при пустых сенсорах
    history_points: List[GpuHistoryPoint] = []
    for r in db_history:
        ts_str = str(r.get("timestamp") or "")
        t_label = ts_str.split("T")[-1][:8] if "T" in ts_str else ts_str[-8:]
        history_points.append(
            GpuHistoryPoint(
                timestamp=ts_str,
                time_label=t_label or "--:--:--",
                load_percent=round(float(r.get("load_percent") or r.get("gpu_load_percent") or 0.0), 1),
                temperature_c=r.get("temperature_gpu_c") or r.get("temperature_c"),
                power_w=r.get("power_draw_w") or r.get("power_w"),
                vram_percent=r.get("memory_percent") or r.get("vram_percent"),
            )
        )

    return GpuLoadResponse(
        status="ok",
        name=target_name,
        vendor=target_gpu.get("vendor", "Intel" if "intel" in target_name.lower() or "uhd" in target_name.lower() else "NVIDIA"),
        core_load_percent=0.0,
        engines=[],
        sensors=[],
        history=history_points,
        available_gpus=available_gpus,
        current_gpu_index=target_idx,
        meta={"source": "telemetry_db_empty", "engines_count": 0},
    )


def init_router(
    storage: Optional[TelemetryStorage] = None,
    lhm_service: Optional[LhmService] = None,
) -> APIRouter:
    """Инициализация роутера GET /api/v1/panel/gpu-load.

    Args:
        storage: Опциональное хранилище TelemetryStorage.
        lhm_service: Опциональный сервис LhmService.

    Returns:
        APIRouter: Настроенный роутер FastAPI.
    """
    router = APIRouter(prefix="/api/v1/panel", tags=["GPU Panel"])
    store = storage or TelemetryStorage.get_instance(read_only=True)
    lhm = lhm_service if lhm_service is not None else (LhmService() if storage is None else None)

    @router.get("/gpu-load", response_model=GpuLoadResponse, summary="Загрузка, температура, паспорт и метрики GPU")
    async def get_gpu_load(
        gpu_index: Optional[int] = Query(None, description="Индекс конкретной видеокарты (0, 1, ...) или None для всех")
    ) -> GpuLoadResponse:
        """Возвращает детальную загрузку, температуру, VRAM, паспорт и историю GPU."""
        available_gpus = _discover_system_gpus(store)

        if gpu_index is not None and 0 <= gpu_index < len(available_gpus):
            return _fetch_single_gpu_data(gpu_index, available_gpus[gpu_index], available_gpus, store, lhm)

        # Собираем данные по каждому GPU
        devices: List[Dict[str, Any]] = []
        for idx, g in enumerate(available_gpus):
            g_resp = _fetch_single_gpu_data(idx, g, available_gpus, store, lhm)
            devices.append(g_resp.model_dump())

        # Выбираем основной адаптер для корневого ответа
        primary_idx = 0
        for idx, g in enumerate(available_gpus):
            v_up = str(g.get("vendor", "")).upper()
            n_up = str(g.get("name", "")).upper()
            if "NVIDIA" in v_up or "GEFORCE" in n_up or "AMD" in v_up or "RADEON" in n_up:
                primary_idx = idx
                break

        main_resp = _fetch_single_gpu_data(primary_idx, available_gpus[primary_idx], available_gpus, store, lhm)
        main_resp.devices = devices
        return main_resp

    return router


__all__ = [
    "init_router",
    "build_gpu_load",
    "GpuLoadResponse",
    "GpuEngineMetric",
    "GpuMemoryMetric",
    "GpuClocksMetric",
    "GpuSensorMetric",
    "GpuHistoryPoint",
    "GpuSpecsInfo",
]
