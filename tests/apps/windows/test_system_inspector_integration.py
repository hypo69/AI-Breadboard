# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test System Inspector Integration
# =============================================================================
# Description:
#   Юнит-тесты для встроенного модуля системного инспектора в составе apps.windows.
#
# File: test_system_inspector_integration.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.system_inspector_router import init_router as init_system_inspector_router
from apps.windows.tui import SystemInspectorState, run_system_inspector


@pytest.fixture
def test_client():
    app = FastAPI()
    app.include_router(init_system_inspector_router())
    return TestClient(app)


def test_system_inspector_status_endpoint(test_client):
    """Проверка эндпоинта /api/system/status."""
    response = test_client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "hostname" in data
    assert "cpu" in data
    assert "memory" in data


def test_system_inspector_processes_endpoint(test_client):
    """Проверка эндпоинта /api/system/processes."""
    response = test_client.get("/api/system/processes?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "processes" in data
    assert isinstance(data["processes"], list)


def test_system_inspector_hardware_endpoint(test_client):
    """Проверка эндпоинта /api/system/hardware."""
    response = test_client.get("/api/system/hardware")
    assert response.status_code == 200
    data = response.json()
    assert "hardware" in data
    assert "sensors" in data


@pytest.mark.asyncio
async def test_system_inspector_state_refresh():
    """Проверка обновления состояния SystemInspectorState."""
    state = SystemInspectorState(sort_by="cpu", process_limit=5)
    await state.refresh()
    assert state.latest_snapshot is not None
    assert state.latest_report is not None


@pytest.mark.asyncio
async def test_run_system_inspector_dry_run():
    """Проверка корректного завершения одного цикла TUI инспектора."""
    await run_system_inspector(interval=0.1, sort_by="cpu", max_iterations=1)
