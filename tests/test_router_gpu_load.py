# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router GPU Load
# =============================================================================
# Description:
#   Тесты роутера GET /api/v1/panel/gpu-load и функции build_gpu_load.
#
# File: test_router_gpu_load.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 03:21:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/v1/panel/gpu-load."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_gpu_load import init_router, build_gpu_load
from apps.windows.telemetry.sqlite import TelemetryStorage


def test_build_gpu_load_full():
    """Тест парсинга полного набора сенсоров GPU."""
    mock_sensors = [
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Clocks", "sensor_name": "GPU Core", "value_raw": "953.7 MHz", "value_num": 953.7},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Clocks", "sensor_name": "GPU Memory", "value_raw": "2505.6 MHz", "value_num": 2505.6},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Temperatures", "sensor_name": "GPU Core", "value_raw": "66.0 °C", "value_num": 66.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "GPU Core", "value_raw": "56.0 %", "value_num": 56.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "GPU Memory Controller", "value_raw": "9.0 %", "value_num": 9.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "GPU Video Engine", "value_raw": "0.0 %", "value_num": 0.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "GPU Memory", "value_raw": "30.8 %", "value_num": 30.8},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "GPU Bus", "value_raw": "30.0 %", "value_num": 30.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "D3D 3D", "value_raw": "19.1 %", "value_num": 19.1},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Data", "sensor_name": "GPU Memory Total", "value_raw": "2048.0 MB", "value_num": 2048.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Data", "sensor_name": "GPU Memory Used", "value_raw": "630.0 MB", "value_num": 630.0},
        {"hardware_name": "NVIDIA GeForce GT 710", "hardware_type": "gpu", "sensor_category": "Data", "sensor_name": "GPU Memory Free", "value_raw": "1417.0 MB", "value_num": 1417.0},
    ]

    resp = build_gpu_load(mock_sensors)
    assert resp.name == "NVIDIA GeForce GT 710"
    assert resp.core_load_percent == 56.0
    assert resp.core_temperature_c == 66.0
    assert resp.memory.total_mb == 2048.0
    assert resp.memory.used_mb == 630.0
    assert resp.memory.used_percent == 30.8
    assert resp.clocks.core_mhz == 953.7
    assert resp.clocks.memory_mhz == 2505.6
    assert len(resp.engines) >= 5

    core_eng = next((e for e in resp.engines if e.name == "GPU Core"), None)
    assert core_eng is not None
    assert core_eng.load_percent == 56.0
    assert core_eng.temperature_c == 66.0


def test_empty_gpu_load(tmp_path, mocker):
    """Пустое хранилище телеметрии и выключенный LHM возвращают статус ok и дефолтные значения."""
    storage = TelemetryStorage(db_path=tmp_path / "t_gpu.db", buffer_mode="direct")
    mock_lhm = mocker.MagicMock()
    mock_lhm.is_running.return_value = False

    app = FastAPI()
    app.include_router(init_router(storage=storage, lhm_service=mock_lhm))
    client = TestClient(app)

    res = client.get("/api/v1/panel/gpu-load")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["core_load_percent"] == 0.0
    assert data["engines"] == []
    assert data["meta"]["source"] == "none"
