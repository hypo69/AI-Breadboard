# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Sql Aggregator
# =============================================================================
# Description:
#   Модульные тесты для многоуровневого SQL-агрегатора телеметрии:
#   raw -> hourly -> daily -> weekly -> monthly -> yearly и фиксации всплесков.
#
# Usage Examples:
#   CLI:
#     pytest tests/apps/windows/telemetry/test_telemetry_sql_aggregator.py
#
# File: test_telemetry_sql_aggregator.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 00:20:00
# =============================================================================

from __future__ import annotations

"""Модульные тесты многоуровневого SQL-агрегатора телеметрии."""

from pathlib import Path
import pytest

from apps.windows.telemetry.sqlite import (
    AggregationLevel,
    TelemetrySqlAggregator,
    TelemetryStorage,
    sensors_aggregate,
)


def test_sql_aggregator_full_chain(tmp_path: Path) -> None:
    """Тестирование полного каскада SQL-агрегации: hourly -> daily -> weekly -> monthly -> yearly."""
    db_file = tmp_path / "telemetry_test.db"
    storage = TelemetryStorage(db_path=db_file)

    # 1. Заполняем raw замеры sensor_polls за 2 дня (каждые 60 секунд)
    # Базовое время: 2026-10-01 00:00:00 UTC (epoch: 1790812800)
    base_epoch = 1790812800.0
    raw_polls = []
    for i in range(2880):  # 2 дня по 1440 минут
        cur_epoch = base_epoch + (i * 60.0)
        val = 20.0 + (i % 10)  # колебания от 20 до 29
        raw_polls.append({
            "id": "cpu_temp",
            "hardware_name": "CPU",
            "sensor_category": "Temperature",
            "sensor_name": "Core 0",
            "unit": "°C",
            "value": val,
            "created_at": cur_epoch,
        })

    # Сохраняем пачкой через storage
    with storage._cm.lock, storage._cm.get_connection() as conn:
        cursor = conn.cursor()
        for p in raw_polls:
            cursor.execute("""
                INSERT INTO sensor_polls (
                    sensor_id, timestamp, created_at, hardware_name,
                    sensor_category, sensor_name, unit, value
                ) VALUES (?, datetime(?, 'unixepoch'), ?, ?, ?, ?, ?, ?)
            """, (
                p["id"], p["created_at"], p["created_at"], p["hardware_name"],
                p["sensor_category"], p["sensor_name"], p["unit"], p["value"],
            ))
        conn.commit()

    # 2. Выполняем почасовую агрегацию
    h_res = storage.aggregate_hourly(start_epoch=base_epoch, end_epoch=base_epoch + 172800.0)
    assert h_res["buckets_aggregated"] == 48

    hourly_rows = storage.get_telemetry_rollups(level="hourly", sensor_id="cpu_temp", limit=100)
    assert len(hourly_rows) == 48
    first_hour = sorted(hourly_rows, key=lambda x: x["bucket_start"])[0]
    assert first_hour["sample_count"] == 60
    assert first_hour["value_min"] == 20.0
    assert first_hour["value_max"] == 29.0
    assert 24.0 <= first_hour["value_avg"] <= 25.0
    assert first_hour["value_first"] == 20.0
    assert first_hour["value_last"] == 29.0
    assert first_hour["value_stddev"] > 0.0

    # 3. Выполняем суточную агрегацию
    d_res = storage.aggregate_daily(start_epoch=base_epoch, end_epoch=base_epoch + 172800.0)
    assert d_res["buckets_aggregated"] == 2

    daily_rows = storage.get_telemetry_rollups(level="daily", sensor_id="cpu_temp", limit=10)
    assert len(daily_rows) == 2
    day0 = sorted(daily_rows, key=lambda x: x["bucket_start"])[0]
    assert day0["sample_count"] == 1440
    assert day0["value_min"] == 20.0
    assert day0["value_max"] == 29.0
    assert 24.0 <= day0["value_avg"] <= 25.0

    # 4. Выполняем недельную агрегацию
    w_res = storage.aggregate_weekly(start_epoch=base_epoch, end_epoch=base_epoch + 172800.0)
    assert w_res["buckets_aggregated"] >= 1
    weekly_rows = storage.get_telemetry_rollups(level="weekly", sensor_id="cpu_temp", limit=10)
    assert len(weekly_rows) >= 1

    # 5. Выполняем месячную агрегацию
    m_res = storage.aggregate_monthly(start_epoch=base_epoch, end_epoch=base_epoch + 172800.0)
    assert m_res["buckets_aggregated"] >= 1
    monthly_rows = storage.get_telemetry_rollups(level="monthly", sensor_id="cpu_temp", limit=10)
    assert len(monthly_rows) >= 1

    # 6. Выполняем годовую агрегацию
    y_res = storage.aggregate_yearly(start_epoch=base_epoch, end_epoch=base_epoch + 172800.0)
    assert y_res["buckets_aggregated"] >= 1
    yearly_rows = storage.get_telemetry_rollups(level="yearly", sensor_id="cpu_temp", limit=10)
    assert len(yearly_rows) >= 1


def test_spike_detection_in_sql_aggregation(tmp_path: Path) -> None:
    """Тестирование автоматической фиксации аномалий и всплесков сенсоров при SQL-агрегации."""
    db_file = tmp_path / "spikes_test.db"
    storage = TelemetryStorage(db_path=db_file)

    base_epoch = 1790812800.0
    # Вставляем 59 обычных измерений около 25 градусов и 1 резкий всплеск до 95 градусов
    with storage._cm.lock, storage._cm.get_connection() as conn:
        cursor = conn.cursor()
        for i in range(59):
            cur_epoch = base_epoch + (i * 60.0)
            cursor.execute("""
                INSERT INTO sensor_polls (
                    sensor_id, timestamp, created_at, hardware_name,
                    sensor_category, sensor_name, unit, value
                ) VALUES (?, datetime(?, 'unixepoch'), ?, 'CPU', 'Temperature', 'Core 0', '°C', ?)
            """, ("cpu_spike_test", cur_epoch, cur_epoch, 25.0 + (i % 2)))

        # Всплеск на 59-й минуте
        spike_epoch = base_epoch + (59 * 60.0)
        cursor.execute("""
            INSERT INTO sensor_polls (
                sensor_id, timestamp, created_at, hardware_name,
                sensor_category, sensor_name, unit, value
            ) VALUES (?, datetime(?, 'unixepoch'), ?, 'CPU', 'Temperature', 'Core 0', '°C', ?)
        """, ("cpu_spike_test", spike_epoch, spike_epoch, 95.0))
        conn.commit()

    # Запускаем почасовую агрегацию с обнаружением всплесков
    storage.aggregate_hourly(start_epoch=base_epoch, end_epoch=base_epoch + 3600.0, detect_spikes=True)

    spikes = storage.get_telemetry_spikes(sensor_id="cpu_spike_test")
    assert len(spikes) >= 1
    s0 = spikes[0]
    assert s0["sensor_id"] == "cpu_spike_test"
    assert s0["value"] == 95.0
    assert s0["spike_type"] == "high"
    assert "Всплеск" in s0["details"]


def test_run_aggregation_pipeline_and_storage_stats(tmp_path: Path) -> None:
    """Тестирование пакетного запуска pipeline и отражения статистики в get_storage_stats."""
    db_file = tmp_path / "pipeline_test.db"
    storage = TelemetryStorage(db_path=db_file)

    base_epoch = 1790812800.0
    with storage._cm.lock, storage._cm.get_connection() as conn:
        cursor = conn.cursor()
        for i in range(120):
            cur_epoch = base_epoch + (i * 60.0)
            cursor.execute("""
                INSERT INTO sensor_polls (
                    sensor_id, timestamp, created_at, hardware_name,
                    sensor_category, sensor_name, unit, value
                ) VALUES (?, datetime(?, 'unixepoch'), ?, 'GPU', 'Load', 'GPU Core', '%', ?)
            """, ("gpu_load_test", cur_epoch, cur_epoch, 50.0))
        conn.commit()

    pipe_res = storage.run_aggregation_pipeline(start_epoch=base_epoch, end_epoch=base_epoch + 7200.0)
    assert pipe_res["hourly"]["buckets_aggregated"] == 2

    stats = storage.get_storage_stats()
    assert stats["telemetry_hourly_count"] == 2
    assert stats["telemetry_daily_count"] >= 1
    assert stats["telemetry_weekly_count"] >= 1
    assert stats["telemetry_monthly_count"] >= 1
    assert stats["telemetry_yearly_count"] >= 1
