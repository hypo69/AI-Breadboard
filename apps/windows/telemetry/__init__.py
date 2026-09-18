# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System and Hardware Telemetry Module Initialization
# =============================================================================
# Description:
#   Exports core system metrics models, sensor probers, and telemetry collectors.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""System and Hardware telemetry engine exports."""

from .models import (
    AnomalyItem,
    BatteryMetrics,
    CpuMetrics,
    DiskIoMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
    HardwareNode,
    HardwareSensor,
    MemoryMetrics,
    NetworkInterfaceMetrics,
    NetworkPortMetrics,
    PhysicalDiskHealth,
    ProcessMetrics,
    RamStickInfo,
    SystemDiagnosticReport,
    SystemHealthAlerts,
    SystemSnapshot,
)
from .sensors import get_hardware_sensors
from .collector import SystemCollector
from .storage import TelemetryStorage
from .service import TelemetryLoggerService
from src.ai.observability.system_engine import SystemDiagnosticEngine

__all__ = [
    "CpuMetrics",
    "MemoryMetrics",
    "RamStickInfo",
    "GpuMetrics",
    "DiskPartitionMetrics",
    "PhysicalDiskHealth",
    "DiskIoMetrics",
    "NetworkInterfaceMetrics",
    "NetworkPortMetrics",
    "BatteryMetrics",
    "SystemHealthAlerts",
    "ProcessMetrics",
    "HardwareSensor",
    "HardwareNode",
    "SystemSnapshot",
    "AnomalyItem",
    "SystemDiagnosticReport",
    "get_hardware_sensors",
    "SystemCollector",
    "SystemDiagnosticEngine",
    "TelemetryStorage",
    "TelemetryLoggerService",
]
