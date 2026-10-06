# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Router About System
# =============================================================================
# Description:
#   Модульные тесты для роутера "О системе" (router_about_system.py)
#   и функций извлечения полного среза телеметрии из базы данных telemetry.db.
#
# Usage Examples:
#   pytest apps/windows/tests/test_router_about_system.py -v
#
# File: test_router_about_system.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 04:30:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для роутера 'О системе' и извлечения телеметрии."""

import pytest
from fastapi.testclient import TestClient
from apps.windows.main import create_windows_app
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.api.routers.router_about_system import (
    query_about_system_from_db,
    query_system_summary_full,
    query_hardware_tree_from_db,
    query_storage_battery_from_db,
    query_backup_health_from_db,
)


@pytest.fixture(scope="module")
def test_client():
    """Создает TestClient для приложения Windows App."""
    app = create_windows_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_query_functions():
    """Проверка прямого вызова функций запроса телеметрии из БД."""
    storage = TelemetryStorage()
    
    overview = query_about_system_from_db(storage)
    assert overview is not None
    assert overview.os.os_name != ""
    assert overview.security.status != ""
    
    summary = await query_system_summary_full(storage)
    assert isinstance(summary, dict)
    assert "os_version" in summary or "hostname" in summary
    
    hw_tree = query_hardware_tree_from_db(storage)
    assert isinstance(hw_tree, list)
    assert len(hw_tree) > 0
    
    storage_battery = query_storage_battery_from_db(storage)
    assert isinstance(storage_battery, dict)
    assert "battery_wear" in storage_battery or "disks_wear" in storage_battery
    
    backup_health = query_backup_health_from_db(storage)
    assert isinstance(backup_health, dict)
    assert "status" in backup_health


def test_api_endpoints(test_client):
    """Проверка всех REST эндпоинтов панели 'О системе'."""
    # 1. Summary
    resp_sum = test_client.get("/api/v1/system/summary")
    assert resp_sum.status_code == 200
    data_sum = resp_sum.json()
    assert isinstance(data_sum, dict)
    assert len(data_sum.keys()) > 10

    # 2. Hardware tree
    resp_hw = test_client.get("/api/v1/system/hardware")
    assert resp_hw.status_code == 200
    assert isinstance(resp_hw.json(), list)

    # 3. Storage & Battery diagnostics
    resp_diag = test_client.get("/api/v1/system/diagnostics/storage-battery")
    assert resp_diag.status_code == 200
    data_diag = resp_diag.json()
    assert "battery_wear" in data_diag or "disks_wear" in data_diag

    # 4. Windows Backup Health
    resp_bak = test_client.get("/api/v1/windows-backup/health")
    assert resp_bak.status_code == 200
    assert resp_bak.json().get("status") in ("ok", "warning", "error")

    # 5. Dashboard KPI Endpoints
    resp_os = test_client.get("/api/v1/dashboard/os")
    assert resp_os.status_code == 200
    assert resp_os.json().get("os_name") != ""

    resp_sec = test_client.get("/api/v1/dashboard/security")
    assert resp_sec.status_code == 200
    assert resp_sec.json().get("status") != ""

    resp_chk = test_client.get("/api/v1/dashboard/checkpoints")
    assert resp_chk.status_code == 200

    resp_stor = test_client.get("/api/v1/dashboard/storage")
    assert resp_stor.status_code == 200
