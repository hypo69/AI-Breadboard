"""System and Hardware telemetry engine exports."""
from .models import AnomalyItem, AppNetworkUsageItem, BatteryMetrics, CpuMetrics, DiskIoMetrics, DiskPartitionMetrics, DriverInfo, ForensicsActivityReport, GpuMetrics, HardwareArchiveEntry, HardwareAuditReport, HardwareChangeItem, HardwareDeviceAudit, HardwareNode, HardwareSensor, KernelThrottlingReport, MemoryMetrics, NetworkAdapterStatistics, NetworkInterfaceMetrics, NetworkPerformanceCounter, NetworkPortMetrics, NetworkUsagePeriodReport, PeripheralsNetworkReport, PhysicalDiskHealth, ProcessLeakDiagnosticsReport, ProcessLeakItem, ProcessMetrics, ProcessNetworkActivity, RamStickInfo, StorageBatteryWearReport, SystemCoreMetrics, SystemDiagnosticReport, SystemHardwareQuick, SystemHealthAlerts, SystemSnapshot
from .sensors import get_hardware_sensors
from .hardware_auditor import HardwareAuditor
from .history_manager import HardwareHistoryManager
from .storage import TelemetryStorage
from .collector import SystemCollector
from .service import TelemetryLoggerService
from .telemetry_config import TelemetryConfigManager
from .file_collector import FileCollector
from .sensor_collector import SensorCollector
from .aggregator import TelemetryAggregator
__all__ = ['CpuMetrics', 'MemoryMetrics', 'RamStickInfo', 'GpuMetrics', 'DiskPartitionMetrics', 'PhysicalDiskHealth', 'DiskIoMetrics', 'NetworkInterfaceMetrics', 'NetworkAdapterStatistics', 'NetworkPerformanceCounter', 'AppNetworkUsageItem', 'NetworkUsagePeriodReport', 'NetworkPortMetrics', 'BatteryMetrics', 'SystemHealthAlerts', 'ProcessMetrics', 'ProcessLeakItem', 'ProcessLeakDiagnosticsReport', 'ForensicsActivityReport', 'KernelThrottlingReport', 'StorageBatteryWearReport', 'PeripheralsNetworkReport', 'HardwareSensor', 'HardwareNode', 'SystemSnapshot', 'SystemCoreMetrics', 'SystemHardwareQuick', 'AnomalyItem', 'SystemDiagnosticReport', 'DriverInfo', 'HardwareDeviceAudit', 'HardwareChangeItem', 'HardwareAuditReport', 'HardwareArchiveEntry', 'get_hardware_sensors', 'HardwareAuditor', 'HardwareHistoryManager', 'TelemetryStorage', 'SystemCollector', 'TelemetryLoggerService', 'TelemetryConfigManager', 'FileCollector', 'SensorCollector', 'TelemetryAggregator', 'DeviceFlappingSensor', 'DeviceTransitionEvent', 'DeepDiagnosticsEngine', 'SystemDiagnosticEngine', 'TelemetryResearcher', 'TelemetryChartGenerator', 'TelemetryDataExtractor', 'TelemetryResearchReport', 'ChartConfig', 'MetricPoint', 'MetricStats', 'TimeSeriesDataset', 'init_research_router']
_LAZY_TELEMETRY_EXPORTS = {'DeepDiagnosticsEngine': ('apps.windows.telemetry.deep_diagnostics', 'DeepDiagnosticsEngine'), 'DeviceFlappingSensor': ('apps.windows.telemetry.device_flapping_sensor', 'DeviceFlappingSensor'), 'DeviceTransitionEvent': ('apps.windows.telemetry.device_flapping_sensor', 'DeviceTransitionEvent'), 'TelemetryResearcher': ('apps.windows.telemetry.research', 'TelemetryResearcher'), 'TelemetryChartGenerator': ('apps.windows.telemetry.research', 'TelemetryChartGenerator'), 'TelemetryDataExtractor': ('apps.windows.telemetry.research', 'TelemetryDataExtractor'), 'TelemetryResearchReport': ('apps.windows.telemetry.research', 'TelemetryResearchReport'), 'ChartConfig': ('apps.windows.telemetry.research', 'ChartConfig'), 'MetricPoint': ('apps.windows.telemetry.research', 'MetricPoint'), 'MetricStats': ('apps.windows.telemetry.research', 'MetricStats'), 'TimeSeriesDataset': ('apps.windows.telemetry.research', 'TimeSeriesDataset'), 'init_research_router': ('apps.windows.telemetry.research', 'init_research_router'), 'SystemDiagnosticEngine': ('apps.windows.observability.system_engine', 'SystemDiagnosticEngine'), 'TelemetryJsonLogger': ('apps.windows.telemetry.json_logger', 'TelemetryJsonLogger')}

def __getattr__(name: str):
    """Ленивая загрузка для экономии памяти и предотвращения циклических зависимостей."""
    if name in _LAZY_TELEMETRY_EXPORTS:
        module_path, attr_name = _LAZY_TELEMETRY_EXPORTS[name]
        module = __import__(module_path, fromlist=[attr_name])
        attr = getattr(module, attr_name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")