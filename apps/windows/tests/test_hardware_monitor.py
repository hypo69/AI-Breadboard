# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Hardware Monitor
# =============================================================================
# Description:
#   Unit-тесты для модуля HardwareMonitor.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.tests.test_hardware_monitor
#   Python API:
#     from apps.windows.tests.test_hardware_monitor import TestHardwareMonitor
#
#     service = TestHardwareMonitor()
#
# File: test_hardware_monitor.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Unit-тесты для модуля HardwareMonitor."""

import unittest
from apps.windows.hardware.hardware_monitor import BatteryMetrics, CpuMetrics, DiskIoMetrics, DiskPartitionMetrics, GpuMetrics, HardwareMonitor, HardwareSnapshot, MemoryMetrics, NetworkMetrics, SensorMetrics, StorageMetrics

class TestHardwareMonitor(unittest.TestCase):
    """Тестирование функциональности HardwareMonitor."""

    def setUp(self) -> None:
        """Инициализация экземпляра монитора перед каждым тестом."""
        self.monitor = HardwareMonitor()

    def test_cpu_metrics(self) -> None:
        """Проверка сбора метрик CPU."""
        cpu = self.monitor.get_cpu_metrics()
        self.assertIsInstance(cpu, CpuMetrics)
        self.assertIsInstance(cpu.model_name, str)
        self.assertGreaterEqual(cpu.physical_cores, 1)
        self.assertGreaterEqual(cpu.logical_cores, 1)
        self.assertGreaterEqual(cpu.utilization_pct, 0.0)
        self.assertLessEqual(cpu.utilization_pct, 100.0)
        self.assertIsInstance(cpu.per_core_pct, list)

    def test_memory_metrics(self) -> None:
        """Проверка сбора метрик оперативной памяти и Swap."""
        mem = self.monitor.get_memory_metrics()
        self.assertIsInstance(mem, MemoryMetrics)
        self.assertGreater(mem.total_gb, 0.0)
        self.assertGreaterEqual(mem.used_gb, 0.0)
        self.assertGreaterEqual(mem.free_gb, 0.0)
        self.assertGreaterEqual(mem.utilization_pct, 0.0)
        self.assertLessEqual(mem.utilization_pct, 100.0)
        self.assertGreaterEqual(mem.swap_total_gb, 0.0)

    def test_gpu_metrics(self) -> None:
        """Проверка сбора метрик GPU."""
        gpus = self.monitor.get_gpu_metrics()
        self.assertIsInstance(gpus, list)
        for g in gpus:
            self.assertIsInstance(g, GpuMetrics)
            self.assertIsNotNone(g.name)
            self.assertIsNotNone(g.vendor)

    def test_storage_metrics(self) -> None:
        """Проверка сбора метрик дисков и накопителей."""
        storage = self.monitor.get_storage_metrics(include_smart=False)
        self.assertIsInstance(storage, StorageMetrics)
        self.assertIsInstance(storage.partitions, list)
        if storage.partitions:
            p = storage.partitions[0]
            self.assertIsInstance(p, DiskPartitionMetrics)
            self.assertGreater(p.total_gb, 0.0)
            self.assertGreaterEqual(p.utilization_pct, 0.0)

    def test_sensor_metrics(self) -> None:
        """Проверка сбора метрик датчиков."""
        sensors = self.monitor.get_sensor_metrics()
        self.assertIsInstance(sensors, list)
        for s in sensors:
            self.assertIsInstance(s, SensorMetrics)
            self.assertIsNotNone(s.sensor_id)
            self.assertIsNotNone(s.name)

    def test_network_metrics(self) -> None:
        """Проверка сбора сетевых метрик."""
        net = self.monitor.get_network_metrics()
        self.assertIsInstance(net, NetworkMetrics)
        self.assertGreaterEqual(net.bytes_sent_sec, 0.0)
        self.assertGreaterEqual(net.bytes_recv_sec, 0.0)
        self.assertGreaterEqual(net.active_connections_count, 0)

    def test_battery_metrics(self) -> None:
        """Проверка сбора метрик батареи."""
        bat = self.monitor.get_battery_metrics()
        self.assertIsInstance(bat, BatteryMetrics)

    def test_get_snapshot_and_dict(self) -> None:
        """Проверка генерации снимка и сериализации в dict."""
        snap = self.monitor.get_snapshot(include_smart=False)
        self.assertIsInstance(snap, HardwareSnapshot)
        self.assertIsNotNone(snap.timestamp)
        self.assertIsInstance(snap.cpu, CpuMetrics)
        self.assertIsInstance(snap.memory, MemoryMetrics)
        self.assertIsInstance(snap.storage, StorageMetrics)
        self.assertIsInstance(snap.network, NetworkMetrics)
        d = snap.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn('cpu', d)
        self.assertIn('memory', d)
        self.assertIn('storage', d)
        self.assertIn('network', d)
        self.assertIn('status_summary', d)

    def test_get_summary_thresholds(self) -> None:
        """Проверка работы логики расчета сводного здоровья."""
        summary = self.monitor.get_summary()
        self.assertIsInstance(summary, dict)
        self.assertIn('status', summary)
        self.assertIn(summary['status'], ['HEALTHY', 'WARNING', 'CRITICAL'])
        self.assertIn('metrics', summary)
if __name__ == '__main__':
    unittest.main()