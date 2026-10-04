# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Telemetry Sensors Extended
# =============================================================================
# Description:
#   Тесты для режимов опроса, темпов, параллельного опроса сенсоров и оборудования без использования моков.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry.test_telemetry_sensors_extended import TestSamplingControllerModesAndTempoReal
#
#     service = TestSamplingControllerModesAndTempoReal()
#
# File: test_telemetry_sensors_extended.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 06:25:00
# =============================================================================

"""Тесты для режимов опроса, темпов, параллельного опроса сенсоров и оборудования без использования моков."""

import time
import concurrent.futures
import pytest

from apps.windows.telemetry.models import SamplingMode
from apps.windows.telemetry.sampling_controller import SamplingController
from apps.windows.telemetry.sensor_collector import SensorCollector
from apps.windows.telemetry.device_flapping_sensor import DeviceFlappingSensor
from apps.windows.telemetry.storage_usage import WindowsStorageUsageCollector
from apps.windows.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
from apps.windows.telemetry_research.hardware_auditor import HardwareAuditor
from apps.windows.telemetry_research.hardware_history_manager import HardwareHistoryManager
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager


class TestSamplingControllerModesAndTempoReal:
    """Тестирование реального контроллера частоты сбора телеметрии и смены режимов."""

    def test_mode_transitions_and_intervals(self):
        controller = SamplingController(initial_mode=SamplingMode.BOOT_AGGRESSIVE)
        assert controller.mode == SamplingMode.BOOT_AGGRESSIVE

        # Переключение в режим мониторинга
        controller.set_mode(SamplingMode.MONITORING)
        assert controller.mode == SamplingMode.MONITORING

        # Переключение в режим инцидента с длительностью
        controller.trigger_incident_mode(duration_seconds=1)
        assert controller.mode == SamplingMode.INCIDENT

        # Проверка реальных интервалов опроса для режимов
        int_inc = controller.get_current_interval()
        assert int_inc > 0.0

        # Ожидание истечения режима инцидента
        time.sleep(1.1)
        assert controller.mode == SamplingMode.MONITORING

        # Режим глубокой экспертизы (FORENSIC)
        controller.set_mode(SamplingMode.FORENSIC)
        assert controller.mode == SamplingMode.FORENSIC


class TestSensorCollectorConcurrencyReal:
    """Тестирование сбора с реальных сенсоров при параллельных вызовах без моков."""

    @pytest.fixture
    def sensor_collector(self):
        config_mgr = TelemetryConfigManager()
        collector = SensorCollector(config_manager=config_mgr)
        return collector

    def test_sensor_collector_basic_poll(self, sensor_collector):
        hw_data = sensor_collector._get_hardware_data()
        assert isinstance(hw_data, dict)

        net_data = sensor_collector._get_internet_speed_data()
        assert isinstance(net_data, dict)

    def test_concurrent_sensor_polling(self, sensor_collector):
        """Проверка одновременного (конкурентного) получения данных из разных сенсоров из 5 потоков."""
        def poll_task(sensor_type: str):
            if sensor_type == 'hw':
                return sensor_collector._get_hardware_data()
            elif sensor_type == 'net':
                return sensor_collector._get_internet_speed_data()
            else:
                return sensor_collector._get_hardware_data()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(poll_task, 'hw'),
                executor.submit(poll_task, 'net'),
                executor.submit(poll_task, 'hw'),
                executor.submit(poll_task, 'net'),
                executor.submit(poll_task, 'hw'),
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        assert len(results) == 5
        for res in results:
            assert isinstance(res, dict)


class TestDeviceFlappingSensorReal:
    """Тестирование реального сенсора нестабильного (flapping) оборудования на PnP API."""

    def test_device_flapping_detection(self):
        sensor = DeviceFlappingSensor(poll_interval_sec=0.1, flapping_threshold=2)
        events = sensor.poll_once()
        assert isinstance(events, list)


class TestStorageSensorsReal:
    """Тестирование реальных анализаторов заполнения накопителей и дисков."""

    def test_storage_usage_calculator(self):
        calc = WindowsStorageUsageCollector()
        res = calc.get_disk_usage_period_report(period_minutes=60)
        assert res is not None

    def test_windows_storage_sensor(self):
        sensor = WindowsStorageSensor()
        snap = sensor.collect_snapshot(force_refresh=True)
        assert isinstance(snap, dict)


class TestHardwareAuditorAndHistoryReal:
    """Тесты реального аудита оборудования и ведения истории изменений."""

    def test_hardware_auditor_perform_audit(self):
        auditor = HardwareAuditor()
        report = auditor.audit_hardware()
        assert report is not None

    def test_hardware_history_manager(self):
        history_mgr = HardwareHistoryManager()
        auditor = HardwareAuditor()
        report = auditor.audit_hardware()
        entry = history_mgr.archive_report(report)
        assert entry is not None

        history = history_mgr.get_history(limit=5)
        assert isinstance(history, list)

        changes = history_mgr.get_change_timeline(limit=5)
        assert isinstance(changes, list)
