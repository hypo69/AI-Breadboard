# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Telemetry Research
# =============================================================================
# Description:
#   Модульные тесты для подсистемы исследования телеметрии, графиков и FastAPI сервиса.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_telemetry_research import sample_telemetry_records
#
#     res = sample_telemetry_records()
#
# File: test_telemetry_research.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Модульные тесты для подсистемы исследования телеметрии, графиков и FastAPI сервиса."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.windows.telemetry_research import (
    ChartConfig,
    MetricStats,
    TelemetryChartGenerator,
    TelemetryDataExtractor,
    TelemetryResearchReport,
    TelemetryResearcher,
)
from apps.windows.telemetry_research.server import app


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

    assert len(report.anomalies) > 0
    anom_metrics = [a.metric for a in report.anomalies]
    assert "CPU Load" in anom_metrics
    assert "CPU Temp" in anom_metrics
    assert "RAM Usage" in anom_metrics

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
    chart_ids = [c.id for c in charts]
    assert "chart_resource_utilization" in chart_ids
    assert "chart_temperatures" in chart_ids

    svg = chart_gen.render_svg_chart(charts[0])
    assert "<svg" in svg
    assert "</svg>" in svg
    assert charts[0].title in svg

    report.charts = charts
    html = chart_gen.render_html_dashboard(report)
    assert "<!DOCTYPE html>" in html
    assert "Исследование телеметрии" in html
    assert str(report.health_score) in html


def test_fastapi_server_endpoints():
    """Тестирование FastAPI роутов и Web GUI."""
    client = TestClient(app)

    # 1. Главная страница
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "text/html" in res_index.headers["content-type"]
    assert "Исследование телеметрии Windows" in res_index.text

    # 2. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # 3. Sources
    res_sources = client.get("/api/sources")
    assert res_sources.status_code == 200
    assert isinstance(res_sources.json(), list)

    # 4. Run research
    res_run = client.post("/api/run-research", json={})
    assert res_run.status_code == 200
    data = res_run.json()
    assert "report_id" in data
    assert "base_report" in data
    assert "hypotheses" in data

    # 5. Records endpoint
    res_rec = client.get("/api/records?page=1&page_size=10")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert "total" in rec_data
    assert "items" in rec_data

    # 6. Dashboard HTML
    res_dash = client.get("/api/dashboard")
    assert res_dash.status_code == 200
    assert "<!DOCTYPE html>" in res_dash.text

    # 7. Current state endpoint (telemetry.db)
    res_curr = client.get("/api/current-state?limit=50")
    assert res_curr.status_code == 200
    curr_data = res_curr.json()
    assert "status" in curr_data
    assert "time_series" in curr_data
    assert "latest_snapshot" in curr_data
    assert "top_processes" in curr_data


def test_extractor_get_current_system_state(tmp_path: Path):
    """Тестирование извлечения актуального состояния из SQLite базы данных."""
    import sqlite3

    db_path = tmp_path / "test_telemetry.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE system_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_total_percent REAL,
            cpu_frequency_mhz REAL,
            memory_total_gb REAL,
            memory_used_gb REAL,
            memory_percent REAL,
            swap_percent REAL,
            gpu_load_percent REAL,
            gpu_temp_c REAL,
            disk_read_bytes_sec REAL,
            disk_write_bytes_sec REAL,
            network_sent_bytes_sec REAL,
            network_recv_bytes_sec REAL,
            uptime_seconds REAL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE process_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            pid INTEGER,
            name TEXT,
            cpu_percent REAL,
            memory_mb REAL,
            memory_percent REAL,
            num_threads INTEGER,
            username TEXT,
            status TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE sensor_polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_name TEXT,
            sensor_category TEXT,
            unit TEXT,
            value REAL,
            hardware_name TEXT,
            timestamp TEXT
        );
        """
    )

    # Вставляем тестовый снепшот
    cur.execute(
        """
        INSERT INTO system_snapshots (
            timestamp, cpu_total_percent, cpu_frequency_mhz, memory_total_gb,
            memory_used_gb, memory_percent, swap_percent, gpu_load_percent,
            gpu_temp_c, disk_read_bytes_sec, disk_write_bytes_sec,
            network_sent_bytes_sec, network_recv_bytes_sec, uptime_seconds
        ) VALUES (
            '2026-10-01T00:00:00Z', 15.5, 3200.0, 32.0, 14.5, 45.3, 10.0, 20.0, 55.0,
            1048576.0, 2097152.0, 512000.0, 1024000.0, 3600.0
        );
        """
    )
    snap_id = cur.lastrowid

    # Вставляем процессы
    cur.execute(
        """
        INSERT INTO process_snapshots (
            snapshot_id, pid, name, cpu_percent, memory_mb, memory_percent, num_threads, username, status
        ) VALUES (?, 1234, 'python.exe', 12.5, 250.0, 0.8, 8, 'user', 'running');
        """,
        (snap_id,),
    )

    # Вставляем сенсор
    cur.execute(
        """
        INSERT INTO sensor_polls (
            sensor_name, sensor_category, unit, value, hardware_name, timestamp
        ) VALUES ('CPU Package', 'Temperature', '°C', 52.0, 'AMD Ryzen 9', '2026-10-01T00:00:00Z');
        """
    )
    conn.commit()
    conn.close()

    extractor = TelemetryDataExtractor()
    state = extractor.get_current_system_state(db_path=db_path, limit=10)

    assert state["status"] == "ok"
    assert state["total_snapshots"] == 1
    assert state["returned_points"] == 1
    assert state["latest_snapshot"]["cpu_total_percent"] == 15.5
    assert state["latest_snapshot"]["memory_percent"] == 45.3
    assert len(state["top_processes"]) == 1
    assert state["top_processes"][0]["name"] == "python.exe"
    assert len(state["sensors"]) == 1
    assert state["sensors"][0]["sensor_name"] == "CPU Package"
    assert len(state["time_series"]["cpu_load"]) == 1
    assert state["time_series"]["cpu_load"][0] == 15.5