# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK Core - Package Root
# =============================================================================
# Description:
#   Ядро SafeOps, системной диагностики, аудита и безопасности Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core import SafeExecutor, WinAPI, DiagnosticsEngine
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:45:00
# =============================================================================

from __future__ import annotations
"""Ядро SafeOps, системной диагностики, аудита и безопасности Windows."""

from .winapi import WinAPI
from .data_model import (
    ProcessInfo,
    ThreadInfo,
    ModuleInfo,
    HandleInfo,
    MemoryInfo,
    ServiceInfo,
    DriverInfo,
    DeviceInfo,
    SystemState,
)
from .correlation_engine import CorrelationEngine
from .diagnostics import DiagnosticsEngine
from .safe_executor import SafeExecutor
from .root_cause_engine import RootCauseEngine
from .system_restore import WindowsSystemRestoreManager
from .system_param_manager import (
    ParameterCategory,
    ParameterChangeRecord,
    ParameterType,
    SafeSystemParamManager,
    SystemParameter,
)
from .process_audit_manager import ProcessAuditManager, ProcessTreeNode, TelemetrySensorStatus
from .models import (
    RiskLevel,
    ActionType,
    RemediationAction,
    AuditFinding,
    DomainAuditResult,
    HealthScoreSummary,
    FullAuditReport,
    InvestigationReport,
)
from .system32_models import (
    AccessType,
    ControlPlaneType,
    System32CatalogSummary,
    System32QueryFilter,
    System32Tool,
    SystemToolCategory,
    TelemetryTier,
    ToolDangerLevel,
    ToolPrivilegeLevel,
)
from .system32_catalog import System32Catalog
from .etw_pipeline import EtwPipelineStatus, EtwSessionInfo, EtwTelemetryPipeline

__all__ = [
    'WinAPI',
    'ProcessInfo',
    'ThreadInfo',
    'ModuleInfo',
    'HandleInfo',
    'MemoryInfo',
    'ServiceInfo',
    'DriverInfo',
    'DeviceInfo',
    'SystemState',
    'CorrelationEngine',
    'DiagnosticsEngine',
    'SafeExecutor',
    'RootCauseEngine',
    'WindowsSystemRestoreManager',
    'SafeSystemParamManager',
    'SystemParameter',
    'ParameterCategory',
    'ParameterType',
    'ParameterChangeRecord',
    'ProcessAuditManager',
    'ProcessTreeNode',
    'TelemetrySensorStatus',
    'RiskLevel',
    'ActionType',
    'RemediationAction',
    'AuditFinding',
    'DomainAuditResult',
    'HealthScoreSummary',
    'FullAuditReport',
    'InvestigationReport',
    'AccessType',
    'ControlPlaneType',
    'TelemetryTier',
    'ToolDangerLevel',
    'ToolPrivilegeLevel',
    'System32Tool',
    'System32QueryFilter',
    'System32CatalogSummary',
    'SystemToolCategory',
    'System32Catalog',
    'EtwPipelineStatus',
    'EtwSessionInfo',
    'EtwTelemetryPipeline',
]