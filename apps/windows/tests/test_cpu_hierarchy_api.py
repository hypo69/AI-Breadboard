# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test CPU Hierarchy API
# =============================================================================
# Description:
#   Тестирование иерархического представления процессора (CPU -> ядра -> потоки
#   -> показатели -> общие сенсоры и история) на уровне телеметрии и API.
#
# Usage Examples:
#   pytest apps/windows/tests/test_cpu_hierarchy_api.py -v
#
# File: test_cpu_hierarchy_api.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:28:00
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_cpu_load import (
    build_cpu_load,
    init_router,
    CpuLoadResponse,
    CpuCoreMetric,
    CpuThreadMetric,
    CpuSensorMetric,
)
from apps.windows.telemetry.sqlite import TelemetryStorage


@pytest.fixture
def temp_telemetry_storage(tmp_path: Path) -> TelemetryStorage:
    """Создаёт временное изолированное хранилище SQLite для тестов."""
    db_file = tmp_path / "test_cpu_telemetry.db"
    storage = TelemetryStorage(
        db_path=db_file,
        buffer_mode="direct",
        auto_flush=True,
        read_only=False,
    )
    return storage


def test_telemetry_get_cpu_hierarchy_metrics(temp_telemetry_storage: TelemetryStorage) -> None:
    """Проверяет извлечение иерархических данных CPU из SQLite на уровне телеметрии."""
    store = temp_telemetry_storage

    # Записываем сенсоры процессора и снимки в БД
    store.save_sensor_polls([
        {
            "id": "cpu_pkg_temp",
            "sensor_name": "CPU Package",
            "sensor_category": "Temperatures",
            "hardware_name": "Intel Core i5-10400",
            "hardware_type": "cpu",
            "value": 62.5,
            "unit": "°C",
        },
        {
            "id": "cpu_pkg_power",
            "sensor_name": "CPU Package",
            "sensor_category": "Powers",
            "hardware_name": "Intel Core i5-10400",
            "hardware_type": "cpu",
            "value": 35.0,
            "unit": "W",
        },
        {
            "id": "disk_speed_latency_C",
            "sensor_name": "Скорость C",
            "sensor_category": "Storage Speed",
            "hardware_name": "Storage",
            "hardware_type": "storage",
            "value": 120.0,
            "unit": "µs",
        }
    ])

    data = store.get_cpu_hierarchy_metrics()
    assert isinstance(data, dict)
    assert "sensors" in data
    assert "snapshot" in data
    assert "history" in data

    # Проверяем, что сенсоры CPU выбраны, а дисковые сенсоры отфильтрованы
    sensor_ids = [s["sensor_id"] for s in data["sensors"]]
    assert "cpu_pkg_temp" in sensor_ids
    assert "cpu_pkg_power" in sensor_ids
    assert "disk_speed_latency_C" not in sensor_ids


def test_build_cpu_load_lhm_hierarchy() -> None:
    """Проверяет построение иерархии 6 ядер / 12 потоков из сенсоров LHM."""
    mock_lhm_sensors: List[Dict[str, Any]] = [
        # Нагрузка потоков
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #1 Thread #1", "value": 43.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #1 Thread #2", "value": 91.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #2 Thread #1", "value": 52.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #2 Thread #2", "value": 87.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #3 Thread #1", "value": 48.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #3 Thread #2", "value": 90.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #4 Thread #1", "value": 54.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #4 Thread #2", "value": 88.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #5 Thread #1", "value": 46.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #5 Thread #2", "value": 83.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #6 Thread #1", "value": 38.0, "unit": "%"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Core #6 Thread #2", "value": 80.0, "unit": "%"},
        # Температуры ядер
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Core #1", "value": 76.0, "unit": "°C"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Core #2", "value": 82.0, "unit": "°C"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Core #3", "value": 74.0, "unit": "°C"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Core #4", "value": 76.0, "unit": "°C"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Core #5", "value": 74.0, "unit": "°C"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Core #6", "value": 73.0, "unit": "°C"},
        # Частоты ядер
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Clocks", "sensor_name": "CPU Core #1", "value": 3870.0, "unit": "MHz"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Clocks", "sensor_name": "CPU Core #2", "value": 3720.0, "unit": "MHz"},
        # Общие сенсоры
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Temperatures", "sensor_name": "CPU Package", "value": 76.0, "unit": "°C"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Powers", "sensor_name": "CPU Package", "value": 38.57, "unit": "W"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Voltages", "sensor_name": "CPU Core", "value": 1.154, "unit": "V"},
        {"hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "sensor_category": "Clocks", "sensor_name": "Bus Speed", "value": 99.8, "unit": "MHz"},
    ]

    resp = build_cpu_load(mock_lhm_sensors)
    assert resp.status == "ok"
    assert resp.name == "Intel Core i5-10400"
    assert resp.cores_count == 6
    assert resp.threads_count == 12
    assert resp.package_temperature_c == 76.0
    assert resp.package_power_w == 38.6

    # Проверка Core #1
    core1 = resp.cores[0]
    assert core1.index == 1
    assert core1.name == "Core #1"
    assert core1.temperature_c == 76.0
    assert core1.frequency_str == "3.87 GHz"
    assert len(core1.threads) == 2
    assert core1.threads[0].name == "Thread #1"
    assert core1.threads[0].load_percent == 43.0
    assert core1.threads[1].name == "Thread #2"
    assert core1.threads[1].load_percent == 91.0

    # Проверка плоской сетки всех 12 потоков
    assert len(resp.threads) == 12
    assert resp.threads[0].name == "Thread #1"
    assert resp.threads[0].core_name == "Core #1"
    assert resp.threads[11].name == "Thread #12"
    assert resp.threads[11].core_name == "Core #6"


def test_build_cpu_load_psutil_fallback() -> None:
    """Проверяет разделение 12 логических процессоров из psutil по 6 физическим ядрам."""
    fake_cores_usage = [43.0, 91.0, 52.0, 87.0, 48.0, 90.0, 54.0, 88.0, 46.0, 83.0, 38.0, 80.0]
    snap = {
        "raw_json": json.dumps({
            "cpu": {
                "model": "AMD Ryzen 5 5600X",
                "total_percent": 67.5,
                "cores_usage": fake_cores_usage,
            }
        })
    }

    resp = build_cpu_load(sensors=[], snapshot=snap)
    assert resp.name == "AMD Ryzen 5 5600X"
    assert resp.total_percent == 67.5
    assert resp.cores_count == 6
    assert resp.threads_count == 12

    # Ядро 1 должно содержать Thread #1 (43%) и Thread #2 (91%)
    core1 = resp.cores[0]
    assert len(core1.threads) == 2
    assert core1.threads[0].load_percent == 43.0
    assert core1.threads[1].load_percent == 91.0


def test_build_cpu_load_no_unknown_sensors() -> None:
    """Проверяет, что сенсоры не содержат Unknown и дисковые метрики отфильтрованы."""
    sensors: List[Dict[str, Any]] = [
        {"sensor_id": "sensor_17", "sensor_name": "Unknown", "sensor_category": "Voltages", "value": 1.15, "unit": "V", "hardware_type": "cpu"},
        {"sensor_id": "disk_speed_latency_C", "sensor_name": "Unknown", "sensor_category": "General", "value": 3857.0, "unit": "µs", "hardware_type": "cpu"},
        {"sensor_id": "fan_cpu", "sensor_name": "CPU Fan", "sensor_category": "Fans", "value": 1450.0, "unit": "RPM", "hardware_type": "system"},
    ]

    resp = build_cpu_load(sensors)
    sensor_names = [s.name for s in resp.sensors]
    for name in sensor_names:
        assert "Unknown" not in name

    assert "Sensor #sensor_17" in sensor_names
    assert "CPU Fan" in sensor_names
    # Дисковая скорость должна быть полностью исключена
    assert not any("disk_speed" in s.id for s in resp.sensors)


def test_cpu_load_api_endpoint(temp_telemetry_storage: TelemetryStorage) -> None:
    """Проверяет интеграцию роутера в FastAPI и ответ GET /api/v1/panel/cpu-load."""
    app = FastAPI()
    router = init_router(storage=temp_telemetry_storage)
    app.include_router(router)

    client = TestClient(app)
    response = client.get("/api/v1/panel/cpu-load")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "cores" in data
    assert "threads" in data
    assert "sensors" in data
    assert "history" in data
    assert "specs" in data
    assert data["specs"] is not None
    assert data["specs"]["physical_cores"] >= 1
