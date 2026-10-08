# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Contracts - Hardware Models
# =============================================================================
# Description:
#   Zero-dependency контракты для спецификаций аппаратного обеспечения и датчиков.
#
# Usage Examples:
#   Python API:
#     from apps.windows.contracts.hardware import CpuMetrics, GpuMetrics, MemoryMetrics
#
# File: hardware.py
# Project: ai-breadboard
# Package: apps.windows.contracts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:39:00
# =============================================================================

from __future__ import annotations
"""Контракты и модели аппаратных датчиков, паспортов железа и телеметрических срезов."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CpuInventoryInfo(BaseModel):
    """Паспорт физического процессора (CPU Inventory)."""
    processor_id: int = 0
    name: str = ""
    vendor: str = ""
    architecture: str = "x86_64"
    physical_cores: int = 1
    logical_cores: int = 1
    base_frequency_mhz: float = 0.0
    max_frequency_mhz: float = 0.0
    l2_cache_kb: Optional[int] = None
    l3_cache_kb: Optional[int] = None
    socket: str = ""
    features: List[str] = Field(default_factory=list)


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


class CpuTelemetrySample(BaseModel):
    """Срез телеметрии нагрузки и температур процессора."""
    timestamp: str = ""
    created_at: float = 0.0
    processor_id: int = 0
    total_percent: float = 0.0
    user_percent: float = 0.0
    kernel_percent: float = 0.0
    frequency_mhz: float = 0.0
    temperature_c: Optional[float] = None
    package_power_w: Optional[float] = None
    core_utilization: List[float] = Field(default_factory=list)
    core_temperatures: List[float] = Field(default_factory=list)


class RamModuleInventoryInfo(BaseModel):
    """Паспорт физического модуля (планки) оперативной памяти (SPD)."""
    slot_id: int = 0
    bank_label: str = "DIMM"
    device_locator: str = ""
    serial_number: str = ""
    part_number: str = ""
    manufacturer: str = ""
    capacity_bytes: int = 0
    capacity_gb: float = 0.0
    speed_mhz: int = 0
    memory_type: str = "DDR4"
    form_factor: str = "DIMM"
    configured_voltage: Optional[float] = None


class MemoryMetrics(BaseModel):
    """RAM and Swap memory metrics."""
    total_gb: float = Field(default=0.0, description="Total physical RAM in GB")
    available_gb: float = Field(default=0.0, description="Available RAM in GB")
    used_gb: float = Field(default=0.0, description="Used RAM in GB")
    percent: float = Field(default=0.0, description="Memory utilization percentage")
    swap_total_gb: float = Field(default=0.0, description="Total swap space in GB")
    swap_used_gb: float = Field(default=0.0, description="Used swap space in GB")
    swap_percent: float = Field(default=0.0, description="Swap utilization percentage")


class RamTelemetrySample(BaseModel):
    """Срез телеметрии использования физической и виртуальной памяти."""
    timestamp: str = ""
    created_at: float = 0.0
    total_bytes: int = 0
    total_gb: float = 0.0
    used_bytes: int = 0
    used_gb: float = 0.0
    available_bytes: int = 0
    available_gb: float = 0.0
    percent_used: float = 0.0
    swap_total_gb: float = 0.0
    swap_used_gb: float = 0.0
    swap_percent: float = 0.0
    pool_paged_mb: Optional[float] = None
    pool_nonpaged_mb: Optional[float] = None


class GpuInventoryInfo(BaseModel):
    """Паспорт графического ускорителя (GPU Inventory)."""
    gpu_id: int = 0
    name: str = ""
    vendor: str = ""
    pci_bus_id: str = ""
    driver_version: str = ""
    driver_date: str = ""
    vram_total_bytes: int = 0
    vram_total_gb: float = 0.0
    cuda_cores: Optional[int] = None
    directx_version: str = ""
    is_primary: bool = True


class GpuMetrics(BaseModel):
    """GPU accelerator telemetry and compute backends."""
    name: str = Field(default="Unknown GPU", description="GPU device model name")
    vendor: str = Field(default="", description="GPU vendor name (NVIDIA, AMD, Intel, etc.)")
    gpu_type: str = Field(default="Discrete", description="Тип GPU (Discrete / Integrated)")
    load_percent: Optional[float] = Field(default=None, description="GPU core load percentage")
    memory_total_gb: float = Field(default=0.0, description="Total VRAM in GB")
    memory_used_gb: float = Field(default=0.0, description="Used VRAM in GB")
    memory_free_gb: float = Field(default=0.0, description="Free VRAM in GB")
    dedicated_memory_mb: Optional[float] = Field(default=None, description="Выделенная память VRAM (МБ)")
    shared_memory_mb: Optional[float] = Field(default=None, description="Общая системная память GPU (МБ)")
    memory_type: str = Field(default="Dedicated VRAM", description="Тип видеопамяти")
    directx_version: str = Field(default="DirectX 12", description="Версия DirectX")
    temperature_celsius: Optional[float] = Field(default=None, description="GPU core temperature in Celsius")
    has_cuda: bool = Field(default=False, description="CUDA support")
    has_rocm: bool = Field(default=False, description="ROCm support")
    has_oneapi: bool = Field(default=False, description="oneAPI support")
    has_directml: bool = Field(default=True, description="DirectML accelerator")
    has_vulkan: bool = Field(default=True, description="Vulkan API")
    has_opencl: bool = Field(default=True, description="OpenCL API")
    compute_apis: List[str] = Field(default_factory=list)
    ai_backends: List[str] = Field(default_factory=list)
    engines: Dict[str, float] = Field(default_factory=dict)


class GpuTelemetrySample(BaseModel):
    """Срез телеметрии графического процессора."""
    timestamp: str = ""
    created_at: float = 0.0
    gpu_id: int = 0
    core_utilization_percent: float = 0.0
    memory_utilization_percent: float = 0.0
    vram_used_bytes: int = 0
    vram_used_gb: float = 0.0
    temperature_c: Optional[float] = None
    fan_speed_percent: Optional[float] = None
    power_draw_w: Optional[float] = None
    core_clock_mhz: Optional[float] = None
    memory_clock_mhz: Optional[float] = None


class NpuMetrics(BaseModel):
    """NPU neural accelerator telemetry."""
    name: str = Field(default="NPU Accelerator", description="NPU device model name")
    vendor: str = Field(default="Intel", description="NPU vendor name")
    driver_version: str = Field(default="", description="Driver version")
    status: str = Field(default="OK", description="Device status")
    tops: Optional[float] = Field(default=None, description="TOPS")


class StorageDriveInventoryInfo(BaseModel):
    """Паспорт физического накопителя данных (NVMe / SSD / HDD)."""
    disk_id: int = 0
    device_id: str = ""
    model: str = ""
    serial_number: str = ""
    firmware_revision: str = ""
    bus_type: str = "NVMe"
    media_type: str = "SSD"
    size_bytes: int = 0
    size_gb: float = 0.0
    partitions_count: int = 1


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
    read_bytes_per_sec: float = Field(default=0.0, description="Read throughput")
    write_bytes_per_sec: float = Field(default=0.0, description="Write throughput")


class DiskTelemetrySample(BaseModel):
    """Срез телеметрии активности накопителя и очередей ввода-вывода."""
    timestamp: str = ""
    created_at: float = 0.0
    disk_id: int = 0
    read_bytes_per_sec: float = 0.0
    write_bytes_per_sec: float = 0.0
    read_ops_per_sec: float = 0.0
    write_ops_per_sec: float = 0.0
    active_time_percent: float = 0.0
    queue_length: float = 0.0
    response_time_ms: float = 0.0
    temperature_c: Optional[float] = None


class NetworkAdapterInventoryInfo(BaseModel):
    """Паспорт сетевого адаптера (Ethernet / Wi-Fi)."""
    adapter_id: str = ""
    name: str = ""
    description: str = ""
    mac_address: str = ""
    manufacturer: str = ""
    is_physical: bool = True
    speed_mbps: float = 0.0


class NetworkTelemetrySample(BaseModel):
    """Срез сетевого трафика и очередей пакетов."""
    timestamp: str = ""
    created_at: float = 0.0
    adapter_id: str = ""
    bytes_sent_per_sec: float = 0.0
    bytes_recv_per_sec: float = 0.0
    packets_sent_per_sec: float = 0.0
    packets_recv_per_sec: float = 0.0
    errors_in: int = 0
    errors_out: int = 0
    bandwidth_utilization_percent: float = 0.0


class MotherboardInventoryInfo(BaseModel):
    """Паспорт материнской платы и BIOS."""
    manufacturer: str = ""
    product: str = ""
    version: str = ""
    serial_number: str = ""
    bios_vendor: str = ""
    bios_version: str = ""
    bios_release_date: str = ""


class SystemHardwareInventory(BaseModel):
    """Полный паспорт аппаратной конфигурации системы."""
    cpu: List[CpuInventoryInfo] = Field(default_factory=list)
    ram_modules: List[RamModuleInventoryInfo] = Field(default_factory=list)
    gpus: List[GpuInventoryInfo] = Field(default_factory=list)
    disks: List[StorageDriveInventoryInfo] = Field(default_factory=list)
    network_adapters: List[NetworkAdapterInventoryInfo] = Field(default_factory=list)
    motherboard: Optional[MotherboardInventoryInfo] = None


@dataclass
class HardwareSensor:
    """Датчик аппаратного мониторинга."""
    identifier: str
    name: str
    sensor_type: str
    value: float
    unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    parent: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "identifier": self.identifier,
            "name": self.name,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "parent": self.parent,
        }
