# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router CPU Load
# =============================================================================
# Description:
#   GET /api/v1/panel/cpu-load — иерархические метрики процессора:
#   физические ядра -> логические потоки -> показатели потоков/ядер ->
#   общие показатели CPU и история загрузки/температур/мощности.
#   Запросы к базе данных производятся на уровне телеметрии.
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
# Updated: 2026-10-06 04:38:00
# =============================================================================

from __future__ import annotations

"""Роутер панели «Загрузка CPU»: иерархия CPU -> ядра -> потоки -> сенсоры из telemetry.db и LHM."""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.modules.hardware.lhm_service import LhmService
from apps.windows.telemetry.sqlite import TelemetryStorage

_CORE_THREAD_RE = re.compile(r"core[\s_#]*(\d+)\s+thread[\s_#]*(\d+)", re.IGNORECASE)
_CORE_ONLY_RE = re.compile(r"core[\s_#]*(\d+)", re.IGNORECASE)
_THREAD_ONLY_RE = re.compile(r"thread[\s_#]*(\d+)", re.IGNORECASE)
_TEMP_CATEGORIES = ("temperature", "temperatures")


class CpuThreadMetric(BaseModel):
    """Метрики отдельного логического потока CPU."""
    index: int = Field(..., description="Глобальный порядковый индекс потока (1..N)")
    core_thread_index: int = Field(default=1, description="Порядковый номер потока внутри своего физического ядра (1..2)")
    name: str = Field(default="", description="Название потока (например, Thread #1)")
    core_index: int = Field(default=1, description="Индекс родительского физического ядра (1..M)")
    core_name: str = Field(default="", description="Имя родительского ядра (например, Core #1)")
    load_percent: float = Field(default=0.0, description="Загрузка логического процессора, %")


class CpuCoreMetric(BaseModel):
    """Метрики одного физического ядра CPU со списком принадлежащих ему потоков."""
    index: int = Field(..., description="Индекс физического ядра (1..M)")
    name: str = Field(default="", description="Название ядра (например, Core #1)")
    load_percent: Optional[float] = Field(default=None, description="Загрузка ядра, %")
    temperature_c: Optional[float] = Field(default=None, description="Температура ядра, °C")
    frequency_mhz: Optional[float] = Field(default=None, description="Частота ядра, МГц")
    frequency_str: str = Field(default="", description="Форматированная частота (например, 3.87 GHz)")
    power_w: Optional[float] = Field(default=None, description="Энергопотребление ядра, Вт")
    voltage_v: Optional[float] = Field(default=None, description="Напряжение ядра, В")
    threads: List[CpuThreadMetric] = Field(default_factory=list, description="Логические потоки физического ядра")
    timestamp: str = Field(default="", description="Время последнего замера")


class CpuSensorMetric(BaseModel):
    """Общий системный сенсор процессора (датчик питания, напряжения, шины, кулера)."""
    id: str = Field(..., description="Уникальный идентификатор сенсора")
    name: str = Field(..., description="Человекочитаемое название сенсора")
    category: str = Field(default="General", description="Категория сенсора (Powers, Voltages, Clocks, etc.)")
    unit: str = Field(default="", description="Единица измерения (W, V, MHz, GHz, °C, RPM, %)")
    value: float = Field(default=0.0, description="Числовое значение")
    value_raw: str = Field(default="", description="Форматированное строковое значение с единицей")
    status: str = Field(default="normal", description="Статус сенсора: normal, warning, danger")


class CpuHistoryPoint(BaseModel):
    """Точка временного ряда истории параметров CPU."""
    timestamp: str = Field(default="", description="ISO время точки")
    time_label: str = Field(default="", description="Короткая метка времени ЧЧ:ММ:СС")
    load_percent: float = Field(default=0.0, description="Общая загрузка CPU, %")
    temperature_c: Optional[float] = Field(default=None, description="Температура Package, °C")
    power_w: Optional[float] = Field(default=None, description="Мощность Package, Вт")


class CpuSpecsInfo(BaseModel):
    """Сводная спецификация и паспортные данные процессора."""
    name: str = Field(default="", description="Наименование модели")
    vendor: str = Field(default="Intel", description="Производитель")
    architecture: str = Field(default="x86_64", description="Архитектура")
    socket: str = Field(default="", description="Разъем / Сокет")
    physical_cores: int = Field(default=0, description="Физические ядра")
    logical_cores: int = Field(default=0, description="Логические потоки")
    base_frequency_mhz: float = Field(default=0.0, description="Базовая частота (МГц)")
    max_frequency_mhz: float = Field(default=0.0, description="Макс. частота (МГц)")
    base_frequency_str: str = Field(default="", description="Форматированная базовая частота")
    max_frequency_str: str = Field(default="", description="Форматированная макс. частота")
    l2_cache_kb: Optional[int] = Field(default=None, description="Кэш L2 (КБ)")
    l3_cache_kb: Optional[int] = Field(default=None, description="Кэш L3 (КБ)")
    l2_cache_str: str = Field(default="", description="Форматированный кэш L2")
    l3_cache_str: str = Field(default="", description="Форматированный кэш L3")
    cache_combined_str: str = Field(default="", description="Объединенная строка кэша L2 / L3")
    stepping: str = Field(default="", description="Степинг / Ревизия")
    features: List[str] = Field(default_factory=list, description="Набор инструкций")


class CpuLoadResponse(BaseModel):
    """Иерархический ответ GET /api/v1/panel/cpu-load."""
    status: str = Field(default="ok", description="Статус ответа")
    name: str = Field(default="CPU", description="Модель процессора")
    total_percent: float = Field(default=0.0, description="Суммарная загрузка CPU, %")
    package_temperature_c: Optional[float] = Field(default=None, description="Температура корпуса CPU (Package), °C")
    package_power_w: Optional[float] = Field(default=None, description="Энергопотребление процессора (Package Power), Вт")
    cores_count: int = Field(default=0, description="Количество физических ядер")
    threads_count: int = Field(default=0, description="Количество логических потоков")
    specs: Optional[CpuSpecsInfo] = Field(default=None, description="Сводный паспорт и спецификации CPU")
    cores: List[CpuCoreMetric] = Field(default_factory=list, description="Физические ядра и их потоки")
    threads: List[CpuThreadMetric] = Field(default_factory=list, description="Сетка всех логических процессоров")
    sensors: List[CpuSensorMetric] = Field(default_factory=list, description="Общие датчики системы и процессора")
    history: List[CpuHistoryPoint] = Field(default_factory=list, description="История параметров CPU")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные запроса")


def _calculate_sensor_status(category: str, value: float) -> str:
    """Определяет статус сенсора по категории и значению."""
    cat = category.lower()
    if "temp" in cat:
        if value >= 80.0:
            return "danger"
        if value >= 68.0:
            return "warning"
        return "normal"
    if "load" in cat:
        if value >= 90.0:
            return "danger"
        if value >= 75.0:
            return "warning"
        return "normal"
    return "normal"


def _format_frequency(mhz: Optional[float]) -> str:
    """Форматирует частоту в МГц или ГГц."""
    if mhz is None or mhz <= 0:
        return "--"
    if mhz >= 1000.0:
        return f"{mhz / 1000.0:.2f} GHz"
    return f"{mhz:.0f} MHz"


def _normalize_sensor_name(sid: str, name: str, cat: str) -> str:
    """Формирует понятное название для общего CPU-сенсора без Unknown."""
    raw = (name or "").strip()
    if not raw or raw.lower() in ("unknown", "sensor"):
        return f"Sensor #{sid}" if sid else "System Sensor"

    # Приводим частые LHM имена к аккуратному виду
    cat_l = cat.lower()
    raw_l = raw.lower()

    if raw_l == "cpu package" and "power" in cat_l:
        return "Package Power"
    if raw_l == "cpu package" and "temp" in cat_l:
        return "CPU Temperature"
    if raw_l == "cpu cores" and "power" in cat_l:
        return "Cores Power"
    if raw_l == "cpu core" and "volt" in cat_l:
        return "Core Voltage"
    if raw_l == "bus speed":
        return "Bus Frequency"
    if raw_l == "core max" and "temp" in cat_l:
        return "Core Max Temp"
    if raw_l == "core average" and "temp" in cat_l:
        return "Core Average Temp"

    return raw


def build_cpu_load(
    sensors: List[Dict[str, Any]],
    snapshot: Optional[Dict[str, Any]] = None,
    history_rows: Optional[List[Dict[str, Any]]] = None,
    inventory: Optional[Dict[str, Any]] = None,
) -> CpuLoadResponse:
    """Собирает иерархический ответ CPU -> физические ядра -> потоки -> сенсоры -> история.

    Args:
        sensors: Записи последних замеров сенсоров.
        snapshot: Данные последнего системного снимка.
        history_rows: Записи исторических снимков.
        inventory: Паспортные данные CPU.

    Returns:
        CpuLoadResponse: Структурированный ответ для UI панели CPU.
    """
    cpu_name = "CPU"
    total_load: Optional[float] = None
    pkg_temp: Optional[float] = None
    pkg_power: Optional[float] = None

    # Поядерные и потоковые хранилища
    thread_loads_by_core: Dict[int, Dict[int, float]] = {}  # core_idx -> {thread_idx: load}
    flat_thread_loads: Dict[int, float] = {}  # thread_idx (1..N) -> load
    core_loads: Dict[int, float] = {}
    core_temps: Dict[int, float] = {}
    core_clocks: Dict[int, float] = {}
    core_powers: Dict[int, float] = {}
    core_volts: Dict[int, float] = {}

    general_sensors_list: List[CpuSensorMetric] = []
    seen_sensor_keys = set()

    # Извлечение базовой информации из инвентаря/снимка
    if inventory and inventory.get("model_name"):
        cpu_name = str(inventory["model_name"]).strip()

    if snapshot:
        raw_str = snapshot.get("raw_json")
        if raw_str:
            try:
                raw_dict = json.loads(raw_str) if isinstance(raw_str, str) else raw_str
                cpu_dict = raw_dict.get("cpu", {})
                if cpu_name == "CPU" and cpu_dict.get("model"):
                    cpu_name = str(cpu_dict["model"]).strip()
                if total_load is None and cpu_dict.get("total_percent") is not None:
                    total_load = round(float(cpu_dict["total_percent"]), 1)
                
                # Обработка плоского массива per_core из psutil если нет LHM потоков
                cores_usage = cpu_dict.get("cores_usage") or []
                for idx, c_val in enumerate(cores_usage):
                    flat_thread_loads[idx + 1] = round(float(c_val), 1)
            except Exception:
                pass

    # Разбор сенсоров
    for row in sensors:
        sid = str(row.get("sensor_id") or row.get("id") or "")
        sname = str(row.get("sensor_name") or row.get("name") or sid)
        htype = str(row.get("hardware_type") or "").lower()
        hname = str(row.get("hardware_name") or "").strip()
        cat = str(row.get("sensor_category") or row.get("category") or "General")

        # Отсекаем дисковые метрики, попавшие по ошибке
        if "disk_speed" in sid or "storage" in cat.lower() or "storage" in htype:
            continue

        if hname and hname.lower() not in ("cpu", "system") and cpu_name == "CPU":
            cpu_name = hname

        raw_val = row.get("value") if row.get("value") is not None else row.get("value_num")
        if raw_val is None:
            continue
        try:
            val_f = float(raw_val)
        except (ValueError, TypeError):
            continue

        unit = str(row.get("unit") or "")
        cat_l = cat.lower()
        sname_l = sname.lower()
        is_temp = cat_l in _TEMP_CATEGORIES or unit == "°C"
        is_load = "load" in cat_l or unit == "%"
        is_clock = "clock" in cat_l or "hz" in unit.lower()
        is_power = "power" in cat_l or unit.lower() == "w"
        is_volt = "volt" in cat_l or unit.lower() == "v"

        # 1. Суммарная загрузка и температура Package
        if sname in ("CPU Total", "cpu_util_total") or sid == "cpu_util_total":
            total_load = round(val_f, 1)
            continue
        if ("package" in sname_l or sid == "cpu_package_temp") and is_temp:
            pkg_temp = round(val_f, 1)
        if ("package" in sname_l or sid == "cpu_package_power") and is_power:
            pkg_power = round(val_f, 1)

        # 2. Потоки конкретного ядра (например: "CPU Core #1 Thread #2" или "Core #1 Thread #1")
        m_ct = _CORE_THREAD_RE.search(sname)
        if m_ct and is_load:
            c_idx = int(m_ct.group(1))
            t_idx = int(m_ct.group(2))
            thread_loads_by_core.setdefault(c_idx, {})[t_idx] = round(val_f, 1)
            continue

        # 3. Метрики ядра (Core #N)
        m_c = _CORE_ONLY_RE.search(sname)
        if m_c and not _CORE_THREAD_RE.search(sname) and "tjmax" not in sname_l and "distance" not in sname_l:
            c_idx = int(m_c.group(1))
            if is_load:
                core_loads[c_idx] = round(val_f, 1)
                continue
            elif is_temp:
                core_temps[c_idx] = round(val_f, 1)
                continue
            elif is_clock:
                core_clocks[c_idx] = round(val_f, 1)
                continue
            elif is_power:
                core_powers[c_idx] = round(val_f, 1)
                continue
            elif is_volt:
                core_volts[c_idx] = round(val_f, 3)
                continue

        # 4. Общие показатели CPU (Package Power, Bus Speed, Voltage, VRM, Fans, TDP, TjMax)
        # Исключаем не-CPU устройства (GPU, Memory RAM, Storage, Network)
        if htype in ("gpu", "memory", "ram", "network", "storage", "disk"):
            continue
        if any(ign in sname_l for ign in ("gpu", "memory used", "memory available", "ethernet", "wi-fi", "d3d", "tckavg", "trcd", "tfaw", "trrd", "tccd", "twr", "twtr", "trfc")):
            continue

        norm_name = _normalize_sensor_name(sid, sname, cat)
        sensor_key = f"{cat_l}_{norm_name.lower()}"
        if sensor_key not in seen_sensor_keys:
            seen_sensor_keys.add(sensor_key)
            if not unit:
                if is_power: unit = "W"
                elif is_volt: unit = "V"
                elif is_temp: unit = "°C"
                elif is_clock: unit = "MHz"
                elif is_load: unit = "%"

            val_str = f"{val_f:.1f} {unit}".strip() if unit else f"{val_f:.1f}"
            if is_volt:
                val_str = f"{val_f:.3f} V"
            elif is_clock and val_f >= 1000.0:
                val_str = f"{val_f / 1000.0:.2f} GHz"

            general_sensors_list.append(
                CpuSensorMetric(
                    id=sid or f"sensor_{len(general_sensors_list)+1}",
                    name=norm_name,
                    category=cat,
                    unit=unit,
                    value=round(val_f, 2),
                    value_raw=val_str,
                    status=_calculate_sensor_status(cat, val_f),
                )
            )

    # 5. Построение иерархии: Физические ядра и их логические потоки
    all_core_indices = sorted(set(list(thread_loads_by_core.keys()) + list(core_temps.keys()) + list(core_clocks.keys()) + list(core_loads.keys())))
    
    # Если индексов ядер не было в LHM, но есть flat_thread_loads из psutil (например 12 потоков)
    if not all_core_indices and flat_thread_loads:
        total_th = len(flat_thread_loads)
        # Стандарт: 2 потока на ядро при HT, либо 1 поток
        threads_per_core = 2 if total_th in (4, 8, 12, 16, 20, 24, 32, 64) else 1
        num_physical = max(1, total_th // threads_per_core)
        all_core_indices = list(range(1, num_physical + 1))
        for c_idx in all_core_indices:
            for t_idx in range(1, threads_per_core + 1):
                g_idx = (c_idx - 1) * threads_per_core + t_idx
                if g_idx in flat_thread_loads:
                    thread_loads_by_core.setdefault(c_idx, {})[t_idx] = flat_thread_loads[g_idx]

    cores_result: List[CpuCoreMetric] = []
    flat_threads_result: List[CpuThreadMetric] = []
    global_thread_counter = 1

    for c_idx in (all_core_indices or [1]):
        core_threads_dict = thread_loads_by_core.get(c_idx, {})
        core_thread_metrics: List[CpuThreadMetric] = []

        # Если потоков для ядра нет явно, создаем хотя бы 1-2
        if not core_threads_dict:
            # Fallback
            th_load = core_loads.get(c_idx, total_load or 0.0)
            core_threads_dict = {1: th_load, 2: th_load}

        for t_local_idx in sorted(core_threads_dict.keys()):
            th_val = core_threads_dict[t_local_idx]
            th_item = CpuThreadMetric(
                index=global_thread_counter,
                core_thread_index=t_local_idx,
                name=f"Thread #{global_thread_counter}",
                core_index=c_idx,
                core_name=f"Core #{c_idx}",
                load_percent=th_val,
            )
            core_thread_metrics.append(th_item)
            flat_threads_result.append(th_item)
            global_thread_counter += 1

        # Нагрузка ядра
        c_load = core_loads.get(c_idx)
        if c_load is None and core_thread_metrics:
            c_load = round(sum(t.load_percent for t in core_thread_metrics) / len(core_thread_metrics), 1)

        c_freq = core_clocks.get(c_idx)
        cores_result.append(
            CpuCoreMetric(
                index=c_idx,
                name=f"Core #{c_idx}",
                load_percent=c_load,
                temperature_c=core_temps.get(c_idx) or pkg_temp,
                frequency_mhz=c_freq,
                frequency_str=_format_frequency(c_freq),
                power_w=core_powers.get(c_idx),
                voltage_v=core_volts.get(c_idx),
                threads=core_thread_metrics,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    # 6. Расчет общего процента загрузки если не был задан
    if total_load is None:
        if cores_result:
            valid_loads = [c.load_percent for c in cores_result if c.load_percent is not None]
            total_load = round(sum(valid_loads) / len(valid_loads), 1) if valid_loads else 0.0
        else:
            total_load = 0.0

    # 7. Формирование истории точек для графиков
    history_points: List[CpuHistoryPoint] = []
    if history_rows:
        for r in history_rows:
            ts_str = str(r.get("timestamp") or "")
            t_label = ts_str.split("T")[-1][:8] if "T" in ts_str else ts_str[-8:]
            p_load = float(r.get("cpu_total_percent") or 0.0)
            
            # Попытка извлечь temp/power из raw_json если есть
            p_temp = None
            p_pow = None
            raw_data = r.get("raw_json")
            if raw_data:
                try:
                    rd = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    p_temp = rd.get("cpu", {}).get("temperature_c") or rd.get("temperature_c")
                    p_pow = rd.get("cpu", {}).get("power_w") or rd.get("power_w")
                except Exception:
                    pass

            history_points.append(
                CpuHistoryPoint(
                    timestamp=ts_str,
                    time_label=t_label or "--:--:--",
                    load_percent=round(p_load, 1),
                    temperature_c=round(float(p_temp), 1) if p_temp is not None else pkg_temp,
                    power_w=round(float(p_pow), 1) if p_pow is not None else pkg_power,
                )
            )

    # 5. Формирование сводного паспорта/спецификации CPU (Specs)
    specs_obj: Optional[CpuSpecsInfo] = None
    inv_data = inventory if isinstance(inventory, dict) else {}
    if inv_data or cpu_name:
        s_name = inv_data.get("name") or cpu_name
        s_vendor = inv_data.get("vendor") or ("Intel" if "intel" in s_name.lower() else ("AMD" if "amd" in s_name.lower() else "Generic"))
        s_arch = inv_data.get("architecture") or "x86_64"
        s_socket = inv_data.get("socket") or ""
        s_p_cores = int(inv_data.get("physical_cores") or len(cores_result) or 1)
        s_l_cores = int(inv_data.get("logical_cores") or len(flat_threads_result) or 1)
        s_base_mhz = float(inv_data.get("base_frequency_mhz") or 2900.0)
        s_max_mhz = float(inv_data.get("max_frequency_mhz") or s_base_mhz)
        s_l2 = inv_data.get("l2_cache_kb")
        s_l3 = inv_data.get("l3_cache_kb")
        s_step = inv_data.get("stepping") or ""

        base_f_str = f"{(s_base_mhz / 1000.0):.2f} GHz" if s_base_mhz >= 1000 else f"{s_base_mhz:.0f} MHz"
        max_f_str = f"{(s_max_mhz / 1000.0):.2f} GHz" if s_max_mhz >= 1000 else f"{s_max_mhz:.0f} MHz"
        l2_str = f"{(s_l2 / 1024.0):.1f} MB" if (s_l2 and s_l2 >= 1024) else (f"{s_l2} KB" if s_l2 else "--")
        l3_str = f"{(s_l3 / 1024.0):.1f} MB" if (s_l3 and s_l3 >= 1024) else (f"{s_l3} KB" if s_l3 else "--")
        cache_comb = f"{l2_str} / {l3_str}" if (s_l2 or s_l3) else "--"

        specs_obj = CpuSpecsInfo(
            name=s_name,
            vendor=s_vendor,
            architecture=s_arch,
            socket=s_socket,
            physical_cores=s_p_cores,
            logical_cores=s_l_cores,
            base_frequency_mhz=s_base_mhz,
            max_frequency_mhz=s_max_mhz,
            base_frequency_str=base_f_str,
            max_frequency_str=max_f_str,
            l2_cache_kb=s_l2,
            l3_cache_kb=s_l3,
            l2_cache_str=l2_str,
            l3_cache_str=l3_str,
            cache_combined_str=cache_comb,
            stepping=s_step,
            features=inv_data.get("features") or [],
        )

    return CpuLoadResponse(
        status="ok",
        name=cpu_name,
        total_percent=round(total_load, 1),
        package_temperature_c=pkg_temp,
        package_power_w=pkg_power,
        cores_count=len(cores_result),
        threads_count=len(flat_threads_result),
        specs=specs_obj,
        cores=cores_result,
        threads=flat_threads_result,
        sensors=general_sensors_list,
        history=history_points,
        meta={
            "source": "telemetry.db/lhm_hierarchy",
            "cores_count": len(cores_result),
            "threads_count": len(flat_threads_result),
            "sensors_count": len(general_sensors_list),
        },
    )


def init_router(
    storage: Optional[TelemetryStorage] = None,
    lhm_service: Optional[LhmService] = None,
) -> APIRouter:
    """Создаёт роутер /api/v1/panel/cpu-load с полной поддержкой иерархии CPU.

    Args:
        storage: Хранилище телеметрии SQLite.
        lhm_service: Сервис LibreHardwareMonitor.

    Returns:
        APIRouter: Роутер с эндпоинтом GET /api/v1/panel/cpu-load.
    """
    router = APIRouter(tags=["CPU Load Panel"])
    store = storage or TelemetryStorage.get_instance(read_only=True)
    lhm = lhm_service if lhm_service is not None else (LhmService() if storage is None else None)

    @router.get("/api/v1/panel/cpu-load", response_model=CpuLoadResponse)
    async def get_panel_cpu_load() -> CpuLoadResponse:
        """Возвращает структурированные иерархические данные CPU из телеметрии и LHM."""
        try:
            # 1. Запрос к базе данных телеметрии для извлечения истории и сохраненных метрик
            db_data = store.get_cpu_hierarchy_metrics()
            db_sensors = db_data.get("sensors", [])
            db_snapshot = db_data.get("snapshot")
            db_inv = db_data.get("inventory")
            db_history = db_data.get("history", [])

            # 2. Если запущен LHM — дополняем живыми данными сенсоров
            if lhm and lhm.is_running():
                lhm_sensors = lhm.get_flattened_sensors()
                if lhm_sensors:
                    resp = build_cpu_load(
                        sensors=lhm_sensors,
                        snapshot=db_snapshot,
                        history_rows=db_history,
                        inventory=db_inv,
                    )
                    resp.meta = {
                        "source": "lhm_live+telemetry.db",
                        "cores_count": len(resp.cores),
                        "threads_count": len(resp.threads),
                    }
                    return resp

            # 3. Ответ на основе данных БД телеметрии
            resp = build_cpu_load(
                sensors=db_sensors,
                snapshot=db_snapshot,
                history_rows=db_history,
                inventory=db_inv,
            )

            # 4. Если данных в БД недостаточно (пустая база) — дополняем через HardwareMonitor
            if not resp.cores and storage is None:
                from apps.windows.modules.hardware.hardware_monitor import HardwareMonitor
                hw = HardwareMonitor()
                cpu_m = hw.get_cpu_metrics()
                flat_th: Dict[int, float] = {}
                for idx, c_val in enumerate(cpu_m.per_core_pct):
                    flat_th[idx + 1] = float(c_val)

                live_snap = {
                    "raw_json": json.dumps({
                        "cpu": {
                            "model": cpu_m.model_name,
                            "total_percent": cpu_m.utilization_pct,
                            "cores_usage": cpu_m.per_core_pct,
                        }
                    })
                }
                resp = build_cpu_load(
                    sensors=db_sensors,
                    snapshot=live_snap,
                    history_rows=db_history,
                    inventory=db_inv,
                )
                resp.meta["source"] = "hardware_monitor_live+telemetry.db"

            return resp

        except Exception as exc:
            logger.error(f"[router_cpu_load] Ошибка формирования метрик CPU: {exc}", exc_info=True)
            return CpuLoadResponse(status="error", meta={"source": "telemetry.db", "error": str(exc)})

    return router


__all__ = [
    "init_router",
    "build_cpu_load",
    "CpuLoadResponse",
    "CpuCoreMetric",
    "CpuThreadMetric",
    "CpuSensorMetric",
    "CpuHistoryPoint",
]
