# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Storage Usage
# =============================================================================
# Description:
#   Тесты для многоуровневой дисковой телеметрии, SMART Lifetime и I/O процессов.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_storage_usage import test_format_bytes
#
#     res = test_format_bytes()
#
# File: test_storage_usage.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 07:00:00
# =============================================================================

from __future__ import annotations
"""Тесты для многоуровневой дисковой телеметрии, SMART Lifetime и I/O процессов."""

import time
from unittest.mock import MagicMock, patch
import pytest

from apps.windows.telemetry.storage_usage import WindowsStorageUsageCollector, _format_bytes
from apps.windows.sdk.modules.storage_manager.core.raw_disk_io import WindowsRawDiskIO
from apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor import StorageDiskHealthInfo, WindowsStorageSensor
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.telemetry.models import AppDiskUsageItem, DiskUsagePeriodReport, PhysicalDiskHealth


def test_format_bytes() -> None:
    """Тестирование вспомогательной функции форматирования байт."""
    assert _format_bytes(0) == '0 B'
    assert _format_bytes(1023) == '1023 B'
    assert _format_bytes(1024) == '1.00 KB'
    assert _format_bytes(1024 * 1024) == '1.00 MB'
    assert _format_bytes(1024 * 1024 * 1024 * 2.5) == '2.50 GB'
    assert _format_bytes(1024 ** 4 * 1.5) == '1.50 TB'


def test_storage_models() -> None:
    """Тестирование создания и валидации моделей PhysicalDiskHealth, AppDiskUsageItem и DiskUsagePeriodReport."""
    disk = PhysicalDiskHealth(
        device_id='Disk 0',
        model='Samsung SSD 980 PRO 1TB',
        media_type='SSD',
        size_gb=1000.0,
        health_status='Healthy',
        operational_status='OK',
        temperature_celsius=38.0,
        interface_type='NVMe',
        lifetime_read_bytes=1024 ** 4 * 15,
        lifetime_write_bytes=1024 ** 4 * 8,
        lifetime_read_tb=15.0,
        lifetime_write_tb=8.0,
        power_on_hours=4200,
        wear_percentage=2.0,
    )
    assert disk.lifetime_read_tb == 15.0
    assert disk.lifetime_write_tb == 8.0
    assert disk.power_on_hours == 4200
    assert disk.wear_percentage == 2.0

    app_item = AppDiskUsageItem(
        process_name='python.exe',
        pid=1234,
        read_bytes=1024 * 1024 * 100,
        write_bytes=1024 * 1024 * 500,
        total_bytes=1024 * 1024 * 600,
        read_formatted='100.00 MB',
        write_formatted='500.00 MB',
        share_percent=75.0,
    )
    assert app_item.process_name == 'python.exe'
    assert app_item.write_formatted == '500.00 MB'
    assert app_item.share_percent == 75.0

    report = DiskUsagePeriodReport(
        period_minutes=60,
        total_read_bytes=1024 * 1024 * 200,
        total_write_bytes=1024 * 1024 * 800,
        total_read_formatted='200.00 MB',
        total_write_formatted='800.00 MB',
        total_formatted='1000.00 MB',
        top_writers=[app_item],
        top_readers=[app_item],
        physical_disks=[disk],
        smart_delta_write_bytes=1024 * 1024 * 850,
        smart_delta_write_formatted='850.00 MB',
        io_difference_bytes=1024 * 1024 * 50,
        summary_text='Test Summary',
    )
    assert report.period_minutes == 60
    assert len(report.top_writers) == 1
    assert report.top_writers[0].process_name == 'python.exe'
    assert report.smart_delta_write_formatted == '850.00 MB'


def test_storage_usage_collector_physical_disks() -> None:
    """Тестирование получения физических дисков через WindowsStorageUsageCollector."""
    mock_sensor = MagicMock(spec=WindowsStorageSensor)
    mock_sensor.get_physical_disks.return_value = [
        StorageDiskHealthInfo(
            device_id='Disk0',
            friendly_name='NVMe Samsung 990 PRO',
            model='Samsung SSD 990 PRO 2TB',
            serial_number='S6B0NS0W123456',
            bus_type='NVMe',
            media_type='SSD',
            size_gb=2000.0,
            health_status='Healthy',
            operational_status='OK',
            temperature_c=41.0,
            wear_percentage=1.0,
            power_on_hours=1200,
            lifetime_read_bytes=1024 ** 4 * 25,
            lifetime_write_bytes=1024 ** 4 * 12,
            lifetime_read_tb=25.0,
            lifetime_write_tb=12.0,
        )
    ]
    mock_raw_io = MagicMock(spec=WindowsRawDiskIO)
    mock_raw_io.list_physical_disks.return_value = [
        {
            'disk_id': 0,
            'device_path': r'\\.\PHYSICALDRIVE0',
            'product': 'Samsung SSD 990 PRO 2TB',
            'bus_type': 'NVMe',
            'smart_health': {
                'temperature_c': 41.0,
                'percentage_used': 1.0,
                'power_on_hours': 1200,
                'data_units_read_tb': 25.0,
                'data_units_written_tb': 12.0,
                'raw_nvme_available': True,
            },
        }
    ]
    collector = WindowsStorageUsageCollector(raw_io=mock_raw_io, storage_sensor=mock_sensor)
    disks = collector.get_physical_disks()
    assert len(disks) == 1
    assert disks[0].model == 'Samsung SSD 990 PRO 2TB'
    assert disks[0].lifetime_read_tb == 25.0
    assert disks[0].lifetime_write_tb == 12.0
    assert disks[0].power_on_hours == 1200


def test_storage_usage_collector_period_report() -> None:
    """Тестирование генерации отчета об использовании диска за период."""
    mock_sensor = MagicMock(spec=WindowsStorageSensor)
    mock_sensor.get_physical_disks.return_value = [
        StorageDiskHealthInfo(
            device_id='Disk0',
            friendly_name='NVMe Micron 3400',
            model='Micron 3400 NVMe 1TB',
            serial_number='221437190ABC',
            bus_type='NVMe',
            media_type='SSD',
            size_gb=1024.0,
            health_status='Healthy',
            operational_status='OK',
            temperature_c=36.0,
            wear_percentage=3.0,
            power_on_hours=5000,
            lifetime_read_bytes=1024 ** 4 * 30,
            lifetime_write_bytes=1024 ** 4 * 18,
            lifetime_read_tb=30.0,
            lifetime_write_tb=18.0,
        )
    ]
    mock_raw_io = MagicMock(spec=WindowsRawDiskIO)
    mock_raw_io.list_physical_disks.return_value = [
        {
            'disk_id': 0,
            'device_path': r'\\.\PHYSICALDRIVE0',
            'product': 'Micron 3400 NVMe 1TB',
            'bus_type': 'NVMe',
            'smart_health': {
                'temperature_c': 36.0,
                'percentage_used': 3.0,
                'power_on_hours': 5000,
                'data_units_read_tb': 30.0,
                'data_units_written_tb': 18.0,
                'raw_nvme_available': True,
            },
        }
    ]
    collector = WindowsStorageUsageCollector(raw_io=mock_raw_io, storage_sensor=mock_sensor)

    # Имитируем опрос процессов
    with patch.object(collector, 'poll_process_io_deltas') as mock_proc:
        mock_proc.return_value = {
            'python.exe': {'pid': 1001, 'read_bytes': 1024 ** 3 * 2, 'write_bytes': 1024 ** 3 * 5},
            'chrome.exe': {'pid': 2002, 'read_bytes': 1024 ** 3 * 3, 'write_bytes': 1024 ** 3 * 1},
        }
        report = collector.get_disk_usage_period_report(period_minutes=60)

        assert report.period_minutes == 60
        assert len(report.top_writers) == 2
        assert report.top_writers[0].process_name == 'python.exe'
        assert report.top_writers[0].share_percent > 80.0
        assert len(report.top_readers) == 2
        assert report.top_readers[0].process_name == 'chrome.exe'
        assert 'python.exe' in report.summary_text
        assert report.physical_disks[0].model == 'Micron 3400 NVMe 1TB'


def test_system_collector_disk_usage_integration() -> None:
    """Тестирование вызова get_disk_usage_report через SystemCollector."""
    collector = SystemCollector()
    report = collector.get_disk_usage_report(period_minutes=1440)
    assert isinstance(report, DiskUsagePeriodReport)
    assert report.period_minutes == 1440
    assert report.summary_text != ''
    assert len(report.physical_disks) >= 1
