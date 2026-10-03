# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router CPU Load
# =============================================================================
# Description:
#   Тесты эндпоинта GET /api/v1/panel/cpu-load (загрузка и температура ядер из БД).
#
# File: test_router_cpu_load.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 01:30:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/v1/panel/cpu-load."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_cpu_load import init_router
from apps.windows.telemetry.sqlite import TelemetryStorage


def _sensor(sid: str, name: str, cat: str, unit: str, value: float) -> dict:
    """Формирует запись сенсора CPU для сохранения в sensor_polls."""
    return {
        "id": sid, "hardware_name": "Test CPU", "hardware_type": "cpu",
        "sensor_category": cat, "sensor_name": name, "unit": unit, "value": value,
    }


@pytest.fixture
def storage(tmp_path):
    """Временное хранилище телеметрии."""
    return TelemetryStorage(db_path=tmp_path / "t.db", buffer_mode="direct")


@pytest.fixture
def client(storage):
    """Тестовый клиент с внедрённым хранилищем (явный DI)."""
    app = FastAPI()
    app.include_router(init_router(storage=storage))
    return TestClient(app)


def test_empty_db(client):
    """Пустая БД: пустой список ядер, статус ok."""
    data = client.get("/api/v1/panel/cpu-load").json()
    assert data["status"] == "ok"
    assert data["cores"] == []
    assert data["total_percent"] == 0.0


def test_cores_load_and_temp(client, storage):
    """Загрузка и температура объединяются по индексу ядра; берутся последние значения."""
    storage.save_sensor_poll(_sensor("cpu_core_0_load", "CPU Core #0", "Load", "%", 10.0), timestamp="2026-10-04T01:00:00+00:00")
    storage.save_sensor_poll(_sensor("cpu_core_0_load", "CPU Core #0", "Load", "%", 40.0), timestamp="2026-10-04T01:00:05+00:00")
    storage.save_sensor_poll(_sensor("cpu_core_1_load", "CPU Core #1", "Load", "%", 20.0), timestamp="2026-10-04T01:00:05+00:00")
    storage.save_sensor_poll(_sensor("cpu_core_0_temp", "CPU Core #0", "Temperatures", "°C", 55.5), timestamp="2026-10-04T01:00:05+00:00")
    storage.save_sensor_poll(_sensor("cpu_util_total", "CPU Total", "Load", "%", 30.0), timestamp="2026-10-04T01:00:05+00:00")
    storage.flush()

    data = client.get("/api/v1/panel/cpu-load").json()
    assert data["total_percent"] == 30.0
    assert [c["index"] for c in data["cores"]] == [0, 1]
    assert data["cores"][0]["load_percent"] == 40.0
    assert data["cores"][0]["temperature_c"] == 55.5
    assert data["cores"][1]["load_percent"] == 20.0
    assert data["cores"][1]["temperature_c"] is None
