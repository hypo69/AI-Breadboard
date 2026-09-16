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
]
