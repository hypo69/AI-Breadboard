# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - LHM CPU Temperatures
# =============================================================================
# Description:
#   Тесты разбора дерева LibreHardwareMonitor и записи температур ядер CPU
#   в телеметрию (SensorCollector) и роутер /api/v1/panel/cpu-load.
#
# File: test_lhm_cpu_temps.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 02:25:00
# =============================================================================

from __future__ import annotations
"""Тесты интеграции температур ядер CPU из LibreHardwareMonitor."""

from apps.windows.api.routers.router_cpu_load import build_cpu_load
from apps.windows.modules.hardware.lhm_service import LhmService, parse_sensor_value
from apps.windows.telemetry.sensor_collector import SensorCollector


def _leaf(text, value):
    """Лист дерева LHM (датчик)."""
    return {"Text": text, "Value": value, "Children": [], "ImageURL": "images/transparent.png"}


def _group(text, icon, children):
    """Узел дерева LHM (оборудование или группа)."""
    return {"Text": text, "ImageURL": icon, "Value": "", "Children": children}


TREE = _group("Sensor", "images_icon/computer.png", [
    _group("Intel Core i5-10400", "images_icon/cpu.png", [
        _group("Temperatures", "images_icon/temperature.png", [
            _leaf("CPU Core #1", "54,0 °C"),
            _leaf("CPU Core #2", "56.0 °C"),
            _leaf("CPU Core #1 Distance to TjMax", "46.0 °C"),
            _leaf("CPU Package", "61.0 °C"),
        ]),
        _group("Load", "images_icon/load.png", [_leaf("CPU Total", "15.0 %")]),
    ]),
])


class _FakeLhm(LhmService):
    """LHM-сервис с фиксированным деревом (без сети)."""

    def is_running(self):
        return True

    def get_sensor_tree(self):
        return TREE


def test_parse_sensor_value():
    """Число извлекается из строки с запятой и единицей измерения."""
    assert parse_sensor_value("54,5 °C") == 54.5
    assert parse_sensor_value("") is None


def test_flatten_tree():
    """Плоский список содержит оборудование, категорию и число."""
    items = LhmService().get_flattened_sensors(TREE)
    temp = [i for i in items if i["sensor_category"] == "Temperatures"]
    assert len(temp) == 4
    assert temp[0]["hardware_type"] == "cpu"
    assert temp[0]["value_num"] == 54.0


def test_collector_emits_core_temps():
    """Коллектор формирует cpu_core_N_temp (0-based, без Distance to TjMax) и cpu_package_temp."""
    collector = SensorCollector(lhm_service=_FakeLhm())
    readings = {r["id"]: r for r in collector.collect_lhm_cpu_readings()}
    assert readings["cpu_core_0_temp"]["value_num"] == 54.0
    assert readings["cpu_core_1_temp"]["value_num"] == 56.0
    assert readings["cpu_package_temp"]["value_num"] == 61.0
    assert len(readings) == 3


def test_router_maps_threads_to_physical_core_temp():
    """12 логических потоков получают температуру своего физического ядра (по 2 потока на ядро)."""
    sensors = []
    for t in range(4):
        sensors.append({"sensor_id": f"cpu_core_{t}_load", "sensor_name": f"CPU Core #{t}", "hardware_type": "cpu",
                        "sensor_category": "Load", "value": 10.0 + t, "timestamp": "x"})
    for c, v in enumerate((50.0, 60.0)):
        sensors.append({"sensor_id": f"cpu_core_{c}_temp", "sensor_name": f"CPU Core #{c + 1}", "hardware_type": "cpu",
                        "sensor_category": "Temperatures", "value": v, "timestamp": "x"})
    data = build_cpu_load(sensors)
    assert [c.temperature_c for c in data.cores] == [50.0, 50.0, 60.0, 60.0]
    assert [c.load_percent for c in data.cores] == [10.0, 11.0, 12.0, 13.0]
