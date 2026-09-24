# -*- coding: utf-8 -*-
"""S.M.A.R.T. storage diagnostics prober using smartctl and WMI."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from logger import logger


@dataclass
class SmartDriveInfo:
    """Detailed drive SMART health data."""
    device: str
    model: str
    serial: str
    firmware: str
    protocol: str
    capacity_gb: float
    health_status: str
    temperature_c: Optional[int] = None
    power_on_hours: Optional[int] = None
    power_cycles: Optional[int] = None
    percentage_used: Optional[int] = None
    reallocated_sectors: Optional[int] = None
    critical_warning: Optional[int] = None
    raw_attributes: Dict[str, Any] = field(default_factory=dict)


class SmartProber:
    """Prober for storage health via smartctl CLI or WMI."""

    _CACHE_DRIVES: List[SmartDriveInfo] = []
    _CACHE_TIME: float = 0.0
    _CACHE_TTL_SEC: float = 30.0

    def __init__(self, custom_smartctl_path: Optional[str] = None) -> None:
        """Initialize smartctl path resolution."""
        self._smartctl_bin = custom_smartctl_path or shutil.which("smartctl") or shutil.which("smartctl.exe")

    @property
    def is_available(self) -> bool:
        """Check if smartctl executable is present."""
        return self._smartctl_bin is not None

    def scan_drives(self, force_refresh: bool = False) -> List[SmartDriveInfo]:
        """Scan all drives and return their SMART health status with caching."""
        import time
        now = time.time()
        if not force_refresh and SmartProber._CACHE_DRIVES and (now - SmartProber._CACHE_TIME < SmartProber._CACHE_TTL_SEC):
            return SmartProber._CACHE_DRIVES

        if not self.is_available:
            logger.debug("smartctl utility not found in PATH; falling back to WMI disk probe")
            drives = self._fallback_wmi_scan()
            SmartProber._CACHE_DRIVES = drives
            SmartProber._CACHE_TIME = now
            return drives

        try:
            cmd = [str(self._smartctl_bin), "--scan", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0 and not result.stdout:
                logger.error(f"smartctl --scan failed: {result.stderr}")
                drives = self._fallback_wmi_scan()
                SmartProber._CACHE_DRIVES = drives
                SmartProber._CACHE_TIME = now
                return drives

            data = json.loads(result.stdout)
            devices = data.get("devices", [])
            drives: List[SmartDriveInfo] = []

            for dev in devices:
                dev_name = dev.get("name")
                if dev_name:
                    info = self.probe_device(dev_name)
                    if info:
                        drives.append(info)

            res = drives if drives else self._fallback_wmi_scan()
            SmartProber._CACHE_DRIVES = res
            SmartProber._CACHE_TIME = now
            return res
        except Exception as e:
            logger.error(f"Failed to probe SMART drives via smartctl: {e}")
            drives = self._fallback_wmi_scan()
            SmartProber._CACHE_DRIVES = drives
            SmartProber._CACHE_TIME = now
            return drives

    def probe_device(self, device_name: str) -> Optional[SmartDriveInfo]:
        """Probe a specific device for detailed SMART data."""
        if not self._smartctl_bin:
            return None

        try:
            cmd = [str(self._smartctl_bin), "-a", device_name, "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if not result.stdout:
                return None

            data = json.loads(result.stdout)
            device_info = data.get("device", {})
            smart_status = data.get("smart_status", {})
            temperature = data.get("temperature", {}).get("current")
            power_cycle = data.get("power_cycle_count")
            power_on = data.get("power_on_time", {}).get("hours")
            nvme_smart = data.get("nvme_smart_health_information_log", {})

            is_passed = smart_status.get("passed", True)
            health = "PASSED" if is_passed else "FAILING"

            percentage_used = nvme_smart.get("percentage_used")
            reallocated = None
            for table_attr in data.get("ata_smart_attributes", {}).get("table", []):
                if table_attr.get("id") == 5:
                    reallocated = table_attr.get("raw", {}).get("value")

            user_capacity = data.get("user_capacity", {}).get("bytes", 0)
            capacity_gb = round(user_capacity / (1024**3), 2) if user_capacity else 0.0

            return SmartDriveInfo(
                device=device_name,
                model=data.get("model_name", device_info.get("name", "Unknown")),
                serial=data.get("serial_number", "Unknown"),
                firmware=data.get("firmware_version", "Unknown"),
                protocol=device_info.get("protocol", "Unknown"),
                capacity_gb=capacity_gb,
                health_status=health,
                temperature_c=temperature or nvme_smart.get("temperature"),
                power_on_hours=power_on or nvme_smart.get("power_on_hours"),
                power_cycles=power_cycle or nvme_smart.get("power_cycles"),
                percentage_used=percentage_used,
                reallocated_sectors=reallocated,
                critical_warning=nvme_smart.get("critical_warning"),
                raw_attributes=data.get("ata_smart_attributes", {}),
            )
        except Exception as e:
            logger.error(f"Error probing device {device_name} with smartctl: {e}")
            return None

    def _fallback_wmi_scan(self) -> List[SmartDriveInfo]:
        """Фолбэк-сканирование накопителей через WindowsStorageSensor и WMI."""
        drives: List[SmartDriveInfo] = []

        # 1. Попытка сбора через нативный WindowsStorageSensor (MSFT_PhysicalDisk + StorageReliabilityCounter)
        try:
            from apps.windows.storage_sensors.windows_storage_sensor import WindowsStorageSensor
            sensor = WindowsStorageSensor(timeout_sec=30)
            physical_disks = sensor.get_physical_disks()
            if physical_disks:
                for d in physical_disks:
                    status_upper = d.health_status.upper()
                    is_passed = "HEALTHY" in status_upper or status_upper == "OK"
                    drives.append(
                        SmartDriveInfo(
                            device=d.device_id,
                            model=d.model or d.friendly_name,
                            serial=d.serial_number,
                            firmware=d.bus_type,
                            protocol=d.bus_type,
                            capacity_gb=d.size_gb,
                            health_status="PASSED" if is_passed else "FAILING",
                            temperature_c=int(d.temperature_c) if d.temperature_c is not None else None,
                            power_on_hours=d.power_on_hours,
                            percentage_used=int(d.wear_percentage) if d.wear_percentage is not None else None,
                            reallocated_sectors=d.read_errors_total or d.write_errors_total,
                            raw_attributes=d.raw_storage_data,
                        )
                    )
                if drives:
                    return drives
        except Exception as e:
            logger.debug(f"WindowsStorageSensor fallback skipped: {e}")

        # 2. Быстрый in-process WMI COM запрос (<10мс)
        try:
            import wmi  # type: ignore
            w = wmi.WMI()
            for disk in w.Win32_DiskDrive():
                size_bytes = int(getattr(disk, "Size", 0) or 0)
                status_str = str(getattr(disk, "Status", "OK") or "OK")
                drives.append(
                    SmartDriveInfo(
                        device=str(getattr(disk, "DeviceID", "Disk")),
                        model=str(getattr(disk, "Model", "Generic Disk")),
                        serial=str(getattr(disk, "SerialNumber", "N/A")).strip(),
                        firmware="WMI-COM",
                        protocol="WMI",
                        capacity_gb=round(size_bytes / (1024**3), 2),
                        health_status="PASSED" if status_str.upper() == "OK" else "WARNING",
                    )
                )
            if drives:
                return drives
        except Exception:
            pass

        # 3. Fallback через прямой Get-CimInstance
        try:
            ps_cmd = (
                "Get-CimInstance Win32_DiskDrive | "
                "Select-Object DeviceID, Model, SerialNumber, Size, Status | "
                "ConvertTo-Json -Compress"
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout)
                items = [raw] if isinstance(raw, dict) else raw
                for item in items:
                    size_bytes = int(item.get("Size") or 0)
                    drives.append(
                        SmartDriveInfo(
                            device=str(item.get("DeviceID", "Disk")),
                            model=str(item.get("Model", "Generic Disk")),
                            serial=str(item.get("SerialNumber", "N/A")),
                            firmware="WMI-Queried",
                            protocol="WMI",
                            capacity_gb=round(size_bytes / (1024**3), 2),
                            health_status="PASSED" if str(item.get("Status")).upper() == "OK" else "WARNING",
                        )
                    )
        except Exception as e:
            logger.error(f"WMI disk fallback scan error: {e}")
        return drives
