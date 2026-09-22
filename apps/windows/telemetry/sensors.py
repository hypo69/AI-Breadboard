# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware Sensors Reader
# =============================================================================
# Description:
#   Probes hardware sensors for temperatures, voltages, and fan speeds on
#   Windows via WMI, LibreHardwareMonitor/OpenHardwareMonitor namespaces,
#   and NVIDIA SMI.
#
# Examples:
#   >>> from apps.windows.telemetry.sensors import get_hardware_sensors
#   >>> sensors = get_hardware_sensors()
#   >>> for s in sensors:
#   ...     print(s.name, s.value, s.unit)
#
# File: sensors.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Prober for hardware thermal, fan, voltage, network, and internet sensors."""

from __future__ import annotations

import os
import subprocess
from typing import List, Optional

from src.logger import logger
from apps.windows.telemetry.models import HardwareSensor
from apps.windows.telemetry.internet_speed import InternetSpeedSensor


def _probe_nvidia_gpu_sensors() -> List[HardwareSensor]:
    """Probe NVIDIA GPU thermal and power sensors via nvidia-smi CLI.

    Returns:
        List[HardwareSensor]: Extracted GPU sensor objects.
    """
    sensors: List[HardwareSensor] = []
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=index,name,temperature.gpu,power.draw,fan.speed",
            "--format=csv,noheader,nounits",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            for line in proc.stdout.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    gpu_idx, gpu_name, temp_str = parts[0], parts[1], parts[2]
                    try:
                        temp_val = float(temp_str)
                        sensors.append(
                            HardwareSensor(
                                sensor_id=f"gpu_{gpu_idx}_temp",
                                name=f"{gpu_name} Core Temp",
                                category="temperature",
                                value=temp_val,
                                unit="°C",
                            )
                        )
                    except ValueError:
                        pass

                    if len(parts) >= 4 and parts[3] and parts[3] != "[N/A]":
                        try:
                            power_val = float(parts[3])
                            sensors.append(
                                HardwareSensor(
                                    sensor_id=f"gpu_{gpu_idx}_power",
                                    name=f"{gpu_name} Power",
                                    category="power",
                                    value=power_val,
                                    unit="W",
                                )
                            )
                        except ValueError:
                            pass

                    if len(parts) >= 5 and parts[4] and parts[4] != "[N/A]":
                        try:
                            fan_val = float(parts[4])
                            sensors.append(
                                HardwareSensor(
                                    sensor_id=f"gpu_{gpu_idx}_fan",
                                    name=f"{gpu_name} Fan Speed",
                                    category="fan",
                                    value=fan_val,
                                    unit="%",
                                )
                            )
                        except ValueError:
                            pass
    except Exception as ex:
        logger.debug(f"NVIDIA GPU sensor probe skipped or unavailable: {ex}")
    return sensors


def _probe_wmi_thermal_zones() -> List[HardwareSensor]:
    """Probe Windows ACPI thermal zones via WMI MSAcpi_ThermalZoneTemperature.

    Returns:
        List[HardwareSensor]: Extracted ACPI thermal sensor readings.
    """
    sensors: List[HardwareSensor] = []
    if os.name != "nt":
        return sensors

    try:
        import pythoncom
        pythoncom.CoInitialize()
        import wmi  # type: ignore

        w = wmi.WMI(namespace="root\\wmi")
        for idx, zone in enumerate(w.MSAcpi_ThermalZoneTemperature()):
            raw_temp = getattr(zone, "CurrentTemperature", None)
            if raw_temp and raw_temp > 0:
                # WMI returns temperature in tenths of Kelvin (dK): C = (dK / 10.0) - 273.15
                celsius = round((float(raw_temp) / 10.0) - 273.15, 1)
                if -20.0 <= celsius <= 125.0:
                    zone_name = getattr(zone, "InstanceName", f"Thermal Zone {idx}")
                    sensors.append(
                        HardwareSensor(
                            sensor_id=f"acpi_thermal_{idx}",
                            name=f"ACPI {zone_name}",
                            category="temperature",
                            value=celsius,
                            unit="°C",
                        )
                    )
    except Exception as ex:
        logger.debug(f"WMI ACPI thermal probe skipped or unavailable: {ex}")
    return sensors


def _probe_libre_hardware_monitor_wmi() -> List[HardwareSensor]:
    """Probe LibreHardwareMonitor or OpenHardwareMonitor WMI namespace if running.

    Returns:
        List[HardwareSensor]: Hardware sensors published to WMI by LHM / OHM.
    """
    sensors: List[HardwareSensor] = []
    if os.name != "nt":
        return sensors

    for namespace in ["root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"]:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            import wmi  # type: ignore

            w = wmi.WMI(namespace=namespace)
            for s in w.Sensor():
                s_name = getattr(s, "Name", "Sensor")
                s_type = getattr(s, "SensorType", "Temperature").lower()
                s_value = getattr(s, "Value", None)
                s_id = getattr(s, "Identifier", f"{s_name}_{s_type}")
                if s_value is not None:
                    unit = "°C" if "temp" in s_type else ("RPM" if "fan" in s_type else ("V" if "volt" in s_type else ""))
                    sensors.append(
                        HardwareSensor(
                            sensor_id=str(s_id),
                            name=str(s_name),
                            category=s_type,
                            value=round(float(s_value), 2),
                            unit=unit,
                            min_value=getattr(s, "Min", None),
                            max_value=getattr(s, "Max", None),
                        )
                    )
            if sensors:
                break
        except Exception:
            continue
    return sensors


def _probe_network_sensors() -> List[HardwareSensor]:
    """Probe network interface metrics using Windows native tools.

    Returns:
        List[HardwareSensor]: Network interface telemetry as sensors.
    """
    sensors: List[HardwareSensor] = []
    
    try:
        import psutil
        
        # Get network I/O counters using psutil (Windows native wrapper)
        current_net_io = psutil.net_io_counters(pernic=True)
        
        if current_net_io:
            for name, stats in current_net_io.items():
                # Create sensors for each interface
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_bytes_recv",
                    name=f"Network {name} Bytes Received",
                    category="network",
                    value=round(stats.bytes_recv, 2),
                    unit="B",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_bytes_sent",
                    name=f"Network {name} Bytes Sent",
                    category="network",
                    value=round(stats.bytes_sent, 2),
                    unit="B",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_packets_recv",
                    name=f"Network {name} Packets Received",
                    category="network",
                    value=stats.packets_recv,
                    unit="pkts",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_packets_sent",
                    name=f"Network {name} Packets Sent",
                    category="network",
                    value=stats.packets_sent,
                    unit="pkts",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_errors_recv",
                    name=f"Network {name} Errors Received",
                    category="network",
                    value=stats.errin,
                    unit="errors",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_errors_sent",
                    name=f"Network {name} Errors Sent",
                    category="network",
                    value=stats.errout,
                    unit="errors",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_dropped_recv",
                    name=f"Network {name} Dropped Received",
                    category="network",
                    value=stats.dropin,
                    unit="pkts",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id=f"net_{name}_dropped_sent",
                    name=f"Network {name} Dropped Sent",
                    category="network",
                    value=stats.dropout,
                    unit="pkts",
                ))
                
    except Exception as ex:
        logger.debug(f"Network sensor probe failed: {ex}")
    
    return sensors


def _probe_internet_speed_sensors() -> List[HardwareSensor]:
    """Probe internet speed metrics.

    Returns:
        List[HardwareSensor]: Internet speed metrics as sensors.
    """
    sensors: List[HardwareSensor] = []
    
    try:
        sensor = InternetSpeedSensor()
        metrics = sensor.measure_internet_speed()
        
        sensors.append(HardwareSensor(
            sensor_id="internet_ping",
            name="Internet Ping",
            category="network",
            value=round(metrics.get("ping_ms", 0.0), 2),
            unit="ms",
        ))
        
        sensors.append(HardwareSensor(
            sensor_id="internet_download",
            name="Internet Download Speed",
            category="network",
            value=round(metrics.get("download_mbps", 0.0), 2),
            unit="Mbps",
        ))
        
        sensors.append(HardwareSensor(
            sensor_id="internet_upload",
            name="Internet Upload Speed",
            category="network",
            value=round(metrics.get("upload_mbps", 0.0), 2),
            unit="Mbps",
        ))
        
        sensors.append(HardwareSensor(
            sensor_id="internet_dns",
            name="DNS Resolution Time",
            category="network",
            value=round(metrics.get("dns_ms", 0.0), 2),
            unit="ms",
        ))
        
    except Exception as ex:
        logger.debug(f"Internet speed sensor probe failed: {ex}")
    
    return sensors


def get_hardware_sensors() -> List[HardwareSensor]:
    """Retrieve all available hardware sensors across all supported backends.

    Returns:
        List[HardwareSensor]: Consolidated list of active hardware sensors.
    """
    all_sensors: List[HardwareSensor] = []
    all_sensors.extend(_probe_nvidia_gpu_sensors())
    all_sensors.extend(_probe_libre_hardware_monitor_wmi())
    all_sensors.extend(_probe_wmi_thermal_zones())
    all_sensors.extend(_probe_network_sensors())
    all_sensors.extend(_probe_internet_speed_sensors())
    return all_sensors
