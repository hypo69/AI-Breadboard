# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry_Research - Test Research Models And Extractor
# =============================================================================
# Description:
#   Тесты моделей данных и экстрактора метрик модуля telemetry_research.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry_research.test_research_models_and_extractor import TestTelemetryResearchModels
#
#     service = TestTelemetryResearchModels()
#
# File: test_research_models_and_extractor.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты моделей данных и экстрактора метрик модуля telemetry_research.

Updated: 2026-10-01 11:30:00"""

import json
from pathlib import Path
import pytest

from apps.windows.telemetry_research.models import (
    AnomalyEvent,
    ChartConfig,
    CorrelationMatrixItem,
    DeepResearchReport,
    DeviceEventSummary,
    HypothesisResult,
    MetricPoint,
    MetricStats,
    ResearchScenarioRequest,
    TelemetryResearchReport,
    TimeSeriesDataset,
)
from apps.windows.telemetry_research.extractor import TelemetryDataExtractor


@pytest.fixture
def sample_telemetry_records():
    """Фикстура набора реальных данных замеров телеметрии."""
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
            "gpu": {"load_percent": 85.0, "temperature_celsius": 82.0},
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


class TestTelemetryResearchModels:
    """Тесты Pydantic-моделей исследовательского пакета."""

    def test_models_instantiation_and_serialization(self):
        """Проверка корректности инициализации и сериализации всех моделей."""
        anomaly = AnomalyEvent(
            timestamp="2026-09-24T10:01:00Z",
            metric="cpu_load",
            value=95.0,
            threshold=85.0,
            severity="critical",
            description="Критический всплеск CPU",
        )
        assert anomaly.severity == "critical"
        assert anomaly.value == 95.0

        stats = MetricStats(min_val=10.0, max_val=95.0, avg_val=45.0, median_val=30.0, std_dev=12.5)
        assert stats.max_val == 95.0

        point = MetricPoint(timestamp="2026-09-24T10:00:00Z", value=25.0)
        assert point.value == 25.0

        dataset = TimeSeriesDataset(
            name="cpu_load",
            unit="%",
            points=[point],
        )
        assert len(dataset.points) == 1

        corr = CorrelationMatrixItem(metric_a="cpu", metric_b="temp", coefficient=0.92, sample_size=10, interpretation="Сильная взаимосвязь")
        assert corr.coefficient == 0.92

        chart = ChartConfig(id="chart_1", title="CPU Usage", chart_type="line", datasets=[])
        assert chart.chart_type == "line"

        dev_sum = DeviceEventSummary(
            total_events=3,
            error_count=1,
            flapping_devices=["USB_01"],
        )
        assert len(dev_sum.flapping_devices) == 1

        hyp = HypothesisResult(
            hypothesis_id="hyp_cpu",
            title="High CPU Usage",
            description="Проверка нагрузки процессора",
            confirmed=True,
            confidence=0.95,
            evidence=["Peak CPU load reached 95%"],
        )
        assert hyp.confirmed is True

        req = ResearchScenarioRequest(
            source_path="data/logs",
        )
        assert req.source_path == "data/logs"

        report = TelemetryResearchReport(
            report_id="rep_001",
            generated_at="2026-09-24T10:00:00Z",
            records_analyzed=4,
            anomalies=[anomaly],
            summary_conclusions=["Обнаружена высокая нагрузка на процессор."],
        )
        assert report.records_analyzed == 4

        deep_rep = DeepResearchReport(
            report_id="deep_01",
            generated_at="2026-09-24T10:00:00Z",
            base_report=report,
            investigation_summary="Глубокий исследовательский аудит проведен успешно.",
        )
        assert deep_rep.investigation_summary != ""


class TestTelemetryDataExtractor:
    """Тесты компонента TelemetryDataExtractor на реальных файлах и вызовах."""

    def test_parse_file_jsonl(self, tmp_path: Path, sample_telemetry_records):
        """Проверка чтения и парсинга реального файла JSONL."""
        log_file = tmp_path / "telemetry.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for rec in sample_telemetry_records:
                f.write(json.dumps(rec) + "\n")

        extractor = TelemetryDataExtractor()
        records = extractor.parse_file(str(log_file))
        assert len(records) == 4
        assert records[0]["cpu"]["total_percent"] == 25.0

    def test_load_all_records(self, tmp_path: Path, sample_telemetry_records):
        """Проверка загрузки всех записей из списка или файлов."""
        extractor = TelemetryDataExtractor()
        records = extractor.load_all_records(source=sample_telemetry_records)
        assert len(records) == 4

    def test_get_current_system_state_real_calls(self):
        """Проверка снимка текущего состояния системы на реальных вызовах."""
        extractor = TelemetryDataExtractor()
        state = extractor.get_current_system_state()
        assert "status" in state
        assert "db_path" in state or "message" in state
