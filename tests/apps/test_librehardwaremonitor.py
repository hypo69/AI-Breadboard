# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor App Tests
# =============================================================================
# Description:
#   Модульные тесты для LibreHardwareMonitor: парсинг значений, обход дерева,
#   поиск датчиков, системная сводка и REST API эндпоинты.
#
# File: test_librehardwaremonitor.py
# Project: ai-breadboard
# Package: tests.apps
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для приложения LibreHardwareMonitor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.hardware.lhm_service import (
    LhmService,
    parse_sensor_value,
)
from apps.windows.hardware import LhmService as LhmServiceWindows
from apps.librehardwaremonitor.core.lhm_service import LhmService as LhmServiceAlias
from apps.librehardwaremonitor.router import init_router


SAMPLE_LHM_TREE = {
    "id": 0,
    "Text": "Sensor",
    "Children": [
        {
            "id": 1,
            "Text": "DESKTOP-TEST",
            "Children": [
                {
                    "id": 2,
                    "Text": "AMD Ryzen 7 7800X3D",
                    "ImageURL": "images/cpu.png",
                    "Children": [
                        {
                            "id": 3,
                            "Text": "Temperatures",
                            "Children": [
                                {"id": 4, "Text": "CPU Package", "Value": "54.2 °C"},
                                {"id": 5, "Text": "Core (Tctl/Tdie)", "Value": "54.2 °C"},
                            ],
                        },
                        {
                            "id": 6,
                            "Text": "Load",
                            "Children": [
                                {"id": 7, "Text": "CPU Total", "Value": "14.2 %"},
                            ],
                        },
                    ],
                },
                {
                    "id": 8,
                    "Text": "NVIDIA GeForce RTX 4080",
                    "ImageURL": "images/nvidia.png",
                    "Children": [
                        {
                            "id": 9,
                            "Text": "Temperatures",
                            "Children": [
                                {"id": 10, "Text": "GPU Core", "Value": "42.0 °C"},
                            ],
                        },
                        {
                            "id": 11,
                            "Text": "Load",
                            "Children": [
                                {"id": 12, "Text": "GPU Core", "Value": "8.5 %"},
                            ],
                        },
                    ],
                },
                {
                    "id": 13,
                    "Text": "Generic Memory",
                    "ImageURL": "images/ram.png",
                    "Children": [
                        {
                            "id": 14,
                            "Text": "Data",
                            "Children": [
                                {"id": 15, "Text": "Memory Used", "Value": "15.4 GB"},
                            ],
                        },
                        {
                            "id": 16,
                            "Text": "Load",
                            "Children": [
                                {"id": 17, "Text": "Memory", "Value": "48.1 %"},
                            ],
                        },
                    ],
                },
            ],
        }
    ],
}


def test_lhm_service_import_compatibility() -> None:
    """Тестирование корректности экспорта LhmService в apps.windows.hardware."""
    assert LhmService is LhmServiceWindows
    assert LhmService is LhmServiceAlias


def test_parse_sensor_value() -> None:
    """Тестирование парсинга строковых значений сенсоров."""
    assert parse_sensor_value("54.2 °C") == (54.2, "°C")
    assert parse_sensor_value("14.2 %") == (14.2, "%")
    assert parse_sensor_value("1.250 V") == (1.250, "V")
    assert parse_sensor_value("1200 RPM") == (1200.0, "RPM")
    assert parse_sensor_value("15,4 GB") == (15.4, "GB")
    assert parse_sensor_value("-5.0 °C") == (-5.0, "°C")
    assert parse_sensor_value(None) == (None, None)
    assert parse_sensor_value("") == (None, None)


def test_find_sensor() -> None:
    """Тестирование точечного поиска сенсора в дереве."""
    svc = LhmService()
    cpu_temp = svc.find_sensor("CPU", "CPU Package", tree=SAMPLE_LHM_TREE)
    assert cpu_temp is not None
    assert cpu_temp["hardware_name"] == "AMD Ryzen 7 7800X3D"
    assert cpu_temp["sensor_name"] == "CPU Package"
    assert cpu_temp["value_num"] == 54.2
    assert cpu_temp["unit"] == "°C"

    gpu_load = svc.find_sensor("NVIDIA", "GPU Core", sensor_type_pattern="Load", tree=SAMPLE_LHM_TREE)
    assert gpu_load is not None
    assert gpu_load["sensor_category"] == "Load"
    assert gpu_load["value_num"] == 8.5

    non_existent = svc.find_sensor("NonExistent", "SensorX", tree=SAMPLE_LHM_TREE)
    assert non_existent is None


def test_get_flattened_sensors() -> None:
    """Тестирование преобразования дерева в плоский список."""
    svc = LhmService()
    flat = svc.get_flattened_sensors(tree=SAMPLE_LHM_TREE)
    assert len(flat) == 7
    names = [x["sensor_name"] for x in flat]
    assert "CPU Package" in names
    assert "GPU Core" in names
    assert "Memory Used" in names


def test_get_system_summary() -> None:
    """Тестирование формирования системной сводки."""
    svc = LhmService()
    summary = svc.get_system_summary(tree=SAMPLE_LHM_TREE)
    assert summary["is_available"] is True
    assert summary["cpu"]["name"] == "AMD Ryzen 7 7800X3D"
    assert summary["cpu"]["temperature_package_c"] == 54.2
    assert summary["cpu"]["load_total_percent"] == 14.2
    assert summary["gpu"]["name"] == "NVIDIA GeForce RTX 4080"
    assert summary["gpu"]["temperature_core_c"] == 42.0
    assert summary["gpu"]["load_core_percent"] == 8.5
    assert summary["memory"]["used_gb"] == 15.4
    assert summary["memory"]["load_percent"] == 48.1


def test_lhm_start_process() -> None:
    """Тестирование вызова запуска процесса LHM."""
    svc = LhmService(binary_path="C:/fake/LibreHardwareMonitor.exe")
    with patch.object(svc, "is_running", return_value=False), \
         patch.object(svc, "is_binary_available", return_value=True), \
         patch("subprocess.Popen") as mock_popen:
        res = svc.start_process()
        assert res is True
        mock_popen.assert_called_once()


def test_lhm_fastapi_endpoints() -> None:
    """Тестирование всех эндпоинтов FastAPI роутера LHM."""
    app = FastAPI()
    app.include_router(init_router())
    client = TestClient(app)

    # 1. /status
    res = client.get("/api/v1/lhm/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_running" in data
    assert "portable_guide" in data

    # 2. /sensors
    with patch.object(LhmService, "get_sensor_tree", return_value=SAMPLE_LHM_TREE):
        res = client.get("/api/v1/lhm/sensors")
        assert res.status_code == 200
        assert "sensors_tree" in res.json()

    # 3. /metrics
    with patch.object(LhmService, "get_sensor_tree", return_value=SAMPLE_LHM_TREE):
        res = client.get("/api/v1/lhm/metrics")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 7
        assert len(data["sensors"]) == 7

    # 4. /summary
    with patch.object(LhmService, "get_sensor_tree", return_value=SAMPLE_LHM_TREE):
        res = client.get("/api/v1/lhm/summary")
        assert res.status_code == 200
        summary = res.json()
        assert summary["cpu"]["temperature_package_c"] == 54.2

    # 5. /launch
    with patch.object(LhmService, "start_process", return_value=True):
        res = client.post("/api/v1/lhm/launch")
        assert res.status_code == 200
        assert res.json()["success"] is True
