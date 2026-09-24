# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Application Tests
# =============================================================================
# Description:
#   Модульные тесты для приложения apps.telemetry_research:
#   проверка моделей данных, исследовательского движка TelemetryResearchEngine,
#   расчета корреляций, проверки системных гипотез, FastAPI роутера и CLI.
#
# File: test_telemetry_research_app.py
# Project: ai-breadboard
# Package: tests.apps
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для приложения исследования телеметрии apps.telemetry_research."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.telemetry_research.engine import TelemetryResearchEngine
from apps.telemetry_research.models import (
    CorrelationMatrixItem,
    DeepResearchReport,
    HypothesisResult,
    ResearchScenarioRequest,
)
from apps.telemetry_research.router import init_router


@pytest.fixture
def sample_research_records():
    """Набор синтетических записей телеметрии для исследования."""
    return [
        {
            "timestamp": "2026-09-24T10:00:00Z",
            "cpu": {"total_percent": 20.0, "temperature_celsius": 40.0},
            "memory": {"percent": 45.0, "used_gb": 7.2},
            "gpu": {"load_percent": 10.0, "temperature_celsius": 48.0},
            "disk_io": {"read_bytes_per_sec": 1000000, "write_bytes_per_sec": 2000000},
        },
        {
            "timestamp": "2026-09-24T10:01:00Z",
            "cpu": {"total_percent": 95.0, "temperature_celsius": 89.0},
            "memory": {"percent": 90.0, "used_gb": 14.4},
            "gpu": {"load_percent": 85.0, "temperature_celsius": 84.0},
            "disk_io": {"read_bytes_per_sec": 10000000, "write_bytes_per_sec": 20000000},
        },
        {
            "timestamp": "2026-09-24T10:02:00Z",
            "cpu": {"total_percent": 85.0, "temperature_celsius": 86.0},
            "memory": {"percent": 89.0, "used_gb": 14.2},
            "gpu": {"load_percent": 75.0, "temperature_celsius": 80.0},
            "disk_io": {"read_bytes_per_sec": 5000000, "write_bytes_per_sec": 8000000},
        },
        {
            "timestamp": "2026-09-24T10:03:00Z",
            "event_type": "ERROR_STATE_CHANGED",
            "device_instance_id": "USB\\VID_9999&PID_0001\\1",
            "friendly_name": "Test Problem USB Device",
            "category": "Контроллер USB",
            "has_problem": True,
            "problem_code": 43,
            "flapping_count_in_window": 3,
        },
    ]


def test_models_instantiation():
    """Тест создания моделей данных исследования."""
    req = ResearchScenarioRequest(cpu_anomaly_threshold=85.0, enable_hypotheses_check=True)
    assert req.cpu_anomaly_threshold == 85.0
    assert req.enable_hypotheses_check is True

    corr = CorrelationMatrixItem(
        metric_a="cpu_load",
        metric_b="cpu_temp",
        coefficient=0.98,
        sample_size=10,
        interpretation="Сильная прямая связь",
    )
    assert corr.coefficient == 0.98

    hyp = HypothesisResult(
        hypothesis_id="H_TEST",
        title="Тестовая гипотеза",
        description="Описание",
        confirmed=True,
        confidence=0.9,
        evidence=["Факт 1"],
        recommendation="Действие",
    )
    assert hyp.confirmed is True


def test_engine_deep_research(sample_research_records):
    """Тест аналитического исследовательского движка."""
    engine = TelemetryResearchEngine()
    req = ResearchScenarioRequest(records=sample_research_records, enable_hypotheses_check=True)
    report = engine.run_deep_research(req)

    assert isinstance(report, DeepResearchReport)
    assert report.base_report.records_analyzed == len(sample_research_records)
    assert len(report.hypotheses) > 0

    # Проверяем подтверждение гипотез по перегреву и сбоям
    hyp_map = {h.hypothesis_id: h for h in report.hypotheses}
    assert hyp_map["H_CPU_THERMAL_STRESS"].confirmed is True
    assert hyp_map["H_RAM_PRESSURE"].confirmed is True
    assert hyp_map["H_DEVICE_INSTABILITY"].confirmed is True

    # Проверяем матрицу корреляций
    assert isinstance(report.correlations, list)
    if report.correlations:
        assert all(abs(c.coefficient) <= 1.0 for c in report.correlations)

    # Проверяем рекомендации и выводы
    assert len(report.actionable_recommendations) > 0
    assert "Исследование завершено" in report.investigation_summary


def test_engine_filter_subsystems(sample_research_records):
    """Тест фильтрации записей по подсистемам."""
    engine = TelemetryResearchEngine()
    req = ResearchScenarioRequest(records=sample_research_records, subsystems=["devices"])
    report = engine.run_deep_research(req)

    assert report.base_report.records_analyzed == 1
    assert report.base_report.device_summary.error_count == 1


def test_router_endpoints(sample_research_records, tmp_path: Path):
    """Тест всех эндпоинтов FastAPI роутера приложения."""
    engine = TelemetryResearchEngine()
    router = init_router(engine=engine)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # 1. Health
    res_health = client.get("/apps/telemetry_research/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # 2. Run research
    res_report = client.post(
        "/apps/telemetry_research/run-research",
        json={"records": sample_research_records},
    )
    assert res_report.status_code == 200
    rep_data = res_report.json()
    assert "report_id" in rep_data
    assert len(rep_data["hypotheses"]) > 0

    # 3. Correlations
    res_corr = client.get("/apps/telemetry_research/correlations")
    assert res_corr.status_code == 200
    assert isinstance(res_corr.json(), list)

    # 4. Hypotheses
    res_hyp = client.get("/apps/telemetry_research/hypotheses")
    assert res_hyp.status_code == 200
    assert isinstance(res_hyp.json(), list)

    # 5. Charts
    res_charts = client.get("/apps/telemetry_research/charts")
    assert res_charts.status_code == 200
    assert isinstance(res_charts.json(), list)

    # 6. Dashboard
    res_dash = client.get("/apps/telemetry_research/dashboard")
    assert res_dash.status_code == 200
    assert "text/html" in res_dash.headers["content-type"]
    assert "Исследование телеметрии" in res_dash.text

    # 7. Sources
    res_sources = client.get("/apps/telemetry_research/sources")
    assert res_sources.status_code == 200
    assert isinstance(res_sources.json(), list)

    # 8. Records
    res_records = client.get("/apps/telemetry_research/records?page=1&page_size=10")
    assert res_records.status_code == 200
    assert "items" in res_records.json()
