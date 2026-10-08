# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Analytics - Package Root
# =============================================================================
# Description:
#   Аналитическое ядро телеметрии: агрегаторы, компакторы, детектор инцидентов,
#   диагностический движок и сгруппированная телеметрия.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.analytics import DiagnosticEngine, GroupedTelemetryBuilder
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.analytics
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Аналитический контур телеметрии, сжатие метрик и построение сгруппированных срезов."""

from apps.windows.telemetry.analytics.diagnostic_engine import DiagnosticEngine
from apps.windows.telemetry.analytics.grouped_telemetry import GroupedTelemetryBuilder
from apps.windows.telemetry.analytics.incident_detector import IncidentDetector
from apps.windows.telemetry.analytics.reboot_analyzer import RebootAnalyzer
from apps.windows.telemetry.analytics.aggregator import TelemetryAggregator
from apps.windows.telemetry.analytics.analyzer import TelemetryAnalyzer
from apps.windows.telemetry.analytics.compactor import TelemetryCompactor

__all__ = [
    "DiagnosticEngine",
    "GroupedTelemetryBuilder",
    "IncidentDetector",
    "RebootAnalyzer",
    "TelemetryAggregator",
    "TelemetryAnalyzer",
    "TelemetryCompactor",
]
