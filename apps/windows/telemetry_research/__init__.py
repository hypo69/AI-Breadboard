# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Research - Compatibility Layer
# =============================================================================
# Description:
#   Слой совместимости: перенаправление импортов в apps.windows.telemetry.analytics.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research import DiagnosticEngine
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:37:00
# =============================================================================

from __future__ import annotations
"""Слой перенаправления в apps.windows.telemetry.analytics."""

from apps.windows.telemetry.analytics import (
    DiagnosticEngine,
    GroupedTelemetryBuilder,
    IncidentDetector,
    RebootAnalyzer,
    TelemetryAggregator,
    TelemetryAnalyzer,
    TelemetryCompactor,
)

__all__ = [
    "DiagnosticEngine",
    "GroupedTelemetryBuilder",
    "IncidentDetector",
    "RebootAnalyzer",
    "TelemetryAggregator",
    "TelemetryAnalyzer",
    "TelemetryCompactor",
]
