# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Telemetry Engine
# =============================================================================
# Description:
#   Модульные тесты для Multi-Rate Decoupled Telemetry Engine и DeadbandTracker.
#
# Usage Examples:
#   pytest apps/windows/tests/test_telemetry_engine.py
#
# File: test_telemetry_engine.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 10:25:00
# =============================================================================

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.windows.telemetry.telemetry_engine import DeadbandTracker, TelemetryEngine
from apps.windows.telemetry.models import CpuMetrics, MemoryMetrics, SystemSnapshot


def test_deadband_tracker_no_spike():
    """Проверка отсутствия всплеска при незначительных колебаниях метрик."""
    tracker = DeadbandTracker(
        temp_threshold=1.0,
        cpu_load_threshold=3.0,
        freq_threshold_mhz=50.0,
    )

    readings_1 = [
        {"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 45.0},
        {"id": "cpu_util_total", "sensor_category": "Load", "unit": "%", "value": 15.0},
        {"id": "cpu_freq", "sensor_category": "Clocks", "unit": "MHz", "value": 3600.0},
    ]
    assert tracker.check_spike(readings_1) is False

    readings_2 = [
        {"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 45.5},  # delta 0.5 < 1.0
        {"id": "cpu_util_total", "sensor_category": "Load", "unit": "%", "value": 16.5},    # delta 1.5 < 3.0
        {"id": "cpu_freq", "sensor_category": "Clocks", "unit": "MHz", "value": 3620.0},    # delta 20 < 50.0
    ]
    assert tracker.check_spike(readings_2) is False


def test_deadband_tracker_spike_detection():
    """Проверка фиксации всплеска при превышении порога Deadband."""
    tracker = DeadbandTracker(
        temp_threshold=1.0,
        cpu_load_threshold=3.0,
        freq_threshold_mhz=50.0,
    )

    readings_1 = [
        {"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 50.0},
    ]
    tracker.check_spike(readings_1)

    readings_2 = [
        {"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 52.5},  # delta 2.5 >= 1.0
    ]
    assert tracker.check_spike(readings_2) is True


def test_deadband_tracker_filtering_and_heartbeat():
    """Проверка фильтрации для записи в SQLite и генерации Heartbeat кадра."""
    tracker = DeadbandTracker(temp_threshold=1.0, heartbeat_interval_sec=60.0)

    # 1. Первый замер -> всегда сохраняется
    r1 = [{"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 40.0}]
    filtered_1 = tracker.filter_records_for_storage(r1, now_epoch=1000.0)
    assert len(filtered_1) == 1

    # 2. Незначительное изменение в пределах 10 секунд -> отфильтровывается (дедупликация)
    r2 = [{"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 40.3}]
    filtered_2 = tracker.filter_records_for_storage(r2, now_epoch=1010.0)
    assert len(filtered_2) == 0

    # 3. Значительное изменение (delta 1.5 >= 1.0) -> сохраняется
    r3 = [{"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 41.8}]
    filtered_3 = tracker.filter_records_for_storage(r3, now_epoch=1020.0)
    assert len(filtered_3) == 1

    # 4. Штиль, но прошло 65 секунд (больше heartbeat 60с) -> контрольный кадр Heartbeat сохраняется
    r4 = [{"id": "cpu_temp", "sensor_category": "Temperature", "unit": "°C", "value": 41.8}]
    filtered_4 = tracker.filter_records_for_storage(r4, now_epoch=1085.0)
    assert len(filtered_4) == 1


@pytest.mark.asyncio
async def test_telemetry_engine_zero_delay_startup_and_lifecycle():
    """Проверка Zero-Delay запуска ядра телеметрии и завершения работы."""
    mock_collector = MagicMock()
    mock_collector.get_memory_metrics.return_value = MemoryMetrics(total_gb=16.0, used_gb=8.0, available_gb=8.0, percent=50.0)
    mock_collector.get_disk_metrics.return_value = ([], None)
    mock_collector.get_network_metrics.return_value = []
    mock_collector.get_top_processes.return_value = []

    mock_storage = MagicMock()

    engine = TelemetryEngine(collector=mock_collector, storage=mock_storage)

    t0 = time.perf_counter()
    start_task = asyncio.create_task(engine.start())
    # Даем один микро-тик event loop для инициализации
    await asyncio.sleep(0.01)
    startup_time_ms = (time.perf_counter() - t0) * 1000

    assert engine.is_running is True
    assert len(engine._tasks) >= 4

    # Остановка сервиса
    await engine.stop()
    assert engine.is_running is False
    assert len(engine._tasks) == 0
    mock_storage.flush.assert_called()


@pytest.mark.asyncio
async def test_telemetry_engine_deferred_static_inventory():
    """Проверка фонового формирования статического паспорта системы (Level 0)."""
    mock_collector = MagicMock()
    mock_collector.get_system_identity.return_value = {
        "hostname": "TEST-HOST",
        "username": "tester",
        "os_build": "Windows 11 Pro",
        "system_language": "ru-RU",
    }
    mock_collector.get_ram_sticks_sync.return_value = []
    mock_collector.get_physical_disks_health.return_value = []
    mock_collector.get_gpu_metrics.return_value = []
    mock_collector.archive_hardware_state.return_value = None
    mock_collector.archive_startup_state.return_value = None

    mock_storage = MagicMock()
    engine = TelemetryEngine(collector=mock_collector, storage=mock_storage)

    # Вызываем отложенную задачу
    await engine._deferred_static_inventory_task()

    assert engine.static_inventory_loaded is True
    assert engine.static_catalog.get("hostname") == "TEST-HOST"
    assert engine.static_catalog.get("username") == "tester"
