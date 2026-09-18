"""
Core Windows API bindings and data models
"""

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
from .system_restore import WindowsSystemRestoreManager
from .system_param_manager import (
    ParameterCategory,
    ParameterChangeRecord,
    ParameterType,
    SafeSystemParamManager,
    SystemParameter,
)
from .process_audit_manager import (
    ProcessAuditManager,
    ProcessTreeNode,
    TelemetrySensorStatus,
)

__all__ = [
    "WinAPI",
    "ProcessInfo",
    "ThreadInfo",
    "ModuleInfo",
    "HandleInfo",
    "MemoryInfo",
    "ServiceInfo",
    "DriverInfo",
    "DeviceInfo",
    "SystemState",
    "CorrelationEngine",
    "DiagnosticsEngine",
    "WindowsSystemRestoreManager",
    "SafeSystemParamManager",
    "SystemParameter",
    "ParameterCategory",
    "ParameterType",
    "ParameterChangeRecord",
    "ProcessAuditManager",
    "ProcessTreeNode",
    "TelemetrySensorStatus",
]

