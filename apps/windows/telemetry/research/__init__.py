# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Telemetry Research Package
# =============================================================================
# Description:
#   Пакет исследования логов телеметрии Windows, извлечения временных рядов,
#   EDA-профилирования, расчета Health Score и генерации интерактивных графиков.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет исследования логов телеметрии и построения графиков."""

from __future__ import annotations

from apps.windows.telemetry.research.analyzer import TelemetryResearcher
from apps.windows.telemetry.research.charts import TelemetryChartGenerator
from apps.windows.telemetry.research.extractor import TelemetryDataExtractor
from apps.windows.telemetry.research.models import (
    AnomalyEvent,
    ChartConfig,
    DeviceEventSummary,
    MetricPoint,
    MetricStats,
    TelemetryResearchReport,
    TimeSeriesDataset,
)
from apps.windows.telemetry.research.router import init_research_router

__all__ = [
    "TelemetryResearcher",
    "TelemetryChartGenerator",
    "TelemetryDataExtractor",
    "TelemetryResearchReport",
    "ChartConfig",
    "MetricPoint",
    "MetricStats",
    "AnomalyEvent",
    "DeviceEventSummary",
    "TimeSeriesDataset",
    "init_research_router",
]
