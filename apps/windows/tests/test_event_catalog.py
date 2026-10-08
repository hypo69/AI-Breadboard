# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Event Catalog
# =============================================================================
# Description:
#   Тестирование иерархического каталога журналов событий Windows, 7 доменов
#   телеметрии, графа происхождения процессов (Provenance) и таймлайна
#   жизненного цикла ОС (Power Lifecycle).
#
# Usage Examples:
#   Python API:
#     pytest apps/windows/tests/test_event_catalog.py -v
#
# File: test_event_catalog.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:40:00
# =============================================================================

from __future__ import annotations
"""Тестирование иерархического каталога журналов событий Windows и реконструкции графов."""

import pytest
from unittest.mock import MagicMock
from apps.windows.telemetry.event_catalog import (
    TelemetryDomain,
    EventProviderCatalogEntry,
    WindowsEventCatalogEngine,
)


@pytest.fixture
def catalog_engine() -> WindowsEventCatalogEngine:
    """Фикстура движка каталога событий."""
    return WindowsEventCatalogEngine()


def test_catalog_engine_initialization(catalog_engine: WindowsEventCatalogEngine):
    """Проверка корректной инициализации каталога и наполнения 7 доменами."""
    catalog = catalog_engine.get_full_catalog()
    assert len(catalog) >= 18

    domains_in_catalog = {entry.domain for entry in catalog}
    expected_domains = {
        TelemetryDomain.SECURITY_IDENTITY,
        TelemetryDomain.PROCESS_SERVICES_TASKS,
        TelemetryDomain.STORAGE_FILESYSTEM,
        TelemetryDomain.NETWORK_COMMUNICATIONS,
        TelemetryDomain.WINDOWS_UPDATE,
        TelemetryDomain.HARDWARE_PNP_DRIVERS,
        TelemetryDomain.POWER_BOOT_SHUTDOWN,
        TelemetryDomain.SYSMON_OBSERVABILITY,
    }
    for dom in expected_domains:
        assert dom in domains_in_catalog


def test_get_catalog_entries_attributes(catalog_engine: WindowsEventCatalogEngine):
    """Проверка обязательных полей записей каталога провайдеров."""
    catalog = catalog_engine.get_full_catalog()
    for entry in catalog:
        assert isinstance(entry, EventProviderCatalogEntry)
        assert entry.id != ""
        assert entry.provider != ""
        assert entry.channel != ""
        assert entry.domain in TelemetryDomain
        assert entry.volume_rating in ("Low", "Medium", "High", "Extreme")
        assert isinstance(entry.key_events, dict)


def test_get_domains_summary(catalog_engine: WindowsEventCatalogEngine):
    """Проверка сводки доменов телеметрии."""
    summary = catalog_engine.get_domains_summary()
    assert "domains" in summary
    assert "total_registered_providers" in summary
    assert "sysmon_installed" in summary
    assert summary["total_registered_providers"] >= 18

    domains = [d["id"] for d in summary["domains"]]
    assert TelemetryDomain.SECURITY_IDENTITY.value in domains
    assert TelemetryDomain.POWER_BOOT_SHUTDOWN.value in domains
    assert TelemetryDomain.STORAGE_FILESYSTEM.value in domains

    for d in summary["domains"]:
        assert d["channels_count"] >= 0
        assert len(d["key_events"]) > 0
        assert d["title"] != ""


def test_reconstruct_process_provenance_mocked(catalog_engine: WindowsEventCatalogEngine):
    """Проверка построения графа происхождения процессов с мокированным хранилищем."""
    mock_events = [
        {
            "event_id": 4688,
            "timestamp": "2026-10-08 01:00:00",
            "subject_user": "CORP\\Administrator",
            "process_name": "C:\\Windows\\System32\\cmd.exe",
            "process_id": 1000,
            "parent_process_id": 500,
            "parent_process_name": "explorer.exe",
            "command_line": "cmd.exe /c start-service MyService",
        },
        {
            "event_id": 4688,
            "timestamp": "2026-10-08 01:00:05",
            "subject_user": "CORP\\Administrator",
            "process_name": "C:\\Windows\\System32\\powershell.exe",
            "process_id": 1050,
            "parent_process_id": 1000,
            "parent_process_name": "cmd.exe",
            "command_line": "powershell.exe -File run.ps1",
        }
    ]

    catalog_engine._storage = MagicMock()
    catalog_engine._storage.get_security_events.return_value = mock_events
    catalog_engine._wevtapi = MagicMock()
    catalog_engine._wevtapi.read_events.return_value = []

    graph = catalog_engine.reconstruct_process_provenance(process_name="cmd.exe", hours=24)
    assert graph is not None
    assert "nodes" in graph
    assert "links" in graph
    assert graph["total_nodes"] >= 2
    assert graph["total_links"] >= 1

    node_names = [n["name"] for n in graph["nodes"]]
    assert "cmd.exe" in node_names
    assert "powershell.exe" in node_names


def test_reconstruct_power_lifecycle_mocked(catalog_engine: WindowsEventCatalogEngine):
    """Проверка реконструкции жизненного цикла питания ОС (Boot/Wake/Crash)."""
    mock_events = [
        {"event_id": 41, "provider": "Microsoft-Windows-Kernel-Power", "timestamp": "2026-10-08 00:01:00", "message": "Kernel Power Crash"},
        {"event_id": 6005, "provider": "EventLog", "timestamp": "2026-10-08 00:02:00", "message": "EventLog started"},
        {"event_id": 42, "provider": "Microsoft-Windows-Kernel-Power", "timestamp": "2026-10-08 00:30:00", "message": "Entering Sleep"},
        {"event_id": 107, "provider": "Microsoft-Windows-Kernel-Power", "timestamp": "2026-10-08 00:45:00", "message": "Resumed from Sleep"},
        {"event_id": 1074, "provider": "USER32", "timestamp": "2026-10-08 01:00:00", "message": "User initiated restart"},
    ]

    catalog_engine._wevtapi = MagicMock()
    catalog_engine._wevtapi.read_events.return_value = mock_events

    timeline = catalog_engine.reconstruct_power_lifecycle(hours=72)
    assert len(timeline) == 5

    phases = [item["phase"] for item in timeline]
    assert "CRASH_UNEXPECTED" in phases
    assert "BOOT" in phases
    assert "SLEEP" in phases
    assert "WAKE" in phases
    assert "SHUTDOWN_PLANNED" in phases


def test_check_sysmon_status(catalog_engine: WindowsEventCatalogEngine):
    """Проверка инспекции статуса Sysmon драйвера."""
    status = catalog_engine.check_sysmon_status()
    assert "installed" in status
    assert "channel_name" in status
    assert "capabilities" in status
    assert isinstance(status["capabilities"], list)
