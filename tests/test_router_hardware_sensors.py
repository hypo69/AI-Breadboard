# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router Hardware Sensors
# =============================================================================
# Description:
#   Тесты роутера GET /api/v1/panel/hardware-sensors и функции build_hardware_sensors.
#
# File: test_router_hardware_sensors.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 05:27:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/v1/panel/hardware-sensors."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_hardware_sensors import (
    init_router,
    build_hardware_sensors,
)
from apps.windows.telemetry.sqlite import TelemetryStorage


def test_build_hardware_sensors_full():
    """Тест парсинга сенсоров из БД и агрегации сводки."""
    mock_rows = [
        {
            "sensor_id": "cpu_temp_package",
            "hardware_name": "Intel Core i5-10400",
            "hardware_type": "cpu",
            "sensor_category": "Temperatures",
            "sensor_name": "CPU Package",
            "unit": "°C",
            "value": 52.0,
            "timestamp": "2026-10-04T05:00:00+00:00",
        },
        {
            "sensor_id": "cpu_load_total",
            "hardware_name": "Intel Core i5-10400",
            "hardware_type": "cpu",
            "sensor_category": "Load",
            "sensor_name": "CPU Total",
            "unit": "%",
            "value": 35.0,
            "timestamp": "2026-10-04T05:00:00+00:00",
        },
        {
            "sensor_id": "gpu_temp_core",
            "hardware_name": "NVIDIA GeForce GT 710",
            "hardware_type": "gpu",
            "sensor_category": "Temperatures",
            "sensor_name": "GPU Core",
            "unit": "°C",
            "value": 66.0,
            "timestamp": "2026-10-04T05:00:00+00:00",
        },
        {
            "sensor_id": "fan_chassis_1",
            "hardware_name": "Motherboard",
            "hardware_type": "motherboard",
            "sensor_category": "Fan",
            "sensor_name": "Chassis Fan #1",
            "unit": "RPM",
            "value": 1150.0,
            "timestamp": "2026-10-04T05:00:00+00:00",
        },
        {
            "sensor_id": "volt_vcore",
            "hardware_name": "Motherboard",
            "hardware_type": "motherboard",
            "sensor_category": "Voltage",
            "sensor_name": "CPU VCore",
            "unit": "V",
            "value": 1.12,
            "timestamp": "2026-10-04T05:00:00+00:00",
        },
    ]

    resp = build_hardware_sensors(mock_rows)
    assert resp.status == "ok"
    assert resp.summary.total_sensors == 5
    assert resp.summary.temperature_count == 2
    assert resp.summary.load_count == 1
    assert resp.summary.fan_count == 1
    assert resp.summary.voltage_count == 1
    assert resp.summary.max_temperature_c == 66.0
    assert len(resp.groups) == 3

    # Проверка группы CPU
    cpu_grp = next(g for g in resp.groups if "Intel" in g.name)
    assert cpu_grp.hardware_type == "cpu"
    assert cpu_grp.max_temperature_c == 52.0
    assert cpu_grp.avg_load_percent == 35.0
    assert len(cpu_grp.sensors) == 2


def test_empty_db(tmp_path, mocker):
    """Тест пустого ответа при отсутствии записей в sensor_polls и выключенном LHM."""
    storage = TelemetryStorage(db_path=tmp_path / "t_sensors.db", buffer_mode="direct", auto_flush=False)
    mock_lhm = mocker.MagicMock()
    mock_lhm.is_running.return_value = False

    app = FastAPI()
    app.include_router(init_router(storage=storage, lhm_service=mock_lhm))
    client = TestClient(app)

    res = client.get("/api/v1/panel/hardware-sensors")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["summary"]["total_sensors"] == 0
    assert data["groups"] == []
    assert data["all_sensors"] == []
