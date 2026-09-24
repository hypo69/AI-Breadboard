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
    DriverInfo,
    ForensicsActivityReport,
    GpuMetrics,
    HardwareArchiveEntry,
    HardwareAuditReport,
    HardwareChangeItem,
    HardwareDeviceAudit,
    HardwareNode,
    HardwareSensor,
    KernelThrottlingReport,
    MemoryMetrics,
    NetworkInterfaceMetrics,
    NetworkPortMetrics,
    PeripheralsNetworkReport,
    PhysicalDiskHealth,
    ProcessLeakDiagnosticsReport,
    ProcessLeakItem,
    ProcessMetrics,
    ProcessNetworkActivity,
    RamStickInfo,
    StorageBatteryWearReport,
    SystemDiagnosticReport,
    SystemHealthAlerts,
    SystemSnapshot,
)
from .sensors import get_hardware_sensors
from .hardware_auditor import HardwareAuditor
from .history_manager import HardwareHistoryManager
from .storage import TelemetryStorage
from .collector import SystemCollector
from .service import TelemetryLoggerService
from .telemetry_config import TelemetryConfigManager
from .json_logger import TelemetryJsonLogger
from .file_collector import FileCollector
from .sensor_collector import SensorCollector
from .aggregator import TelemetryAggregator
from .device_flapping_sensor import DeviceFlappingSensor, DeviceTransitionEvent
from .deep_diagnostics import DeepDiagnosticsEngine
from .research import (
    ChartConfig,
    MetricPoint,
    MetricStats,
    TelemetryChartGenerator,
    TelemetryDataExtractor,
    TelemetryResearchReport,
    TelemetryResearcher,
    TimeSeriesDataset,
    init_research_router,
)

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
    "ProcessLeakItem",
    "ProcessLeakDiagnosticsReport",
    "ForensicsActivityReport",
    "KernelThrottlingReport",
    "StorageBatteryWearReport",
    "PeripheralsNetworkReport",
    "HardwareSensor",
    "HardwareNode",
    "SystemSnapshot",
    "AnomalyItem",
    "SystemDiagnosticReport",
    "DriverInfo",
    "HardwareDeviceAudit",
    "HardwareChangeItem",
    "HardwareAuditReport",
    "HardwareArchiveEntry",
    "get_hardware_sensors",
    "HardwareAuditor",
    "HardwareHistoryManager",
    "TelemetryStorage",
    "SystemCollector",
    "TelemetryLoggerService",
    "TelemetryConfigManager",
    "TelemetryJsonLogger",
    "FileCollector",
    "SensorCollector",
    "TelemetryAggregator",
    "DeviceFlappingSensor",
    "DeviceTransitionEvent",
    "DeepDiagnosticsEngine",
    "SystemDiagnosticEngine",
    "TelemetryResearcher",
    "TelemetryChartGenerator",
    "TelemetryDataExtractor",
    "TelemetryResearchReport",
    "ChartConfig",
    "MetricPoint",
    "MetricStats",
    "TimeSeriesDataset",
    "init_research_router",
]


def __getattr__(name: str):
    """Lazy import to prevent circular dependency cycles."""
    if name == "SystemDiagnosticEngine":
        from src.ai.observability.system_engine import SystemDiagnosticEngine
        return SystemDiagnosticEngine
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

