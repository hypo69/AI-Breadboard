# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Sensors
# =============================================================================
# Description:
#   Движок считывания показаний температурных датчиков, напряжений и вентиляторов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sensors import get_hardware_sensors
#
#     res = get_hardware_sensors()
#
# File: sensors.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:00:00
# =============================================================================

from __future__ import annotations
"""Движок считывания показаний аппаратных сенсоров, сетевых метрик и скорости FAST.com."""

import json
import os
import subprocess
from typing import List, Optional
try:
    import wmi
    _WMI_AVAILABLE = True
except ImportError:
    _WMI_AVAILABLE = False
from logger import logger
from .models import HardwareSensor
from .internet_speed import InternetSpeedSensor
from .sensor_registry import SensorProvider

# NOTE: GPU temperature, power, and fan sensors are sourced from:
#   1. GpuProber._probe_nvidia() -> HardwareMonitor.get_gpu_metrics()
#   2. sensor_collector.extract_sensor_readings() normalizes GpuMetrics to sensor_id format

def _probe_acpi_thermal_zones() -> List[HardwareSensor]:
    """Сбор данных температурных зон Windows ACPI через CIM с fallback на WMI.

    Returns:
        List[HardwareSensor]: Список показаний термальных зон ACPI.
    """
    sensors: List[HardwareSensor] = []
    if os.name != 'nt':
        return sensors

    # 1. Первичный сбор через CIM (Get-CimInstance)
    try:
        cmd = [
            'powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
            'Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | '
            'Select-Object InstanceName, CurrentTemperature | ConvertTo-Json -Compress'
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout.strip())
            items = [raw_data] if isinstance(raw_data, dict) else (raw_data if isinstance(raw_data, list) else [])
            for idx, zone in enumerate(items):
                raw_temp = zone.get('CurrentTemperature')
                if raw_temp and raw_temp > 0:
                    celsius = round(float(raw_temp) / 10.0 - 273.15, 1)
                    if -20.0 <= celsius <= 125.0:
                        zone_name = zone.get('InstanceName') or f'Thermal Zone {idx}'
                        sensor = HardwareSensor(
                            sensor_id=f'acpi_thermal_{idx}',
                            name=f'ACPI {zone_name}',
                            category='temperature',
                            value=celsius,
                            unit='°C'
                        )
                        sensor.provider = SensorProvider.CIM_SYSTEM
                        sensors.append(sensor)
            if sensors:
                return sensors
    except Exception as ex:
        logger.debug(f'CIM ACPI thermal probe skipped or error: {ex}')

    # 2. Fallback / слой совместимости через WMI
    try:
        import wmi
        import pythoncom
        pythoncom.CoInitialize()
        w = wmi.WMI(namespace='root\\wmi')
        for idx, zone in enumerate(w.MSAcpi_ThermalZoneTemperature()):
            raw_temp = getattr(zone, 'CurrentTemperature', None)
            if raw_temp and raw_temp > 0:
                celsius = round(float(raw_temp) / 10.0 - 273.15, 1)
                if -20.0 <= celsius <= 125.0:
                    zone_name = getattr(zone, 'InstanceName', f'Thermal Zone {idx}')
                    sensor = HardwareSensor(
                        sensor_id=f'acpi_thermal_{idx}',
                        name=f'ACPI {zone_name}',
                        category='temperature',
                        value=celsius,
                        unit='°C'
                    )
                    sensor.provider = SensorProvider.WMI_FALLBACK
                    sensors.append(sensor)
    except Exception as ex:
        logger.debug(f'WMI ACPI thermal fallback probe skipped: {ex}')

    return sensors

def _probe_network_sensors() -> List[HardwareSensor]:
    """Probe network interface metrics using Windows native tools.

    Returns:
        List[HardwareSensor]: Network interface telemetry as sensors with provider marker.
    """
    sensors: List[HardwareSensor] = []
    try:
        import psutil
        current_net_io = psutil.net_io_counters(pernic=True)
        if current_net_io:
            for name, stats in current_net_io.items():
                # Create sensors with provider marker
                s1 = HardwareSensor(sensor_id=f'net_{name}_bytes_recv', name=f'Network {name} Bytes Received', category='network', value=round(stats.bytes_recv, 2), unit='B')
                s1.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s1)
                
                s2 = HardwareSensor(sensor_id=f'net_{name}_bytes_sent', name=f'Network {name} Bytes Sent', category='network', value=round(stats.bytes_sent, 2), unit='B')
                s2.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s2)
                
                s3 = HardwareSensor(sensor_id=f'net_{name}_packets_recv', name=f'Network {name} Packets Received', category='network', value=stats.packets_recv, unit='pkts')
                s3.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s3)
                
                s4 = HardwareSensor(sensor_id=f'net_{name}_packets_sent', name=f'Network {name} Packets Sent', category='network', value=stats.packets_sent, unit='pkts')
                s4.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s4)
                
                s5 = HardwareSensor(sensor_id=f'net_{name}_errors_recv', name=f'Network {name} Errors Received', category='network', value=stats.errin, unit='errors')
                s5.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s5)
                
                s6 = HardwareSensor(sensor_id=f'net_{name}_errors_sent', name=f'Network {name} Errors Sent', category='network', value=stats.errout, unit='errors')
                s6.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s6)
                
                s7 = HardwareSensor(sensor_id=f'net_{name}_dropped_recv', name=f'Network {name} Dropped Received', category='network', value=stats.dropin, unit='pkts')
                s7.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s7)
                
                s8 = HardwareSensor(sensor_id=f'net_{name}_dropped_sent', name=f'Network {name} Dropped Sent', category='network', value=stats.dropout, unit='pkts')
                s8.provider = SensorProvider.NETWORK_SENSOR
                sensors.append(s8)
    except Exception as ex:
        logger.debug(f'Network sensor probe failed: {ex}')
    return sensors

def _probe_internet_speed_sensors() -> List[HardwareSensor]:
    """Собрать показания скорости интернета и характеристик сети FAST.com.

    Returns:
        List[HardwareSensor]: Метрики скорости интернета и задержки с маркером провайдера.
    """
    sensors: List[HardwareSensor] = []
    try:
        sensor = InternetSpeedSensor()
        metrics = sensor.measure_internet_speed()

        s1 = HardwareSensor(
            sensor_id='internet_ping',
            name='Internet Ping',
            category='network',
            value=round(metrics.get('ping_ms', 0.0), 2),
            unit='ms'
        )
        s1.provider = SensorProvider.INTERNET_SPEED
        sensors.append(s1)

        s2 = HardwareSensor(
            sensor_id='internet_download',
            name='Internet Download Speed',
            category='network',
            value=round(metrics.get('download_mbps', 0.0), 2),
            unit='Mbps'
        )
        s2.provider = SensorProvider.INTERNET_SPEED
        sensors.append(s2)

        s3 = HardwareSensor(
            sensor_id='internet_upload',
            name='Internet Upload Speed',
            category='network',
            value=round(metrics.get('upload_mbps', 0.0), 2),
            unit='Mbps'
        )
        s3.provider = SensorProvider.INTERNET_SPEED
        sensors.append(s3)

        s4 = HardwareSensor(
            sensor_id='internet_bufferbloat',
            name='Internet Bufferbloat',
            category='network',
            value=round(metrics.get('bufferbloat_ms', 0.0), 2),
            unit='ms'
        )
        s4.provider = SensorProvider.INTERNET_SPEED
        sensors.append(s4)

        s5 = HardwareSensor(
            sensor_id='internet_latency_loaded',
            name='Internet Loaded Latency',
            category='network',
            value=round(metrics.get('latency_loaded_ms', 0.0), 2),
            unit='ms'
        )
        s5.provider = SensorProvider.INTERNET_SPEED
        sensors.append(s5)
    except Exception as ex:
        logger.debug(f'Ошибка опроса сенсора скорости интернета: {ex}')
    return sensors

def _probe_storage_sensors() -> List[HardwareSensor]:
    """Сбор сенсоров температуры и надежности накопителей.

    :return: Список объектов HardwareSensor для дисков с provider marker.
    """
    sensors: List[HardwareSensor] = []
    if os.name != 'nt':
        return sensors
    try:
        from apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
        sensor = WindowsStorageSensor(timeout_sec=30)
        disks = sensor.get_physical_disks()
        for disk in disks:
            disk_slug = disk.device_id.replace('\\', '_').replace('.', '_')
            if disk.temperature_c is not None:
                s1 = HardwareSensor(sensor_id=f'disk_temp_{disk_slug}', name=f'{disk.friendly_name} Temperature', category='temperature', value=float(disk.temperature_c), unit='°C')
                s1.provider = SensorProvider.WINDOWS_STORAGE
                sensors.append(s1)
            if disk.wear_percentage is not None:
                s2 = HardwareSensor(sensor_id=f'disk_wear_{disk_slug}', name=f'{disk.friendly_name} Wear', category='wear', value=float(disk.wear_percentage), unit='%')
                s2.provider = SensorProvider.WINDOWS_STORAGE
                sensors.append(s2)
    except Exception as ex:
        logger.debug(f'Ошибка сбора сенсоров накопителей: {ex}')
    return sensors

def _probe_cloud_storage_sensors() -> List[HardwareSensor]:
    """Сбор сенсоров свободного и занятого места для облачного хранилища OneDrive.

    Returns:
        List[HardwareSensor]: Список сенсоров для дисков OneDrive с provider marker.
    """
    import shutil
    sensors: List[HardwareSensor] = []
    od_paths: List[str] = []
    for env_var in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        val = os.environ.get(env_var)
        if val and os.path.exists(val) and (val not in od_paths):
            od_paths.append(val)
    if not od_paths:
        home = os.path.expanduser('~')
        candidate = os.path.join(home, 'OneDrive')
        if os.path.exists(candidate):
            od_paths.append(candidate)
    if os.name == 'nt':
        try:
            import winreg
            for subkey in ('Software\\Microsoft\\OneDrive\\Accounts\\Personal', 'Software\\Microsoft\\OneDrive\\Accounts\\Business1', 'Software\\Microsoft\\OneDrive'):
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey) as k:
                        val, _ = winreg.QueryValueEx(k, 'UserFolder')
                        if val and os.path.exists(val) and (val not in od_paths):
                            od_paths.append(val)
                except OSError:
                    pass
        except Exception:
            pass
    for idx, od_path in enumerate(od_paths):
        try:
            usage = shutil.disk_usage(od_path)
            free_gb = round(usage.free / 1024 ** 3, 2)
            total_gb = round(usage.total / 1024 ** 3, 2)
            used_pct = round(usage.used / max(usage.total, 1) * 100.0, 1)
            slug = f'_{idx + 1}' if len(od_paths) > 1 else ''
            label_suffix = f' ({os.path.basename(od_path)})' if len(od_paths) > 1 else ''
            
            s1 = HardwareSensor(sensor_id=f'onedrive{slug}_free_gb', name=f'OneDrive Free Space{label_suffix}', category='storage', value=free_gb, unit='GB')
            s1.provider = SensorProvider.SENSOR_COLLECTOR
            sensors.append(s1)
            
            s2 = HardwareSensor(sensor_id=f'onedrive{slug}_used_percent', name=f'OneDrive Used Percent{label_suffix}', category='storage', value=used_pct, unit='%')
            s2.provider = SensorProvider.SENSOR_COLLECTOR
            sensors.append(s2)
            
            s3 = HardwareSensor(sensor_id=f'onedrive{slug}_total_gb', name=f'OneDrive Total Capacity{label_suffix}', category='storage', value=total_gb, unit='GB')
            s3.provider = SensorProvider.SENSOR_COLLECTOR
            sensors.append(s3)
        except Exception as ex:
            logger.debug(f'Ошибка сбора сенсора для OneDrive ({od_path}): {ex}')
    return sensors

def get_hardware_sensors() -> List[HardwareSensor]:
    """Retrieve all available hardware sensors across all supported backends.
    
    NOTE: GPU sensors (temperature, power, fan) are NOT included here to avoid
    duplication. They are collected via GpuProber in HardwareMonitor.get_gpu_metrics()
    and then normalized by SensorCollector.extract_sensor_readings().

    Returns:
        List[HardwareSensor]: Consolidated list of active hardware sensors.
    """
    all_sensors: List[HardwareSensor] = []
    # GPU sensors excluded - collected via GpuProber to avoid duplicate nvidia-smi calls
    all_sensors.extend(_probe_acpi_thermal_zones())
    all_sensors.extend(_probe_storage_sensors())
    all_sensors.extend(_probe_cloud_storage_sensors())
    all_sensors.extend(_probe_network_sensors())
    all_sensors.extend(_probe_internet_speed_sensors())
    return all_sensors