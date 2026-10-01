# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research -   Init  
# =============================================================================
# Description:
#   Пакет исследования логов телеметрии, визуализации и FastAPI Web GUI.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Пакет исследования логов телеметрии, визуализации и FastAPI Web GUI."""

from .analyzer import TelemetryResearcher
from .charts import TelemetryChartGenerator
from .extractor import TelemetryDataExtractor
from .models import (
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
from .diagnostic_engine import DiagnosticEngine, SystemDiagnosticEngine
from .deep_diagnostics import DeepDiagnosticsEngine
from .incident_detector import IncidentDetector
from .reboot_analyzer import WindowsRebootAnalyzer
from .aggregator import TelemetryAggregator
from .grouped_telemetry import (
    GroupedTelemetryBuilder,
    GroupDiagnoseRequest,
    GroupDiagnosticResult,
    SynthesisRequest,
    SynthesisDiagnosticResult,
)
from .compactor import TelemetryCompactor, compute_percentile
from .hardware_history_manager import HardwareHistoryManager
from .hardware_auditor import HardwareAuditor
from .audit_startup_checker import AuditStartupChecker, StartupAuditResult, run_startup_audit

__all__ = [
    "TelemetryResearcher",
    "TelemetryChartGenerator",
    "TelemetryDataExtractor",
    "TelemetryResearchReport",
    "DeepResearchReport",
    "ChartConfig",
    "MetricPoint",
    "MetricStats",
    "AnomalyEvent",
    "DeviceEventSummary",
    "TimeSeriesDataset",
    "CorrelationMatrixItem",
    "HypothesisResult",
    "ResearchScenarioRequest",
    "DiagnosticEngine",
    "SystemDiagnosticEngine",
    "DeepDiagnosticsEngine",
    "IncidentDetector",
    "WindowsRebootAnalyzer",
    "TelemetryAggregator",
    "GroupedTelemetryBuilder",
    "GroupDiagnoseRequest",
    "GroupDiagnosticResult",
    "SynthesisRequest",
    "SynthesisDiagnosticResult",
    "TelemetryCompactor",
    "compute_percentile",
    "HardwareHistoryManager",
    "HardwareAuditor",
    "AuditStartupChecker",
    "StartupAuditResult",
    "run_startup_audit",
]
