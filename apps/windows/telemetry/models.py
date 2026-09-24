# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System and Hardware Telemetry Data Models
# =============================================================================
# Description:
#   Pydantic data models for CPU, GPU, RAM, Disks, Network, Sensors, Processes,
#   and AI diagnostic telemetry snapshots.
#
# File: models.py
# Project: ai-breadboard
# Package: src.system
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Data models for system metrics, hardware specs, sensors, and telemetry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class TelemetryProvider(ABC):
    """Абстрактный базовый класс для всех компонентов системы, предоставляющих телеметрию."""
    
    @abstractmethod
    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает список сенсоров, предоставляемых данным компонентом."""
        pass



class CpuMetrics(BaseModel):
    """CPU usage and architecture metrics."""

    model: str = Field(default="", description="CPU model name")
    architecture: str = Field(default="x86_64", description="CPU architecture")
    physical_cores: int = Field(default=1, description="Physical core count")
    logical_cores: int = Field(default=1, description="Logical core count (threads)")
    total_percent: float = Field(default=0.0, description="Overall CPU usage percentage")
    per_core_percent: List[float] = Field(default_factory=list, description="Usage percentage per logical core")
    frequency_mhz: float = Field(default=0.0, description="Current CPU frequency in MHz")
    temperature_celsius: Optional[float] = Field(default=None, description="Package temperature in Celsius")


class MemoryMetrics(BaseModel):
    """RAM and Swap memory metrics."""

    total_gb: float = Field(default=0.0, description="Total physical RAM in GB")
    available_gb: float = Field(default=0.0, description="Available RAM in GB")
    used_gb: float = Field(default=0.0, description="Used RAM in GB")
    percent: float = Field(default=0.0, description="Memory utilization percentage")
    swap_total_gb: float = Field(default=0.0, description="Total swap space in GB")
    swap_used_gb: float = Field(default=0.0, description="Used swap space in GB")
    swap_percent: float = Field(default=0.0, description="Swap utilization percentage")


class GpuMetrics(BaseModel):
    """GPU accelerator telemetry."""

    name: str = Field(default="Unknown GPU", description="GPU device model name")
    load_percent: Optional[float] = Field(default=None, description="GPU core load percentage")
    memory_total_gb: float = Field(default=0.0, description="Total VRAM in GB")
    memory_used_gb: float = Field(default=0.0, description="Used VRAM in GB")
    memory_free_gb: float = Field(default=0.0, description="Free VRAM in GB")
    temperature_celsius: Optional[float] = Field(default=None, description="GPU core temperature in Celsius")
    has_cuda: bool = Field(default=False, description="CUDA support availability")
    has_directml: bool = Field(default=False, description="DirectML accelerator availability")


class DiskPartitionMetrics(BaseModel):
    """Storage partition metrics."""

    device: str = Field(default="", description="Partition mount device or drive letter")
    mountpoint: str = Field(default="", description="Mount point path")
    fstype: str = Field(default="", description="Filesystem type")
    total_gb: float = Field(default=0.0, description="Total capacity in GB")
    used_gb: float = Field(default=0.0, description="Used space in GB")
    free_gb: float = Field(default=0.0, description="Free space in GB")
    percent: float = Field(default=0.0, description="Utilization percentage")


class DiskIoMetrics(BaseModel):
    """Disk read and write I/O rates."""

    read_bytes_per_sec: float = Field(default=0.0, description="Read throughput in bytes/s")
    write_bytes_per_sec: float = Field(default=0.0, description="Write throughput in bytes/s")
    read_count_per_sec: float = Field(default=0.0, description="Read operations per second")
    write_count_per_sec: float = Field(default=0.0, description="Write operations per second")


class NetworkInterfaceMetrics(BaseModel):
    """Network adapter telemetry."""

    name: str = Field(default="", description="Adapter interface name")
    is_up: bool = Field(default=True, description="Interface link status")
    speed_mbps: int = Field(default=0, description="Link speed in Mbps")
    bytes_sent_per_sec: float = Field(default=0.0, description="Upload rate in bytes/s")
    bytes_recv_per_sec: float = Field(default=0.0, description="Download rate in bytes/s")
    ip_addresses: List[str] = Field(default_factory=list, description="Assigned IP addresses")


class ProcessMetrics(BaseModel):
    """Per-process telemetry item (Wireshark-style stream row)."""

    pid: int = Field(..., description="Process identifier")
    name: str = Field(..., description="Process binary name")
    status: str = Field(default="running", description="Process execution status")
    cpu_percent: float = Field(default=0.0, description="CPU usage percentage")
    memory_mb: float = Field(default=0.0, description="Resident memory in Megabytes")
    memory_percent: float = Field(default=0.0, description="Memory usage percentage")
    num_threads: int = Field(default=1, description="Number of active threads")
    username: Optional[str] = Field(default=None, description="Owner username")
    cmdline: Optional[str] = Field(default=None, description="Command line invocation")
    read_bytes_sec: float = Field(default=0.0, description="Disk read rate in bytes/sec")
    write_bytes_sec: float = Field(default=0.0, description="Disk write rate in bytes/sec")


class BatteryMetrics(BaseModel):
    """Battery and power state telemetry."""

    has_battery: bool = Field(default=False, description="Whether host has battery power")
    percent: Optional[float] = Field(default=None, description="Battery charge percentage")
    power_plugged: Optional[bool] = Field(default=None, description="Whether AC power is connected")
    secs_left: Optional[int] = Field(default=None, description="Seconds of battery remaining")
    power_profile: str = Field(default="Balanced", description="Active Windows power scheme")


class PhysicalDiskHealth(BaseModel):
    """Physical drive SMART and health telemetry."""

    device_id: str = Field(default="", description="Drive identifier or disk index")
    model: str = Field(default="Physical Drive", description="Drive model name")
    media_type: str = Field(default="SSD", description="Media type (NVMe, SSD, HDD)")
    size_gb: float = Field(default=0.0, description="Drive total capacity in GB")
    health_status: str = Field(default="Healthy", description="Drive health status (Healthy, Warning, Unhealthy)")
    operational_status: str = Field(default="OK", description="Operational status")
    temperature_celsius: Optional[float] = Field(default=None, description="Drive temperature if available")
    interface_type: Optional[str] = Field(default=None, description="Drive interface or bus type (NVMe, SATA, USB, etc.)")


class RamStickInfo(BaseModel):
    """Physical RAM stick SPD details."""

    bank_label: str = Field(default="DIMM", description="Memory slot label")
    capacity_gb: float = Field(default=0.0, description="Module capacity in GB")
    speed_mhz: int = Field(default=0, description="Configured clock speed in MHz/MTs")
    manufacturer: str = Field(default="Generic", description="Memory manufacturer")
    part_number: str = Field(default="", description="Module part number")
    memory_type: str = Field(default="DDR4/DDR5", description="Memory technology type")


class NetworkPortMetrics(BaseModel):
    """Active listening TCP/UDP port item."""

    port: int = Field(..., description="Listening port number")
    protocol: str = Field(default="TCP", description="Protocol: TCP / UDP")
    address: str = Field(default="0.0.0.0", description="Bind IP address")
    pid: Optional[int] = Field(default=None, description="Owning process PID")
    process_name: Optional[str] = Field(default=None, description="Owning process executable name")


class SystemHealthAlerts(BaseModel):
    """System reliability and event log alerts."""

    reboot_pending: bool = Field(default=False, description="Whether a system reboot is pending")
    critical_events_count: int = Field(default=0, description="Critical event logs in last 24h")
    latest_alert: str = Field(default="Система стабильна", description="Summary of latest health event")


class HardwareSensor(BaseModel):
    """Hardware sensor reading (AIDA64 style)."""

    sensor_id: str = Field(..., description="Unique sensor identifier")
    name: str = Field(..., description="Human readable sensor name")
    category: str = Field(default="temperature", description="Category: temperature, fan, voltage, power")
    value: float = Field(..., description="Current numeric sensor reading")
    unit: str = Field(default="°C", description="Measurement unit")
    min_value: Optional[float] = Field(default=None, description="Recorded minimum")
    max_value: Optional[float] = Field(default=None, description="Recorded maximum")


class HardwareNode(BaseModel):
    """AIDA64-like hardware component tree item."""

    category: str = Field(..., description="Component category (Motherboard, CPU, GPU, Memory, Storage)")
    name: str = Field(..., description="Device or component name")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Detailed hardware properties")
    children: List[HardwareNode] = Field(default_factory=list, description="Sub-components or devices")


class MonitorInfo(BaseModel):
    """Connected display monitor details."""

    device: str = Field(default="", description="Display device name (e.g. \\\\.\\DISPLAY1)")
    name: str = Field(default="Monitor", description="Friendly monitor name or model")
    adapter: str = Field(default="", description="Display adapter name")
    width: int = Field(default=1920, description="Display resolution width")
    height: int = Field(default=1080, description="Display resolution height")
    frequency_hz: int = Field(default=60, description="Refresh rate in Hz")
    bits_per_pixel: int = Field(default=32, description="Color bit depth")
    is_primary: bool = Field(default=False, description="Whether this is the primary display")


class WindowsUpdateInfo(BaseModel):
    """Windows Update status and recent hotfixes."""

    status: str = Field(default="Up to date", description="Overall update status")
    installed_kb_count: int = Field(default=0, description="Total installed KBs")
    recent_hotfixes: List[str] = Field(default_factory=list, description="Recent KB identifiers")
    latest_installed_on: Optional[str] = Field(default=None, description="Date of most recent update")


class OfficeSuiteInfo(BaseModel):
    """Microsoft Office and productivity suite detection telemetry."""

    installed: bool = Field(default=False, description="Whether an Office suite is installed")
    product_name: Optional[str] = Field(default=None, description="Product suite name (e.g. Microsoft 365, Office 2021)")
    version: Optional[str] = Field(default=None, description="Office suite release version string")
    publisher: Optional[str] = Field(default=None, description="Software vendor/publisher name")
    status: str = Field(default="Не установлен", description="Human-readable office status summary")


class CloudStorageInfo(BaseModel):
    """Cloud drive and synchronization storage telemetry (OneDrive)."""

    installed: bool = Field(default=False, description="Whether cloud storage drive is detected and active")
    name: str = Field(default="OneDrive", description="Cloud storage service name")
    path: Optional[str] = Field(default=None, description="Local synchronized root folder path")
    total_gb: Optional[float] = Field(default=None, description="Total storage volume capacity in GB")
    used_gb: Optional[float] = Field(default=None, description="Used space in GB")
    free_gb: Optional[float] = Field(default=None, description="Free available space in GB")
    percent_used: Optional[float] = Field(default=None, description="Storage disk utilization percentage")
    status: str = Field(default="Не настроено", description="Human-readable cloud storage status")


class SystemSnapshot(BaseModel):
    """Complete system and hardware telemetry snapshot."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of snapshot",
    )
    hostname: str = Field(default="", description="Machine host name")
    username: str = Field(default="", description="Current logged in username")
    os_name: str = Field(default="Windows", description="Operating system name and version")
    os_build: str = Field(default="", description="Operating system build number")
    system_language: str = Field(default="", description="System UI language")
    user_locale: str = Field(default="", description="User locale")
    system_locale: str = Field(default="", description="System locale")
    timezone: str = Field(default="", description="System timezone")
    codepage: str = Field(default="", description="Active system code pages")
    input_languages: List[str] = Field(default_factory=list, description="Installed keyboard input layouts")
    os_install_date: str = Field(default="", description="Operating system installation date")
    uptime_seconds: float = Field(default=0.0, description="System uptime in seconds")
    cpu: CpuMetrics = Field(default_factory=CpuMetrics, description="CPU metrics")
    memory: MemoryMetrics = Field(default_factory=MemoryMetrics, description="RAM and Swap metrics")
    ram_sticks: List[RamStickInfo] = Field(default_factory=list, description="Installed physical RAM modules")
    gpus: List[GpuMetrics] = Field(default_factory=list, description="Detected GPU accelerators")
    monitors: List[MonitorInfo] = Field(default_factory=list, description="Connected display monitors")
    updates: WindowsUpdateInfo = Field(default_factory=WindowsUpdateInfo, description="Windows Update information")
    office: OfficeSuiteInfo = Field(default_factory=OfficeSuiteInfo, description="Office suite telemetry")
    onedrive: CloudStorageInfo = Field(default_factory=CloudStorageInfo, description="OneDrive cloud storage telemetry")
    disks: List[DiskPartitionMetrics] = Field(default_factory=list, description="Disk partitions")
    physical_disks: List[PhysicalDiskHealth] = Field(default_factory=list, description="Physical storage disks and SMART health")
    disk_io: DiskIoMetrics = Field(default_factory=DiskIoMetrics, description="Aggregate disk I/O rates")
    network: List[NetworkInterfaceMetrics] = Field(default_factory=list, description="Network interfaces")
    listening_ports: List[NetworkPortMetrics] = Field(default_factory=list, description="Active listening ports and sockets")
    battery: BatteryMetrics = Field(default_factory=BatteryMetrics, description="Battery and power state")
    alerts: SystemHealthAlerts = Field(default_factory=SystemHealthAlerts, description="System health and reliability alerts")
    sensors: List[HardwareSensor] = Field(default_factory=list, description="Hardware sensor readings")
    top_processes: List[ProcessMetrics] = Field(default_factory=list, description="Top active processes")


class AnomalyItem(BaseModel):
    """Specific detected anomaly or performance bottleneck."""

    subsystem: str = Field(..., description="Subsystem (CPU, RAM, GPU, Disk, Network, Process)")
    severity: str = Field(default="warning", description="Severity level: info, warning, critical")
    title: str = Field(..., description="Brief anomaly summary")
    description: str = Field(..., description="Detailed diagnostic description")


class SystemDiagnosticReport(BaseModel):
    """AI-powered diagnostic audit report."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Audit timestamp",
    )
    health_score: int = Field(default=100, description="System health score (0-100)")
    summary: str = Field(..., description="High-level health and performance summary")
    anomalies: List[AnomalyItem] = Field(default_factory=list, description="List of detected anomalies")
    recommendations: List[str] = Field(default_factory=list, description="Actionable optimization suggestions")
    ai_model_used: str = Field(default="heuristic", description="AI Model identifier or heuristic engine")
    system_instruction: Optional[str] = Field(default=None, description="System instruction used for AI model")
    generated_prompt: Optional[str] = Field(default=None, description="Exact prompt sent to AI model")
    raw_response: Optional[str] = Field(default=None, description="Raw response text from AI provider")
    error: Optional[str] = Field(default=None, description="Error details if inference failed")
    stages: List[Dict[str, Any]] = Field(default_factory=list, description="Step-by-step audit stages")


class DriverInfo(BaseModel):
    """Сведения об установленном драйвере устройства и его актуальности."""

    name: str = Field(default="", description="Имя драйвера или сервиса")
    driver_version: str = Field(default="", description="Версия установленного драйвера")
    driver_date: Optional[str] = Field(default=None, description="Дата релиза драйвера (ISO или YYYY-MM-DD)")
    provider: str = Field(default="Unknown", description="Поставщик драйвера (NVIDIA, Intel, Microsoft и др.)")
    inf_name: Optional[str] = Field(default=None, description="Имя INF-файла драйвера (oem*.inf)")
    is_signed: bool = Field(default=True, description="Наличие цифровой подписи WHQL")
    is_inbox: bool = Field(default=False, description="Является ли драйвер стандартным (inbox) от Microsoft")
    age_days: Optional[int] = Field(default=None, description="Возраст драйвера в днях")
    currency_status: str = Field(default="Актуален", description="Статус актуальности: Актуален, Устарел, Базовый драйвер ОС")


class HardwareDeviceAudit(BaseModel):
    """Единица аудита аппаратного устройства с драйверами, датами и сенсорами."""

    device_id: str = Field(..., description="Уникальный идентификатор инстанса устройства (PnP Instance ID)")
    name: str = Field(..., description="Понятное наименование устройства")
    device_class: str = Field(default="Device", description="Класс устройства (Display, Processor, Net, DiskDrive и др.)")
    manufacturer: str = Field(default="Unknown", description="Производитель оборудования")
    install_date: Optional[str] = Field(default=None, description="Дата первой/текущей установки устройства в системе")
    status: str = Field(default="OK", description="Рабочий статус устройства (OK, Problem, Error, Disabled)")
    problem_code: int = Field(default=0, description="Код ошибки PnP (0 если исправно, 10, 43, 28 при сбое)")
    driver: Optional[DriverInfo] = Field(default=None, description="Сведения об используемом драйвере")
    sensors: List[HardwareSensor] = Field(default_factory=list, description="Сенсоры, привязанные к данному оборудованию")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные аппаратные параметры")


class HardwareChangeItem(BaseModel):
    """Зафиксированное изменение в аппаратной конфигурации или драйверах."""

    change_type: str = Field(..., description="Тип изменения: added, removed, driver_updated, status_changed, hardware_altered")
    device_id: str = Field(..., description="Идентификатор затронутого устройства")
    device_name: str = Field(..., description="Наименование устройства")
    description: str = Field(..., description="Подробное описание изменения на русском языке")
    previous_value: Optional[Dict[str, Any]] = Field(default=None, description="Предыдущее состояние параметра")
    current_value: Optional[Dict[str, Any]] = Field(default=None, description="Новое состояние параметра")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Временная метка обнаружения изменения",
    )


class HardwareAuditReport(BaseModel):
    """Полный отчет аудита аппаратного обеспечения с привязкой сенсоров и драйверов."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Время проведения аудита (UTC)",
    )
    devices_count: int = Field(default=0, description="Общее количество обнаруженных устройств")
    problem_devices_count: int = Field(default=0, description="Количество устройств с ошибками PnP")
    outdated_drivers_count: int = Field(default=0, description="Количество устройств с устаревшими драйверами")
    devices: List[HardwareDeviceAudit] = Field(default_factory=list, description="Список проаудированных устройств")
    summary: str = Field(default="", description="Сводка состояния аппаратной части")
    changes_since_last_archive: List[HardwareChangeItem] = Field(
        default_factory=list,
        description="Изменения, обнаруженные по сравнению с последним сохраненным архивом",
    )


class HardwareArchiveEntry(BaseModel):
    """Запись в архиве истории оборудования."""

    archive_id: str = Field(..., description="Уникальный идентификатор архивного снимка")
    timestamp: str = Field(..., description="Время создания архива")
    devices_count: int = Field(default=0, description="Количество устройств в архиве")
    changes_count: int = Field(default=0, description="Количество изменений, зафиксированных в этом архиве")
    report: HardwareAuditReport = Field(..., description="Полный отчет аудита оборудования")

