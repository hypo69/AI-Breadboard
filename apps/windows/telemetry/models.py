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

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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


class SystemSnapshot(BaseModel):
    """Complete system and hardware telemetry snapshot."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of snapshot",
    )
    hostname: str = Field(default="", description="Machine host name")
    os_name: str = Field(default="Windows", description="Operating system name and version")
    uptime_seconds: float = Field(default=0.0, description="System uptime in seconds")
    cpu: CpuMetrics = Field(default_factory=CpuMetrics, description="CPU metrics")
    memory: MemoryMetrics = Field(default_factory=MemoryMetrics, description="RAM and Swap metrics")
    gpus: List[GpuMetrics] = Field(default_factory=list, description="Detected GPU accelerators")
    disks: List[DiskPartitionMetrics] = Field(default_factory=list, description="Disk partitions")
    disk_io: DiskIoMetrics = Field(default_factory=DiskIoMetrics, description="Aggregate disk I/O rates")
    network: List[NetworkInterfaceMetrics] = Field(default_factory=list, description="Network interfaces")
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
