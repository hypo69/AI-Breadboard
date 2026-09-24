# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Telemetry SQLite Storage Tests
# =============================================================================
# Description:
#   Модульные тесты для постоянного SQLite хранилища телеметрии:
#   TelemetryStorage (снимки, процессы, сенсоры, события, архивы,
#   очистка устаревших записей, миграция из CSV).
#
# File: test_telemetry_storage.py
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модульные тесты для базы данных телеметрии SQLite."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import pytest

from apps.windows.telemetry.models import (
    CpuMetrics,
    DiskIoMetrics,
    GpuMetrics,
    HardwareArchiveEntry,
    HardwareAuditReport,
    MemoryMetrics,
    ProcessMetrics,
    SystemSnapshot,
)
from apps.windows.telemetry.storage import TelemetryStorage
from apps.windows.telemetry.service import TelemetryLoggerService
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.research.extractor import TelemetryDataExtractor


@pytest.fixture
def test_storage(tmp_path: Path) -> TelemetryStorage:
    """Создает изолированный экземпляр базы данных SQLite для тестов."""
    db_file = tmp_path / "test_telemetry.db"
    return TelemetryStorage(db_path=db_file)


def _create_sample_snapshot() -> SystemSnapshot:
    """Вспомогательная функция для создания тестового SystemSnapshot."""
    return SystemSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        hostname="TEST-PC",
        uptime_seconds=3600.0,
        cpu=CpuMetrics(
            total_percent=25.5,
            frequency_mhz=3800.0,
            per_core_percent=[20.0, 30.0],
        ),
        memory=MemoryMetrics(
            total_gb=16.0,
            used_gb=8.0,
            percent=50.0,
            swap_percent=10.0,
        ),
        gpus=[
            GpuMetrics(
                name="NVIDIA GeForce RTX 3080",
                load_percent=45.0,
                temperature_celsius=62.0,
            )
        ],
        disk_io=DiskIoMetrics(
            read_bytes_per_sec=1024 * 1024,
            write_bytes_per_sec=2 * 1024 * 1024,
            read_count_per_sec=100,
            write_count_per_sec=200,
        ),
        top_processes=[
            ProcessMetrics(
                pid=1001,
                name="chrome.exe",
                status="running",
                cpu_percent=12.5,
                memory_mb=450.0,
                memory_percent=2.8,
                num_threads=24,
                username="DOMAIN\\user",
            ),
            ProcessMetrics(
                pid=1002,
                name="python.exe",
                status="running",
                cpu_percent=8.0,
                memory_mb=210.0,
                memory_percent=1.3,
                num_threads=8,
                username="DOMAIN\\user",
            ),
        ],
    )


def test_storage_init_and_stats(test_storage: TelemetryStorage) -> None:
    """Тестирование создания базы данных и схемы таблиц."""
    stats = test_storage.get_storage_stats()
    assert stats["snapshots_count"] == 0
    assert stats["process_snapshots_count"] == 0
    assert stats["sensor_polls_count"] == 0
    assert stats["events_count"] == 0
    assert stats["hardware_audits_count"] == 0
    assert Path(stats["db_path"]).exists()


def test_save_and_get_snapshots(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения и извлечения срезов системы и процессов."""
    snapshot = _create_sample_snapshot()
    snapshot_id = test_storage.save_snapshot(snapshot, top_n=10)
    assert snapshot_id > 0

    snapshots = test_storage.get_snapshots(limit=10)
    assert len(snapshots) == 1
    snap_data = snapshots[0]
    assert snap_data["hostname"] == "TEST-PC"
    assert snap_data["cpu_total_percent"] == 25.5
    assert snap_data["memory_percent"] == 50.0
    assert snap_data["gpu_load_percent"] == 45.0
    assert snap_data["gpu_temp_c"] == 62.0

    # Проверка извлечения процессов снимка
    procs = test_storage.get_snapshot_processes(snapshot_id)
    assert len(procs) == 2
    assert procs[0]["name"] == "chrome.exe"
    assert procs[0]["pid"] == 1001
    assert procs[0]["cpu_percent"] == 12.5


def test_get_process_history(test_storage: TelemetryStorage) -> None:
    """Тестирование получения истории процесса по имени или PID."""
    snapshot = _create_sample_snapshot()
    test_storage.save_snapshot(snapshot)

    chrome_history = test_storage.get_process_history(name="chrome")
    assert len(chrome_history) == 1
    assert chrome_history[0]["name"] == "chrome.exe"

    pid_history = test_storage.get_process_history(pid=1002)
    assert len(pid_history) == 1
    assert pid_history[0]["name"] == "python.exe"


def test_save_sensor_polls_and_batch(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения отдельных замеров и пакета сенсоров."""
    sensor1 = {
        "id": "cpu_temp_1",
        "hardware_name": "Intel Core i5",
        "hardware_type": "cpu",
        "sensor_category": "Temperatures",
        "sensor_name": "CPU Package",
        "unit": "°C",
        "value": 55.0,
    }
    s_id = test_storage.save_sensor_poll(sensor1)
    assert s_id > 0

    batch = [
        {
            "id": "fan_1",
            "hardware_name": "Mainboard",
            "hardware_type": "mainboard",
            "sensor_category": "Fans",
            "sensor_name": "Chassis Fan #1",
            "unit": "RPM",
            "value": 1200.0,
        },
        {
            "id": "gpu_temp_1",
            "hardware_name": "NVIDIA GPU",
            "hardware_type": "gpu",
            "sensor_category": "Temperatures",
            "sensor_name": "GPU Core",
            "unit": "°C",
            "value": 60.0,
        },
    ]
    batch_count = test_storage.save_sensor_polls_batch(batch)
    assert batch_count == 2

    # Проверка получения истории сенсоров
    temp_sensors = test_storage.get_sensor_history(category="Temperatures")
    assert len(temp_sensors) == 2

    latest = test_storage.get_latest_sensors()
    assert len(latest) == 3


def test_save_and_get_events(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения и фильтрации событий телеметрии."""
    ev1_id = test_storage.save_event(
        event_type="process_start",
        event_details={"process": "notepad.exe", "pid": 4567},
        severity="info",
    )
    assert ev1_id > 0

    ev2_id = test_storage.save_event(
        event_type="hardware_change",
        event_details={"device": "USB Mouse", "action": "connected"},
        severity="warning",
    )
    assert ev2_id > 0

    all_events = test_storage.get_events()
    assert len(all_events) == 2

    hw_events = test_storage.get_events(event_type="hardware_change")
    assert len(hw_events) == 1
    assert hw_events[0]["severity"] == "warning"


def test_save_hardware_archive(test_storage: TelemetryStorage) -> None:
    """Тестирование сохранения архивных снимков оборудования."""
    entry = HardwareArchiveEntry(
        archive_id="hw_test_001",
        timestamp=datetime.now(timezone.utc).isoformat(),
        devices_count=42,
        changes_count=1,
        report=HardwareAuditReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            hostname="TEST-HOST",
            devices_count=42,
            problem_devices_count=0,
            outdated_drivers_count=1,
        ),
    )

    aid = test_storage.save_hardware_archive(entry)
    assert aid > 0

    stats = test_storage.get_storage_stats()
    assert stats["hardware_audits_count"] == 1


def test_cleanup_old_records(test_storage: TelemetryStorage) -> None:
    """Тестирование удаления устаревших записей телеметрии."""
    snapshot = _create_sample_snapshot()
    test_storage.save_snapshot(snapshot)
    test_storage.save_event("test_ev", {"msg": "old"})

    # При retention_days=0 удаляются все записи
    deleted = test_storage.cleanup_old_records(retention_days=0)
    assert deleted >= 1

    stats = test_storage.get_storage_stats()
    assert stats["snapshots_count"] == 0
    assert stats["events_count"] == 0


def test_migrate_csv_to_db(tmp_path: Path, test_storage: TelemetryStorage) -> None:
    """Тестирование миграции исторических CSV файлов в SQLite базу данных."""
    csv_dir = tmp_path / "csv_logs"
    csv_dir.mkdir()

    # Создаем тестовый файл системных срезов
    snap_csv = csv_dir / "telemetry_20260924.csv"
    with open(snap_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "hostname", "cpu_percent", "memory_percent",
            "gpu_load", "disk_io_read", "disk_io_write", "network_recv", "network_sent"
        ])
        writer.writerow([
            "2026-09-24T12:00:00+03:00", "TEST-HOST", 35.0, 60.0,
            50.0, 1048576, 2097152, 50000, 10000
        ])

    # Создаем тестовый файл сенсоров
    sensor_csv = csv_dir / "hardware_monitor_polls.csv"
    with open(sensor_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "hardware", "sensor_name", "category", "value", "unit"])
        writer.writerow(["2026-09-24T12:00:00+03:00", "CPU", "Core Temp", "Temperatures", 65.5, "°C"])

    # Запускаем миграцию
    results = test_storage.migrate_csv_to_db(csv_dir=csv_dir)
    assert results["snapshots"] == 1
    assert results["sensor_polls"] == 1

    stats = test_storage.get_storage_stats()
    assert stats["snapshots_count"] == 1
    assert stats["sensor_polls_count"] == 1


from unittest.mock import MagicMock


def test_service_with_sqlite_storage(test_storage: TelemetryStorage) -> None:
    """Тестирование работы сервиса TelemetryLoggerService с SQLite хранилищем."""
    mock_collector = MagicMock(spec=SystemCollector)
    service = TelemetryLoggerService(
        interval_sec=0.2,
        top_processes=5,
        collector=mock_collector,
        storage=test_storage,
    )
    assert service.storage == test_storage

    # Запись события через сервис
    ev_id = service.record_event("service_start", {"mode": "test"})
    assert ev_id > 0

    events = test_storage.get_events(event_type="service_start")
    assert len(events) == 1

    status = service.get_status()
    assert "storage_stats" in status
    assert status["storage_stats"]["events_count"] == 1


def test_system_collector_db_methods(test_storage: TelemetryStorage) -> None:
    """Тестирование методов сохранения в БД у SystemCollector."""
    collector = SystemCollector(
        storage=test_storage,
        auditor=MagicMock(),
        history_manager=MagicMock(),
    )
    snap = _create_sample_snapshot()

    snap_id = collector.save_snapshot_to_db(snapshot=snap, top_n=5)
    assert snap_id > 0

    snapshots = collector.get_snapshots(limit=5)
    assert len(snapshots) == 1

    procs = collector.get_process_history(name="chrome")
    assert len(procs) == 1


def test_extractor_load_from_database(test_storage: TelemetryStorage) -> None:
    """Тестирование извлечения данных из базы SQLite в TelemetryDataExtractor."""
    snapshot = _create_sample_snapshot()
    test_storage.save_snapshot(snapshot)
    test_storage.save_event("custom_event", {"val": 123})

    extractor = TelemetryDataExtractor(storage=test_storage)
    db_records = extractor.load_from_database()
    assert len(db_records) >= 2

    # Проверка через load_all_records
    all_recs = extractor.load_all_records(include_database=True)
    assert len(all_recs) >= 2
