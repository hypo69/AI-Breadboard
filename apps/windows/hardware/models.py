# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Normalized Hardware Data Models
# =============================================================================
# Description:
#   Единая нормализованная модель оборудования (Hardware Inventory) и телеметрии
#   датчиков реального времени, согласованная со всеми источниками данных.
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Нормализованные модели данных для оборудования и телеметрии."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CpuInventory:
    """Нормализованные данные процессора (CPU)."""
    model_name: str
    vendor: str = "Unknown"
    architecture: str = "x64"
    socket: Optional[str] = None
    physical_cores: int = 0
    logical_cores: int = 0
    base_clock_mhz: Optional[float] = None
    max_clock_mhz: Optional[float] = None
    l1_cache_kb: Optional[int] = None
    l2_cache_kb: Optional[int] = None
    l3_cache_kb: Optional[int] = None
    microcode: Optional[str] = None
    tj_max_c: Optional[float] = None
    source_provider: str = "Native"


@dataclass
class MotherboardInventory:
    """Нормализованные данные материнской платы и BIOS."""
    manufacturer: str = "Unknown"
    product_name: str = "Unknown"
    version: Optional[str] = None
    serial_number: Optional[str] = None
    chipset: Optional[str] = None
    bios_vendor: Optional[str] = None
    bios_version: Optional[str] = None
    bios_release_date: Optional[str] = None
    source_provider: str = "Native"


@dataclass
class MemoryModule:
    """Сведения об отдельном модуле оперативной памяти (DIMM)."""
    slot_label: str
    capacity_gb: float
    memory_type: str  # DDR4, DDR5, LPDDR5
    speed_mhz: Optional[int] = None
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    timings: Optional[str] = None


@dataclass
class MemoryInventory:
    """Нормализованные данные оперативной памяти."""
    total_physical_gb: float
    total_available_gb: float
    modules: List[MemoryModule] = field(default_factory=list)
    source_provider: str = "Native"


@dataclass
class GpuInventory:
    """Нормализованные данные графического адаптера (GPU)."""
    index: int
    name: str
    vendor: str  # NVIDIA, AMD, Intel
    driver_version: str
    vram_total_mb: float
    vram_type: Optional[str] = None
    bus_interface: Optional[str] = None
    pcie_link_speed: Optional[str] = None
    pcie_link_width: Optional[str] = None
    source_provider: str = "Native"


@dataclass
class StorageDeviceInventory:
    """Нормализованные данные накопителя (NVMe / SATA SSD / HDD)."""
    device_id: str
    model: str
    vendor: str = "Unknown"
    interface_type: str = "Unknown"  # NVMe, SATA, USB
    media_type: str = "Unknown"      # SSD, HDD
    size_gb: float = 0.0
    serial_number: Optional[str] = None
    firmware_revision: Optional[str] = None
    health_status: str = "OK"        # OK, Warning, Critical
    health_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    power_on_hours: Optional[int] = None
    power_cycle_count: Optional[int] = None
    tbw_written_tb: Optional[float] = None
    smart_attributes: Dict[str, Any] = field(default_factory=dict)
    source_provider: str = "Native"


@dataclass
class StorageInventory:
    """Нормализованный список всех накопителей системы."""
    devices: List[StorageDeviceInventory] = field(default_factory=list)
    source_provider: str = "Native"


@dataclass
class SystemHardwareInventory:
    """Полный объединенный инвентарь аппаратного обеспечения рабочей станции."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    cpu: Optional[CpuInventory] = None
    motherboard: Optional[MotherboardInventory] = None
    memory: Optional[MemoryInventory] = None
    gpus: List[GpuInventory] = field(default_factory=list)
    storage: Optional[StorageInventory] = None
    sources_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return asdict(self)


@dataclass
class SensorReading:
    """Единичное показание аппаратного датчика."""
    name: str
    sensor_type: str  # Temperature, Fan, Voltage, Power, Clock, Load
    value: float
    unit: str         # °C, RPM, V, W, MHz, %
    hardware_name: str
    hardware_type: str # CPU, GPU, Motherboard, Storage
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class SensorSnapshot:
    """Снимок показаний всех датчиков в реальном времени."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_provider: str = "Native"
    sensors: List[SensorReading] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return asdict(self)
