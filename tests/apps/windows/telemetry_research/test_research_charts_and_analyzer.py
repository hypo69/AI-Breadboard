# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows Telemetry_Research - Test Research Charts And Analyzer
# =============================================================================
# Description:
#   Тесты генерации графиков и аналитических сценариев гипотез.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.telemetry_research.test_research_charts_and_analyzer import TestTelemetryChartGenerator
#
#     service = TestTelemetryChartGenerator()
#
# File: test_research_charts_and_analyzer.py
# Project: ai-breadboard
# Package: tests.apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

from __future__ import annotations
"""Тесты генерации графиков и аналитических сценариев гипотез.

Updated: 2026-10-01 11:30:00"""

import json
from pathlib import Path
import pytest

from apps.windows.telemetry_research.extractor import TelemetryDataExtractor
from apps.windows.telemetry_research.charts import TelemetryChartGenerator
from apps.windows.telemetry_research.analyzer import TelemetryResearcher
from apps.windows.telemetry_research.models import ResearchScenarioRequest


@pytest.fixture
def sample_telemetry_records():
    """Набор данных телеметрии с пиковой нагрузкой, аномалиями и флэттер-событиями."""
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
            "disk_io": {"read_bytes_per_sec": 52428800, "write_bytes_per_sec": 104857600},
        },
        {
            "timestamp": "2026-09-24T10:02:00Z",
            "cpu": {"total_percent": 30.0, "temperature_celsius": 50.0},
            "memory": {"percent": 45.0, "used_gb": 7.2},
            "gpu": {"load_percent": 20.0, "temperature_celsius": 52.0},
            "disk_io": {"read_bytes_per_sec": 2097152, "write_bytes_per_sec": 1048576},
        },
    ]


class TestTelemetryChartGenerator:
    """Тестирование компонента генерации отчетов и спецификаций графиков."""

    def test_render_html_dashboard(self, sample_telemetry_records):
        """Проверка рендеринга интерактивного HTML дашборда."""
        researcher = TelemetryResearcher()
        report = researcher.analyze(sample_telemetry_records)

        chart_gen = TelemetryChartGenerator()
        html_content = chart_gen.render_html_dashboard(report)

        assert "<html" in html_content.lower()
        assert "исследование телеметрии" in html_content.lower()
        assert report.report_id in html_content

    def test_render_svg_chart(self):
        """Проверка построения векторной SVG визуализации."""
        chart_gen = TelemetryChartGenerator()
        from apps.windows.telemetry_research.models import ChartConfig

        chart = ChartConfig(
            id="test_svg",
            title="Тестовый график",
            labels=["10:00", "10:01", "10:02"],
            datasets=[{"label": "CPU (%)", "data": [10.0, 50.0, 30.0], "borderColor": "#38BDF8"}],
        )
        svg_xml = chart_gen.render_svg_chart(chart)
        assert "<svg" in svg_xml
        assert "Тестовый график" in svg_xml


class TestTelemetryResearcher:
    """Тестирование генерации исследовательского отчета и гипотез."""

    def test_analyze_records(self, sample_telemetry_records):
        """Проверка полного цикла исследования прямых записей."""
        researcher = TelemetryResearcher()
        report = researcher.analyze(sample_telemetry_records)

        assert report.records_analyzed == 3
        assert report.health_score < 100.0
        assert len(report.anomalies) >= 1

    def test_deep_research(self, sample_telemetry_records):
        """Проверка формирования глубокого исследовательского отчета DeepResearchReport."""
        researcher = TelemetryResearcher()
        deep_report = researcher.run_deep_research(scenario=ResearchScenarioRequest(records=sample_telemetry_records))

        assert deep_report.report_id != ""
        assert deep_report.investigation_summary != ""
        assert isinstance(deep_report.hypotheses, list)

    def test_analyze_empty_source(self):
        """Проверка устойчивости при анализе пустых данных."""
        researcher = TelemetryResearcher()
        report = researcher.analyze([])

        assert report.records_analyzed == 0
        assert report.health_score == 100.0
        assert len(report.anomalies) == 0
