# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Hardware Audit And History
# =============================================================================
# Description:
#   Unit and integration tests for hardware audit, driver currency, and history archives.
#
# Usage Examples:
#   Python API:
#     from tests.test_hardware_audit_and_history import TestHardwareAuditor
#
#     service = TestHardwareAuditor()
#
# File: test_hardware_audit_and_history.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 05:32:00
# =============================================================================

from __future__ import annotations
"""Unit and integration tests for hardware audit, driver currency, and history archives."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from apps.windows.telemetry.win32_ffi.setupapi import PnPDeviceInfo
from apps.windows.telemetry import DriverInfo, HardwareArchiveEntry, HardwareAuditor, HardwareAuditReport, HardwareChangeItem, HardwareDeviceAudit, HardwareHistoryManager, HardwareSensor, SystemCollector


class TestHardwareAuditor:
    """Набор тестов для движка аудита оборудования и драйверов."""

    def test_parse_wmi_and_iso_dates(self):
        """Проверка корректного парсинга дат WMI и строковых форматов."""
        auditor = HardwareAuditor()
        dt1 = auditor._parse_wmi_date('20231114000000.000000+000')
        assert dt1 is not None
        assert dt1.year == 2023
        assert dt1.month == 11
        assert dt1.day == 14
        dt2 = auditor._parse_wmi_date('2024-05-20')
        assert dt2 is not None
        assert dt2.year == 2024
        assert dt2.month == 5
        assert dt2.day == 20
        dt3 = auditor._parse_wmi_date('15.08.2022')
        assert dt3 is not None
        assert dt3.year == 2022
        assert dt3.month == 8
        assert dt3.day == 15
        assert auditor._parse_wmi_date(None) is None
        assert auditor._parse_wmi_date('') is None

    def test_evaluate_driver_currency(self):
        """Проверка расчета актуальности драйверов по возрасту и вендору."""
        auditor = HardwareAuditor()
        fresh_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        status, age = auditor._evaluate_driver_currency(fresh_dt, 'NVIDIA', 'Display')
        assert status == 'Актуален'
        assert age is not None
        old_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        status, age = auditor._evaluate_driver_currency(old_dt, 'Realtek', 'Net')
        assert 'Устарел' in status
        ancient_dt = datetime(2015, 1, 1, tzinfo=timezone.utc)
        status, age = auditor._evaluate_driver_currency(ancient_dt, 'Generic', 'Display')
        assert 'Критически устарел' in status
        status_ms, _ = auditor._evaluate_driver_currency(ancient_dt, 'Microsoft', 'System')
        assert status_ms == 'Стандартный системный драйвер'

    def test_bind_sensors_to_device(self):
        """Проверка правильной привязки сенсоров к компонентам."""
        auditor = HardwareAuditor()
        sensors = [HardwareSensor(sensor_id='gpu_0_temp', name='NVIDIA RTX Core Temp', category='temperature', value=45.0, unit='°C'), HardwareSensor(sensor_id='gpu_0_fan', name='NVIDIA Fan Speed', category='fan', value=30.0, unit='%'), HardwareSensor(sensor_id='acpi_thermal_0', name='ACPI Thermal Zone', category='temperature', value=40.0, unit='°C'), HardwareSensor(sensor_id='net_eth0_bytes_recv', name='Network Bytes Received', category='network', value=100.0, unit='B')]
        gpu_dev = HardwareDeviceAudit(device_id='PCI/VEN_10DE&DEV_2484', name='NVIDIA GeForce RTX 3070', device_class='Display', manufacturer='NVIDIA')
        matched_gpu = auditor._bind_sensors_to_device(gpu_dev, sensors)
        assert len(matched_gpu) == 2
        assert any((s.sensor_id == 'gpu_0_temp' for s in matched_gpu))
        assert any((s.sensor_id == 'gpu_0_fan' for s in matched_gpu))
        cpu_dev = HardwareDeviceAudit(device_id='ROOT/CPU/0000', name='Intel Core i7-12700K', device_class='Processor', manufacturer='Intel')
        matched_cpu = auditor._bind_sensors_to_device(cpu_dev, sensors)
        assert len(matched_cpu) == 1
        assert matched_cpu[0].sensor_id == 'acpi_thermal_0'

    def test_audit_hardware_mocked(self):
        """Проверка полного цикла аудита с моками SetupAPI и WMI."""
        mock_setupapi = MagicMock()
        mock_setupapi.get_all_devices.return_value = [PnPDeviceInfo(device_instance_id='PCI/VEN_10DE&DEV_2484/0001', friendly_name='NVIDIA GeForce RTX 3070', hardware_id='PCI/VEN_10DE&DEV_2484', device_class='Display', manufacturer='NVIDIA', has_problem=False, status_code=0, problem_code=0), PnPDeviceInfo(device_instance_id='USB/VID_046D&PID_C52B/0002', friendly_name='Logitech USB Receiver', hardware_id='USB/VID_046D&PID_C52B', device_class='HIDClass', manufacturer='Logitech', has_problem=True, status_code=1024, problem_code=10)]
        auditor = HardwareAuditor(setupapi_client=mock_setupapi)
        with patch.object(auditor, '_get_drivers_from_wmi', return_value={'PCI/VEN_10DE&DEV_2484/0001': {'name': 'NVIDIA Driver', 'driver_version': '560.94', 'driver_date_raw': '20260215000000.000000+000', 'provider': 'NVIDIA', 'inf_name': 'oem42.inf', 'is_signed': True}}):
            report = auditor.audit_hardware(sensors=[])
            assert isinstance(report, HardwareAuditReport)
            assert report.devices_count == 2
            assert report.problem_devices_count == 1
            assert report.devices[0].driver is not None
            assert report.devices[0].driver.driver_version == '560.94'
            assert report.devices[0].driver.currency_status == 'Актуален'
            assert report.devices[1].status == 'Problem'
            assert report.devices[1].problem_code == 10

    def test_device_install_date_fallback_to_database(self, tmp_path: Path):
        """Проверка логики: если дата не найдена в реестре, сверяем с БД (пишем сегодняшнюю дату или возвращаем существующую)."""
        from apps.windows.telemetry.sqlite import TelemetryStorage
        db_file = tmp_path / 'test_telemetry.db'
        storage = TelemetryStorage(db_path=db_file, auto_flush=False)
        try:
            auditor = HardwareAuditor(storage=storage)

            dev_id = r'HID\VID_046D&PID_C52B&MI_01&COL04\8&33FCB7EE&0&0003'
            dev_name = 'HID-compliant vendor-defined device'

            # в) Такого устройства нет в БД -> записываем с текущей датой
            with patch('os.name', 'posix'):
                date1 = auditor._get_device_install_date_registry(dev_id, dev_name, 'HIDClass')
                assert date1 is not None
                today_prefix = datetime.now(timezone.utc).strftime('%d.%m.%Y')
                assert date1.startswith(today_prefix)

                # Проверяем, что дата действительно записана в БД
                db_date = storage.get_device_install_date(dev_id)
                assert db_date == date1

                # а) Такое устройство уже есть в базе и у него есть дата -> пропускаем запись, возвращаем сохраненную
                date2 = auditor._get_device_install_date_registry(dev_id, dev_name, 'HIDClass')
                assert date2 == date1

            # а) Проверка с предварительно установленной архивной датой
            preset_dev_id = r'USB\VID_1234&PID_5678\0001'
            preset_date = '01.01.2023 12:00'
            storage.get_or_create_device_install_date(
                device_instance_id=preset_dev_id,
                friendly_name='Preset Device',
                device_class='USB',
                default_date=preset_date
            )
            resolved_date = auditor._get_device_install_date_registry(preset_dev_id, 'Preset Device', 'USB')
            assert resolved_date == preset_date

            # б) Такое устройство есть в базе, но у него нет даты (пустая) -> ставим текущую дату в записи в БД
            empty_dev_id = r'USB\VID_9999&PID_0000\0002'
            # Вставляем устройство с пустой датой
            with storage._get_connection() as conn:
                conn.execute(
                    "INSERT INTO device_inventory (device_instance_id, friendly_name, device_class, install_date, created_at, updated_at) VALUES (?, ?, ?, '', 1000.0, 1000.0)",
                    (empty_dev_id, 'Empty Date Device', 'USB')
                )
                conn.commit()

            with patch('os.name', 'posix'):
                filled_date = auditor._get_device_install_date_registry(empty_dev_id, 'Empty Date Device', 'USB')
                assert filled_date is not None
                assert filled_date.startswith(today_prefix)
                # Проверяем, что в БД теперь проставлена дата
                db_filled_date = storage.get_device_install_date(empty_dev_id)
                assert db_filled_date == filled_date
        finally:
            storage.close()


class TestHardwareHistoryAndDiff:
    """Набор тестов для менеджера истории и детектора изменений (Diff Engine)."""

    def test_diff_engine_detects_added_removed_and_modified_drivers(self):
        """Проверка детекции новых, удаленных устройств и обновления драйверов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HardwareHistoryManager(archive_dir=Path(tmpdir))
            base_report = HardwareAuditReport(devices_count=2, devices=[HardwareDeviceAudit(device_id='DEV_GPU_01', name='NVIDIA GPU', device_class='Display', driver=DriverInfo(driver_version='550.00', driver_date='2024-01-01', provider='NVIDIA')), HardwareDeviceAudit(device_id='DEV_AUDIO_01', name='Old Sound Card', device_class='MEDIA')])
            current_report = HardwareAuditReport(devices_count=2, devices=[HardwareDeviceAudit(device_id='DEV_GPU_01', name='NVIDIA GPU', device_class='Display', driver=DriverInfo(driver_version='560.94', driver_date='2024-08-20', provider='NVIDIA')), HardwareDeviceAudit(device_id='DEV_NET_01', name='New Wi-Fi Adapter', device_class='Net', manufacturer='Intel')])
            changes = manager.detect_changes(current_report=current_report, baseline_report=base_report)
            assert len(changes) == 3
            types = {c.change_type for c in changes}
            assert 'added' in types
            assert 'removed' in types
            assert 'driver_updated' in types
            drv_change = next((c for c in changes if c.change_type == 'driver_updated'))
            assert '560.94' in drv_change.description
            added_change = next((c for c in changes if c.change_type == 'added'))
            assert added_change.device_id == 'DEV_NET_01'
            removed_change = next((c for c in changes if c.change_type == 'removed'))
            assert removed_change.device_id == 'DEV_AUDIO_01'

    def test_archive_save_and_history_retrieval(self):
        """Проверка сохранения архива на диск, индексации и чтения истории."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HardwareHistoryManager(archive_dir=Path(tmpdir))
            report1 = HardwareAuditReport(devices_count=1, devices=[HardwareDeviceAudit(device_id='DEV_01', name='Primary Device')])
            entry1 = manager.archive_report(report1)
            assert isinstance(entry1, HardwareArchiveEntry)
            assert entry1.devices_count == 1
            report2 = HardwareAuditReport(devices_count=2, devices=[HardwareDeviceAudit(device_id='DEV_01', name='Primary Device'), HardwareDeviceAudit(device_id='DEV_02', name='Secondary Device')])
            entry2 = manager.archive_report(report2)
            assert entry2.changes_count == 1
            assert len(entry2.report.changes_since_last_archive) == 1
            history = manager.get_history()
            assert len(history) == 2
            assert history[0]['archive_id'] == entry2.archive_id
            timeline = manager.get_change_timeline()
            assert len(timeline) == 1
            assert timeline[0].change_type == 'added'
            assert timeline[0].device_id == 'DEV_02'
            loaded = manager.get_archive_by_id(entry1.archive_id)
            assert loaded is not None
            assert loaded.archive_id == entry1.archive_id

class TestSystemCollectorAuditIntegration:
    """Тестирование интеграции аудита оборудования с SystemCollector."""

    @pytest.mark.asyncio
    async def test_get_snapshot_does_not_trigger_live_hardware_audit(self):
        """Проверка того, что при вызове get_snapshot не происходит живого сканирования оборудования через auditor.audit_hardware."""
        mock_auditor = MagicMock()
        mock_auditor.audit_hardware.side_effect = RuntimeError("Живой аудит оборудования не должен вызываться при запросе снимка!")
        collector = SystemCollector(auditor=mock_auditor)
        snapshot = await collector.get_snapshot(process_limit=5)
        assert snapshot is not None
        mock_auditor.audit_hardware.assert_not_called()

    def test_collector_hardware_audit_methods(self):
        """Проверка вызовов методов аудита и архивации в SystemCollector."""
        collector = SystemCollector()
        report = collector.get_hardware_audit()
        assert isinstance(report, HardwareAuditReport)
        assert report.devices_count >= 1
        entry = collector.archive_hardware_state(auto_diff=True)
        assert isinstance(entry, HardwareArchiveEntry)
        assert entry.archive_id.startswith('hw_')
        history = collector.get_hardware_history(limit=5)
        assert isinstance(history, list)
        assert len(history) >= 1