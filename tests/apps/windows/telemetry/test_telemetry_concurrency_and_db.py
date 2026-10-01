# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry Concurrency And Db
# =============================================================================
# Description:
#   Тесты параллельной записи, считывания и агрегации в БД TelemetryStorage.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_concurrency_and_db import TestTelemetryStorageConcurrencyAndOperations
#
#     service = TestTelemetryStorageConcurrencyAndOperations()
#
# File: test_telemetry_concurrency_and_db.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты параллельной записи, считывания и агрегации в БД TelemetryStorage.

Updated: 2026-10-01 11:05:00"""

import os
import time
import concurrent.futures
from datetime import datetime, timezone
import pytest

from apps.windows.telemetry.models import SystemSnapshot, TelemetryIncident
from apps.windows.telemetry.sqlite import TelemetryStorage
# Updated: 2026-10-01 11:30:00
from apps.windows.telemetry_research.aggregator import TelemetryAggregator
from apps.windows.telemetry_research.grouped_telemetry import GroupedTelemetryBuilder


@pytest.fixture
def temp_db_storage(tmp_path):
    """Фикстура изолированного TelemetryStorage на диске."""
    db_file = tmp_path / "test_telemetry_concurrency.db"
    storage = TelemetryStorage(
        db_path=db_file,
        buffer_mode='direct',
        auto_flush=False,
        max_db_size_mb=100.0,
        retention_days=7
    )
    yield storage
    storage.close()


class TestTelemetryStorageConcurrencyAndOperations:
    """Тесты надежности и параллельной работы TelemetryStorage."""

    def test_save_and_read_snapshots(self, temp_db_storage):
        """Проверка последовательной записи и считывания снимков."""
        now_iso = datetime.now(timezone.utc).isoformat()
        snap1 = SystemSnapshot(timestamp=now_iso)
        snap_id1 = temp_db_storage.save_snapshot(snap1)
        assert snap_id1 > 0

        snap2 = SystemSnapshot(timestamp=now_iso)
        snap_id2 = temp_db_storage.save_snapshot(snap2)
        assert snap_id2 > snap_id1

        results = temp_db_storage.get_snapshots(limit=10)
        assert len(results) >= 2

    def test_save_and_read_incidents(self, temp_db_storage):
        """Проверка записи и выгрузки системных инцидентов."""
        inc = TelemetryIncident(
            incident_id="INC-001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rule_id="cpu_spike",
            trigger_type="threshold",
            severity="critical",
            title="Высокая загрузка ЦП",
            description="ЦП загружен на 99%"
        )
        saved = temp_db_storage.save_incident(inc)
        assert saved is True

        incidents = temp_db_storage.get_incidents(limit=10)
        assert len(incidents) >= 1
        assert incidents[0]['incident_id'] == "INC-001"

    def test_concurrent_writes(self, temp_db_storage):
        """Проверка высоконагруженной записи снимков и сенсоров из 10 параллельных потоков."""
        def worker_write_task(worker_id: int):
            for i in range(10):
                now_str = datetime.now(timezone.utc).isoformat()
                snap = SystemSnapshot(timestamp=now_str)
                temp_db_storage.save_snapshot(snap)
                temp_db_storage.save_sensor_poll(
                    sensor_item={
                        'sensor_id': f"sensor_{worker_id}_{i}",
                        'category': 'cpu',
                        'metric_name': 'temperature',
                        'value': 45.0 + i,
                        'unit': 'C',
                        'status': 'ok'
                    },
                    timestamp=now_str
                )
            return True

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_write_task, w) for w in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(results)
        snaps = temp_db_storage.get_snapshots(limit=200)
        assert len(snaps) == 100

    def test_db_cleanup_and_vacuum(self, temp_db_storage):
        """Проверка ротации базы данных и чистки устаревших записей."""
        temp_db_storage.cleanup_old_records(retention_days=0)
        temp_db_storage.enforce_size_limit(max_size_mb=0.001)
        stats = temp_db_storage.get_storage_stats()
        assert isinstance(stats, dict)


class TestTelemetryAggregatorAndGroupedBuilder:
    """Тестирование агрегатора метрик и строителя сгруппированной телеметрии."""

    def test_aggregator_hourly_and_daily(self, temp_db_storage):
        aggregator = TelemetryAggregator(storage=temp_db_storage)
        
        # Наполним базу несколькими снимками
        now_str = datetime.now(timezone.utc).isoformat()
        for i in range(5):
            temp_db_storage.save_snapshot(SystemSnapshot(timestamp=now_str))

        aggregator.poll_once()
        status = aggregator.get_status()
        assert isinstance(status, dict)

    def test_grouped_telemetry_builder(self, temp_db_storage):
        now_str = datetime.now(timezone.utc).isoformat()
        snap = SystemSnapshot(timestamp=now_str)
        grouped_info = GroupedTelemetryBuilder.build_compute_thermals_group(snap)
        assert grouped_info is not None
        assert grouped_info.group_id is not None
