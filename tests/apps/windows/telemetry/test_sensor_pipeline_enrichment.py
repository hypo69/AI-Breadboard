# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry - Sensor Pipeline Enrichment
# =============================================================================
# Description:
#   Модульные тесты конвейера сбора сенсоров: CIM как основной интерфейс,
#   WMI как fallback и LHM для обогащения только отсутствующими датчиками.
#
# Usage Examples:
#   CLI:
#     pytest tests/apps/windows/telemetry/test_sensor_pipeline_enrichment.py -v
#
# File: test_sensor_pipeline_enrichment.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:10:00
# =============================================================================

"""Тесты конвейера сбора сенсоров с CIM, WMI fallback и LHM enrichment."""

import json
import subprocess
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from apps.windows.telemetry.sensors import _probe_acpi_thermal_zones
from apps.windows.telemetry.sensor_collector import SensorCollector
from apps.windows.telemetry.sensor_registry import SensorProvider
from apps.windows.telemetry.sqlite import TelemetryStorage


class TestSensorPipelineEnrichment:
    """Набор тестов для проверки многоуровневого опроса сенсоров."""

    def test_probe_acpi_thermal_zones_cim_primary(self, monkeypatch):
        """Проверяет первичный успешный опрос через CIM (Get-CimInstance)."""
        mock_cim_output = json.dumps([
            {"InstanceName": "ACPI\\ThermalZone\\TZ00_0", "CurrentTemperature": 3050}
        ])
        
        mock_run = MagicMock()
        mock_run.returncode = 0
        mock_run.stdout = mock_cim_output
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_run)

        sensors = _probe_acpi_thermal_zones()
        assert len(sensors) == 1
        assert sensors[0].sensor_id == "acpi_thermal_0"
        assert sensors[0].value == 31.9  # 3050/10 - 273.15 = 31.85 -> 31.9
        assert sensors[0].provider == SensorProvider.CIM_SYSTEM

    def test_probe_acpi_thermal_zones_wmi_fallback(self, monkeypatch):
        """Проверяет переключение на WMI fallback при недоступности CIM."""
        import sys
        # Мокаем сбой CIM
        mock_run = MagicMock()
        mock_run.returncode = 1
        mock_run.stdout = ""
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_run)

        # Мокаем объект WMI
        class MockZone:
            CurrentTemperature = 3010
            InstanceName = "ACPI\\ThermalZone\\Fallback_0"

        mock_wmi_mod = MagicMock()
        mock_wmi_instance = MagicMock()
        mock_wmi_instance.MSAcpi_ThermalZoneTemperature.return_value = [MockZone()]
        mock_wmi_mod.WMI.return_value = mock_wmi_instance
        
        mock_pythoncom = MagicMock()

        monkeypatch.setitem(sys.modules, "wmi", mock_wmi_mod)
        monkeypatch.setitem(sys.modules, "pythoncom", mock_pythoncom)

        with patch("apps.windows.telemetry.sensors._WMI_AVAILABLE", True):
            sensors = _probe_acpi_thermal_zones()

        assert len(sensors) == 1
        assert sensors[0].sensor_id == "acpi_thermal_0"
        assert sensors[0].value == 27.9  # 3010/10 - 273.15 = 27.85 -> 27.9
        assert sensors[0].provider == SensorProvider.WMI_FALLBACK

    def test_sensor_collector_lhm_enrichment_only_missing(self):
        """Проверяет, что LHM только обогащает недостающие сенсоры и не дублирует существующие."""
        mock_lhm = MagicMock()
        mock_lhm.is_running.return_value = True
        mock_lhm.get_flattened_sensors.return_value = [
            # Сенсор, который уже будет в базовом наборе (через id)
            {
                "hardware_name": "CPU",
                "hardware_type": "cpu",
                "sensor_category": "Load",
                "sensor_name": "CPU Total",
                "value_raw": "50.0 %",
                "value_num": 50.0,
            },
            # Уникальный детальный сенсор LHM (температура ядра)
            {
                "hardware_name": "CPU",
                "hardware_type": "cpu",
                "sensor_category": "Temperatures",
                "sensor_name": "CPU Core #1",
                "value_raw": "48.5 °C",
                "value_num": 48.5,
            },
            # Уникальный сенсор мощности в Ваттах
            {
                "hardware_name": "CPU",
                "hardware_type": "cpu",
                "sensor_category": "Powers",
                "sensor_name": "CPU Package Power",
                "value_raw": "35.2 W",
                "value_num": 35.2,
            },
        ]

        collector = SensorCollector(lhm_service=mock_lhm)
        
        hardware_data = {
            "cpu": {
                "model": "Intel Core i7",
                "utilization_pct": 25.0,
            }
        }

        readings = collector.extract_sensor_readings(hardware_data)
        ids = [r["id"] for r in readings]

        # Базовый сенсор присутствует
        assert "cpu_util_total" in ids
        # Сенсоры LHM enrichment добавлены
        assert "lhm_cpu_cpu_core_1" in ids
        assert "lhm_cpu_cpu_package_power" in ids

        # Проверяем провайдер обогащенного сенсора
        enriched_item = next(r for r in readings if r["id"] == "lhm_cpu_cpu_package_power")
        assert enriched_item["_provider"] == SensorProvider.LHM_ENRICHED
        assert enriched_item["unit"] == "W"
        assert enriched_item["value"] == 35.2

    def test_sqlite_sensor_polls_clean_schema_and_batch_insert(self, tmp_path: Path):
        """Проверяет создание чистой таблицы sensor_polls и запись пакета с raw_json."""
        db_path = tmp_path / "test_telemetry.db"
        storage = TelemetryStorage(db_path=str(db_path), buffer_mode="direct")

        items = [
            {
                "id": "cpu_util_total",
                "hardware_name": "Intel CPU",
                "hardware_type": "cpu",
                "sensor_category": "Load",
                "sensor_name": "CPU Total",
                "unit": "%",
                "value": 15.5,
                "_provider": SensorProvider.CIM_SYSTEM,
                "raw_json": '{"source": "cim", "metric": "load"}',
            },
            {
                "id": "lhm_cpu_package_power",
                "hardware_name": "Intel CPU",
                "hardware_type": "cpu",
                "sensor_category": "Powers",
                "sensor_name": "Package Power",
                "unit": "W",
                "value": 42.1,
                "_provider": SensorProvider.LHM_ENRICHED,
                "raw_json": '{"source": "lhm", "watt": 42.1}',
            }
        ]

        saved_count = storage.save_sensor_polls_batch(items)
        assert saved_count == 2

        # Проверяем записи напрямую из БД
        with storage._get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT sensor_id, provider, value, raw_json FROM sensor_polls ORDER BY id ASC").fetchall()
            assert len(rows) == 2
            assert rows[0][0] == "cpu_util_total"
            assert rows[0][1] == "CIM_SYSTEM"
            assert rows[0][2] == 15.5
            assert "source" in rows[0][3]

            assert rows[1][0] == "lhm_cpu_package_power"
            assert rows[1][1] == "LHM_ENRICHED"
            assert rows[1][2] == 42.1
