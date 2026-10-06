# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Hardware Sensors
# =============================================================================
# Description:
#   GET /api/v1/panel/hardware-sensors — детальное табло сенсоров оборудования
#   из таблицы sensor_polls базы данных telemetry.db (температуры, нагрузки,
#   вентиляторы, напряжения, частоты, мощности и накопители).
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_hardware_sensors import init_router
#     app.include_router(init_router())
#
# File: router_hardware_sensors.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-05 23:40:00
# =============================================================================

from __future__ import annotations
"""Роутер табло «Сенсоры оборудования»: структурированные метрики оборудования из telemetry.db."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.modules.hardware.lhm_service import LhmService
from apps.windows.telemetry.sqlite import TelemetryStorage

_SQL_LATEST_SENSORS = """
SELECT sp.* FROM sensor_polls sp
INNER JOIN (
    SELECT sensor_id, MAX(id) as max_id
    FROM sensor_polls
    GROUP BY sensor_id
) latest ON sp.id = latest.max_id
ORDER BY sp.hardware_type, sp.sensor_category, sp.sensor_name;
"""


class HardwareSensorItem(BaseModel):
    """Единичный сенсор оборудования."""
    id: str = Field(..., description="Уникальный ID сенсора")
    hardware_name: str = Field(default="Hardware", description="Имя оборудования")
    hardware_type: str = Field(default="system", description="Тип оборудования (cpu, gpu, storage, etc.)")
    sensor_category: str = Field(default="General", description="Категория (Temperatures, Load, Fan, etc.)")
    sensor_name: str = Field(..., description="Название сенсора")
    unit: str = Field(default="", description="Единица измерения (°C, %, RPM, V, W, MHz, MB/s)")
    value: float = Field(default=0.0, description="Числовое значение")
    value_raw: str = Field(default="", description="Текстовое значение с единицей")
    status: str = Field(default="normal", description="Статус сенсора: normal, warning, danger")
    timestamp: str = Field(default="", description="Время замера")


class HardwareGroupMetric(BaseModel):
    """Группа сенсоров одного компонента оборудования."""
    name: str = Field(..., description="Название компонента (Intel Core i5, NVIDIA GPU, etc.)")
    hardware_type: str = Field(default="system", description="Тип компонента")
    sensors_count: int = Field(default=0, description="Количество сенсоров в группе")
    max_temperature_c: Optional[float] = Field(default=None, description="Макс. температура компонента, °C")
    avg_load_percent: Optional[float] = Field(default=None, description="Средняя нагрузка компонента, %")
    sensors: List[HardwareSensorItem] = Field(default_factory=list, description="Список сенсоров группы")


class HardwareSensorsSummary(BaseModel):
    """Сводка по всем сенсорам системы."""
    total_sensors: int = Field(default=0, description="Общее количество сенсоров")
    temperature_count: int = Field(default=0, description="Датчиков температуры")
    load_count: int = Field(default=0, description="Датчиков нагрузки")
    fan_count: int = Field(default=0, description="Датчиков вентиляторов")
    voltage_count: int = Field(default=0, description="Датчиков напряжения")
    clock_count: int = Field(default=0, description="Датчиков частоты")
    power_count: int = Field(default=0, description="Датчиков мощности")
    max_temperature_c: Optional[float] = Field(default=None, description="Максимальная температура в системе, °C")
    max_temperature_sensor: Optional[str] = Field(default=None, description="Имя самого горячего сенсора")
    warnings_count: int = Field(default=0, description="Число предупреждений/аномалий")
    timestamp: str = Field(default="", description="Время последнего снимка из БД")


class HardwareSensorsResponse(BaseModel):
    """Ответ GET /api/v1/panel/hardware-sensors."""
    status: str = Field(default="ok", description="Статус ответа")
    summary: HardwareSensorsSummary = Field(default_factory=HardwareSensorsSummary, description="Сводка сенсоров")
    groups: List[HardwareGroupMetric] = Field(default_factory=list, description="Группы оборудования с сенсорами")
    all_sensors: List[HardwareSensorItem] = Field(default_factory=list, description="Плоский список всех сенсоров")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные ответа")


def _calculate_sensor_status(category: str, value: float) -> str:
    """Определяет статус сенсора (normal, warning, danger)."""
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
    if "fan" in cat:
        if value <= 0.0:
            return "warning"
        return "normal"
    return "normal"


def build_hardware_sensors(rows: List[Dict[str, Any]]) -> HardwareSensorsResponse:
    """Собирает структурированное табло сенсоров оборудования из строк БД sensor_polls.

    Args:
        rows: Строки последних показаний сенсоров из telemetry.db.

    Returns:
        HardwareSensorsResponse: Структурированный ответ с группировкой и виджетами.
    """
    if not rows:
        return HardwareSensorsResponse(
            summary=HardwareSensorsSummary(),
            groups=[],
            all_sensors=[],
            meta={"source": "telemetry.db", "table": "sensor_polls", "sensors_count": 0},
        )

    all_items: List[HardwareSensorItem] = []
    groups_map: Dict[str, Dict[str, Any]] = {}

    temp_count = 0
    load_count = 0
    fan_count = 0
    volt_count = 0
    clock_count = 0
    power_count = 0
    warnings_count = 0

    max_temp: Optional[float] = None
    max_temp_name: Optional[str] = None
    latest_ts = ""

    for r in rows:
        sid = str(r.get("sensor_id") or r.get("name") or "sensor")
        hname = str(r.get("hardware_name") or "Оборудование")
        htype = str(r.get("hardware_type") or "system")
        cat = str(r.get("sensor_category") or "General")
        sname = str(r.get("sensor_name") or sid)
        unit = str(r.get("unit") or "")
        ts = str(r.get("timestamp") or "")
        if ts and (not latest_ts or ts > latest_ts):
            latest_ts = ts

        raw_val = r.get("value")
        val_num = float(raw_val) if raw_val is not None else 0.0
        val_raw_str = f"{val_num:.1f} {unit}".strip() if unit else f"{val_num:.1f}"

        status = _calculate_sensor_status(cat, val_num)
        if status in ("warning", "danger"):
            warnings_count += 1

        cat_l = cat.lower()
        if "temp" in cat_l:
            temp_count += 1
            if max_temp is None or val_num > max_temp:
                max_temp = val_num
                max_temp_name = f"{hname} - {sname}"
        elif "load" in cat_l:
            load_count += 1
        elif "fan" in cat_l:
            fan_count += 1
        elif "volt" in cat_l:
            volt_count += 1
        elif "clock" in cat_l:
            clock_count += 1
        elif "power" in cat_l:
            power_count += 1

        item = HardwareSensorItem(
            id=sid,
            hardware_name=hname,
            hardware_type=htype,
            sensor_category=cat,
            sensor_name=sname,
            unit=unit,
            value=round(val_num, 2),
            value_raw=val_raw_str,
            status=status,
            timestamp=ts,
        )
        all_items.append(item)

        # Группировка
        if hname not in groups_map:
            groups_map[hname] = {
                "name": hname,
                "hardware_type": htype,
                "sensors": [],
                "temps": [],
                "loads": [],
            }
        groups_map[hname]["sensors"].append(item)
        if "temp" in cat_l:
            groups_map[hname]["temps"].append(val_num)
        elif "load" in cat_l:
            groups_map[hname]["loads"].append(val_num)

    # Формирование списка групп
    groups_list: List[HardwareGroupMetric] = []
    for gname, gdata in groups_map.items():
        temps = gdata["temps"]
        loads = gdata["loads"]
        groups_list.append(
            HardwareGroupMetric(
                name=gname,
                hardware_type=gdata["hardware_type"],
                sensors_count=len(gdata["sensors"]),
                max_temperature_c=round(max(temps), 1) if temps else None,
                avg_load_percent=round(sum(loads) / len(loads), 1) if loads else None,
                sensors=gdata["sensors"],
            )
        )

    summary = HardwareSensorsSummary(
        total_sensors=len(all_items),
        temperature_count=temp_count,
        load_count=load_count,
        fan_count=fan_count,
        voltage_count=volt_count,
        clock_count=clock_count,
        power_count=power_count,
        max_temperature_c=round(max_temp, 1) if max_temp is not None else None,
        max_temperature_sensor=max_temp_name,
        warnings_count=warnings_count,
        timestamp=latest_ts,
    )

    return HardwareSensorsResponse(
        status="ok",
        summary=summary,
        groups=groups_list,
        all_sensors=all_items,
        meta={
            "source": "telemetry.db",
            "table": "sensor_polls",
            "sensors_count": len(all_items),
            "groups_count": len(groups_list),
        },
    )


def init_router(
    storage: Optional[TelemetryStorage] = None,
    lhm_service: Optional[LhmService] = None,
) -> APIRouter:
    """Создаёт роутер /api/v1/panel/hardware-sensors.

    Args:
        storage: Хранилище телеметрии (по умолчанию — синглтон в режиме read_only).
        lhm_service: Сервис LibreHardwareMonitor.

    Returns:
        APIRouter: Роутер с эндпоинтом GET /api/v1/panel/hardware-sensors.
    """
    router = APIRouter(tags=["Hardware Sensors Panel"])
    store = storage or TelemetryStorage.get_instance(read_only=True)

    @router.get("/api/v1/panel/hardware-sensors", response_model=HardwareSensorsResponse)
    async def get_panel_hardware_sensors() -> HardwareSensorsResponse:
        """Возвращает актуальное табло сенсоров оборудования из базы данных telemetry.db."""
        try:
            with store._lock, store._get_connection() as conn:
                rows = [dict(r) for r in conn.execute(_SQL_LATEST_SENSORS).fetchall()]

            return build_hardware_sensors(rows)
        except Exception as exc:
            logger.error(f"[router_hardware_sensors] Ошибка чтения сенсоров из БД: {exc}", exc_info=True)
            return HardwareSensorsResponse(
                status="error",
                meta={"source": "telemetry.db", "error": str(exc)},
            )

    return router


__all__ = [
    "init_router",
    "build_hardware_sensors",
    "HardwareSensorItem",
    "HardwareGroupMetric",
    "HardwareSensorsSummary",
    "HardwareSensorsResponse",
]
