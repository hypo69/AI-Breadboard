# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Windows Diagnostic & Administration Center Package
# =============================================================================
# Description:
#   Комплексный набор инструментов диагностики, аудита, оптимизации,
#   безопасности и SafeOps управления для Windows.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI Windows Diagnostic & Administration Center."""

__version__ = "2.0.0"
__author__ = "hypo69"

from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
from apps.windows.ai_w64_collector import AIW64Collector, get_w64_collector, start_w64_collector, stop_w64_collector
from apps.windows.ai_w64_etw_collector import AIW64ETWCollector
from apps.windows.core.data_model import (
    AppCategory,
    AppExecutionInfo,
    InstalledAppInfo,
    SoftwareAuditReport,
    SystemState,
)
from apps.windows.core.models import (
    ActionType,
    AuditFinding,
    DomainAuditResult,
    FullAuditReport,
    HealthScoreSummary,
    InvestigationReport,
    RemediationAction,
    RiskLevel,
)
from apps.windows.core.root_cause_engine import RootCauseEngine
from apps.windows.core.safe_executor import SafeExecutor
from apps.windows.core.software_audit import SoftwareAuditEngine
from apps.windows.core.winapi import WinAPI
from apps.windows.process_intelligence import ProcessIntelligence
from apps.windows.router import init_router, router

__all__ = [
    "WinAPI",
    "SystemState",
    "ProcessIntelligence",
    "SoftwareAuditEngine",
    "InstalledAppInfo",
    "AppCategory",
    "AppExecutionInfo",
    "SoftwareAuditReport",
    "RootCauseEngine",
    "SafeExecutor",
    "WindowsAIDiagnostician",
    "WindowsAIRootCauseAnalyzer",
    "AIW64Collector",
    "AIW64ETWCollector",
    "get_w64_collector",
    "start_w64_collector",
    "stop_w64_collector",
    "RiskLevel",
    "ActionType",
    "RemediationAction",
    "AuditFinding",
    "DomainAuditResult",
    "HealthScoreSummary",
    "FullAuditReport",
    "InvestigationReport",
    "init_router",
    "router",
]
