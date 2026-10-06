# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Telemetry - Schema Tests
# =============================================================================
# Description:
#   Тестирование структуры таблиц телеметрии SQLite и целостности связей.
#
# File: test_telemetry_schema.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:30:00
# =============================================================================

import gc
import sqlite3
import tempfile
from pathlib import Path
import pytest

from apps.windows.telemetry.sqlite.storage import TelemetryStorage


@pytest.fixture
def temp_db_conn():
    """Создает временное хранилище TelemetryStorage и возвращает sqlite3 соединение."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test_telemetry.db"
    storage = TelemetryStorage(db_path=db_path, buffer_mode="direct", auto_flush=False)
    conn = sqlite3.connect(str(db_path))
    yield conn
    conn.close()
    storage.close()
    gc.collect()


def test_tables_exist(temp_db_conn):
    """Убеждаемся, что созданы все ожидаемые таблицы телеметрии и оборудования."""
    cur = temp_db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = {row[0] for row in cur.fetchall()}
    expected = {
        "sensor_polls",
        "system_snapshots",
        "disk_inventory",
        "volume_inventory",
        "disk_health_snapshots",
        "disk_performance_samples",
        "disk_io_events",
        "cpu_inventory",
        "cpu_telemetry_samples",
        "ram_module_inventory",
        "ram_telemetry_samples",
        "gpu_inventory",
        "gpu_telemetry_samples",
        "network_adapter_inventory",
        "network_adapter_samples",
    }
    missing = expected - tables
    assert not missing, f"Отсутствуют таблицы: {missing}"


def test_indexes_exist(temp_db_conn):
    """Проверяем, что созданы необходимые индексы для ускорения выборок."""
    cur = temp_db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';"
    )
    indexes = {row[0] for row in cur.fetchall()}
    assert "idx_disk_perf_name_time" in indexes
    assert "idx_disk_health_disk_time" in indexes
    assert "idx_cpu_samples_time" in indexes
    assert "idx_ram_samples_time" in indexes
    assert "idx_gpu_samples_time" in indexes
    assert "idx_net_samples_time" in indexes

