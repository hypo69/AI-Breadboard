# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research and Chart Generator Tests
# =============================================================================
# Description:
#   Модульные тесты для аналитического движка исследования логов телеметрии:
#   TelemetryDataExtractor, TelemetryResearcher, TelemetryChartGenerator,
#   FastAPI роутера и генерации SVG/HTML дашбордов.
#
# File: test_telemetry_research.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модульные тесты для подсистемы исследования телеметрии и генерации графиков."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.windows.telemetry.research import (
    ChartConfig,
    MetricStats,
    TelemetryChartGenerator,
    TelemetryDataExtractor,
    TelemetryResearchReport,
    TelemetryResearcher,
    init_research_router,
)


@pytest.fixture
def sample_telemetry_records():
    """Набор тестовых записей телеметрии."""
    return [
        {
            "timestamp": "2026-09-24T10:00:00Z",
            "cpu": {"total_percent": 25.0, "temperature_celsius": 45.0},
            "memory": {"percent": 40.0, "used_gb": 6.4},
            "gpu": {"load_percent": 15.0, "temperature_celsius": 50.0},
            "disk_io": {"read_bytes_per_sec": 1048576, "write_bytes_per_sec": 2097152},
        },
        {
            "timestamp": "2026-09-24T10:01:00Z",
            "cpu": {"total_percent": 95.0, "temperature_celsius": 88.0},
            "memory": {"percent": 92.0, "used_gb": 14.7},
            "gpu": {"load_percent": 80.0, "temperature_celsius": 75.0},
            "disk_io": {"read_bytes_per_sec": 5242880, "write_bytes_per_sec": 10485760},
        },
        {
            "timestamp": "2026-09-24T10:02:00Z",
            "cpu": {"total_percent": 30.0, "temperature_celsius": 50.0},
            "memory": {"percent": 45.0, "used_gb": 7.2},
            "gpu": {"load_percent": 20.0, "temperature_celsius": 52.0},
            "disk_io": {"read_bytes_per_sec": 2097152, "write_bytes_per_sec": 1048576},
        },
        {
            "timestamp": "2026-09-24T10:03:00Z",
            "event_type": "ERROR_STATE_CHANGED",
            "device_instance_id": "USB\\VID_1234&PID_5678\\01",
            "friendly_name": "USB Flash Disk",
            "category": "Накопитель",
            "has_problem": True,
            "problem_code": 43,
            "flapping_count_in_window": 2,
        },
    ]


def test_extractor_parse_jsonl(tmp_path: Path, sample_telemetry_records):
    """Тестирование парсинга JSONL файлов телеметрии."""
    log_file = tmp_path / "telemetry.jsonl"
    with log_file.open("w", encoding="utf-8") as f:
        for rec in sample_telemetry_records:
            f.write(json.dumps(rec) + "\n")

    extractor = TelemetryDataExtractor(default_log_dirs=[tmp_path])
    files = extractor.discover_log_files(tmp_path)
    assert len(files) == 1
    assert files[0] == log_file

    parsed = extractor.parse_file(log_file)
    assert len(parsed) == len(sample_telemetry_records)
    assert parsed[0]["cpu"]["total_percent"] == 25.0


def test_researcher_analysis(sample_telemetry_records):
    """Тестирование аналитического движка и вычисления метрик."""
    researcher = TelemetryResearcher()
    report = researcher.analyze(sample_telemetry_records)

    assert isinstance(report, TelemetryResearchReport)
    assert report.records_analyzed == len(sample_telemetry_records)
    assert "cpu_load" in report.statistics
    assert "ram_used_percent" in report.statistics
    assert "cpu_temp" in report.statistics

    cpu_stats = report.statistics["cpu_load"]
    assert cpu_stats.min_val == 25.0
    assert cpu_stats.max_val == 95.0
    assert cpu_stats.count == 3

    # Проверка детекции аномалий
    assert len(report.anomalies) > 0
    anom_metrics = [a.metric for a in report.anomalies]
    assert "CPU Load" in anom_metrics
    assert "CPU Temp" in anom_metrics
    assert "RAM Usage" in anom_metrics

    # Проверка сбоев устройств
    assert report.device_summary.error_count == 1
    assert len(report.device_summary.flapping_devices) == 1
    assert report.health_score < 100.0
    assert len(report.summary_conclusions) > 0


def test_chart_generator(sample_telemetry_records):
    """Тестирование генерации спецификаций графиков, SVG и HTML дашборда."""
    researcher = TelemetryResearcher()
    chart_gen = TelemetryChartGenerator()

    report = researcher.analyze(sample_telemetry_records)
    records = researcher.extractor.load_all_records(sample_telemetry_records)
    ts_map = researcher._extract_time_series(records)

    charts = chart_gen.generate_chart_configs(ts_map, report)
    assert len(charts) >= 3

    # Проверка наличия графика ресурсов и температур
    chart_ids = [c.id for c in charts]
    assert "chart_resource_utilization" in chart_ids
    assert "chart_temperatures" in chart_ids

    # Рендеринг SVG
    svg = chart_gen.render_svg_chart(charts[0])
    assert "<svg" in svg
    assert "</svg>" in svg
    assert charts[0].title in svg

    # Рендеринг HTML
    report.charts = charts
    html = chart_gen.render_html_dashboard(report)
    assert "<!DOCTYPE html>" in html
    assert "Исследование телеметрии" in html
    assert str(report.health_score) in html


def test_research_router_endpoints(sample_telemetry_records):
    """Тестирование REST API эндпоинтов исследования телеметрии."""
    app = FastAPI()
    app.include_router(init_research_router())
    client = TestClient(app)

    # 1. POST /report
    response = client.post(
        "/api/windows/telemetry/research/report",
        json={"records": sample_telemetry_records},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert data["records_analyzed"] == len(sample_telemetry_records)
    assert len(data["charts"]) > 0

    # 2. GET /charts
    charts_resp = client.get("/api/windows/telemetry/research/charts")
    assert charts_resp.status_code == 200
    assert isinstance(charts_resp.json(), list)

    # 3. GET /dashboard
    dash_resp = client.get("/api/windows/telemetry/research/dashboard")
    assert dash_resp.status_code == 200
    assert "text/html" in dash_resp.headers["content-type"]
    assert "AI-Breadboard" in dash_resp.text

    # 4. GET /files
    files_resp = client.get("/api/windows/telemetry/research/files")
    assert files_resp.status_code == 200
    assert isinstance(files_resp.json(), list)

    # 5. GET /records
    records_resp = client.get("/api/windows/telemetry/research/records?page=1&page_size=10")
    assert records_resp.status_code == 200
    rdata = records_resp.json()
    assert "total" in rdata
    assert "items" in rdata
    assert "page" in rdata
