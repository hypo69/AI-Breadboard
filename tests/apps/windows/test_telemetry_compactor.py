# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Compactor
# =============================================================================
# Description:
#   Тесты математического сжатия метрик и перцентилей.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_compactor import test_compute_percentile
#
#     res = test_compute_percentile()
#
# File: test_telemetry_compactor.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты математического сжатия метрик и перцентилей."""

import pytest
from apps.windows.telemetry.compactor import TelemetryCompactor, compute_percentile


def test_compute_percentile():
    """Проверяет точный расчет 95-го перцентиля на контрольных выборках."""
    assert compute_percentile([]) == 0.0
    assert compute_percentile([42.0]) == 42.0

    # 100 значений от 1 до 100
    values = list(range(1, 101))
    p95 = compute_percentile(values, 95.0)
    assert 94.0 <= p95 <= 96.0

    # Импульс майнера: 9 нулей и одна сотня
    burst = [0.0] * 9 + [100.0]
    burst_p95 = compute_percentile(burst, 95.0)
    assert burst_p95 > 50.0  # Перцентиль четко отражает всплеск, в отличие от среднего 10%


def test_tier_for_age():
    """Проверяет определение уровня сжатия в зависимости от возраста данных."""
    assert TelemetryCompactor.get_tier_for_age(30.0) == "1s"
    assert TelemetryCompactor.get_tier_for_age(120.0) == "2s"
    assert TelemetryCompactor.get_tier_for_age(600.0) == "5s"
    assert TelemetryCompactor.get_tier_for_age(1200.0) == "10s"
    assert TelemetryCompactor.get_tier_for_age(3000.0) == "30s"
    assert TelemetryCompactor.get_tier_for_age(5000.0) == "1m"
    assert TelemetryCompactor.get_tier_for_age(20000.0) == "5m"
    assert TelemetryCompactor.get_tier_for_age(50000.0) == "15m"
    assert TelemetryCompactor.get_tier_for_age(200000.0) == "1h"
    assert TelemetryCompactor.get_tier_for_age(1000000.0) == "6h"


def test_compact_system_metrics():
    """Проверяет сжатие системных метрик с расчетом средних, пиков и суммарных объемов."""
    # Эмулируем 60 замеров по 1 секунде
    samples = []
    for i in range(60):
        # Всплеск нагрузки на 30-й секунде
        cpu = 100.0 if i == 30 else 5.0
        disk_w = (100.0 * 1024 * 1024) if i == 30 else 0.0  # 100 МБ/с на 1 секунду
        samples.append({
            "cpu_total_percent": cpu,
            "memory_used_gb": 8.0,
            "memory_percent": 50.0,
            "disk_read_bytes_sec": 0.0,
            "disk_write_bytes_sec": disk_w,
            "network_recv_bytes_sec": 0.0,
            "network_sent_bytes_sec": 0.0,
        })

    rollup = TelemetryCompactor.compact_system_metrics(
        samples=samples,
        period_start="2026-10-01T12:00:00+00:00",
        period_end="2026-10-01T12:01:00+00:00",
        tier="1m",
    )

    assert rollup.sample_count == 60
    assert rollup.cpu_max == 100.0
    assert rollup.cpu_min == 5.0
    assert rollup.cpu_avg > 5.0
    assert rollup.disk_write_max_mbs >= 100.0
    assert rollup.disk_write_total_mb >= 95.0


def test_compact_process_metrics():
    """Проверяет группировку и агрегацию метрик процессов."""
    proc_samples = [
        {"name": "miner.exe", "pid": 4812, "cpu_percent": 10.0, "memory_mb": 100.0, "read_bytes_sec": 0.0, "write_bytes_sec": 0.0},
        {"name": "miner.exe", "pid": 4812, "cpu_percent": 90.0, "memory_mb": 150.0, "read_bytes_sec": 0.0, "write_bytes_sec": 1024 * 1024 * 50},
        {"name": "explorer.exe", "pid": 1000, "cpu_percent": 2.0, "memory_mb": 200.0, "read_bytes_sec": 0.0, "write_bytes_sec": 0.0},
    ]

    rollups = TelemetryCompactor.compact_process_metrics(
        proc_samples,
        period_start="2026-10-01T12:00:00+00:00",
        period_end="2026-10-01T12:01:00+00:00",
    )

    assert len(rollups) == 2
    miner_r = next(r for r in rollups if r.name == "miner.exe")
    assert miner_r.cpu_max == 90.0
    assert miner_r.cpu_avg == 50.0
    assert miner_r.ram_max_mb == 150.0
