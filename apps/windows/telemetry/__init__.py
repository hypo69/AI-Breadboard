# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry -   Init  
# =============================================================================
# Description:
#   Exports core system metrics models, sensor probers, and telemetry collectors.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 01:45:00
# =============================================================================

"""Exports core system metrics models, sensor probers, and telemetry collectors."""

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
    ProcessLifecycleEvent,
    ProcessMetrics,
    ProcessNetworkActivity,
    ProcessProvenanceInfo,
    ProcessProvenanceReport,
    ProcessTokenInfo,
    RamStickInfo,
    StorageBatteryWearReport,
    SystemDiagnosticReport,
    SystemHealthAlerts,
    SystemSnapshot,
    W64CollectorStatus,
    W64SystemEvent,
    ETWTraceEvent,
)
from .sensors import get_hardware_sensors
from .sqlite import TelemetryStorage
from .collector import SystemCollector
from .service import TelemetryLoggerService
from .telemetry_config import TelemetryConfigManager
from .json_logger import TelemetryJsonLogger
from .file_collector import FileCollector
from .sensor_collector import SensorCollector
from .device_flapping_sensor import DeviceFlappingSensor, DeviceTransitionEvent
from .windows_storage_sensor import (
    StorageDiskHealthInfo,
    WindowsStorageSensor,
    collect_storage_snapshot,
    save_snapshot,
)
from .storage_usage import WindowsStorageUsageCollector
from .w64_collector import (
    AIW64Collector,
    get_w64_collector,
    start_w64_collector,
    stop_w64_collector,
)
from .w64_etw_collector import AIW64ETWCollector
from apps.windows.telemetry_research.aggregator import TelemetryAggregator
from apps.windows.telemetry_research.grouped_telemetry import GroupedTelemetryBuilder
from apps.windows.telemetry_research.incident_detector import IncidentDetector
from apps.windows.telemetry_research.reboot_analyzer import WindowsRebootAnalyzer
from apps.windows.telemetry_research.hardware_auditor import HardwareAuditor
from apps.windows.telemetry_research.deep_diagnostics import DeepDiagnosticsEngine
from apps.windows.telemetry_research.hardware_history_manager import HardwareHistoryManager



__all__ = [
    "AIW64Collector",
    "AIW64ETWCollector",
    "get_w64_collector",
    "start_w64_collector",
    "stop_w64_collector",
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
    "ProcessProvenanceInfo",
    "ProcessLifecycleEvent",
    "ProcessProvenanceReport",
    "ProcessTokenInfo",
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
    "IncidentDetector",
    "WindowsRebootAnalyzer",
    "GroupedTelemetryBuilder",
    "TelemetryCompactor",
    "AuditStartupChecker",
    "StorageDiskHealthInfo",
    "WindowsStorageSensor",
    "WindowsStorageUsageCollector",
    "collect_storage_snapshot",
    "save_snapshot",
    "W64CollectorStatus",
    "W64SystemEvent",
    "ETWTraceEvent",
    "init_telemetry_database",
    "get_default_telemetry_db_path",
]


def __getattr__(name: str):
    """Ленивый импорт диагностического движка для предотвращения циклических зависимостей."""
    if name in ("DiagnosticEngine", "SystemDiagnosticEngine"):
        from apps.windows.telemetry_research.diagnostic_engine import DiagnosticEngine, SystemDiagnosticEngine
        if name == "DiagnosticEngine":
            return DiagnosticEngine
        return SystemDiagnosticEngine
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")