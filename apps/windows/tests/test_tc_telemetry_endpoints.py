# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test TC Telemetry Endpoints
# =============================================================================
# Description:
#   Модульные тесты для эндпоинтов телеметрии, роллапов, БД SQLite и сэмплирования
#   в router_tc.py.
#
# Usage Examples:
#   pytest apps/windows/tests/test_tc_telemetry_endpoints.py
#
# File: test_tc_telemetry_endpoints.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 06:05:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для расширенных эндпоинтов телеметрии в router_tc."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_tc import init_router


@pytest.fixture
def tc_client() -> TestClient:
    """Создает тестовый клиент с подключенным router_tc."""
    app = FastAPI()
    router = init_router()
    app.include_router(router)
    return TestClient(app)


def test_get_telemetry_rollups_endpoint(tc_client: TestClient) -> None:
    """Проверяет эндпоинт /api/v1/tc/telemetry/rollups."""
    response = tc_client.get("/api/v1/tc/telemetry/rollups?level=hourly&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["level"] == "hourly"
    assert isinstance(data["rollups"], list)


def test_get_telemetry_db_stats_endpoint(tc_client: TestClient) -> None:
    """Проверяет эндпоинт /api/v1/tc/telemetry/db-stats."""
    response = tc_client.get("/api/v1/tc/telemetry/db-stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_path" in data
    assert "pragmas" in data
    assert data["pragmas"]["journal_mode"] == "WAL"
    assert data["buffer_ram_limit_mb"] == 32


def test_get_telemetry_incidents_endpoint(tc_client: TestClient) -> None:
    """Проверяет эндпоинт /api/v1/tc/telemetry/incidents."""
    response = tc_client.get("/api/v1/tc/telemetry/incidents?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["incidents"], list)


def test_get_telemetry_sysmon_endpoint(tc_client: TestClient) -> None:
    """Проверяет эндпоинт /api/v1/tc/telemetry/sysmon."""
    response = tc_client.get("/api/v1/tc/telemetry/sysmon?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["events"], list)


def test_get_powershell_scripts_endpoint(tc_client: TestClient) -> None:
    """Проверяет эндпоинт /api/v1/tc/telemetry/powershell-scripts."""
    response = tc_client.get("/api/v1/tc/telemetry/powershell-scripts?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["script_blocks"], list)


def test_sampling_status_and_trigger_forensic(tc_client: TestClient) -> None:
    """Проверяет эндпоинты статуса сэмплирования и триггера forensic-режима."""
    # 1. Проверяем текущий статус
    resp1 = tc_client.get("/api/v1/tc/sampling/status")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "ok"
    assert "mode" in data1
    assert "interval_seconds" in data1

    # 2. Триггерим режим forensic
    resp2 = tc_client.post("/api/v1/tc/sampling/trigger-forensic", json={"duration_seconds": 15.0})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "ok"
    assert data2["mode"] == "forensic"
    assert data2["interval_seconds"] == 0.25
