# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Aggregator
# =============================================================================
# Description:
#   Модульные тесты для компонентов потоковой телеметрии Windows.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_aggregator import test_telemetry_config_manager
#
#     res = test_telemetry_config_manager()
#
# File: test_telemetry_aggregator.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Модульные тесты для компонентов потоковой телеметрии Windows."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from apps.windows.telemetry import FileCollector, SensorCollector, TelemetryAggregator, TelemetryConfigManager, TelemetryJsonLogger

def test_telemetry_config_manager(tmp_path: Path) -> None:
    """Тестирование загрузки и работы с конфигурацией телеметрии."""
    sample_config = {'interval_seconds': 10.0, 'max_file_size_mb': 50, 'watch_directories': ['C:\\Test'], 'log_filename': 'test_polls.json', 'sensors': {'cpu': {'enabled': True, 'interval_seconds': 2.0, 'metrics': ['load']}, 'gpu': {'enabled': False, 'interval_seconds': 5.0, 'metrics': ['temperature']}}}
    config_file = tmp_path / 'config.json'
    config_file.write_text(json.dumps(sample_config), encoding='utf-8')
    mgr = TelemetryConfigManager(config_path=str(config_file))
    assert mgr.is_sensor_enabled('cpu') is True
    assert mgr.is_sensor_enabled('gpu') is False
    assert mgr.get_sensor_interval('cpu') == 2.0
    assert mgr.get_sensor_interval('gpu') == 5.0
    assert mgr.get_sensor_metrics('cpu') == ['load']
    assert mgr.get_enabled_sensors() == ['cpu']
    assert 'cpu' in mgr.get_all_sensor_names()

@pytest.mark.skip(reason="Логирование телеметрии в JSON больше не используется")
def test_telemetry_json_logger(tmp_path: Path) -> None:
    """Тестирование записи и авторотации логгера телеметрии."""
    log_dir = tmp_path / 'logs'
    logger = TelemetryJsonLogger(log_dir=str(log_dir), filename='test.json', max_file_size_mb=0.001)
    record1 = {'measurement': 1, 'data': 'hello'}
    record2 = {'measurement': 2, 'data': 'world'}
    assert logger.log(record1) is True
    assert logger.get_last_measurement() == record1
    assert logger.get_log_file_size() > 0
    batch_count = logger.log_batch([record2, {'measurement': 3, 'data': 'x' * 2000}])
    assert batch_count == 2
    logger.log({'measurement': 4, 'data': 'after_rotation'})
    files = list(log_dir.glob('*.json'))
    assert len(files) >= 1

@patch('apps.windows.telemetry.sensor_collector.InternetSpeedSensor')
@patch('apps.windows.telemetry.sensor_collector.HardwareMonitor')
def test_sensor_collector_snapshot(mock_hw_cls: MagicMock, mock_speed_cls: MagicMock) -> None:
    """Тестирование сбора аппаратного снимка сенсоров."""
    mock_hw = MagicMock()
    mock_hw.get_telemetry_snapshot.return_value = {'timestamp': '2026-09-24T18:00:00Z', 'cpu_usage_percent': 15.0, 'memory_used_mb': 4096, 'gpu_temperature_c': 50}
    mock_hw_cls.return_value = mock_hw
    mock_speed = MagicMock()
    mock_speed.get_metrics.return_value = {'ping_ms': 12.0, 'download_mbps': 100.0, 'upload_mbps': 50.0}
    mock_speed_cls.return_value = mock_speed
    collector = SensorCollector()
    snapshot = collector.get_hardware_snapshot()
    assert 'timestamp' in snapshot
    assert 'sensors' in snapshot
    assert isinstance(snapshot['sensors'], list)
    if snapshot['sensors']:
        first = snapshot['sensors'][0]
        assert 'id' in first
        assert 'hardware_name' in first
        assert 'sensor_category' in first
        assert 'sensor_name' in first
        assert 'unit' in first
        assert 'values' in first
        assert isinstance(first['values'], list)

@pytest.mark.skip(reason="Сбор события в файлы больше не используется")
def test_file_collector_events(tmp_path: Path) -> None:
    """Тестирование работы коллектора файловых событий."""
    test_dir = str(tmp_path)
    mock_watcher = MagicMock()
    mock_watcher.start.return_value = True
    mock_watcher.get_recent_events.return_value = []
    with patch('apps.windows.telemetry.file_collector.DirectoryWatcher', return_value=mock_watcher):
        collector = FileCollector(watch_dirs=[test_dir])
        assert collector.add_watch_dir(test_dir) is False
        events = collector.get_recent_events(limit=10)
        assert isinstance(events, list)
        collector.stop()
        mock_watcher.stop.assert_called()

def test_telemetry_aggregator_lifecycle(tmp_path: Path) -> None:
    """Тестирование жизненного цикла агрегатора телеметрии."""
    log_dir = tmp_path / 'telemetry_logs'
    mock_fc = MagicMock(spec=FileCollector)
    mock_fc.get_recent_events.return_value = []
    mock_fc.stop.return_value = None
    mock_sc = MagicMock(spec=SensorCollector)
    mock_sc.get_hardware_snapshot.return_value = {'timestamp': '2026-09-24T12:00:00+03:00', 'sensors': [{'id': 'cpu_1', 'hardware_name': 'CPU', 'value': 25.0}]}
    from apps.windows.telemetry.sqlite import TelemetryStorage
    test_storage = TelemetryStorage(db_path=tmp_path / 'agg_test.db')
    aggregator = TelemetryAggregator(log_dir=str(log_dir), file_collector=mock_fc, sensor_collector=mock_sc, storage=test_storage)
    aggregator.poll_once()
    last = aggregator.get_last_measurement()
    assert last is not None
    assert 'hardware' in last
    assert 'file_events' in last
    status = aggregator.get_status()
    assert status['measurement_count'] == 1
    assert status['is_running'] is False
    assert aggregator.start() is True
    assert aggregator.get_status()['is_running'] is True
    assert aggregator.start() is False
    time.sleep(0.1)
    assert aggregator.stop() is True
    assert aggregator.get_status()['is_running'] is False

def test_telemetry_config_default_apps_windows_path() -> None:
    """Проверка загрузки конфигурации сенсоров по умолчанию из apps/windows/config.json."""
    mgr = TelemetryConfigManager()
    all_sensors = mgr.get_all_sensor_names()
    assert 'cpu' in all_sensors
    assert 'gpu' in all_sensors
    assert 'ram' in all_sensors
    assert 'disk' in all_sensors
    assert 'network' in all_sensors
    assert 'sensors' in all_sensors
    assert 'internet' in all_sensors
    assert mgr.is_sensor_enabled('cpu') is True
    assert mgr.get_sensor_interval('cpu') == 5.0
    assert mgr.get_sensor_interval('gpu') == 10.0
    assert mgr.get_sensor_interval('ram') == 10.0
    assert mgr.get_sensor_interval('disk') == 30.0
    assert mgr.get_sensor_interval('network') == 10.0
    assert mgr.get_sensor_interval('sensors') == 10.0
    assert mgr.get_sensor_interval('internet') == 120.0

def test_all_sensors_polling_metrics() -> None:
    """Тестирование доступности метрик для каждого сенсора."""
    mgr = TelemetryConfigManager()
    assert 'clocks' in mgr.get_sensor_metrics('cpu')
    assert 'power' in mgr.get_sensor_metrics('gpu')
    assert 'swap' in mgr.get_sensor_metrics('ram')
    assert 'io' in mgr.get_sensor_metrics('disk')
    assert 'throughput' in mgr.get_sensor_metrics('network')
    assert 'voltage' in mgr.get_sensor_metrics('sensors')
    assert 'ping' in mgr.get_sensor_metrics('internet')

def test_sensor_collector_extract_readings() -> None:
    """Тестирование извлечения показаний сенсоров в SensorCollector."""
    collector = SensorCollector()
    dummy_hardware = {'cpu': {'model': 'Intel Core i5-10400', 'utilization_pct': 25.0, 'per_core_pct': [10.0, 20.0, 30.0], 'frequency_current_mhz': 4000.0}, 'memory': {'utilization_pct': 60.0, 'swap_utilization_pct': 15.0}, 'storage': {'partitions': [{'device': 'C:', 'mountpoint': 'C:\\', 'utilization_pct': 70.0}], 'io_rates': {'read_bytes_sec': 1024, 'write_bytes_sec': 2048}}, 'network': {'bytes_sent_sec': 500, 'bytes_recv_sec': 1500}}
    dummy_extra_sensors = {'available': True, 'sensors': [{'id': 38, 'hardware_name': 'Intel Core i5-10400', 'hardware_type': 'cpu', 'sensor_category': 'Temperatures', 'sensor_name': 'CPU Core #4 Distance to TjMax', 'unit': '°C', 'value_num': 56.0}]}
    dummy_internet = {'available': True, 'ping_ms': 12.5, 'download_mbps': 100.0, 'upload_mbps': 50.0, 'dns_ms': 5.0}
    readings = collector.extract_sensor_readings(dummy_hardware, dummy_extra_sensors, dummy_internet)
    assert len(readings) > 0
    extra_sensor = next((s for s in readings if s['id'] == 38))
    assert extra_sensor['hardware_name'] == 'Intel Core i5-10400'
    assert extra_sensor['sensor_category'] == 'Temperatures'
    assert extra_sensor['sensor_name'] == 'CPU Core #4 Distance to TjMax'
    assert extra_sensor['unit'] == '°C'
    assert extra_sensor['value'] == 56.0

@pytest.mark.skip(reason="Метод record_sensors устарел")
def test_telemetry_json_logger_incrementing_values(tmp_path: Path) -> None:
    """Тестирование инкрементации замеров в массив values [{"num": ..., "time": ...}]."""
    log_dir = tmp_path / 'logs'
    logger = TelemetryJsonLogger(log_dir=str(log_dir), filename='sensors.json', max_file_size_mb=50.0)
    sensor1 = {'id': 38, 'hardware_name': 'Intel Core i5-10400', 'hardware_type': 'cpu', 'sensor_category': 'Temperatures', 'sensor_name': 'CPU Core #4 Distance to TjMax', 'unit': '°C', 'value': 56.0}
    assert logger.record_sensors([sensor1], timestamp='2026-09-24T15:21:21+03:00') is True
    sensor1_next = dict(sensor1, value=58.5)
    assert logger.record_sensors([sensor1_next], timestamp='2026-09-24T15:21:26+03:00') is True
    assert logger.record_sensors([sensor1_next], timestamp='2026-09-24T15:21:30+03:00') is True
    assert len(logger.get_sensors_registry()[0]['values']) == 2
    sensor1_changed = dict(sensor1, value=60.0)
    assert logger.record_sensors([sensor1_changed], timestamp='2026-09-24T15:21:35+03:00') is True
    assert len(logger.get_sensors_registry()[0]['values']) == 3
    assert logger.get_sensors_registry()[0]['values'][2] == {'num': 60.0, 'time': '2026-09-24T15:21:35+03:00'}