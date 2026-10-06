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
# Updated: 2026-10-06 17:39:00
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

    # 4.1. Throttling Diagnostics & Refresh
    resp_thr = test_client.get("/api/v1/system/diagnostics/throttling")
    assert resp_thr.status_code == 200
    data_thr = resp_thr.json()
    assert data_thr.get("status") == "ok"
    assert "dpc_latency_pct" in data_thr

    resp_thr_ref = test_client.post("/api/v1/system/diagnostics/throttling/refresh")
    assert resp_thr_ref.status_code == 200
    assert resp_thr_ref.json().get("status") == "ok"

    # 4.2. Process Leaks & Refresh
    resp_leaks = test_client.get("/api/v1/system/diagnostics/leaks?limit=10")
    assert resp_leaks.status_code == 200
    data_leaks = resp_leaks.json()
    assert "total_processes" in data_leaks or "all_processes" in data_leaks

    resp_leaks_tc = test_client.get("/api/v1/tc/process-leaks?limit=10")
    assert resp_leaks_tc.status_code == 200

    resp_leaks_ref = test_client.post("/api/v1/system/diagnostics/leaks/refresh?limit=10")
    assert resp_leaks_ref.status_code == 200

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

    # 6. Rename Computer Endpoint
    # Тест некорректного имени
    resp_invalid = test_client.post("/api/v1/system/rename-computer", json={"new_name": "INVALID NAME!"})
    assert resp_invalid.status_code == 200
    assert resp_invalid.json().get("status") == "error"

    # Тест совпадения имени
    import platform
    current_host = platform.node() or "Host"
    resp_same = test_client.post("/api/v1/system/rename-computer", json={"new_name": current_host})
    assert resp_same.status_code == 200
    assert resp_same.json().get("status") == "ok"

    # 7. Change Workgroup Endpoint
    # Тест некорректного имени рабочей группы
    resp_wg_inv = test_client.post("/api/v1/system/change-workgroup", json={"new_workgroup": "INVALID WG!#"})
    assert resp_wg_inv.status_code == 200
    assert resp_wg_inv.json().get("status") == "error"

    # Тест совпадения имени рабочей группы
    from apps.windows.api.routers.router_about_system import get_windows_workgroup
    cur_wg = get_windows_workgroup()
    resp_wg_same = test_client.post("/api/v1/system/change-workgroup", json={"new_workgroup": cur_wg})
    assert resp_wg_same.status_code == 200
    assert resp_wg_same.json().get("status") == "ok"

    # 8. Regional Options Endpoint
    resp_reg = test_client.get("/api/v1/system/regional-options")
    assert resp_reg.status_code == 200
    reg_data = resp_reg.json()
    assert "current_timezone" in reg_data
    assert "timezones" in reg_data
    assert isinstance(reg_data["timezones"], list)
    assert len(reg_data["timezones"]) > 0
    assert "locales" in reg_data
    assert isinstance(reg_data["locales"], list)

    # 9. Set Timezone Endpoint
    # Некорректный запрос (несуществующая таймзона)
    resp_tz_err = test_client.post("/api/v1/system/set-timezone", json={"timezone_id": "NonExistent_TZ_999"})
    assert resp_tz_err.status_code == 200
    assert resp_tz_err.json().get("status") in ("error", "ok")

    # Корректный запрос (с текущей таймзоной)
    cur_tz = reg_data.get("current_timezone") or "UTC"
    resp_tz_ok = test_client.post("/api/v1/system/set-timezone", json={"timezone_id": cur_tz})
    assert resp_tz_ok.status_code == 200
    assert resp_tz_ok.json().get("status") == "ok"

    # 10. Set Locale Endpoint
    # Некорректная локаль
    resp_loc_err = test_client.post("/api/v1/system/set-locale", json={"system_locale": "invalid-locale-xxx"})
    assert resp_loc_err.status_code == 200
    assert resp_loc_err.json().get("status") == "error"

    # Корректная локаль
    resp_loc_ok = test_client.post("/api/v1/system/set-locale", json={"system_locale": "ru-RU", "user_locale": "ru-RU"})
    assert resp_loc_ok.status_code == 200
    assert resp_loc_ok.json().get("status") == "ok"

    # 11. Update User Profile Endpoint
    # Некорректное имя пользователя
    resp_usr_err = test_client.post("/api/v1/system/update-user-profile", json={"username": "invalid user name!@#$"})
    assert resp_usr_err.status_code == 200
    assert resp_usr_err.json().get("status") == "error"

    # Валидный запрос обновления профиля
    cur_usr = reg_data.get("current_username") or "onela"
    resp_usr_ok = test_client.post("/api/v1/system/update-user-profile", json={
        "username": cur_usr,
        "full_name": "Test User Full Name",
        "description": "Test Account Description"
    })
    assert resp_usr_ok.status_code == 200
    assert resp_usr_ok.json().get("status") == "ok"
