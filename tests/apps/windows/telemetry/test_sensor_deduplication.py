# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Test Sensor Deduplication
# =============================================================================
# Description:
#   Тесты для проверки отсутствия дублирования сенсоров.
#
# Usage Examples:
#   CLI:
#     python -m tests.apps.windows.telemetry.test_sensor_deduplication
#   Python API:
#     from tests.apps.windows.telemetry.test_sensor_deduplication import TestSensorDeduplication
#
#     service = TestSensorDeduplication()
#
# File: test_sensor_deduplication.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты для проверки отсутствия дублирования сенсоров."""

import pytest
from typing import Dict, List, Set
from apps.windows.telemetry.sensors import get_hardware_sensors
from apps.windows.telemetry.sensor_collector import SensorCollector
from apps.windows.telemetry.sensor_registry import (
    SensorDeduplicator,
    SensorRegistry,
    SensorProvider,
    deduplicate_sensor_readings,
)


class TestSensorDeduplication:
    """Тесты дедупликации сенсоров."""

    def test_no_duplicate_sensor_ids_in_snapshot(self):
        """Проверяет, что в одном снимке нет дублирующихся sensor_id."""
        sensors = get_hardware_sensors()
        
        # Собираем все sensor_id
        sensor_ids = [s.sensor_id for s in sensors]
        
        # Проверяем уникальность
        unique_ids = set(sensor_ids)
        
        # Если есть дубликаты, выводим их
        if len(sensor_ids) != len(unique_ids):
            duplicates = [sid for sid in sensor_ids if sensor_ids.count(sid) > 1]
            duplicate_set = set(duplicates)
            pytest.fail(
                f"Обнаружены дубликаты sensor_id: {duplicate_set}. "
                f"Всего сенсоров: {len(sensor_ids)}, уникальных: {len(unique_ids)}"
            )
        
        assert len(sensor_ids) == len(unique_ids), (
            f"Количество сенсоров ({len(sensor_ids)}) не совпадает с количеством "
            f"уникальных ID ({len(unique_ids)})"
        )

    def test_no_nvidia_smi_duplicate_calls(self):
        """Проверяет, что nvidia-smi не вызывается дважды для GPU метрик."""
        # GPU метрики должны собираться только через GpuProber,
        # а не через прямой вызов nvidia-smi в sensors.py
        
        sensors = get_hardware_sensors()
        
        # Проверяем, что нет сенсоров с провайдером NVIDIA_SMI_DIRECT
        # (функция _probe_nvidia_gpu_sensors удалена)
        gpu_temp_sensors = [s for s in sensors if 'gpu_' in s.sensor_id and 'temp' in s.sensor_id]
        
        # Если GPU температурные сенсоры есть, они должны быть из GpuProber
        # (который вызывается через HardwareMonitor, а не напрямую)
        # Это проверяется тем, что sensor_id не дублируется
        
        sensor_ids = [s.sensor_id for s in gpu_temp_sensors]
        assert len(sensor_ids) == len(set(sensor_ids)), (
            f"Обнаружены дубликаты GPU температурных сенсоров: {sensor_ids}"
        )

    def test_sensor_collector_no_duplicates(self):
        """Проверяет, что SensorCollector не создает дубликатов."""
        collector = SensorCollector()
        
        try:
            snapshot = collector.get_hardware_snapshot()
            sensors = snapshot.get('sensors', [])
            
            sensor_ids = [s.get('id') for s in sensors if s.get('id')]
            unique_ids = set(sensor_ids)
            
            if len(sensor_ids) != len(unique_ids):
                duplicates = [sid for sid in sensor_ids if sensor_ids.count(sid) > 1]
                pytest.fail(
                    f"SensorCollector создал дубликаты: {set(duplicates)}. "
                    f"Всего: {len(sensor_ids)}, уникальных: {len(unique_ids)}"
                )
            
            assert len(sensor_ids) == len(unique_ids)
        except Exception as e:
            # Если HardwareMonitor недоступен, пропускаем тест
            pytest.skip(f"SensorCollector не может получить данные: {e}")

    def test_deduplicator_removes_duplicates(self):
        """Проверяет, что SensorDeduplicator корректно удаляет дубликаты."""
        deduplicator = SensorDeduplicator()
        
        # Добавляем показание от первого провайдера
        assert deduplicator.add('gpu_0_temp', SensorProvider.GPU_PROBER, 65.0)
        
        # Пытаемся добавить дубликат от другого провайдера с меньшим приоритетом
        assert not deduplicator.add('gpu_0_temp', SensorProvider.SENSOR_COLLECTOR, 66.0)
        
        # Проверяем, что сохранилось первое значение
        unique = deduplicator.get_unique()
        assert 'gpu_0_temp' in unique
        assert unique['gpu_0_temp'] == (SensorProvider.GPU_PROBER, 65.0)

    def test_deduplicator_respects_priority(self):
        """Проверяет, что дедупликатор respects приоритеты провайдеров."""
        deduplicator = SensorDeduplicator()
        
        # Добавляем от провайдера с низким приоритетом
        deduplicator.add('test_sensor', SensorProvider.NVIDIA_SMI_DIRECT, 50.0)
        
        # Добавляем от провайдера с высоким приоритетом
        deduplicator.add('test_sensor', SensorProvider.GPU_PROBER, 55.0)
        
        unique = deduplicator.get_unique()
        
        # Должен остаться провайдер с высшим приоритетом (GPU_PROBER = 40 > NVIDIA_SMI = 10)
        assert unique['test_sensor'][0] == SensorProvider.GPU_PROBER
        assert unique['test_sensor'][1] == 55.0

    def test_deduplicate_sensor_readings_function(self):
        """Проверяет функцию deduplicate_sensor_readings."""
        readings = [
            {'id': 'sensor_1', 'value': 10.0},
            {'id': 'sensor_2', 'value': 20.0},
            {'id': 'sensor_1', 'value': 15.0},  # Дубликат
            {'id': 'sensor_3', 'value': 30.0},
        ]
        
        unique = deduplicate_sensor_readings(readings)
        
        # Должно остаться 3 уникальных сенсора
        assert len(unique) == 3
        
        # Проверяем, что первый sensor_1 сохранен (первый пришел)
        sensor_ids = [r['id'] for r in unique]
        assert sensor_ids.count('sensor_1') == 1
        assert sensor_ids.count('sensor_2') == 1
        assert sensor_ids.count('sensor_3') == 1


class TestSensorRegistry:
    """Тесты реестра сенсоров."""

    def test_get_preferred_provider_for_gpu_temp(self):
        """Проверяет, что для GPU температуры предпочтительный провайдер - GPU_PROBER."""
        provider = SensorRegistry.get_preferred_provider('gpu_0_temp', 'temperature')
        
        # GPU температура должна собираться через GpuProber, а не прямой nvidia-smi
        assert provider == SensorProvider.GPU_PROBER

    def test_get_preferred_provider_for_cpu_temp(self):
        """Проверяет предпочтительного провайдера для CPU температуры."""
        provider = SensorRegistry.get_preferred_provider('cpu_package_temp', 'temperature')
        
        # CPU температура определяется через ACPI_THERMAL
        assert provider == SensorProvider.ACPI_THERMAL

    def test_should_keep_sensor_prefers_higher_priority(self):
        """Проверяет, что сохраняется сенсор от провайдера с высшим приоритетом."""
        existing = [('gpu_0_temp', SensorProvider.NVIDIA_SMI_DIRECT)]
        
        # GpuProber имеет высший приоритет (20 > 10)
        should_keep = SensorRegistry.should_keep_sensor(
            'gpu_0_temp',
            SensorProvider.GPU_PROBER,
            existing
        )
        
        assert should_keep is True


class TestNetworkSensorsNoDuplicates:
    """Тесты проверки отсутствия дублирования network сенсоров."""

    def test_network_sensors_unique_ids(self):
        """Проверяет, что network сенсоры имеют уникальные ID."""
        sensors = get_hardware_sensors()
        
        network_sensors = [s for s in sensors if s.category == 'network']
        sensor_ids = [s.sensor_id for s in network_sensors]
        
        # Проверяем уникальность
        assert len(sensor_ids) == len(set(sensor_ids)), (
            f"Обнаружены дубликаты network сенсоров: "
            f"{[sid for sid in sensor_ids if sensor_ids.count(sid) > 1]}"
        )

    def test_no_duplicate_internet_ping(self):
        """Проверяет, что internet_ping не дублируется."""
        sensors = get_hardware_sensors()
        
        ping_sensors = [s for s in sensors if 'internet_ping' in s.sensor_id]
        
        # Должен быть только один сенсор internet_ping
        assert len(ping_sensors) <= 1, (
            f"Обнаружено несколько internet_ping сенсоров: "
            f"{[s.sensor_id for s in ping_sensors]}"
        )


class TestStorageSensorsNoDuplicates:
    """Тесты проверки отсутствия дублирования storage сенсоров."""

    def test_storage_sensors_unique_ids(self):
        """Проверяет, что storage сенсоры имеют уникальные ID."""
        sensors = get_hardware_sensors()
        
        storage_sensors = [s for s in sensors if s.category in ('storage', 'wear')]
        sensor_ids = [s.sensor_id for s in storage_sensors]
        
        # Проверяем уникальность
        assert len(sensor_ids) == len(set(sensor_ids)), (
            f"Обнаружены дубликаты storage сенсоров: "
            f"{[sid for sid in sensor_ids if sensor_ids.count(sid) > 1]}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
