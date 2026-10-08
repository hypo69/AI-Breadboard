# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Package Root
# =============================================================================
# Description:
#   AI Windows Diagnostic & Administration Center: единый входной пакет.
#
# Usage Examples:
#   Python API:
#     from apps.windows import RiskLevel, WinAPI, SafeExecutor
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:20:00
# =============================================================================

from __future__ import annotations
"""AI Windows Diagnostic & Administration Center: слоистая чистая архитектура."""

from pathlib import Path

_modules_dir = Path(__file__).resolve().parent / "modules"
if _modules_dir.exists() and str(_modules_dir) not in __path__:
    __path__.append(str(_modules_dir))

# Контракты (Слой 1)
from apps.windows.contracts import (
    RiskLevel,
    ActionType,
    RemediationAction,
    AuditFinding,
    DomainAuditResult,
    HealthScoreSummary,
    FullAuditReport,
    InvestigationReport,
    TelemetryTier,
    ProcessState,
    ThreadState,
    ServiceState,
    ContractCpuMetrics,
    ContractMemoryMetrics,
    ContractGpuMetrics,
    ContractHardwareSensor,
    ContractSystemSnapshot,
    ContractProcessMetrics,
    ContractProcessTokenInfo,
    ContractTelemetryIncident,
)

# C-FFI Win32 (Слой 2)
from apps.windows.native import (
    win32_error_check,
    WindowsErrorDecoder,
    PDHManager,
    WindowsEventLogAPI,
    ServiceManagerFFI,
    SetupAPI,
    NativeNT,
)

# Ядро и SafeOps (Слой 4)
from apps.windows.core.winapi import WinAPI
from apps.windows.core.safe_executor import SafeExecutor
from apps.windows.core.safe_ops import SafeExecutor as SafeOpsExecutor
from apps.windows.core.root_cause_engine import RootCauseEngine
from apps.windows.core.software_audit import SoftwareAuditEngine
from apps.windows.core.data_model import (
    InstalledAppInfo,
    AppCategory,
    AppExecutionInfo,
    SoftwareAuditReport,
)

# Телеметрия (Слой 3)
from apps.windows.telemetry.w64_collector import (
    AIW64Collector,
    get_w64_collector,
    start_w64_collector,
    stop_w64_collector,
)
from apps.windows.telemetry.w64_etw_collector import AIW64ETWCollector
from apps.windows.telemetry.analytics.diagnostic_engine import DiagnosticEngine

# ИИ и Диагностика (Слой 6)
from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer

__version__ = "3.0.0"
__author__ = "hypo69"

__all__ = [
    # Контракты
    "RiskLevel",
    "ActionType",
    "RemediationAction",
    "AuditFinding",
    "DomainAuditResult",
    "HealthScoreSummary",
    "FullAuditReport",
    "InvestigationReport",
    "TelemetryTier",
    "ProcessState",
    "ThreadState",
    "ServiceState",
    "ContractCpuMetrics",
    "ContractMemoryMetrics",
    "ContractGpuMetrics",
    "ContractHardwareSensor",
    "ContractSystemSnapshot",
    "ContractProcessMetrics",
    "ContractProcessTokenInfo",
    "ContractTelemetryIncident",
    # Нативные
    "win32_error_check",
    "WindowsErrorDecoder",
    "PDHManager",
    "WindowsEventLogAPI",
    "ServiceManagerFFI",
    "SetupAPI",
    "NativeNT",
    # Core
    "WinAPI",
    "SafeExecutor",
    "SafeOpsExecutor",
    "RootCauseEngine",
    "SoftwareAuditEngine",
    "InstalledAppInfo",
    "AppCategory",
    "AppExecutionInfo",
    "SoftwareAuditReport",
    # Telemetry
    "AIW64Collector",
    "AIW64ETWCollector",
    "get_w64_collector",
    "start_w64_collector",
    "stop_w64_collector",
    "DiagnosticEngine",
    # AI
    "WindowsAIDiagnostician",
    "WindowsAIRootCauseAnalyzer",
]