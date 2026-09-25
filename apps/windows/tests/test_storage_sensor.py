# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Windows Storage Sensor
# =============================================================================
# Description:
#   Тесты для модуля нативных сенсоров дисков WindowsStorageSensor, нормализации
#   снимков, интеграции со SmartProber, NativeWinProvider и StorageCollector.
#
# File: test_storage_sensor.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модульные тесты сенсора накопителей Windows."""

import unittest
from unittest.mock import MagicMock, patch

from apps.windows.core.modules.storage_collector import StorageCollector
from apps.windows.hardware.providers.native_win_provider import NativeWinProvider
from apps.windows.storage_sensors.windows_storage_sensor import (
    StorageDiskHealthInfo,
    WindowsStorageSensor,
    collect_storage_snapshot,
)


class TestWindowsStorageSensor(unittest.TestCase):
    """Набор тестов для сенсора накопителей Windows."""

    def setUp(self) -> None:
        """Подготовка тестовых фикстур."""
        self.sensor = WindowsStorageSensor(timeout_sec=5, ttl_sec=1.0)
        self.sample_raw_data = {
            "physical_storage": [
                {
                    "DeviceId": "0",
                    "FriendlyName": "Samsung SSD 980 PRO 1TB",
                    "Model": "Samsung SSD 980 PRO 1TB",
                    "SerialNumber": "S5GXNF0R123456",
                    "BusType": 17,  # NVMe
                    "MediaType": 4,  # SSD
                    "Size": 1000204886016,
                    "HealthStatus": 0,  # Healthy
                    "OperationalStatus": "OK",
                }
            ],
            "storage_reliability": [
                {
                    "DeviceId": "0",
                    "Temperature": 42.0,
                    "Wear": 3.0,
                    "PowerOnHours": 4500,
                    "ReadErrorsTotal": 0,
                    "WriteErrorsTotal": 0,
                    "ReadLatencyMax": 15.0,
                    "WriteLatencyMax": 20.0,
                }
            ],
            "physical_disks": [
                {
                    "DeviceID": "\\\\.\\PHYSICALDRIVE0",
                    "Model": "Samsung SSD 980 PRO 1TB",
                    "SerialNumber": "S5GXNF0R123456",
                    "Size": 1000204886016,
                    "Status": "OK",
                    "InterfaceType": "NVMe",
                }
            ],
            "event_log": [],
            "performance_counters": [],
        }

    def test_normalize_snapshot_structure(self) -> None:
        """Проверка структуры нормализованного снимка."""
        snapshot = self.sensor.normalize_snapshot(self.sample_raw_data)
        self.assertIn("schema_version", snapshot)
        self.assertIn("platform", snapshot)
        self.assertIn("sources", snapshot)
        self.assertIn("summary", snapshot)

        self.assertEqual(snapshot["summary"]["storage_disk_count"], 1)
        self.assertEqual(snapshot["summary"]["reliability_counter_count"], 1)

    def test_get_physical_disks_from_msft_storage(self) -> None:
        """Проверка парсинга физических дисков MSFT_PhysicalDisk с надежностью."""
        with patch.object(self.sensor, "collect_snapshot") as mock_collect:
            mock_collect.return_value = self.sensor.normalize_snapshot(self.sample_raw_data)
            disks = self.sensor.get_physical_disks()

            self.assertEqual(len(disks), 1)
            disk = disks[0]
            self.assertIsInstance(disk, StorageDiskHealthInfo)
            self.assertEqual(disk.model, "Samsung SSD 980 PRO 1TB")
            self.assertEqual(disk.bus_type, "NVMe")
            self.assertEqual(disk.media_type, "SSD")
            self.assertEqual(disk.health_status, "Healthy")
            self.assertEqual(disk.temperature_c, 42.0)
            self.assertEqual(disk.wear_percentage, 3.0)
            self.assertEqual(disk.power_on_hours, 4500)

    def test_get_physical_disks_fallback_wmi(self) -> None:
        """Проверка фолбэка на Win32_DiskDrive при отсутствии MSFT_PhysicalDisk."""
        raw_wmi_only = {
            "physical_storage": [],
            "storage_reliability": [],
            "physical_disks": [
                {
                    "DeviceID": "\\\\.\\PHYSICALDRIVE1",
                    "Model": "WDC WD20EZAZ",
                    "SerialNumber": "WD-WCC4N123456",
                    "Size": 2000398934016,
                    "Status": "OK",
                    "InterfaceType": "IDE",
                }
            ],
        }
        with patch.object(self.sensor, "collect_snapshot") as mock_collect:
            mock_collect.return_value = self.sensor.normalize_snapshot(raw_wmi_only)
            disks = self.sensor.get_physical_disks()

            self.assertEqual(len(disks), 1)
            disk = disks[0]
            self.assertEqual(disk.model, "WDC WD20EZAZ")
            self.assertEqual(disk.media_type, "HDD")
            self.assertEqual(disk.health_status, "Healthy")

    def test_native_win_provider_storage_integration(self) -> None:
        """Проверка интеграции StorageDeviceInventory и сенсоров в NativeWinProvider."""
        provider = NativeWinProvider()
        with patch("apps.windows.storage_sensors.windows_storage_sensor.WindowsStorageSensor.get_physical_disks") as mock_disks:
            mock_disks.return_value = [
                StorageDiskHealthInfo(
                    device_id="Disk0",
                    friendly_name="Kingston KC3000 2TB",
                    model="Kingston KC3000 2TB",
                    serial_number="50026B76854321",
                    bus_type="NVMe",
                    media_type="SSD",
                    size_gb=1907.73,
                    health_status="Healthy",
                    operational_status="OK",
                    temperature_c=45.0,
                    wear_percentage=2.0,
                    power_on_hours=3200,
                )
            ]
            inv = provider.probe_inventory()
            self.assertIsNotNone(inv)
            self.assertIsNotNone(inv.storage)
            self.assertTrue(len(inv.storage.devices) >= 1)
            dev = inv.storage.devices[0]
            self.assertEqual(dev.model, "Kingston KC3000 2TB")
            self.assertEqual(dev.interface_type, "NVMe")
            self.assertEqual(dev.health_pct, 98.0)

            sensors = provider.probe_sensors()
            self.assertIsNotNone(sensors)
            temp_sensors = [s for s in sensors.sensors if s.hardware_type == "Storage"]
            self.assertTrue(len(temp_sensors) >= 1)
            self.assertEqual(temp_sensors[0].value, 45.0)

    def test_storage_collector_audit_findings(self) -> None:
        """Проверка формирования находок аудита StorageCollector при сбое диска."""
        collector = StorageCollector()
        with patch("apps.windows.storage_sensors.windows_storage_sensor.WindowsStorageSensor.get_physical_disks") as mock_disks:
            mock_disks.return_value = [
                StorageDiskHealthInfo(
                    device_id="Disk1",
                    friendly_name="Failing HDD Seagate 2TB",
                    model="Seagate ST2000DM008",
                    serial_number="W9A12345",
                    bus_type="SATA",
                    media_type="HDD",
                    size_gb=1863.0,
                    health_status="Unhealthy",
                    operational_status="Error",
                    temperature_c=55.0,
                    wear_percentage=98.0,
                    power_on_hours=55000,
                )
            ]
            audit = collector.collect()
            self.assertIn(audit.status, ("critical", "warning"))
            self.assertTrue(any("Отказ" in f.title or "отказ" in f.title or "здоровь" in f.title for f in audit.findings))


if __name__ == "__main__":
    unittest.main()
