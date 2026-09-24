# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware Audit, Drivers, Sensors, and History Unit Tests
# =============================================================================
# Description:
#   Комплексные модульные и интеграционные тесты для аудита оборудования,
#   параметров драйверов, актуальности, привязки сенсоров, истории архивов
#   и детектора изменений железа (Diff Engine).
#
# File: test_hardware_audit_and_history.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit and integration tests for hardware audit, driver currency, and history archives."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.setupapi import PnPDeviceInfo
from apps.windows.telemetry import (
    DriverInfo,
    HardwareArchiveEntry,
    HardwareAuditor,
    HardwareAuditReport,
    HardwareChangeItem,
    HardwareDeviceAudit,
    HardwareHistoryManager,
    HardwareSensor,
    SystemCollector,
)
from src.api.router_system import init_router


class TestHardwareAuditor:
    """Набор тестов для движка аудита оборудования и драйверов."""

    def test_parse_wmi_and_iso_dates(self):
        """Проверка корректного парсинга дат WMI и строковых форматов."""
        auditor = HardwareAuditor()

        # WMI format
        dt1 = auditor._parse_wmi_date("20231114000000.000000+000")
        assert dt1 is not None
        assert dt1.year == 2023
        assert dt1.month == 11
        assert dt1.day == 14

        # ISO format
        dt2 = auditor._parse_wmi_date("2024-05-20")
        assert dt2 is not None
        assert dt2.year == 2024
        assert dt2.month == 5
        assert dt2.day == 20

        # Russian DD.MM.YYYY
        dt3 = auditor._parse_wmi_date("15.08.2022")
        assert dt3 is not None
        assert dt3.year == 2022
        assert dt3.month == 8
        assert dt3.day == 15

        # Invalid/Empty
        assert auditor._parse_wmi_date(None) is None
        assert auditor._parse_wmi_date("") is None

    def test_evaluate_driver_currency(self):
        """Проверка расчета актуальности драйверов по возрасту и вендору."""
        auditor = HardwareAuditor()

        # Свежий драйвер (< 2 лет)
        fresh_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        status, age = auditor._evaluate_driver_currency(fresh_dt, "NVIDIA", "Display")
        assert status == "Актуален"
        assert age is not None

        # Устаревший драйвер (> 2 лет, но < 5 лет)
        old_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        status, age = auditor._evaluate_driver_currency(old_dt, "Realtek", "Net")
        assert "Устарел" in status

        # Критически устаревший (> 5 лет)
        ancient_dt = datetime(2015, 1, 1, tzinfo=timezone.utc)
        status, age = auditor._evaluate_driver_currency(ancient_dt, "Generic", "Display")
        assert "Критически устарел" in status

        # Системный inbox Microsoft (> 5 лет)
        status_ms, _ = auditor._evaluate_driver_currency(ancient_dt, "Microsoft", "System")
        assert status_ms == "Стандартный системный драйвер"

    def test_bind_sensors_to_device(self):
        """Проверка правильной привязки сенсоров к компонентам."""
        auditor = HardwareAuditor()

        sensors = [
            HardwareSensor(sensor_id="gpu_0_temp", name="NVIDIA RTX Core Temp", category="temperature", value=45.0, unit="°C"),
            HardwareSensor(sensor_id="gpu_0_fan", name="NVIDIA Fan Speed", category="fan", value=30.0, unit="%"),
            HardwareSensor(sensor_id="acpi_thermal_0", name="ACPI Thermal Zone", category="temperature", value=40.0, unit="°C"),
            HardwareSensor(sensor_id="net_eth0_bytes_recv", name="Network Bytes Received", category="network", value=100.0, unit="B"),
        ]

        gpu_dev = HardwareDeviceAudit(
            device_id="PCI/VEN_10DE&DEV_2484",
            name="NVIDIA GeForce RTX 3070",
            device_class="Display",
            manufacturer="NVIDIA",
        )
        matched_gpu = auditor._bind_sensors_to_device(gpu_dev, sensors)
        assert len(matched_gpu) == 2
        assert any(s.sensor_id == "gpu_0_temp" for s in matched_gpu)
        assert any(s.sensor_id == "gpu_0_fan" for s in matched_gpu)

        cpu_dev = HardwareDeviceAudit(
            device_id="ROOT/CPU/0000",
            name="Intel Core i7-12700K",
            device_class="Processor",
            manufacturer="Intel",
        )
        matched_cpu = auditor._bind_sensors_to_device(cpu_dev, sensors)
        assert len(matched_cpu) == 1
        assert matched_cpu[0].sensor_id == "acpi_thermal_0"

    def test_audit_hardware_mocked(self):
        """Проверка полного цикла аудита с моками SetupAPI и WMI."""
        mock_setupapi = MagicMock()
        mock_setupapi.get_all_devices.return_value = [
            PnPDeviceInfo(
                device_instance_id="PCI/VEN_10DE&DEV_2484/0001",
                friendly_name="NVIDIA GeForce RTX 3070",
                hardware_id="PCI/VEN_10DE&DEV_2484",
                device_class="Display",
                manufacturer="NVIDIA",
                has_problem=False,
                status_code=0,
                problem_code=0,
            ),
            PnPDeviceInfo(
                device_instance_id="USB/VID_046D&PID_C52B/0002",
                friendly_name="Logitech USB Receiver",
                hardware_id="USB/VID_046D&PID_C52B",
                device_class="HIDClass",
                manufacturer="Logitech",
                has_problem=True,
                status_code=0x400,
                problem_code=10,
            ),
        ]

        auditor = HardwareAuditor(setupapi_client=mock_setupapi)
        with patch.object(
            auditor,
            "_get_drivers_from_wmi",
            return_value={
                "PCI/VEN_10DE&DEV_2484/0001": {
                    "name": "NVIDIA Driver",
                    "driver_version": "560.94",
                    "driver_date_raw": "20260215000000.000000+000",
                    "provider": "NVIDIA",
                    "inf_name": "oem42.inf",
                    "is_signed": True,
                }
            },
        ):
            report = auditor.audit_hardware(sensors=[])
            assert isinstance(report, HardwareAuditReport)
            assert report.devices_count == 2
            assert report.problem_devices_count == 1
            assert report.devices[0].driver is not None
            assert report.devices[0].driver.driver_version == "560.94"
            assert report.devices[0].driver.currency_status == "Актуален"
            assert report.devices[1].status == "Problem"
            assert report.devices[1].problem_code == 10


class TestHardwareHistoryAndDiff:
    """Набор тестов для менеджера истории и детектора изменений (Diff Engine)."""

    def test_diff_engine_detects_added_removed_and_modified_drivers(self):
        """Проверка детекции новых, удаленных устройств и обновления драйверов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HardwareHistoryManager(archive_dir=Path(tmpdir))

            base_report = HardwareAuditReport(
                devices_count=2,
                devices=[
                    HardwareDeviceAudit(
                        device_id="DEV_GPU_01",
                        name="NVIDIA GPU",
                        device_class="Display",
                        driver=DriverInfo(driver_version="550.00", driver_date="2024-01-01", provider="NVIDIA"),
                    ),
                    HardwareDeviceAudit(
                        device_id="DEV_AUDIO_01",
                        name="Old Sound Card",
                        device_class="MEDIA",
                    ),
                ],
            )

            current_report = HardwareAuditReport(
                devices_count=2,
                devices=[
                    HardwareDeviceAudit(
                        device_id="DEV_GPU_01",
                        name="NVIDIA GPU",
                        device_class="Display",
                        driver=DriverInfo(driver_version="560.94", driver_date="2024-08-20", provider="NVIDIA"),
                    ),
                    HardwareDeviceAudit(
                        device_id="DEV_NET_01",
                        name="New Wi-Fi Adapter",
                        device_class="Net",
                        manufacturer="Intel",
                    ),
                ],
            )

            changes = manager.detect_changes(current_report=current_report, baseline_report=base_report)
            assert len(changes) == 3

            types = {c.change_type for c in changes}
            assert "added" in types
            assert "removed" in types
            assert "driver_updated" in types

            drv_change = next(c for c in changes if c.change_type == "driver_updated")
            assert "560.94" in drv_change.description

            added_change = next(c for c in changes if c.change_type == "added")
            assert added_change.device_id == "DEV_NET_01"

            removed_change = next(c for c in changes if c.change_type == "removed")
            assert removed_change.device_id == "DEV_AUDIO_01"

    def test_archive_save_and_history_retrieval(self):
        """Проверка сохранения архива на диск, индексации и чтения истории."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HardwareHistoryManager(archive_dir=Path(tmpdir))

            report1 = HardwareAuditReport(
                devices_count=1,
                devices=[
                    HardwareDeviceAudit(device_id="DEV_01", name="Primary Device"),
                ],
            )
            entry1 = manager.archive_report(report1)
            assert isinstance(entry1, HardwareArchiveEntry)
            assert entry1.devices_count == 1

            # Второй снимок с добавлением устройства
            report2 = HardwareAuditReport(
                devices_count=2,
                devices=[
                    HardwareDeviceAudit(device_id="DEV_01", name="Primary Device"),
                    HardwareDeviceAudit(device_id="DEV_02", name="Secondary Device"),
                ],
            )
            entry2 = manager.archive_report(report2)
            assert entry2.changes_count == 1
            assert len(entry2.report.changes_since_last_archive) == 1

            # Проверка чтения истории
            history = manager.get_history()
            assert len(history) == 2
            assert history[0]["archive_id"] == entry2.archive_id

            # Проверка таймлайна изменений
            timeline = manager.get_change_timeline()
            assert len(timeline) == 1
            assert timeline[0].change_type == "added"
            assert timeline[0].device_id == "DEV_02"

            # Проверка загрузки архива по ID
            loaded = manager.get_archive_by_id(entry1.archive_id)
            assert loaded is not None
            assert loaded.archive_id == entry1.archive_id


class TestSystemCollectorAndRouterIntegration:
    """Тестирование интеграции аудита оборудования с SystemCollector и FastAPI."""

    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.include_router(init_router())
        return TestClient(app)

    def test_collector_hardware_audit_methods(self):
        """Проверка вызовов методов аудита и архивации в SystemCollector."""
        collector = SystemCollector()
        report = collector.get_hardware_audit()
        assert isinstance(report, HardwareAuditReport)
        assert report.devices_count >= 1

        entry = collector.archive_hardware_state(auto_diff=True)
        assert isinstance(entry, HardwareArchiveEntry)
        assert entry.archive_id.startswith("hw_")

        history = collector.get_hardware_history(limit=5)
        assert isinstance(history, list)
        assert len(history) >= 1

    def test_api_hardware_endpoints(self, client: TestClient):
        """Проверка REST API эндпоинтов /hardware/audit, /history, /changes, /archive."""
        # 1. GET /api/v1/system/hardware/audit
        res_audit = client.get("/api/v1/system/hardware/audit")
        assert res_audit.status_code == 200
        data_audit = res_audit.json()
        assert "devices_count" in data_audit
        assert "devices" in data_audit
        assert len(data_audit["devices"]) >= 1

        # 2. POST /api/v1/system/hardware/archive
        res_arch = client.post("/api/v1/system/hardware/archive")
        assert res_arch.status_code == 200
        data_arch = res_arch.json()
        assert "archive_id" in data_arch

        # 3. GET /api/v1/system/hardware/history
        res_hist = client.get("/api/v1/system/hardware/history")
        assert res_hist.status_code == 200
        data_hist = res_hist.json()
        assert isinstance(data_hist, list)
        assert len(data_hist) >= 1

        # 4. GET /api/v1/system/hardware/changes
        res_changes = client.get("/api/v1/system/hardware/changes")
        assert res_changes.status_code == 200
        data_changes = res_changes.json()
        assert isinstance(data_changes, list)
