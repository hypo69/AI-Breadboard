# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Disk Tables Tests
# =============================================================================
# Description:
#   Тестирование нормализованных таблиц телеметрии накопителей и томов в SQLite.
#
# File: test_storage_disk_tables.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 01:51:00
# =============================================================================

import gc
import tempfile
import pytest
from pathlib import Path

from apps.windows.telemetry.sqlite.storage import TelemetryStorage
from apps.windows.sdk.modules.storage_manager.core.models import (
    VolumeInfo,
    DiskDetailedInfo,
    DiskPerformanceMetrics,
    DiskIOEvent,
)


@pytest.fixture
def temp_storage():
    """Создает временное хранилище TelemetryStorage для изоляции тестов."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test_telemetry.db"
    storage = TelemetryStorage(
        db_path=db_path,
        buffer_mode='direct',
        auto_flush=False,
    )
    yield storage
    storage.close()
    gc.collect()


def test_disk_inventory_upsert_and_read(temp_storage):
    """Проверка сохранения и чтения паспорта физического диска."""
    disk = DiskDetailedInfo(
        disk_id=0,
        device_path=r"\\.\PhysicalDrive0",
        friendly_name="Samsung SSD 990 PRO 2TB",
        serial_number="S6PNNJ0W123456",
        vendor="Samsung",
        product="SSD 990 PRO",
        revision="5B2QJXD7",
        media_type="SSD",
        bus_type="NVMe",
        size_bytes=2000398934016,
        size_gb=1863.01,
        is_removable=False,
        is_writable=True,
    )

    temp_storage.save_disk_inventory(disk)
    items = temp_storage.get_disk_inventory(disk_id=0)
    assert len(items) == 1
    assert items[0]["serial_number"] == "S6PNNJ0W123456"
    assert items[0]["vendor"] == "Samsung"
    assert items[0]["bus_type"] == "NVMe"

    # Проверка UPSERT (обновление прошивки)
    disk.revision = "5B2QJXD8"
    temp_storage.save_disk_inventory(disk)
    items_updated = temp_storage.get_disk_inventory(disk_id=0)
    assert len(items_updated) == 1
    assert items_updated[0]["revision"] == "5B2QJXD8"


def test_volume_inventory_upsert_and_read(temp_storage):
    """Проверка сохранения и чтения паспорта томов."""
    vol = VolumeInfo(
        volume_id="C:",
        drive_letter="C:",
        label="System",
        filesystem="NTFS",
        total_gb=931.5,
        free_gb=450.2,
        available_gb=450.2,
        cluster_size_bytes=4096,
        sector_size_bytes=512,
        volume_guid="{12345678-1234-1234-1234-123456789abc}",
    )

    temp_storage.save_volume_inventory(vol)
    vols = temp_storage.get_volume_inventory()
    assert len(vols) == 1
    assert vols[0]["drive_letter"] == "C:"
    assert vols[0]["volume_guid"] == "{12345678-1234-1234-1234-123456789abc}"
    assert vols[0]["cluster_size_bytes"] == 4096


def test_disk_health_and_history(temp_storage):
    """Проверка сохранения метрик здоровья и извлечения истории."""
    health_entry = {
        "disk_id": 0,
        "serial_number": "S6PNNJ0W123456",
        "temperature_c": 42.0,
        "wear_percent": 1.0,
        "available_spare": 100.0,
        "tbw_written_tb": 12.5,
        "tbw_read_tb": 25.0,
        "power_cycles": 150,
        "power_on_hours": 3200,
        "unsafe_shutdowns": 2,
        "media_errors": 0,
    }

    temp_storage.save_disk_health_snapshot(health_entry)
    history = temp_storage.get_disk_health_history(disk_id=0)
    assert len(history) == 1
    assert history[0]["temperature_c"] == 42.0
    assert history[0]["tbw_written_tb"] == 12.5


def test_disk_performance_and_io_events(temp_storage):
    """Проверка сэмплов производительности диска и I/O событий процессов."""
    perf = DiskPerformanceMetrics(
        disk_name=r"\PhysicalDisk(0 C:)",
        percent_disk_time=15.4,
        read_bytes_sec=1048576.0,
        write_bytes_sec=20971520.0,
        read_iops=120.0,
        write_iops=450.0,
        avg_read_latency_ms=1.2,
        avg_write_latency_ms=0.8,
        queue_length=1.2,
    )
    temp_storage.save_disk_performance_sample(perf)

    io_ev = DiskIOEvent(
        pid=1234,
        process_name="python.exe",
        disk_id=0,
        operation="WRITE",
        bytes_count=65536,
        duration_ms=0.45,
        offset=1048576,
    )
    temp_storage.save_disk_io_event(io_ev)

    perf_samples = temp_storage.get_disk_performance_samples()
    assert len(perf_samples) == 1
    assert perf_samples[0]["percent_disk_time"] == 15.4
    assert perf_samples[0]["read_bytes_sec"] == 1048576.0

    io_events = temp_storage.get_disk_io_events(pid=1234)
    assert len(io_events) == 1
    assert io_events[0]["process_name"] == "python.exe"
    assert io_events[0]["operation"] == "WRITE"
    assert io_events[0]["bytes_count"] == 65536
