# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Hardware Providers - Native Win Provider
# =============================================================================
# Description:
#   Провайдер нативных интерфейсов Windows (WinAPI, WMI, DXGI, SMBIOS).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.hardware.providers.native_win_provider import NativeWinProvider
#
#     service = NativeWinProvider()
#
# File: native_win_provider.py
# Project: ai-breadboard
# Package: apps.windows.modules.hardware.providers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 06:25:00
# =============================================================================

from __future__ import annotations
"""Провайдер нативных интерфейсов Windows (WinAPI, WMI, DXGI, SMBIOS)."""

import os
import platform
from typing import List, Optional
import psutil
from logger import logger
from apps.windows.hardware.base import BaseHardwareProvider, ProviderCapability, ProviderStatus, ProviderTier
from apps.windows.hardware.models import CpuInventory, GpuInventory, MemoryInventory, MemoryModule, MotherboardInventory, SensorReading, SensorSnapshot, StorageDeviceInventory, StorageInventory, SystemHardwareInventory
from apps.windows.hardware.gpu_prober import GpuProber

class NativeWinProvider(BaseHardwareProvider):
    """Нативный системный провайдер Windows (Tier 1)."""

    def __init__(self) -> None:
        """Инициализация нативного провайдера."""
        super().__init__(name='Native Windows API', tier=ProviderTier.TIER_1_NATIVE, binary_path=None)
        self._status = ProviderStatus.AVAILABLE

    def is_available(self) -> bool:
        """Нативный провайдер всегда доступен на платформе Windows."""
        return os.name == 'nt'

    def get_capabilities(self) -> List[ProviderCapability]:
        """Возможности нативного провайдера."""
        return [ProviderCapability.CPU_INVENTORY, ProviderCapability.MOTHERBOARD_INVENTORY, ProviderCapability.RAM_INVENTORY, ProviderCapability.GPU_INVENTORY, ProviderCapability.STORAGE_INVENTORY, ProviderCapability.LIVE_SENSORS]

    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать инвентарь оборудования через WMI, DXGI и WinAPI."""
        inv = SystemHardwareInventory(sources_used=[self.name])
        try:
            freq = psutil.cpu_freq()
            inv.cpu = CpuInventory(model_name=platform.processor() or 'Windows Host CPU', vendor='AuthenticAMD' if 'amd' in platform.processor().lower() else 'GenuineIntel', architecture=platform.machine(), physical_cores=psutil.cpu_count(logical=False) or 0, logical_cores=psutil.cpu_count(logical=True) or 0, base_clock_mhz=freq.current if freq else None, max_clock_mhz=freq.max if freq else None, source_provider=self.name)
        except Exception as e:
            logger.debug(f'Ошибка сбора CPU инвентаря: {e}')
        try:
            vm = psutil.virtual_memory()
            # Собираем общую информацию о памяти
            inv.memory = MemoryInventory(total_physical_gb=round(vm.total / 1024 ** 3, 2), total_available_gb=round(vm.available / 1024 ** 3, 2), source_provider=self.name)
            # Сбор данных о каждом модуле памяти через WMI (wmic)
            try:
                import subprocess, csv, io
                cmd = ['wmic', 'memorychip', 'get', 'BankLabel,Capacity,Speed,Manufacturer,PartNumber,SerialNumber', '/format:csv']
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                text = output.decode(errors='ignore')
                reader = csv.DictReader(io.StringIO(text))
                modules = []
                for row in reader:
                    try:
                        capacity_bytes = int(row.get('Capacity') or 0)
                        capacity_gb = round(capacity_bytes / 1024 ** 3, 2) if capacity_bytes else 0
                        modules.append(MemoryModule(
                            slot_label=row.get('BankLabel', '').strip() or 'N/A',
                            capacity_gb=capacity_gb,
                            memory_type='DDR',  # тип не определён, placeholder
                            speed_mhz=int(row.get('Speed') or 0) if row.get('Speed') else None,
                            manufacturer=row.get('Manufacturer', '').strip() or None,
                            part_number=row.get('PartNumber', '').strip() or None,
                            serial_number=row.get('SerialNumber', '').strip() or None,
                        ))
                    except Exception:
                        continue
                inv.memory.modules = modules
            except Exception as e:
                logger.debug(f'Ошибка сбора информации о модулях RAM: {e}')
        except Exception as e:
            logger.debug(f'Ошибка сбора RAM инвентаря: {e}')
        try:
            prober = GpuProber()
            for g in prober.probe_all():
                inv.gpus.append(GpuInventory(index=g.index, name=g.name, vendor=g.vendor, driver_version=g.driver_version, vram_total_mb=g.memory_total_mb or 0.0, source_provider=self.name))
        except Exception as e:
            logger.debug(f'Ошибка сбора GPU инвентаря: {e}')
        try:
            storage = StorageInventory(source_provider=self.name)
            try:
                from apps.windows.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
                sensor = WindowsStorageSensor(timeout_sec=30)
                phys_disks = sensor.get_physical_disks()
                for d in phys_disks:
                    wear = d.wear_percentage
                    health_pct = max(0.0, 100.0 - float(wear)) if wear is not None else None
                    storage.devices.append(StorageDeviceInventory(device_id=d.device_id, model=d.model or d.friendly_name, vendor='Standard Storage', interface_type=d.bus_type, media_type=d.media_type, size_gb=d.size_gb, serial_number=d.serial_number, health_status=d.health_status, health_pct=health_pct, temperature_c=d.temperature_c, power_on_hours=d.power_on_hours, smart_attributes=d.raw_storage_data, source_provider=self.name))
            except Exception as e:
                logger.debug(f'Ошибка сбора физических дисков: {e}')
            if not storage.devices:
                for part in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        storage.devices.append(StorageDeviceInventory(device_id=part.device, model=f'Logical Disk {part.mountpoint}', interface_type='Storage', media_type='Volume', size_gb=round(usage.total / 1024 ** 3, 2), source_provider=self.name))
                    except Exception:
                        continue
            inv.storage = storage
        except Exception as e:
            logger.debug(f'Ошибка сбора Storage инвентаря: {e}')
        inv.motherboard = MotherboardInventory(product_name='Windows Host Motherboard', manufacturer='Standard PC', source_provider=self.name)
        return inv

    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Собрать базовые показания датчиков psutil, GPU и дисков."""
        snapshot = SensorSnapshot(source_provider=self.name)
        try:
            snapshot.sensors.append(SensorReading(name='CPU Utilization', sensor_type='Load', value=psutil.cpu_percent(interval=None), unit='%', hardware_name='CPU', hardware_type='CPU'))
            snapshot.sensors.append(SensorReading(name='RAM Utilization', sensor_type='Load', value=psutil.virtual_memory().percent, unit='%', hardware_name='Memory', hardware_type='Memory'))
        except Exception:
            pass
        try:
            prober = GpuProber()
            for g in prober.probe_all():
                if g.temperature_gpu_c is not None:
                    snapshot.sensors.append(SensorReading(name=f'{g.name} Temperature', sensor_type='Temperature', value=g.temperature_gpu_c, unit='°C', hardware_name=g.name, hardware_type='GPU'))
        except Exception:
            pass
        try:
            from apps.windows.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
            sensor = WindowsStorageSensor(timeout_sec=30)
            for disk in sensor.get_physical_disks():
                if disk.temperature_c is not None:
                    snapshot.sensors.append(SensorReading(name=f'{disk.friendly_name} Temperature', sensor_type='Temperature', value=disk.temperature_c, unit='°C', hardware_name=disk.friendly_name, hardware_type='Storage'))
        except Exception as e:
            logger.debug(f'Ошибка получения сенсоров дисков: {e}')
        return snapshot