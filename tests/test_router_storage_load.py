# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Router Storage Load
# =============================================================================
# Description:
#   Тесты роутера GET /api/v1/panel/storage-load и функции build_storage_load.
#
# File: test_router_storage_load.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 06:25:00
# =============================================================================

from __future__ import annotations
"""Тесты роутера /api/v1/panel/storage-load."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.api.routers.router_storage_load import (
    init_router,
    build_storage_load,
    DiskDriveMetric,
    DiskPartitionMetric,
)
from apps.windows.modules.storage_manager.core.windows_storage_sensor import StorageDiskHealthInfo


def test_build_storage_load_with_physical_and_lhm():
    """Тест объединения физических накопителей (включая Samsung NVMe) с LHM и разделами."""
    mock_physical = [
        StorageDiskHealthInfo(
            device_id="Disk3",
            model="Samsung SSD 990 EVO Plus 2TB",
            friendly_name="Samsung SSD 990 EVO Plus 2TB",
            serial_number="S990EVO123",
            bus_type="RAID",
            media_type="SSD",
            size_gb=1863.0,
            health_status="Healthy",
            operational_status="OK",
            temperature_c=0.0,
        ),
        StorageDiskHealthInfo(
            device_id="Disk1",
            model="CT1000MX500SSD1",
            friendly_name="CT1000MX500SSD1",
            serial_number="CRUCIAL456",
            bus_type="RAID",
            media_type="SSD",
            size_gb=931.5,
            health_status="Healthy",
            operational_status="OK",
            temperature_c=0.0,
        ),
    ]

    mock_sensors = [
        {"hardware_name": "CT1000MX500SSD1", "hardware_type": "storage", "sensor_category": "Temperatures", "sensor_name": "Temperature", "value_raw": "31.0 °C", "value_num": 31.0},
        {"hardware_name": "CT1000MX500SSD1", "hardware_type": "storage", "sensor_category": "Load", "sensor_name": "Used Space", "value_raw": "92.2 %", "value_num": 92.2},
        {"hardware_name": "CT1000MX500SSD1", "hardware_type": "storage", "sensor_category": "Throughput", "sensor_name": "Read Rate", "value_raw": "1.5 MB/s", "value_num": 1.5},
    ]

    mock_partitions = [
        {"device": "C:\\", "mountpoint": "C:\\", "fstype": "NTFS", "total_gb": 1863.0, "used_gb": 940.0, "free_gb": 923.0, "used_percent": 50.5},
        {"device": "D:\\", "mountpoint": "D:\\", "fstype": "NTFS", "total_gb": 931.5, "used_gb": 858.0, "free_gb": 73.5, "used_percent": 92.2},
    ]

    resp = build_storage_load(
        sensors=mock_sensors,
        physical_disks=mock_physical,
        partitions_data=mock_partitions,
    )

    assert resp.status == "ok"
    assert len(resp.drives) == 2
    assert len(resp.partitions) == 2

    # Проверка Samsung SSD 990 EVO Plus (NVMe)
    samsung = next((d for d in resp.drives if "Samsung" in d.name), None)
    assert samsung is not None
    assert samsung.media_type == "NVMe"
    assert samsung.total_gb == 1863.0
    assert samsung.used_percent == 50.5
    assert samsung.used_gb == 940.0

    # Проверка Crucial SSD с подхватом температуры и скорости из LHM
    crucial = next((d for d in resp.drives if "CT1000" in d.name), None)
    assert crucial is not None
    assert crucial.temperature_c == 31.0
    assert crucial.used_percent == 92.2
    assert crucial.read_rate_raw == "1.5 MB/s"


def test_empty_storage_load(mocker):
    """Тест пустого ответа при отсутствии сенсоров."""
    mock_lhm = mocker.MagicMock()
    mock_lhm.is_running.return_value = False
    mock_sensor = mocker.MagicMock()
    mock_sensor.get_physical_disks.return_value = []

    app = FastAPI()
    app.include_router(init_router(lhm_service=mock_lhm, storage_sensor=mock_sensor))
    client = TestClient(app)

    res = client.get("/api/v1/panel/storage-load")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "summary" in data
    assert "drives" in data
    assert "partitions" in data
