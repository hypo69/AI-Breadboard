# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Roadmap Optimizations
# =============================================================================
# Description:
#   Тесты оптимизаций SQLite, PRAGMA-директив, составных индексов, лимитов памяти буферов,
#   фонового агрегатора, расширений WevtAPI (Sysmon / PowerShell) и FORENSIC сэмплинга.
#
# Usage Examples:
#   pytest tests/apps/windows/telemetry/test_telemetry_roadmap_optimizations.py
#
# File: test_telemetry_roadmap_optimizations.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 05:35:00
# =============================================================================

from __future__ import annotations

"""Тесты для проверки выполнения дорожной карты оптимизаций телеметрии и базы данных SQLite."""

import sqlite3
import time
from pathlib import Path
import pytest

from apps.windows.telemetry.models import SamplingMode
from apps.windows.telemetry.ring_buffer import TelemetryRingBuffer
from apps.windows.telemetry.sampling_controller import SamplingController
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.telemetry.sqlite.aggregator import TelemetrySqlAggregator
from apps.windows.telemetry.sqlite.buffer import TelemetryBuffer
from apps.windows.telemetry.sqlite.connection import TelemetryConnectionManager
from apps.windows.telemetry.sqlite.schema import init_database_schema
from apps.windows.telemetry.sqlite.writer import TelemetryWriter
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI


class TestDatabaseAndStorageOptimizations:
    """Тестирование низкоуровневых оптимизаций SQLite и механизмов управления памятью."""

    def test_connection_pragmas_and_performance(self, tmp_path: Path):
        """Проверка применения оптимизированных PRAGMA директив соединения."""
        db_path = tmp_path / "test_pragmas.db"
        cm = TelemetryConnectionManager(db_path=db_path, read_only=False)

        with cm.get_connection() as conn:
            # Проверяем PRAGMA journal_mode
            cur = conn.execute("PRAGMA journal_mode;")
            j_mode = cur.fetchone()[0]
            assert str(j_mode).lower() == "wal"

            # Проверяем PRAGMA synchronous
            cur = conn.execute("PRAGMA synchronous;")
            sync_val = cur.fetchone()[0]
            assert sync_val in (1, "NORMAL", "normal")

            # Проверяем foreign_keys
            cur = conn.execute("PRAGMA foreign_keys;")
            fk_val = cur.fetchone()[0]
            assert fk_val == 1

            # Проверяем busy_timeout
            cur = conn.execute("PRAGMA busy_timeout;")
            timeout_val = cur.fetchone()[0]
            assert timeout_val >= 10000

    def test_composite_covering_indexes_created(self, tmp_path: Path):
        """Проверка генерации всех составных покрывающих индексов в схеме SQLite."""
        db_path = tmp_path / "test_indexes.db"
        cm = TelemetryConnectionManager(db_path=db_path, read_only=False)

        with cm.get_connection() as conn:
            init_database_schema(conn)

            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index';")
            indexes = {row[0] for row in cur.fetchall()}

            expected_indexes = [
                "idx_snapshots_created_host",
                "idx_proc_snap_snapshot_cpu",
                "idx_rollups_tier_start_end",
                "idx_incidents_sev_time",
                "idx_telemetry_hourly_sensor",
                "idx_telemetry_daily_sensor",
                "idx_telemetry_weekly_sensor",
                "idx_telemetry_monthly_sensor",
                "idx_telemetry_yearly_sensor",
            ]

            for idx in expected_indexes:
                assert idx in indexes, f"Индекс {idx} должен присутствовать в схеме"

    def test_ring_buffer_ram_limit_and_eviction(self):
        """Проверка жесткого ограничения по оперативной памяти (RAM) для кольцевого буфера."""
        # Устанавливаем емкость 100 элементов и лимит 10 КБ
        rb = TelemetryRingBuffer(capacity=100, max_bytes=10 * 1024)
        assert rb.max_bytes == 1024 * 1024  # min clamp 1MB

        # Создаем буфер с малым лимитом для проверки вытеснения
        small_rb = TelemetryRingBuffer(capacity=50, max_bytes=1024 * 1024)

        large_payload = {"data": "X" * 100000, "metrics": list(range(1000))}
        for i in range(20):
            small_rb.append({"index": i, "payload": large_payload})

        # Должны остаться только те элементы, что помещаются в лимит памяти
        assert small_rb.count() > 0
        assert small_rb.count() < 20
        assert small_rb.current_bytes <= small_rb.max_bytes

    def test_telemetry_buffer_ram_limit_auto_flush(self, tmp_path: Path):
        """Проверка автоматического сброса TelemetryBuffer при превышении лимита RAM."""
        db_path = tmp_path / "test_buf_ram.db"
        cm = TelemetryConnectionManager(db_path=db_path, read_only=False)
        with cm.get_connection() as conn:
            init_database_schema(conn)

        writer = TelemetryWriter(cm)
        buf = TelemetryBuffer(
            connection_manager=cm,
            writer=writer,
            buffer_mode='memory',
            buffer_size=1000,  # Высокий лимит по количеству
            flush_interval_seconds=300.0,
            max_buffer_bytes=1024 * 1024,  # Лимит 1 МБ
        )

        large_rec = {"type": "event", "event_type": "StressTest", "details": {"blob": "A" * 200000}}
        for _ in range(7):
            buf.enqueue(large_rec)

        # После превышения 1 МБ буфер должен автоматически сброситься в SQLite
        assert buf.get_buffered_count() < 7

        with cm.get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM telemetry_events;")
            count = cur.fetchone()[0]
            assert count >= 1

        buf.close()

    def test_aggregator_background_scheduler(self, tmp_path: Path):
        """Проверка работы фонового планировщика каскадной агрегации."""
        db_path = tmp_path / "test_sched.db"
        cm = TelemetryConnectionManager(db_path=db_path, read_only=False)
        with cm.get_connection() as conn:
            init_database_schema(conn)

        agg = TelemetrySqlAggregator(cm)
        agg.start_background_scheduler(interval_seconds=10.0)
        assert agg._scheduler_running is True
        assert agg._scheduler_timer is not None

        agg.stop_background_scheduler()
        assert agg._scheduler_running is False
        assert agg._scheduler_timer is None

    def test_storage_background_aggregator_delegation(self, tmp_path: Path):
        """Проверка делегирования фонового планировщика через фасад TelemetryStorage."""
        db_path = tmp_path / "test_storage_agg.db"
        storage = TelemetryStorage(db_path=db_path, buffer_mode="direct")

        storage.start_background_aggregator(interval_seconds=15.0)
        assert storage.aggregator._scheduler_running is True

        storage.stop_background_aggregator()
        assert storage.aggregator._scheduler_running is False
        storage.close()


class TestSamplingControllerForensicMode:
    """Тестирование высокочастотного режима FORENSIC в SamplingController."""

    def test_trigger_forensic_mode_and_interval(self):
        """Проверка перехода в режим FORENSIC и интервала 250 мс."""
        controller = SamplingController()
        controller.trigger_forensic_mode(duration_seconds=5.0)

        assert controller.mode == SamplingMode.FORENSIC
        assert controller.get_current_interval() == 0.25
        status = controller.get_status()
        assert status["incident_active"] is True
        assert status["mode"] == "forensic"


class TestWevtAPIExtensions:
    """Тестирование методов опроса каналов Sysmon и PowerShell в WevtAPI."""

    def test_wevtapi_script_blocks_method_signature(self):
        """Проверка наличия и сигнатуры метода query_powershell_script_blocks."""
        wevt = WevtAPI()
        res = wevt.query_powershell_script_blocks(limit=5)
        assert isinstance(res, list)

    def test_wevtapi_sysmon_events_method_signature(self):
        """Проверка наличия и сигнатуры метода query_sysmon_events."""
        wevt = WevtAPI()
        res = wevt.query_sysmon_events(limit=5, event_ids=[1, 7])
        assert isinstance(res, list)
