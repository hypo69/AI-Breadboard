# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core -   Init  
# =============================================================================
# Description:
#   Core Windows API bindings and data models
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 15:15:00
# =============================================================================

"""Core Windows API bindings and data models"""

from .winapi import WinAPI
from .data_model import ProcessInfo, ThreadInfo, ModuleInfo, HandleInfo, MemoryInfo, ServiceInfo, DriverInfo, DeviceInfo, SystemState
from .correlation_engine import CorrelationEngine
from .diagnostics import DiagnosticsEngine
from .system_restore import WindowsSystemRestoreManager
from .system_param_manager import ParameterCategory, ParameterChangeRecord, ParameterType, SafeSystemParamManager, SystemParameter
from .process_audit_manager import ProcessAuditManager, ProcessTreeNode, TelemetrySensorStatus
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
    'WindowsSystemRestoreManager',
    'SafeSystemParamManager',
    'SystemParameter',
    'ParameterCategory',
    'ParameterType',
    'ParameterChangeRecord',
    'ProcessAuditManager',
    'ProcessTreeNode',
    'TelemetrySensorStatus',
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