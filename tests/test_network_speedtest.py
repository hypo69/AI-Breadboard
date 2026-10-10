# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Network Speedtest (FAST.com / bufferbloat)
# =============================================================================
# File: test_network_speedtest.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 04:55:00
# =============================================================================

"""Тесты расчёта latency, bufferbloat, сенсора телеметрии и часового кеширования NetworkSpeedTester."""

import time
from unittest.mock import MagicMock, patch

import pytest

from apps.windows.sdk.modules.network.speedtest import NetworkSpeedTester
from apps.windows.telemetry.internet_speed import InternetSpeedSensor, get_internet_speed_sensors


def test_latency_stats_empty() -> None:
    """Пустая выборка даёт нулевую статистику."""
    assert NetworkSpeedTester._latency_stats([])['count'] == 0


def test_latency_stats_values() -> None:
    """Медиана, min/max и jitter считаются корректно."""
    stats = NetworkSpeedTester._latency_stats([8.0, 10.0, 9.0])
    assert stats['median_ms'] == 9.0
    assert stats['min_ms'] == 8.0 and stats['max_ms'] == 10.0
    assert stats['jitter_ms'] == 1.5


def test_quality_downgraded_by_bufferbloat() -> None:
    """Высокий bufferbloat снижает оценку даже при отличной скорости."""
    tester = NetworkSpeedTester()
    assert tester._evaluate_quality(900, 100, 7, 5)['rating'] == 'A+'
    assert tester._evaluate_quality(900, 100, 7, 80)['rating'] == 'B'
    assert tester._evaluate_quality(900, 100, 7, 273)['rating'] == 'C'


@pytest.mark.asyncio
async def test_run_full_speedtest_error_handling_no_fallback() -> None:
    """При недоступности FAST.com возвращается ошибка без перехода на сторонние провайдеры."""
    tester = NetworkSpeedTester()
    with patch.object(tester, 'resolve_fast_target', return_value=None):
        report = await tester.run_full_speedtest()
        assert report['provider'] == 'fast.com'
        assert report['download']['status'] == 'ERROR'
        assert report['quality']['rating'] == 'F'
        assert report['record']['provider'] == 'fast.com'


def test_internet_speed_sensor_caching() -> None:
    """Сенсор телеметрии кеширует замеры на 1 час (3600 секунд)."""
    InternetSpeedSensor.clear_cache()
    sensor = InternetSpeedSensor(cache_ttl=3600)

    mock_report = {
        'provider': 'fast.com',
        'server': 'api.fast.com (Frankfurt, DE)',
        'download': {'speed_mbps': 250.5, 'status': 'SUCCESS'},
        'upload': {'speed_mbps': 85.2, 'status': 'SUCCESS'},
        'ping_ms': 12.4,
        'latency_unloaded_ms': 12.4,
        'latency_loaded_ms': 18.6,
        'bufferbloat_ms': 6.2,
        'meta': {'ip': '198.51.100.1', 'isp': 'Test Provider'}
    }

    with patch.object(sensor, '_run_speedtest_sync', return_value=mock_report) as mock_run:
        res1 = sensor.measure_internet_speed()
        assert mock_run.call_count == 1
        assert res1['download_mbps'] == 250.5
        assert res1['upload_mbps'] == 85.2
        assert res1['ping_ms'] == 12.4
        assert res1['bufferbloat_ms'] == 6.2
        assert res1['provider'] == 'fast.com'

        # Второй вызов должен взять данные из кеша без повторного запуска
        res2 = sensor.measure_internet_speed()
        assert mock_run.call_count == 1
        assert res2['download_mbps'] == 250.5

        # Принудительный сброс кеша
        res3 = sensor.measure_internet_speed(force_refresh=True)
        assert mock_run.call_count == 2
        assert res3['download_mbps'] == 250.5


def test_get_internet_speed_sensors_structure() -> None:
    """Функция get_internet_speed_sensors возвращает список сенсоров нужного формата."""
    InternetSpeedSensor.clear_cache()
    mock_metrics = {
        'available': True,
        'download_mbps': 120.0,
        'upload_mbps': 45.0,
        'ping_ms': 15.0,
        'bufferbloat_ms': 4.0,
        'latency_loaded_ms': 19.0,
        'provider': 'fast.com'
    }
    with patch.object(InternetSpeedSensor, 'measure_internet_speed', return_value=mock_metrics):
        sensors = get_internet_speed_sensors()
        sensor_ids = {s['sensor_id']: s for s in sensors}
        assert 'internet_download' in sensor_ids
        assert 'internet_upload' in sensor_ids
        assert 'internet_ping' in sensor_ids
        assert 'internet_bufferbloat' in sensor_ids
        assert 'internet_latency_loaded' in sensor_ids
        assert sensor_ids['internet_download']['value'] == 120.0
        assert sensor_ids['internet_download']['unit'] == 'Mbps'
        assert sensor_ids['internet_bufferbloat']['value'] == 4.0
