# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - System32 Catalog Test
# =============================================================================
# Description:
#   Тестирование расширенного каталога возможностей System32, 66 категорий,
#   Control Planes, Telemetry Tiers, USN Journal, подкоманд и REST API эндпоинтов.
#
# Usage Examples:
#   pytest apps/windows/tests/test_system32_catalog.py -v
#
# File: test_system32_catalog.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 15:15:00
# =============================================================================

from __future__ import annotations
"""Тестирование расширенного каталога возможностей System32, Tiers, Control Planes и REST API."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.windows.sdk.core.system32_catalog import System32Catalog
from apps.windows.sdk.core.system32_models import (
    AccessType,
    ControlPlaneType,
    System32QueryFilter,
    SystemToolCategory,
    TelemetryTier,
    ToolDangerLevel,
    ToolPrivilegeLevel,
)
from apps.windows.sdk.core.etw_pipeline import EtwTelemetryPipeline
from apps.windows.api.routers.router_system32_catalog import router as system32_router


@pytest.fixture
def catalog() -> System32Catalog:
    """Фикстура для синглтона каталога System32."""
    return System32Catalog.get_instance()


@pytest.fixture
def test_app() -> FastAPI:
    """Фикстура тестового приложения FastAPI с подключенным роутером System32."""
    app = FastAPI(title="Test System32 Catalog API")
    app.include_router(system32_router)
    return app


def test_catalog_initialization_and_categories(catalog: System32Catalog):
    """Проверка полноты инициализации расширенного каталога и категорий."""
    all_tools = catalog.get_all_tools()
    assert len(all_tools) >= 80, f"Ожидалось не менее 80 инструментов, найдено {len(all_tools)}"

    # Проверка присутствия ключевых категорий
    assert len(catalog.get_tools_by_category(SystemToolCategory.STORAGE_DISKS)) > 0
    assert len(catalog.get_tools_by_category(SystemToolCategory.ETW_PERFORMANCE_TRACING)) > 0
    assert len(catalog.get_tools_by_category(SystemToolCategory.NETWORK_NETSH)) > 0
    assert len(catalog.get_tools_by_category(SystemToolCategory.MMC_MANAGEMENT_MSC)) > 0
    assert len(catalog.get_tools_by_category(SystemToolCategory.CONTROL_PANEL_CPL)) > 0
    assert len(catalog.get_tools_by_category(SystemToolCategory.CMD_BUILTINS)) > 0


def test_telemetry_tiers_and_control_planes(catalog: System32Catalog):
    """Проверка разбиения по градации AITelemetry Tiers и Control Planes."""
    # Проверка Tiers
    observe_tools = catalog.get_tools_by_tier(TelemetryTier.OBSERVE)
    assert len(observe_tools) > 15
    assert any(t.executable == "systeminfo.exe" for t in observe_tools)

    diagnose_tools = catalog.get_tools_by_tier(TelemetryTier.DIAGNOSE)
    assert len(diagnose_tools) > 0
    assert any(t.executable == "pktmon.exe" for t in diagnose_tools)

    destructive_tools = catalog.get_tools_by_tier(TelemetryTier.DESTRUCTIVE)
    assert len(destructive_tools) > 0
    assert any(t.executable == "diskpart.exe" for t in destructive_tools)

    recovery_tools = catalog.get_tools_by_tier(TelemetryTier.RECOVERY)
    assert len(recovery_tools) > 0
    assert any(t.executable == "reagentc.exe" for t in recovery_tools)

    # Проверка Control Planes
    cli_tools = catalog.get_tools_by_control_plane(ControlPlaneType.CLI)
    assert len(cli_tools) > 20

    etw_tools = catalog.get_tools_by_control_plane(ControlPlaneType.ETW)
    assert len(etw_tools) >= 3

    gui_tools = catalog.get_tools_by_control_plane(ControlPlaneType.GUI_MMC_CPL)
    assert len(gui_tools) >= 15


def test_subcommands_and_usn_journal(catalog: System32Catalog):
    """Проверка подкоманд утилит и поддержки NTFS USN Journal."""
    # fsutil usn
    fsutil = catalog.get_tool("fsutil.exe")
    assert fsutil is not None
    assert fsutil.usn_journal_enabled is True
    assert "usn" in fsutil.subcommands_tree
    assert "queryjournal" in fsutil.subcommands_tree["usn"]

    usn_tools = catalog.get_usn_tools()
    assert len(usn_tools) > 0
    assert any(t.executable == "fsutil.exe" for t in usn_tools)

    # diskpart subcommands tree
    diskpart = catalog.get_tool("diskpart.exe")
    assert diskpart is not None
    assert "vdisk" in diskpart.subcommands_tree
    assert "attach" in diskpart.subcommands_tree["vdisk"]

    # netsh subcommands tree
    netsh = catalog.get_tool("netsh.exe")
    assert netsh is not None
    assert "advfirewall" in netsh.subcommands_tree
    assert "wlan" in netsh.subcommands_tree


def test_catalog_filtering_and_search(catalog: System32Catalog):
    """Проверка фильтрации по Tier, Control Plane и текстового поиска."""
    # Фильтр по Tier и Control Plane
    etw_filter = System32QueryFilter(primary_control_plane=ControlPlaneType.ETW)
    etw_res = catalog.filter_tools(etw_filter)
    assert len(etw_res) >= 3

    # Фильтр по CMD builtins
    cmd_filter = System32QueryFilter(is_cmd_builtin=True)
    cmd_res = catalog.filter_tools(cmd_filter)
    assert len(cmd_res) >= 15
    assert any(t.executable == "dir" for t in cmd_res)

    # Поиск по ключевым словам
    usn_search = catalog.filter_tools(System32QueryFilter(search_query="USN"))
    assert any(t.executable == "fsutil.exe" for t in usn_search)


def test_system_inventory_and_availability(catalog: System32Catalog):
    """Проверка инвентаризации файлов на хосте."""
    inv = catalog.get_system_inventory()
    assert inv["total_registered"] >= 80
    assert inv["total_installed"] > 0

    # Проверка встроенной команды CMD
    dir_stat = catalog.check_availability("dir")
    assert dir_stat["available"] is True
    assert dir_stat["source"] == "CMD Internal"


@pytest.mark.asyncio
async def test_etw_pipeline_execution():
    """Проверка сбора статуса конвейера ETW."""
    pipeline = EtwTelemetryPipeline.get_instance()
    status = await pipeline.get_pipeline_status()
    assert "Sensors -> ETW / Performance Counters -> AITelemetry -> SQLite" in status.pipeline_architecture


@pytest.mark.asyncio
async def test_rest_api_extended_endpoints(test_app: FastAPI):
    """Тестирование новых и существующих REST API эндпоинтов."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/v1/system32/catalog
        r_cat = await client.get("/api/v1/system32/catalog")
        assert r_cat.status_code == 200
        assert r_cat.json()["total"] >= 80

        # GET /api/v1/system32/tiers
        r_tiers = await client.get("/api/v1/system32/tiers")
        assert r_tiers.status_code == 200
        assert "OBSERVE" in r_tiers.json()["tiers"]
        assert "DESTRUCTIVE" in r_tiers.json()["tiers"]

        # GET /api/v1/system32/control-planes
        r_cp = await client.get("/api/v1/system32/control-planes")
        assert r_cp.status_code == 200
        assert "ETW" in r_cp.json()["control_planes"]
        assert "GUI_MMC_CPL" in r_cp.json()["control_planes"]

        # GET /api/v1/system32/subcommands/diskpart.exe
        r_sub = await client.get("/api/v1/system32/subcommands/diskpart.exe")
        assert r_sub.status_code == 200
        sub_data = r_sub.json()
        assert "vdisk" in sub_data["subcommands_tree"]

        # GET /api/v1/system32/usn-journal
        r_usn = await client.get("/api/v1/system32/usn-journal")
        assert r_usn.status_code == 200
        assert r_usn.json()["total"] >= 1

        # GET /api/v1/system32/summary
        r_sum = await client.get("/api/v1/system32/summary")
        assert r_sum.status_code == 200
        assert r_sum.json()["total_tools"] >= 80
