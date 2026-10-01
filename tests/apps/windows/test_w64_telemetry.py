# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test W64 Telemetry
# =============================================================================
# Description:
#   Тесты для подсистемы AI Windows 64-bit Telemetry Collector.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_w64_telemetry import test_w64_models
#
#     res = test_w64_models()
#
# File: test_w64_telemetry.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты для подсистемы AI Windows 64-bit Telemetry Collector."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from apps.windows.telemetry.models import (
    ETWTraceEvent,
    W64CollectorStatus,
    W64SystemEvent,
)
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.w64_collector import (
    AIW64Collector,
    get_w64_collector,
    start_w64_collector,
    stop_w64_collector,
)
from apps.windows.telemetry.w64_etw_collector import AIW64ETWCollector
from apps.windows.telemetry.service import TelemetryLoggerService
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
import apps.windows as windows_pkg
import apps.windows.telemetry as telemetry_pkg


def test_w64_models() -> None:
    """Тестирование моделей данных W64SystemEvent, ETWTraceEvent и W64CollectorStatus."""
    evt = W64SystemEvent(
        event_id="evt_123",
        timestamp="2026-09-30T19:00:00Z",
        event_type="process_start",
        path="C:\\Windows\\explorer.exe",
        pid=1234,
        name="explorer.exe",
        details={"cmdline": "explorer.exe"},
    )
    evt_dict = evt.to_dict()
    assert evt_dict["event_id"] == "evt_123"
    assert evt_dict["event_type"] == "process_start"
    assert evt_dict["pid"] == 1234
    assert evt_dict["cmdline"] == "explorer.exe"

    etw_evt = ETWTraceEvent(
        event_id="etw_456",
        timestamp="2026-09-30T19:00:00Z",
        event_type="etw_process_create",
        provider="Microsoft-Windows-Security-Auditing",
        payload={"ProcessId": "0x123", "NewProcessName": "calc.exe"},
    )
    etw_dict = etw_evt.to_dict()
    assert etw_dict["event_id"] == "etw_456"
    assert etw_dict["event_type"] == "etw_process_create"
    assert etw_dict["payload"]["NewProcessName"] == "calc.exe"

    status = W64CollectorStatus(
        running=True,
        events_count=42,
        log_dir="C:\\logs",
        last_event_time="2026-09-30T19:05:00Z",
    )
    assert status.running is True
    assert status.events_count == 42


def test_w64_storage_integration(tmp_path: Path) -> None:
    """Тестирование сохранения и извлечения W64 событий через TelemetryStorage."""
    db_file = tmp_path / "telemetry_test.db"
    storage = TelemetryStorage(db_path=db_file)

    event_data = {
        "event_id": "test_evt_1",
        "timestamp": "2026-09-30T19:10:00Z",
        "event_type": "process_start",
        "path": "C:\\Windows\\notepad.exe",
        "pid": 5678,
        "name": "notepad.exe",
        "username": "tester",
    }
    row_id = storage.save_w64_event(event_data, provider="w64_collector")
    assert row_id > 0

    etw_data = {
        "event_id": "test_etw_1",
        "timestamp": "2026-09-30T19:11:00Z",
        "event_type": "etw_file_access",
        "path": "C:\\secret.txt",
        "pid": 5678,
        "name": "tester",
    }
    storage.save_w64_event(etw_data, provider="w64_etw_collector")

    events = storage.get_w64_events(limit=10)
    assert len(events) == 2

    proc_events = storage.get_w64_events(event_type="process_start")
    assert len(proc_events) == 1
    assert proc_events[0]["event_id"] == "test_evt_1"

    stats = storage.get_stats()
    assert stats["w64_events_count"] == 2


def test_w64_collector_lifecycle_and_callback(tmp_path: Path) -> None:
    """Тестирование жизненного цикла сборщика AIW64Collector, JSONL логов и callback."""
    log_dir = tmp_path / "w64_logs"
    db_file = tmp_path / "telemetry.db"
    storage = TelemetryStorage(db_path=db_file)

    collected_events = []

    def on_event(evt: dict) -> None:
        collected_events.append(evt)

    collector = AIW64Collector(
        log_dir=str(log_dir),
        poll_interval_sec=0.1,
        storage=storage,
        on_event_callback=on_event,
        monitored_paths=[str(tmp_path)],
    )

    assert collector.get_status()["running"] is False
    assert collector.start() is True
    assert collector.get_status()["running"] is True

    # Имитируем фиксацию события напрямую
    test_event = {"pid": 9999, "name": "test_process.exe"}
    collector._log_event("process_start", test_event)

    assert len(collected_events) == 1
    assert collected_events[0]["event_type"] == "process_start"
    assert collected_events[0]["pid"] == 9999

    assert collector.stop() is True
    assert collector.get_status()["running"] is False

    # Проверяем, что создался JSONL лог
    jsonl_files = list(log_dir.glob("*.jsonl"))
    assert len(jsonl_files) >= 1

    # Проверяем события в хранилище
    stored = collector.get_events(limit=10)
    assert len(stored) >= 1


def test_w64_etw_collector_lifecycle(tmp_path: Path) -> None:
    """Тестирование жизненного цикла AIW64ETWCollector."""
    log_dir = tmp_path / "etw_logs"
    db_file = tmp_path / "telemetry.db"
    storage = TelemetryStorage(db_path=db_file)

    emitted = []
    etw = AIW64ETWCollector(
        log_dir=str(log_dir),
        poll_interval_sec=0.1,
        storage=storage,
        on_event_callback=lambda e: emitted.append(e),
    )

    assert etw.start() is True
    assert etw.get_status()["running"] is True

    etw._log_event("etw_process_create", {"ProcessName": "cmd.exe", "ProcessId": 1234})

    assert len(emitted) == 1
    assert emitted[0]["event_type"] == "etw_process_create"

    assert etw.stop() is True
    assert etw.get_status()["running"] is False

    events = etw.get_events(limit=5)
    assert len(events) >= 1


def test_telemetry_service_with_w64_integration(tmp_path: Path) -> None:
    """Тестирование запуска и остановки W64 сборщиков в составе TelemetryLoggerService."""
    config_file = tmp_path / "config.json"
    config_data = {
        "w64_collector": {
            "enabled": True,
            "enable_file_monitoring": False,
            "enable_process_monitoring": False,
            "enable_registry_monitoring": False,
            "enable_network_monitoring": False,
            "enable_event_log_monitoring": False,
            "enable_process_trace": False,
            "enable_disk_trace": False,
            "enable_network_trace": False,
            "enable_registry_trace": False,
        }
    }
    config_file.write_text(json.dumps(config_data), encoding="utf-8")
    cfg_mgr = TelemetryConfigManager(config_path=str(config_file))
    db_file = tmp_path / "telemetry_service_test.db"
    storage = TelemetryStorage(db_path=db_file)

    service = TelemetryLoggerService(
        interval_sec=0.1,
        storage=storage,
        config_manager=cfg_mgr,
        enable_w64=True,
    )

    assert service.w64_collector is not None
    assert service.w64_etw_collector is not None

    assert service.start() is True
    assert service.is_running is True
    assert service.w64_collector.get_status()["running"] is True
    assert service.w64_etw_collector.get_status()["running"] is True

    time.sleep(0.2)

    assert service.stop() is True
    assert service.is_running is False
    assert service.w64_collector.get_status()["running"] is False
    assert service.w64_etw_collector.get_status()["running"] is False


def test_package_exports() -> None:
    """Проверка корректного экспорта компонентов через пакеты telemetry и windows."""
    assert hasattr(telemetry_pkg, "AIW64Collector")
    assert hasattr(telemetry_pkg, "AIW64ETWCollector")
    assert hasattr(telemetry_pkg, "W64SystemEvent")
    assert hasattr(telemetry_pkg, "ETWTraceEvent")
    assert hasattr(telemetry_pkg, "get_w64_collector")

    # Проверка ленивого импорта из корня apps.windows
    assert windows_pkg.AIW64Collector is telemetry_pkg.AIW64Collector
    assert windows_pkg.AIW64ETWCollector is telemetry_pkg.AIW64ETWCollector

