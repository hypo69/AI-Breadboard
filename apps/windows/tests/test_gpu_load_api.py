# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - GPU Load API Tests
# =============================================================================
# Description:
#   Модульные тесты для эндпоинта GET /api/v1/panel/gpu-load, структуры
#   спецификаций GpuSpecsInfo, сенсоров GpuSensorMetric и истории замеров.
#
# Usage Examples:
#   pytest apps/windows/tests/test_gpu_load_api.py -v
#
# File: test_gpu_load_api.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 07:27:00
# =============================================================================

from __future__ import annotations

"""Модульные тесты роутера и моделей панели «Загрузка GPU»."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_gpu_load import (
    GpuClocksMetric,
    GpuEngineMetric,
    GpuHistoryPoint,
    GpuLoadResponse,
    GpuMemoryMetric,
    GpuSensorMetric,
    GpuSpecsInfo,
    build_gpu_load,
    init_router,
)


@pytest.fixture
def mock_gpu_sensors():
    """Тестовые показания датчиков GPU."""
    return [
        {
            "sensor_id": "gpu_core_load",
            "sensor_name": "GPU Core",
            "sensor_category": "Load",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 42.5,
            "unit": "%",
        },
        {
            "sensor_id": "gpu_mem_ctrl_load",
            "sensor_name": "Memory Controller",
            "sensor_category": "Load",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 18.0,
            "unit": "%",
        },
        {
            "sensor_id": "gpu_core_temp",
            "sensor_name": "GPU Core",
            "sensor_category": "Temperatures",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 58.0,
            "unit": "°C",
        },
        {
            "sensor_id": "gpu_hotspot_temp",
            "sensor_name": "GPU Hot Spot",
            "sensor_category": "Temperatures",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 68.5,
            "unit": "°C",
        },
        {
            "sensor_id": "gpu_power_draw",
            "sensor_name": "GPU Package Power",
            "sensor_category": "Powers",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 145.2,
            "unit": "W",
        },
        {
            "sensor_id": "gpu_voltage",
            "sensor_name": "GPU Core Voltage",
            "sensor_category": "Voltages",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 0.985,
            "unit": "V",
        },
        {
            "sensor_id": "gpu_core_clock",
            "sensor_name": "GPU Core Clock",
            "sensor_category": "Clocks",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 2550.0,
            "unit": "MHz",
        },
        {
            "sensor_id": "gpu_mem_clock",
            "sensor_name": "GPU Memory Clock",
            "sensor_category": "Clocks",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 11200.0,
            "unit": "MHz",
        },
        {
            "sensor_id": "gpu_fan_speed",
            "sensor_name": "GPU Fan Speed",
            "sensor_category": "Fans",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 1350.0,
            "unit": "RPM",
        },
        {
            "sensor_id": "gpu_vram_used",
            "sensor_name": "GPU Memory Used",
            "sensor_category": "Data",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 4096.0,
            "unit": "MB",
        },
        {
            "sensor_id": "gpu_vram_total",
            "sensor_name": "GPU Memory Total",
            "sensor_category": "Data",
            "hardware_name": "NVIDIA GeForce RTX 4080",
            "hardware_type": "gpu",
            "value": 16384.0,
            "unit": "MB",
        },
    ]


@pytest.fixture
def mock_gpu_inventory():
    """Тестовый паспорт GPU."""
    return {
        "name": "NVIDIA GeForce RTX 4080",
        "vendor": "NVIDIA",
        "driver_version": "560.94",
        "driver_date": "2026-08-20",
        "vram_bytes": 17179869184,
        "vram_gb": 16.0,
        "pci_bus_id": "PCIe x16 Gen4",
        "cuda_cores": 9728,
        "directml_supported": True,
    }


def test_build_gpu_load_structured(mock_gpu_sensors, mock_gpu_inventory):
    """Проверка сборки ответа GPU с паспортом, движками, сенсорами и памятью."""
    resp = build_gpu_load(
        sensors=mock_gpu_sensors,
        inventory=mock_gpu_inventory,
        history_samples=[
            {"timestamp": "2026-10-06T05:00:00", "load_percent": 35.0, "temperature_gpu_c": 55.0, "power_draw_w": 120.0},
            {"timestamp": "2026-10-06T05:00:05", "load_percent": 42.5, "temperature_gpu_c": 58.0, "power_draw_w": 145.2},
        ],
    )

    assert resp.status == "ok"
    assert resp.name == "NVIDIA GeForce RTX 4080"
    assert resp.vendor == "NVIDIA"
    assert resp.core_load_percent == 42.5
    assert resp.core_temperature_c == 58.0
    assert resp.hotspot_temperature_c == 68.5
    assert resp.power_w == 145.2
    assert resp.fan_speed_rpm == 1350.0

    # Проверка VRAM
    assert resp.memory.total_mb == 16384.0
    assert resp.memory.used_mb == 4096.0
    assert resp.memory.used_percent == 25.0

    # Проверка Specs
    assert resp.specs is not None
    assert resp.specs.vendor == "NVIDIA"
    assert resp.specs.vram_gb == 16.0
    assert "16.0 GB" in resp.specs.vram_str
    assert "4.0 / 16.0 GB (25%)" in resp.specs.vram_used_str
    assert resp.specs.pci_bus == "PCIe x16 Gen4"
    assert resp.specs.driver_version == "560.94"

    # Проверка движков
    engine_names = [e.name for e in resp.engines]
    assert "GPU Core" in engine_names
    assert "Memory Controller" in engine_names

    # Проверка сенсоров
    assert len(resp.sensors) >= 4
    sensor_names = [s.name for s in resp.sensors]
    assert any("power" in n.lower() for n in sensor_names)
    assert any("volt" in n.lower() for n in sensor_names)

    # Проверка истории
    assert len(resp.history) == 2
    assert resp.history[0].load_percent == 35.0
    assert resp.history[1].load_percent == 42.5


def test_gpu_load_router_api(mock_gpu_sensors, mock_gpu_inventory):
    """Проверка роутера FastAPI для GET /api/v1/panel/gpu-load."""
    class MockStorage:
        def get_gpu_inventory(self):
            return [mock_gpu_inventory]

        def get_gpu_telemetry_samples(self, limit=60):
            return []

        def get_latest_sensors(self):
            return mock_gpu_sensors

    class MockLhm:
        def is_running(self):
            return True

        def get_flattened_sensors(self):
            return mock_gpu_sensors

    app = FastAPI()
    router = init_router(storage=MockStorage(), lhm_service=MockLhm())
    app.include_router(router)

    client = TestClient(app)
    response = client.get("/api/v1/panel/gpu-load")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["name"] == "NVIDIA GeForce RTX 4080"
    assert data["core_load_percent"] == 42.5
    assert data["specs"]["vram_gb"] == 16.0
    assert len(data["engines"]) >= 2
    assert len(data["sensors"]) >= 4


def test_multi_gpu_isolation_and_selection():
    """Проверка изоляции сенсоров между несколькими видеокартами и query параметра gpu_index."""
    mixed_sensors = [
        # Сенсоры Intel iGPU
        {"sensor_id": "intel_load", "sensor_name": "GPU Core", "sensor_category": "Load", "hardware_name": "Intel(R) UHD Graphics 630", "hardware_type": "gpu", "value": 5.0, "unit": "%"},
        # Сенсоры NVIDIA GPU
        {"sensor_id": "nvidia_load", "sensor_name": "GPU Core", "sensor_category": "Load", "hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "value": 45.0, "unit": "%"},
        {"sensor_id": "nvidia_temp", "sensor_name": "GPU Core", "sensor_category": "Temperatures", "hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "value": 62.0, "unit": "°C"},
    ]

    gpus_inv = [
        {"gpu_id": 0, "name": "Intel(R) UHD Graphics 630", "vendor": "Intel", "vram_gb": 1.0, "driver_version": "31.0"},
        {"gpu_id": 1, "name": "NVIDIA GeForce GT 710", "vendor": "NVIDIA", "vram_gb": 2.0, "driver_version": "456.71"},
    ]

    class MockMultiGpuStorage:
        def get_gpu_inventory(self):
            return gpus_inv

        def get_gpu_telemetry_samples(self, gpu_id=None, limit=60):
            return []

        def get_latest_sensors(self):
            return mixed_sensors

    class MockMultiGpuLhm:
        def is_running(self):
            return True

        def get_flattened_sensors(self):
            return mixed_sensors

    app = FastAPI()
    router = init_router(storage=MockMultiGpuStorage(), lhm_service=MockMultiGpuLhm())
    app.include_router(router)
    client = TestClient(app)

    # 1. По умолчанию выбирается дискретная карта NVIDIA
    resp_def = client.get("/api/v1/panel/gpu-load")
    assert resp_def.status_code == 200
    d_def = resp_def.json()
    assert d_def["name"] == "NVIDIA GeForce GT 710"
    assert d_def["vendor"] == "NVIDIA"
    assert d_def["core_load_percent"] == 45.0
    assert d_def["core_temperature_c"] == 62.0
    assert len(d_def["available_gpus"]) == 2

    # 2. Явный выбор Intel iGPU (gpu_index=0)
    resp_intel = client.get("/api/v1/panel/gpu-load?gpu_index=0")
    assert resp_intel.status_code == 200
    d_intel = resp_intel.json()
    assert d_intel["name"] == "Intel(R) UHD Graphics 630"
    assert d_intel["vendor"] == "Intel"
    assert d_intel["core_load_percent"] == 5.0
    # Сенсор температуры от NVIDIA НЕ должен попадать в Intel
    assert d_intel["core_temperature_c"] is None
    assert d_intel["current_gpu_index"] == 0


def test_cpu_sensors_excluded_from_intel_igpu():
    """Проверка, что сенсоры CPU (ядра, вольтаж, Package Power) строго отсекаются от Intel iGPU."""
    dirty_cpu_and_gpu_sensors = [
        # Сенсоры процессора Intel
        {"sensor_id": "cpu_total_load", "sensor_name": "CPU Total", "sensor_category": "Load", "hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "value": 75.0, "unit": "%"},
        {"sensor_id": "cpu_core_1_thread_1", "sensor_name": "CPU Core #1 Thread #1", "sensor_category": "Load", "hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "value": 90.0, "unit": "%"},
        {"sensor_id": "cpu_package_power", "sensor_name": "CPU Package", "sensor_category": "Powers", "hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "value": 52.0, "unit": "W"},
        {"sensor_id": "cpu_bus_speed", "sensor_name": "Bus Speed", "sensor_category": "Clocks", "hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "value": 100.1, "unit": "MHz"},
        {"sensor_id": "cpu_core_volt", "sensor_name": "CPU Core", "sensor_category": "Voltages", "hardware_name": "Intel Core i5-10400", "hardware_type": "cpu", "value": 1.14, "unit": "V"},
        # Реальный сенсор встроенного GPU
        {"sensor_id": "gpu_d3d_3d", "sensor_name": "D3D 3D", "sensor_category": "Load", "hardware_name": "Intel(R) UHD Graphics 630", "hardware_type": "gpu", "value": 12.0, "unit": "%"},
    ]

    igpu_inv = {
        "name": "Intel(R) UHD Graphics 630",
        "vendor": "Intel",
        "driver_version": "31.0.101.2111",
        "vram_gb": 1.0,
    }

    resp = build_gpu_load(
        sensors=dirty_cpu_and_gpu_sensors,
        inventory=igpu_inv,
        target_gpu_name="Intel(R) UHD Graphics 630",
    )

    # Ни одного сенсора CPU не должно оказаться в блоках движков или сенсорах GPU
    engine_names = [e.name for e in resp.engines]
    sensor_names = [s.name for s in resp.sensors]

    assert "CPU Total" not in engine_names
    assert "CPU Core #1 Thread #1" not in engine_names
    assert "CPU Package" not in sensor_names
    assert "CPU Core" not in sensor_names
    assert "Bus Speed" not in sensor_names
    assert resp.power_w is None  # Мощность CPU Package не должна стать GPU power

    # Должен остаться только реальный графический движок
    assert "D3D 3D" in engine_names
