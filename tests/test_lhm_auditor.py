# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for LHM Sensor & Hardware Auditor
# =============================================================================
# Description:
#   Тесты для модуля LhmSensorAuditor: сбор и усреднение залогированных данных LHM,
#   формирование списка физических устройств, генерация промпта и AI-аудит оборудования.
#
# File: test_lhm_auditor.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit-тесты для LhmSensorAuditor и эндпоинтов аудита LHM."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.hardware.lhm_auditor import LhmSensorAuditor
from src.api.router_system import init_router as init_system_router


@pytest.fixture
def mock_lhm_logs(tmp_path: Path) -> Path:
    """Создает временный CSV-файл с залогированными данными LHM для тестирования."""
    csv_file = tmp_path / "librehardwaremonitor_polls.csv"
    headers = ["timestamp", "hardware", "sensor_name", "category", "value", "unit", "raw_value"]
    rows = [
        ["2026-09-23T10:00:00Z", "Intel Core i5-10400", "CPU Core", "Voltages", "1.10", "V", "1.10 V"],
        ["2026-09-23T10:01:00Z", "Intel Core i5-10400", "CPU Core", "Voltages", "1.20", "V", "1.20 V"],
        ["2026-09-23T10:00:00Z", "Intel Core i5-10400", "Core Max", "Temperatures", "45.0", "°C", "45.0 °C"],
        ["2026-09-23T10:01:00Z", "Intel Core i5-10400", "Core Max", "Temperatures", "55.0", "°C", "55.0 °C"],
        ["2026-09-23T10:00:00Z", "Intel Core i5-10400", "CPU Core #1", "Clocks", "4000.0", "MHz", "4000.0 MHz"],
        ["2026-09-23T10:00:00Z", "NVIDIA GeForce GT 710", "GPU Core", "Temperatures", "42.0", "°C", "42.0 °C"],
        ["2026-09-23T10:01:00Z", "NVIDIA GeForce GT 710", "GPU Core", "Temperatures", "48.0", "°C", "48.0 °C"],
        ["2026-09-23T10:00:00Z", "CT1000MX500SSD1", "Temperature", "Temperatures", "33.0", "°C", "33.0 °C"],
    ]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return tmp_path


def test_lhm_auditor_aggregation(mock_lhm_logs: Path) -> None:
    """Проверка сбора и корректного усреднения залогированных показателей сенсоров."""
    auditor = LhmSensorAuditor(log_dir=mock_lhm_logs)
    data = auditor.collect_and_aggregate_logs()

    assert data["devices_count"] == 3
    assert "Intel Core i5-10400" in data["devices"]
    assert "NVIDIA GeForce GT 710" in data["devices"]
    assert "CT1000MX500SSD1" in data["devices"]

    # Проверка усреднения для CPU Core Voltage (1.10 и 1.20 -> avg 1.15)
    cpu_volt = next(
        s for s in data["aggregated_sensors"]
        if s["hardware"] == "Intel Core i5-10400" and s["sensor_name"] == "CPU Core" and s["category"] == "Voltages"
    )
    assert cpu_volt["avg"] == 1.15
    assert cpu_volt["min"] == 1.10
    assert cpu_volt["max"] == 1.20
    assert cpu_volt["samples_count"] == 2

    # Проверка усреднения для CPU Core Max Temp (45.0 и 55.0 -> avg 50.0)
    cpu_temp = next(
        s for s in data["aggregated_sensors"]
        if s["hardware"] == "Intel Core i5-10400" and s["sensor_name"] == "Core Max"
    )
    assert cpu_temp["avg"] == 50.0
    assert cpu_temp["max"] == 55.0


def test_lhm_auditor_prompt_generation(mock_lhm_logs: Path) -> None:
    """Проверка генерации структурированного промпта для AI со списком реальных устройств."""
    auditor = LhmSensorAuditor(log_dir=mock_lhm_logs)
    data = auditor.collect_and_aggregate_logs()
    prompt = auditor.build_audit_prompt(data)

    assert "СПИСОК РЕАЛЬНЫХ УСТРОЙСТВ" in prompt
    assert "- Intel Core i5-10400" in prompt
    assert "- NVIDIA GeForce GT 710" in prompt
    assert "- CT1000MX500SSD1" in prompt
    assert "УСРЕДНЁННЫЕ ПОКАЗАТЕЛИ СЕНСОРОВ" in prompt
    assert "ТВОЯ ЗАДАЧА" in prompt
    assert "Сравни эти усреднённые залогированные показатели с характеристиками и спецификациями реального железа" in prompt


@pytest.mark.asyncio
async def test_lhm_auditor_ai_audit_with_mock_model(mock_lhm_logs: Path) -> None:
    """Проверка вызова AI-модели и формирования отчета аудита."""
    mock_chat_model = MagicMock()
    mock_chat_model.ask = AsyncMock(return_value="Все физические устройства работают штатно. Параметры соответствуют номиналу.")
    mock_chat_model._model_name = "mock-gpt"

    auditor = LhmSensorAuditor(log_dir=mock_lhm_logs)
    report = await auditor.audit_sensors_with_ai(chat_model=mock_chat_model)

    assert report["success"] is True
    assert report["health_score"] >= 85
    assert report["devices_count"] == 3
    assert "Intel Core i5-10400" in report["devices"]
    assert "Все физические устройства работают штатно" in report["comparison_report"]
    assert report["ai_model_used"] == "mock-gpt"
    mock_chat_model.ask.assert_awaited_once()


def test_system_router_lhm_audit_endpoint(mock_lhm_logs: Path) -> None:
    """Проверка REST API эндпоинта POST /api/v1/system/lhm-audit."""
    app = FastAPI()
    mock_model = MagicMock()
    mock_model.ask = AsyncMock(return_value="AI заключение по оборудованию.")
    sys_router = init_system_router(chat_model=mock_model)
    app.include_router(sys_router)
    client = TestClient(app)

    with patch("apps.windows.hardware.lhm_auditor.get_apps_log_dir", return_value=mock_lhm_logs):
        res = client.post("/api/v1/system/lhm-audit")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "comparison_report" in data
