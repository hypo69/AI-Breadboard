# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Telemetry and Hardware Collector
# =============================================================================
# Description:
#   Collects live CPU, RAM, GPU, storage, process stream, and AIDA64-style
#   hardware component hierarchy with resilient psutil/WMI/ctypes fallbacks.
#
# Examples:
#   >>> from apps.windows.telemetry.collector import SystemCollector
#   >>> collector = SystemCollector()
#   >>> snapshot = collector.get_snapshot()
#   >>> print(snapshot.cpu.total_percent, snapshot.memory.percent)
#
# File: collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""System metrics and hardware hierarchy collector engine."""

from __future__ import annotations

import asyncio
import ctypes
import getpass
import locale
import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore
    PSUTIL_AVAILABLE = False

# probe_hardware импортируется лениво при необходимости, чтобы не загружать AI-библиотеки
from logger import logger
from apps.windows.telemetry.models import (
    AnomalyItem,
    BatteryMetrics,
    CloudStorageInfo,
    CpuMetrics,
    DiskIoMetrics,
    DiskPartitionMetrics,
    DriverInfo,
    GpuMetrics,
    HardwareArchiveEntry,
    HardwareAuditReport,
    HardwareChangeItem,
    HardwareDeviceAudit,
    HardwareNode,
    HardwareSensor,
    MemoryMetrics,
    MonitorInfo,
    NetworkInterfaceMetrics,
    NetworkPortMetrics,
    OfficeSuiteInfo,
    PhysicalDiskHealth,
    ProcessMetrics,
    ProcessNetworkActivity,
    RamStickInfo,
    SystemCoreMetrics,
    SystemHardwareQuick,
    SystemHealthAlerts,
    SystemSnapshot,
    WindowsUpdateInfo,
)
from apps.windows.telemetry.sensors import get_hardware_sensors
from apps.windows.telemetry.hardware_auditor import HardwareAuditor
from apps.windows.telemetry.history_manager import HardwareHistoryManager
from apps.windows.telemetry.storage import TelemetryStorage


class SystemCollector:
    """Telemetry collector for system load, hardware devices, and processes."""

    def __init__(
        self,
        auditor: Optional[HardwareAuditor] = None,
        history_manager: Optional[HardwareHistoryManager] = None,
        storage: Optional[TelemetryStorage] = None,
    ) -> None:
        """Initialize telemetry collector with timing, I/O baseline, hardware auditor, and storage."""
        self._last_disk_io = psutil.disk_io_counters() if PSUTIL_AVAILABLE else None
        self._last_net_io = psutil.net_io_counters(pernic=True) if PSUTIL_AVAILABLE else None
        self._last_proc_net_io: Dict[int, Tuple[float, float, float]] = {}
        self._last_time = time.time()
        self._cpu_model_cached: Optional[str] = None
        self._identity_cached: Optional[Dict[str, Any]] = None
        self._monitors_cached: Optional[List[MonitorInfo]] = None
        self._updates_cached: Optional[WindowsUpdateInfo] = None
        self._office_cached: Optional[OfficeSuiteInfo] = None
        self._ram_sticks_cached: Optional[List[RamStickInfo]] = None
        self._ram_sticks_cache_time: float = 0.0
        self._physical_disks_cached: Optional[List[PhysicalDiskHealth]] = None
        self._physical_disks_cache_time: float = 0.0
        self.auditor = auditor or HardwareAuditor()
        self.history_manager = history_manager or HardwareHistoryManager()
        self.storage = storage or TelemetryStorage.get_instance()

    def get_system_identity(self) -> Dict[str, Any]:
        """Collect host identity, current user, system language, and locale parameters.

        Returns:
            Dict[str, Any]: Detailed system identity and localization dictionary.
        """
        if self._identity_cached:
            return self._identity_cached

        hostname = socket.gethostname()
        domain = os.environ.get("USERDOMAIN", "")
        username_raw = os.environ.get("USERNAME") or getpass.getuser()
        full_username = f"{domain}\\{username_raw}" if domain and domain != hostname else username_raw

        user_locale = "ru-RU"
        system_locale = "ru-RU"
        codepage = "UTF-8"
        input_languages: List[str] = []

        if os.name == "nt":
            try:
                buf = ctypes.create_unicode_buffer(100)
                if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 100):
                    user_locale = buf.value or "ru-RU"
                if ctypes.windll.kernel32.GetSystemDefaultLocaleName(buf, 100):
                    system_locale = buf.value or "ru-RU"

                acp = ctypes.windll.kernel32.GetACP()
                oemcp = ctypes.windll.kernel32.GetOEMCP()
                codepage = f"ACP: {acp} | OEM: {oemcp} (UTF-8)"

                # Keyboard layout languages
                count = ctypes.windll.user32.GetKeyboardLayoutList(0, None)
                if count > 0:
                    hkls = (ctypes.c_void_p * count)()
                    ctypes.windll.user32.GetKeyboardLayoutList(count, hkls)
                    lang_map = {
                        0x0419: "Русский (RU)",
                        0x0409: "English (US)",
                        0x040D: "עברית (IL)",
                        0x0422: "Українська (UA)",
                        0x0407: "Deutsch (DE)",
                        0x040C: "Français (FR)",
                    }
                    for h in hkls:
                        lang_id = (h.value if hasattr(h, 'value') and h.value else int(h)) & 0xFFFF
                        lang_name = lang_map.get(lang_id, f"Layout 0x{lang_id:04X}")
                        if lang_name not in input_languages:
                            input_languages.append(lang_name)
            except Exception as ex:
                logger.debug(f"Failed to query native Windows locale: {ex}")

        if not input_languages:
            input_languages = ["Русский (RU)", "English (US)"]

        # Timezone string
        try:
            tz_offset = datetime.now().astimezone().strftime("%z")
            tz_name = datetime.now().astimezone().tzname() or time.tzname[0]
            timezone_str = f"{tz_name} (UTC{tz_offset[:3]}:{tz_offset[3:]})"
        except Exception:
            timezone_str = "UTC+03:00"

        # Resolve system language display name
        loc_lang = user_locale.lower()
        if "ru" in loc_lang:
            sys_lang_display = "Русский (Россия) [ru-RU]"
        elif "he" in loc_lang:
            sys_lang_display = "עברית (ישראל) [he-IL]"
        elif "en" in loc_lang:
            sys_lang_display = "English (United States) [en-US]"
        else:
            sys_lang_display = f"{user_locale}"

        os_build = platform.version() or "10.0.26200"
        os_install_date = ""

        if os.name == "nt":
            try:
                import winreg

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                    val, _ = winreg.QueryValueEx(key, "InstallDate")
                    if val:
                        os_install_date = datetime.fromtimestamp(val).strftime("%d.%m.%Y %H:%M")
            except Exception as ex:
                logger.debug(f"Failed to query Windows InstallDate from registry: {ex}")

        self._identity_cached = {
            "hostname": hostname,
            "username": full_username,
            "os_build": os_build,
            "os_install_date": os_install_date,
            "system_language": sys_lang_display,
            "user_locale": user_locale,
            "system_locale": system_locale,
            "timezone": timezone_str,
            "codepage": codepage,
            "input_languages": input_languages,
        }
        return self._identity_cached

    async def _resolve_cpu_model(self) -> str:
        """Resolve CPU brand/model name from platform or WMI.

        Returns:
            str: Resolved CPU model name.
        """
        if self._cpu_model_cached:
            return self._cpu_model_cached

        model = platform.processor() or ""
        if os.name == "nt" and (not model or "Intel64" in model or "AMD64" in model):
            try:
                from src.utils.com_worker import com_worker
                def _get_cpu():
                    import pythoncom
                    pythoncom.CoInitialize()
                    import wmi
                    w = wmi.WMI()
                    cpus = w.Win32_Processor()
                    return str(cpus[0].Name).strip() if cpus else None
                
                res = await com_worker.run(_get_cpu)
                if res:
                    model = res
            except Exception:
                pass

        if not model:
            model = f"{platform.machine()} {os.cpu_count() or 1}-Core Processor"

        self._cpu_model_cached = model
        return model

    async def get_cpu_metrics(self) -> CpuMetrics:
        """Collect real-time CPU utilization and architecture details.

        Returns:
            CpuMetrics: Current CPU performance metrics.
        """
        logical_cores = os.cpu_count() or 1
        physical_cores = max(1, logical_cores // 2) if logical_cores > 1 else 1

        if PSUTIL_AVAILABLE:
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            total = round(sum(per_core) / max(len(per_core), 1), 1) if per_core else 0.0
            physical = psutil.cpu_count(logical=False) or physical_cores
            logical = psutil.cpu_count(logical=True) or logical_cores

            freq_mhz = 0.0
            try:
                freq = psutil.cpu_freq()
                if freq:
                    freq_mhz = round(freq.current, 1)
            except Exception:
                pass

            return CpuMetrics(
                model=await self._resolve_cpu_model(),
                architecture=platform.machine(),
                physical_cores=physical,
                logical_cores=logical,
                total_percent=total,
                per_core_percent=per_core,
                frequency_mhz=freq_mhz,
            )

        return CpuMetrics(
            model=await self._resolve_cpu_model(),
            architecture=platform.machine(),
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            total_percent=10.0,
            per_core_percent=[10.0] * logical_cores,
            frequency_mhz=2400.0,
        )

    def get_memory_metrics(self) -> MemoryMetrics:
        """Collect RAM and swap memory consumption.

        Returns:
            MemoryMetrics: Current memory usage statistics.
        """
        if PSUTIL_AVAILABLE:
            vm = psutil.virtual_memory()
            sm = psutil.swap_memory()

            return MemoryMetrics(
                total_gb=round(vm.total / (1024**3), 2),
                available_gb=round(vm.available / (1024**3), 2),
                used_gb=round((vm.total - vm.available) / (1024**3), 2),
                percent=round(vm.percent, 1),
                swap_total_gb=round(sm.total / (1024**3), 2),
                swap_used_gb=round(sm.used / (1024**3), 2),
                swap_percent=round(sm.percent, 1),
            )

        # Windows ctypes fallback for RAM
        total_ram_gb = 16.0
        used_ram_gb = 8.0
        if os.name == "nt":
            try:
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_ram_gb = round(stat.ullTotalPhys / (1024**3), 2)
                    avail_ram_gb = round(stat.ullAvailPhys / (1024**3), 2)
                    used_ram_gb = round(total_ram_gb - avail_ram_gb, 2)
                    percent = round(stat.dwMemoryLoad, 1)
                    return MemoryMetrics(
                        total_gb=total_ram_gb,
                        available_gb=avail_ram_gb,
                        used_gb=used_ram_gb,
                        percent=percent,
                        swap_total_gb=round(stat.ullTotalPageFile / (1024**3), 2),
                        swap_used_gb=round((stat.ullTotalPageFile - stat.ullAvailPageFile) / (1024**3), 2),
                        swap_percent=round((1.0 - (stat.ullAvailPageFile / max(stat.ullTotalPageFile, 1))) * 100, 1),
                    )
            except Exception:
                pass

        return MemoryMetrics(
            total_gb=total_ram_gb,
            available_gb=total_ram_gb - used_ram_gb,
            used_gb=used_ram_gb,
            percent=50.0,
            swap_total_gb=16.0,
            swap_used_gb=2.0,
            swap_percent=12.5,
        )

    def get_gpu_metrics(self) -> List[GpuMetrics]:
        """Collect GPU accelerator load, VRAM, and capabilities.

        Returns:
            List[GpuMetrics]: Detected GPU devices with telemetry.
        """
        gpus: List[GpuMetrics] = []
        try:
            from apps.windows.hardware.gpu_prober import GpuProber
            prober = GpuProber()
            gpu_list = prober.probe_all()
            for g in gpu_list:
                gpus.append(
                    GpuMetrics(
                        name=g.name,
                        memory_total_gb=round((g.memory_total_mb or 0.0) / 1024.0, 2),
                        memory_used_gb=round((g.memory_used_mb or 0.0) / 1024.0, 2),
                        load_percent=g.utilization_gpu_pct,
                        temperature_celsius=g.temperature_gpu_c,
                        has_cuda=(g.vendor.lower() == "nvidia"),
                        has_directml=True,
                    )
                )
        except Exception as ex:
            logger.debug(f"Failed to probe GPUs via GpuProber: {ex}")
            try:
                from src.ai.orchestration.hardware import probe_hardware
                hw = probe_hardware()
                for g in hw.gpus:
                    gpus.append(
                        GpuMetrics(
                            name=g.get("name", "NVIDIA GPU"),
                            memory_total_gb=round(g.get("vram_mb", 0) / 1024.0, 2),
                            has_cuda=hw.has_cuda,
                            has_directml=hw.has_directml,
                        )
                    )
            except Exception as inner_ex:
                logger.debug(f"Failed to probe GPUs via fallback: {inner_ex}")

        if not gpus:
            gpus.append(
                GpuMetrics(
                    name="Integrated Display Controller",
                    memory_total_gb=0.0,
                    has_cuda=False,
                    has_directml=False,
                )
            )
        return gpus

    def get_disk_metrics(self) -> tuple[List[DiskPartitionMetrics], DiskIoMetrics]:
        """Collect disk partitions capacity and read/write rates.

        Returns:
            tuple[List[DiskPartitionMetrics], DiskIoMetrics]: Partitions and I/O rates.
        """
        partitions: List[DiskPartitionMetrics] = []
        io_metrics = DiskIoMetrics()

        if PSUTIL_AVAILABLE:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    vol_name = ""
                    is_virtual = False
                    drive_type = "Fixed"

                    if os.name == "nt":
                        try:
                            import ctypes
                            vol_buf = ctypes.create_unicode_buffer(1024)
                            fs_buf = ctypes.create_unicode_buffer(1024)
                            mount_root = part.mountpoint if part.mountpoint.endswith("\\") else f"{part.mountpoint}\\"
                            if ctypes.windll.kernel32.GetVolumeInformationW(
                                mount_root, vol_buf, 1024, None, None, None, fs_buf, 1024
                            ):
                                vol_name = vol_buf.value

                            dos_buf = ctypes.create_unicode_buffer(1024)
                            clean_dev = part.device.rstrip("\\")
                            ctypes.windll.kernel32.QueryDosDeviceW(clean_dev, dos_buf, 1024)
                            dos_dev = dos_buf.value

                            if (
                                "google" in vol_name.lower()
                                or "@" in vol_name
                                or "onedrive" in vol_name.lower()
                                or "dropbox" in vol_name.lower()
                                or ("volume{" in dos_dev.lower() and "harddiskvolume" not in dos_dev.lower())
                            ):
                                is_virtual = True
                                drive_type = "Google Drive" if ("google" in vol_name.lower() or "@" in vol_name) else "Cloud / Virtual"
                        except Exception:
                            pass

                    partitions.append(
                        DiskPartitionMetrics(
                            device=part.device,
                            mountpoint=part.mountpoint,
                            fstype=part.fstype,
                            total_gb=round(usage.total / (1024**3), 2),
                            used_gb=round(usage.used / (1024**3), 2),
                            free_gb=round(usage.free / (1024**3), 2),
                            percent=round(usage.percent, 1),
                            volume_name=vol_name or None,
                            is_virtual=is_virtual,
                            drive_type=drive_type,
                        )
                    )
                except (PermissionError, OSError):
                    continue

            now = time.time()
            elapsed = max(now - self._last_time, 0.1)
            current_io = psutil.disk_io_counters()

            if current_io and self._last_disk_io:
                io_metrics.read_bytes_per_sec = max(0.0, (current_io.read_bytes - self._last_disk_io.read_bytes) / elapsed)
                io_metrics.write_bytes_per_sec = max(0.0, (current_io.write_bytes - self._last_disk_io.write_bytes) / elapsed)
                io_metrics.read_count_per_sec = max(0.0, (current_io.read_count - self._last_disk_io.read_count) / elapsed)
                io_metrics.write_count_per_sec = max(0.0, (current_io.write_count - self._last_disk_io.write_count) / elapsed)

            self._last_disk_io = current_io
        else:
            # Fallback for C: drive on Windows
            drive = "C:\\" if os.name == "nt" else "/"
            try:
                import shutil
                total, used, free = shutil.disk_usage(drive)
                partitions.append(
                    DiskPartitionMetrics(
                        device="C:" if os.name == "nt" else "/",
                        mountpoint=drive,
                        fstype="NTFS" if os.name == "nt" else "ext4",
                        total_gb=round(total / (1024**3), 2),
                        used_gb=round(used / (1024**3), 2),
                        free_gb=round(free / (1024**3), 2),
                        percent=round((used / max(total, 1)) * 100, 1),
                    )
                )
            except Exception:
                pass

        return partitions, io_metrics

    def get_network_metrics(self) -> List[NetworkInterfaceMetrics]:
        """Collect network interface statuses and throughput rates.

        Returns:
            List[NetworkInterfaceMetrics]: Network adapters metrics.
        """
        interfaces: List[NetworkInterfaceMetrics] = []

        if PSUTIL_AVAILABLE:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            current_net_io = psutil.net_io_counters(pernic=True)

            now = time.time()
            elapsed = max(now - self._last_time, 0.1)

            for name, addr_list in addrs.items():
                stat = stats.get(name)
                is_up = stat.isup if stat else True
                speed = stat.speed if stat else 0
                ips = [a.address for a in addr_list if a.family == socket.AF_INET]

                sent_rate = 0.0
                recv_rate = 0.0
                if current_net_io and name in current_net_io and self._last_net_io and name in self._last_net_io:
                    cur = current_net_io[name]
                    prev = self._last_net_io[name]
                    sent_rate = max(0.0, (cur.bytes_sent - prev.bytes_sent) / elapsed)
                    recv_rate = max(0.0, (cur.bytes_recv - prev.bytes_recv) / elapsed)

                interfaces.append(
                    NetworkInterfaceMetrics(
                        name=name,
                        is_up=is_up,
                        speed_mbps=speed,
                        bytes_sent_per_sec=sent_rate,
                        bytes_recv_per_sec=recv_rate,
                        ip_addresses=ips,
                    )
                )

            self._last_net_io = current_net_io
        else:
            try:
                host_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                host_ip = "127.0.0.1"
            interfaces.append(
                NetworkInterfaceMetrics(
                    name="Primary Network Adapter",
                    is_up=True,
                    speed_mbps=1000,
                    bytes_sent_per_sec=0.0,
                    bytes_recv_per_sec=0.0,
                    ip_addresses=[host_ip],
                )
            )

        return interfaces

    def get_top_processes(self, limit: int = 25, sort_by: str = "cpu") -> List[ProcessMetrics]:
        """Retrieve active processes sorted by resource consumption.

        Args:
            limit: Maximum processes to return (0 for all active processes).
            sort_by: Attribute to sort by ('cpu', 'memory'/'ram', 'handles'/'descriptors').

        Returns:
            List[ProcessMetrics]: Ranked process metrics.
        """
        procs: List[ProcessMetrics] = []

        if PSUTIL_AVAILABLE:
            handle_attr = "num_handles" if os.name == "nt" else "num_fds"
            proc_attrs = ["pid", "name", "status", "cpu_percent", "memory_info", "memory_percent", "num_threads", "username", handle_attr]
            for p in psutil.process_iter(attrs=proc_attrs):
                try:
                    info = p.info
                    mem_info = info.get("memory_info")
                    rss_mb = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0.0
                    cpu_p = round(info.get("cpu_percent") or 0.0, 1)
                    num_h = info.get(handle_attr) or 0

                    procs.append(
                        ProcessMetrics(
                            pid=info["pid"],
                            name=info.get("name") or "unknown",
                            status=info.get("status") or "running",
                            cpu_percent=cpu_p,
                            memory_mb=rss_mb,
                            memory_percent=round(info.get("memory_percent") or 0.0, 1),
                            num_threads=info.get("num_threads") or 1,
                            num_handles=num_h,
                            username=info.get("username"),
                        )
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        else:
            # Fallback current process
            procs.append(
                ProcessMetrics(
                    pid=os.getpid(),
                    name="python.exe",
                    status="running",
                    cpu_percent=1.5,
                    memory_mb=120.0,
                    memory_percent=1.0,
                    num_threads=8,
                    num_handles=42,
                    username=os.getenv("USERNAME", "SYSTEM"),
                )
            )

        sort_key = (sort_by or "cpu").lower()
        if sort_key in ("handles", "descriptors"):
            procs.sort(key=lambda x: x.num_handles, reverse=True)
        elif sort_key in ("memory", "ram"):
            procs.sort(key=lambda x: x.memory_mb, reverse=True)
        else:
            procs.sort(key=lambda x: x.cpu_percent, reverse=True)

        if limit is None or limit <= 0:
            return procs

        return procs[:limit]

    def get_battery_metrics(self) -> BatteryMetrics:
        """Collect laptop or UPS battery charge level and AC power status.

        Returns:
            BatteryMetrics: Current battery and power status.
        """
        if PSUTIL_AVAILABLE and hasattr(psutil, "sensors_battery"):
            try:
                bat = psutil.sensors_battery()
                if bat is not None:
                    return BatteryMetrics(
                        has_battery=True,
                        percent=round(bat.percent, 1),
                        power_plugged=bat.power_plugged,
                        secs_left=bat.secsleft if bat.secsleft > 0 else None,
                        power_profile="AC / Battery",
                    )
            except Exception as ex:
                logger.debug(f"Battery probe failed: {ex}")

        return BatteryMetrics(
            has_battery=False,
            percent=None,
            power_plugged=True,
            secs_left=None,
            power_profile="AC Mains / Desktop",
        )

    def get_physical_disks_health(self) -> List[PhysicalDiskHealth]:
        """Собрать данные о физических дисках, SMART, типах носителей и здоровье через единый сенсор.

        Returns:
            List[PhysicalDiskHealth]: Список обнаруженных физических накопителей.
        """
        now = time.time()
        if self._physical_disks_cached is not None and (now - self._physical_disks_cache_time) < 60.0:
            return self._physical_disks_cached

        disks: List[PhysicalDiskHealth] = []
        if os.name == "nt":
            try:
                from apps.windows.storage_sensors.windows_storage_sensor import WindowsStorageSensor
                sensor = WindowsStorageSensor()
                phys_disks = sensor.get_physical_disks()
                for d in phys_disks:
                    disks.append(
                        PhysicalDiskHealth(
                            device_id=d.device_id,
                            model=d.model or d.friendly_name or "Physical Drive",
                            media_type=d.media_type or "SSD",
                            size_gb=round(d.size_gb, 1) if d.size_gb else 0.0,
                            health_status=d.health_status or "Healthy",
                            operational_status=d.operational_status or "OK",
                            temperature_celsius=d.temperature_c,
                            interface_type=d.bus_type or "NVMe",
                        )
                    )
            except Exception as ex:
                logger.debug(f"Ошибка сбора физических дисков через WindowsStorageSensor: {ex}")

        if not disks:
            disks.append(
                PhysicalDiskHealth(
                    device_id="Disk 0",
                    model="System Drive (NVMe/SSD)",
                    media_type="SSD",
                    size_gb=512.0,
                    health_status="Healthy",
                    operational_status="OK",
                    interface_type="NVMe",
                )
            )

        self._physical_disks_cached = disks
        self._physical_disks_cache_time = now
        return disks

    async def get_ram_sticks(self) -> List[RamStickInfo]:
        """Collect physical memory stick (SPD) details via WMI.

        Returns:
            List[RamStickInfo]: Installed physical RAM modules.
        """
        now = time.time()
        if self._ram_sticks_cached is not None and (now - self._ram_sticks_cache_time) < 60.0:
            return self._ram_sticks_cached

        sticks: List[RamStickInfo] = []
        if os.name == "nt":
            from src.utils.com_worker import com_worker
            async def _probe():
                def _do_probe():
                    import wmi
                    _sticks: List[RamStickInfo] = []
                    w = wmi.WMI()
                    mems = w.Win32_PhysicalMemory()
                    type_map = {
                        20: "DDR",
                        21: "DDR2",
                        24: "DDR3",
                        26: "DDR4",
                        34: "DDR5",
                    }
                    for m in mems:
                        cap_gb = round(int(m.Capacity or 0) / (1024**3), 1)
                        speed = int(m.Speed or m.ConfiguredClockSpeed or 3200)
                        m_type = type_map.get(m.SMBIOSMemoryType, "DDR4/DDR5")
                        _sticks.append(
                            RamStickInfo(
                                bank_label=str(m.BankLabel or m.DeviceLocator or "DIMM").strip(),
                                capacity_gb=cap_gb,
                                speed_mhz=speed,
                                manufacturer=str(m.Manufacturer or "Generic").strip(),
                                part_number=str(m.PartNumber or "").strip(),
                                memory_type=m_type,
                            )
                        )
                    return _sticks
                return await com_worker.run(_do_probe)
            try:
                sticks = await _probe()
            except Exception as ex:
                logger.debug(f"Failed to query physical memory sticks: {ex}")

        self._ram_sticks_cached = sticks
        self._ram_sticks_cache_time = now
        return sticks

    def get_listening_ports(self, limit: int = 15) -> List[NetworkPortMetrics]:
        """Collect active listening TCP/UDP sockets with process attribution.

        Args:
            limit: Maximum listening ports to return.

        Returns:
            List[NetworkPortMetrics]: Active listening ports.
        """
        ports: List[NetworkPortMetrics] = []
        if PSUTIL_AVAILABLE:
            try:
                conns = psutil.net_connections(kind="inet")
                seen = set()
                for c in conns:
                    if c.status == "LISTEN" or c.type == socket.SOCK_DGRAM:
                        p_num = c.laddr.port
                        if p_num in seen:
                            continue
                        seen.add(p_num)

                        p_name = None
                        if c.pid:
                            try:
                                p_name = psutil.Process(c.pid).name()
                            except Exception:
                                pass

                        ports.append(
                            NetworkPortMetrics(
                                port=p_num,
                                protocol="TCP" if c.type == socket.SOCK_STREAM else "UDP",
                                address=c.laddr.ip or "0.0.0.0",
                                pid=c.pid,
                                process_name=p_name,
                            )
                        )
                        if len(ports) >= limit:
                            break
            except Exception as ex:
                logger.debug(f"Failed to query listening ports: {ex}")

        return ports

    def get_process_network_activity(
        self, limit: int = 50, only_internet: bool = False
    ) -> List[ProcessNetworkActivity]:
        """Collect active network connections and traffic attribution for processes.

        Args:
            limit: Maximum connections to return.
            only_internet: Whether to restrict only to external internet addresses.

        Returns:
            List[ProcessNetworkActivity]: Active network connections with process and traffic description.
        """
        activities: List[ProcessNetworkActivity] = []
        if not PSUTIL_AVAILABLE:
            return activities

        try:
            raw_conns = psutil.net_connections(kind="inet")
        except Exception as ex:
            logger.debug(f"Failed to query network connections: {ex}")
            return activities

        proc_cache: Dict[int, Dict[str, Any]] = {}
        now_ts = time.time()

        def _get_proc_info(pid: Optional[int]) -> Dict[str, Any]:
            if not pid or pid == 0:
                return {
                    "name": "System Idle",
                    "user": "SYSTEM",
                    "read_kb": 0.0,
                    "write_kb": 0.0,
                    "delta_read_kb": 0.0,
                    "delta_write_kb": 0.0,
                    "read_speed_kbs": 0.0,
                    "write_speed_kbs": 0.0,
                }
            if pid == 4:
                return {
                    "name": "System",
                    "user": "NT AUTHORITY\\SYSTEM",
                    "read_kb": 0.0,
                    "write_kb": 0.0,
                    "delta_read_kb": 0.0,
                    "delta_write_kb": 0.0,
                    "read_speed_kbs": 0.0,
                    "write_speed_kbs": 0.0,
                }
            if pid in proc_cache:
                return proc_cache[pid]
            try:
                p = psutil.Process(pid)
                pname = p.name()
                puser = ""
                try:
                    puser = p.username()
                except Exception:
                    puser = ""

                read_kb = 0.0
                write_kb = 0.0
                delta_read_kb = 0.0
                delta_write_kb = 0.0
                read_speed_kbs = 0.0
                write_speed_kbs = 0.0

                try:
                    io = p.io_counters()
                    read_kb = round(io.read_bytes / 1024, 1)
                    write_kb = round(io.write_bytes / 1024, 1)

                    if hasattr(self, "_last_proc_net_io") and pid in self._last_proc_net_io:
                        prev_t, prev_r, prev_w = self._last_proc_net_io[pid]
                        dt = max(now_ts - prev_t, 0.1)
                        if io.read_bytes >= prev_r:
                            delta_read_kb = round((io.read_bytes - prev_r) / 1024, 1)
                            read_speed_kbs = round(delta_read_kb / dt, 1)
                        if io.write_bytes >= prev_w:
                            delta_write_kb = round((io.write_bytes - prev_w) / 1024, 1)
                            write_speed_kbs = round(delta_write_kb / dt, 1)

                    if hasattr(self, "_last_proc_net_io"):
                        self._last_proc_net_io[pid] = (now_ts, io.read_bytes, io.write_bytes)
                except Exception:
                    pass

                info = {
                    "name": pname,
                    "user": puser,
                    "read_kb": read_kb,
                    "write_kb": write_kb,
                    "delta_read_kb": delta_read_kb,
                    "delta_write_kb": delta_write_kb,
                    "read_speed_kbs": read_speed_kbs,
                    "write_speed_kbs": write_speed_kbs,
                }
                proc_cache[pid] = info
                return info
            except Exception:
                info = {
                    "name": f"PID {pid}",
                    "user": "",
                    "read_kb": 0.0,
                    "write_kb": 0.0,
                    "delta_read_kb": 0.0,
                    "delta_write_kb": 0.0,
                    "read_speed_kbs": 0.0,
                    "write_speed_kbs": 0.0,
                }
                proc_cache[pid] = info
                return info

        def _is_ext_internet(ip: str) -> bool:
            if not ip:
                return False
            if ip in ("127.0.0.1", "::1", "0.0.0.0", "::") or ip.startswith("127.") or ip.startswith("fe80:"):
                return False
            return True

        for c in raw_conns:
            laddr_str = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
            raddr_str = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
            rip = c.raddr.ip if c.raddr else ""
            rport = c.raddr.port if c.raddr else 0
            lport = c.laddr.port if c.laddr else 0

            is_ext = _is_ext_internet(rip)
            if only_internet and not is_ext:
                continue

            proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
            status = c.status or ("LISTEN" if not c.raddr else "ESTABLISHED")
            p_info = _get_proc_info(c.pid)
            p_name = p_info["name"]
            p_user = p_info["user"]

            service_type, sent_desc, recv_desc = self._classify_traffic(
                p_name, rport or lport, proto, status, is_ext
            )

            activities.append(
                ProcessNetworkActivity(
                    pid=c.pid or 0,
                    name=p_name,
                    user=p_user,
                    local_address=laddr_str,
                    remote_address=raddr_str,
                    remote_host=None,
                    protocol=proto,
                    status=status,
                    is_internet=is_ext,
                    service_type=service_type,
                    sent_kb=p_info.get("write_kb", 0.0),
                    recv_kb=p_info.get("read_kb", 0.0),
                    delta_sent_kb=p_info.get("delta_write_kb", 0.0),
                    delta_recv_kb=p_info.get("delta_read_kb", 0.0),
                    sent_rate_kbs=p_info.get("write_speed_kbs", 0.0),
                    recv_rate_kbs=p_info.get("read_speed_kbs", 0.0),
                    sent_summary=sent_desc,
                    recv_summary=recv_desc,
                )
            )
            if len(activities) >= limit:
                break

        return activities

    @staticmethod
    def _classify_traffic(
        proc_name: str, port: int, proto: str, status: str, is_internet: bool
    ) -> tuple[str, str, str]:
        """Classify network traffic service type and generate human-readable summaries."""
        p_lower = proc_name.lower()

        # 1. Listen sockets
        if status == "LISTEN" or not is_internet:
            if "python" in p_lower or "uvicorn" in p_lower or "node" in p_lower:
                return (
                    "Локальный Web API / Сервер",
                    "HTTP ответы локальным клиентам / WebSockets",
                    "Входящие HTTP запросы от фронтенда / браузера",
                )
            return (
                "Локальная служба / Socket",
                "Служебные ответы локальной подсистемы",
                "Ожидание входящих подключений (Listen)",
            )

        # 2. Port-based classification with Process-specific context
        if port in (443, 8443):
            if any(b in p_lower for b in ("edge", "chrome", "firefox", "brave", "opera", "browser")):
                return (
                    "HTTPS / Веб-навигация",
                    "Исходящие HTTPS запросы, URL заголовки, формы, cookies",
                    "HTML страницы, скрипты, видео, изображения, медиа",
                )
            if any(m in p_lower for m in ("telegram", "discord", "slack", "whatsapp", "skype")):
                return (
                    "Мессенджер / Зашифрованный чат",
                    "Текстовые сообщения, медиа-файлы, голосовые пакеты, пинги",
                    "Входящие сообщения, аудио/видеопоток, обновления чатов",
                )
            if any(s in p_lower for s in ("onedrive", "googledrivefs", "dropbox", "cloud")):
                return (
                    "Облачная синхронизация / Хранилище",
                    "Выгрузка локальных файлов, метаданные изменений",
                    "Синхронизация файлов из облака, снимки папок",
                )
            if any(d in p_lower for d in ("code", "devenv", "language_server", "python", "pycharm", "git")):
                return (
                    "Разработка / LLM API & Git",
                    "AI промпты к LLM моделям, API вызовы, git push, пакеты",
                    "Сгенерированный AI код, ответы API, пакеты библиотек",
                )
            if any(w in p_lower for w in ("svchost", "system", "msmpeng", "searchindexer", "spoolsv")):
                return (
                    "Системные службы Windows / Облако MS",
                    "Телеметрия Defender, проверка сертификатов, запросы ОС",
                    "Сигнатуры безопасности, метаданные обновлений Windows",
                )
            return (
                "HTTPS / Зашифрованный веб-трафик",
                "Зашифрованные HTTPS/TLS запросы и полезная нагрузка",
                "Ответы удаленного веб-сервера, зашифрованные данные",
            )

        if port in (80, 8080):
            return (
                "HTTP / Открытый веб-трафик",
                "HTTP GET/POST запросы, клиентские заголовки",
                "HTML веб-страницы, незашифрованный контент, ответы",
            )

        if port == 53:
            return (
                "DNS / Разрешение имен",
                "Запросы на получение IP-адресов доменов (DNS Queries)",
                "DNS-ответы с IP-адресами серверов (DNS Answers)",
            )

        if port in (5222, 5223, 5228):
            return (
                "Push-нотификации / XMPP",
                "Heartbeat пинги, исходящие push-запросы",
                "Входящие фоновые push-уведомления и события",
            )

        if port == 22:
            return (
                "SSH / Защищенный терминал",
                "Команды консоли, зашифрованные SSH сессии",
                "Вывод удаленного терминала, файловые потоки SFTP",
            )

        if port == 7680:
            return (
                "WUDO / P2P обновления Windows",
                "P2P раздача фрагментов обновлений ОС",
                "P2P получение компонентов обновлений ОС",
            )

        if port in (465, 587):
            return (
                "SMTP / Почтовая отправка",
                "Исходящие электронные письма (MIME/SMTP)",
                "Квитанции доставки, подтверждения почтового сервера",
            )

        if port in (993, 995):
            return (
                "IMAP/POP3 / Почтовый прием",
                "Команды проверки новых писем и папок",
                "Входящие электронные письма, заголовки, вложения",
            )

        # Fallback
        return (
            f"{proto}/{port}",
            f"Исходящие пакеты данных ({proto}) на порт {port}",
            f"Входящие пакеты и ответы сервера с порта {port}",
        )

    def get_health_alerts(self) -> SystemHealthAlerts:
        """Check system reliability indicators and pending reboot status.

        Returns:
            SystemHealthAlerts: Consolidated system health alert indicators.
        """
        reboot_pending = False
        if os.name == "nt":
            try:
                import winreg

                # Check Windows Update RebootPending registry key
                reboot_keys = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
                ]
                for k in reboot_keys:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, k):
                            reboot_pending = True
                            break
                    except OSError:
                        pass
            except Exception:
                pass

        alert_msg = "Требуется перезагрузка для обновлений Windows" if reboot_pending else "Система работает стабильно"

        return SystemHealthAlerts(
            reboot_pending=reboot_pending,
            critical_events_count=0,
            latest_alert=alert_msg,
        )

    def get_monitors(self) -> List[MonitorInfo]:
        """Collect connected display monitors, resolutions and refresh rates.

        Returns:
            List[MonitorInfo]: Detected active display monitors.
        """
        if self._monitors_cached is not None:
            return self._monitors_cached

        monitors: List[MonitorInfo] = []
        if os.name == "nt":
            try:
                import ctypes.wintypes

                user32 = ctypes.windll.user32

                class DISPLAY_DEVICEW(ctypes.Structure):
                    _fields_ = [
                        ("cb", ctypes.wintypes.DWORD),
                        ("DeviceName", ctypes.wintypes.WCHAR * 32),
                        ("DeviceString", ctypes.wintypes.WCHAR * 128),
                        ("StateFlags", ctypes.wintypes.DWORD),
                        ("DeviceID", ctypes.wintypes.WCHAR * 128),
                        ("DeviceKey", ctypes.wintypes.WCHAR * 128),
                    ]

                adapter_map: Dict[str, Dict[str, str]] = {}
                for i in range(16):
                    disp = DISPLAY_DEVICEW()
                    disp.cb = ctypes.sizeof(DISPLAY_DEVICEW)
                    if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(disp), 0):
                        break
                    if disp.StateFlags & 1:  # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
                        mon = DISPLAY_DEVICEW()
                        mon.cb = ctypes.sizeof(DISPLAY_DEVICEW)
                        mon_name = ""
                        if user32.EnumDisplayDevicesW(disp.DeviceName, 0, ctypes.byref(mon), 0):
                            mon_name = mon.DeviceString
                        adapter_map[disp.DeviceName] = {
                            "adapter": disp.DeviceString,
                            "mon_name": mon_name or "Display Monitor",
                        }

                class MONITORINFOEXW(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.wintypes.DWORD),
                        ("rcMonitor", ctypes.wintypes.RECT),
                        ("rcWork", ctypes.wintypes.RECT),
                        ("dwFlags", ctypes.wintypes.DWORD),
                        ("szDevice", ctypes.wintypes.WCHAR * 32),
                    ]

                class DEVMODEW(ctypes.Structure):
                    _fields_ = [
                        ("dmDeviceName", ctypes.wintypes.WCHAR * 32),
                        ("dmSpecVersion", ctypes.wintypes.WORD),
                        ("dmDriverVersion", ctypes.wintypes.WORD),
                        ("dmSize", ctypes.wintypes.WORD),
                        ("dmDriverExtra", ctypes.wintypes.WORD),
                        ("dmFields", ctypes.wintypes.DWORD),
                        ("dmOrientation", ctypes.c_short),
                        ("dmPaperSize", ctypes.c_short),
                        ("dmPaperLength", ctypes.c_short),
                        ("dmPaperWidth", ctypes.c_short),
                        ("dmScale", ctypes.c_short),
                        ("dmCopies", ctypes.c_short),
                        ("dmDefaultSource", ctypes.c_short),
                        ("dmPrintQuality", ctypes.c_short),
                        ("dmColor", ctypes.c_short),
                        ("dmDuplex", ctypes.c_short),
                        ("dmYResolution", ctypes.c_short),
                        ("dmTTOption", ctypes.c_short),
                        ("dmCollate", ctypes.c_short),
                        ("dmFormName", ctypes.wintypes.WCHAR * 32),
                        ("dmLogPixels", ctypes.wintypes.WORD),
                        ("dmBitsPerPel", ctypes.wintypes.DWORD),
                        ("dmPelsWidth", ctypes.wintypes.DWORD),
                        ("dmPelsHeight", ctypes.wintypes.DWORD),
                        ("dmDisplayFlags", ctypes.wintypes.DWORD),
                        ("dmDisplayFrequency", ctypes.wintypes.DWORD),
                    ]

                def _enum_cb(h_mon: Any, hdc: Any, lprc: Any, dw_data: Any) -> bool:
                    info = MONITORINFOEXW()
                    info.cbSize = ctypes.sizeof(MONITORINFOEXW)
                    user32.GetMonitorInfoW(h_mon, ctypes.byref(info))
                    dev = info.szDevice
                    w = info.rcMonitor.right - info.rcMonitor.left
                    h = info.rcMonitor.bottom - info.rcMonitor.top
                    is_prim = bool(info.dwFlags & 1)

                    freq = 60
                    bits = 32
                    dm = DEVMODEW()
                    dm.dmSize = ctypes.sizeof(DEVMODEW)
                    if user32.EnumDisplaySettingsW(dev, -1, ctypes.byref(dm)):
                        if dm.dmDisplayFrequency:
                            freq = dm.dmDisplayFrequency
                        if dm.dmBitsPerPel:
                            bits = dm.dmBitsPerPel
                        if dm.dmPelsWidth and dm.dmPelsHeight:
                            w, h = dm.dmPelsWidth, dm.dmPelsHeight

                    ad_info = adapter_map.get(dev, {})
                    monitors.append(
                        MonitorInfo(
                            device=dev,
                            name=ad_info.get("mon_name", "Display Monitor"),
                            adapter=ad_info.get("adapter", ""),
                            width=w,
                            height=h,
                            frequency_hz=freq,
                            bits_per_pixel=bits,
                            is_primary=is_prim,
                        )
                    )
                    return True

                cb_type = ctypes.WINFUNCTYPE(
                    ctypes.c_bool,
                    ctypes.wintypes.HMONITOR,
                    ctypes.wintypes.HDC,
                    ctypes.POINTER(ctypes.wintypes.RECT),
                    ctypes.wintypes.LPARAM,
                )
                user32.EnumDisplayMonitors(None, None, cb_type(_enum_cb), 0)
            except Exception as ex:
                logger.debug(f"Failed to query connected monitors: {ex}")

        if not monitors:
            monitors.append(
                MonitorInfo(
                    device=r"\\.\DISPLAY1",
                    name="Primary Monitor",
                    adapter="Display Adapter",
                    width=1920,
                    height=1080,
                    frequency_hz=60,
                    bits_per_pixel=32,
                    is_primary=True,
                )
            )

        self._monitors_cached = monitors
        return monitors

    def get_updates_info(self) -> WindowsUpdateInfo:
        """Collect Windows Update status and recent installed hotfixes.

        Returns:
            WindowsUpdateInfo: Summary of updates status and installed KBs.
        """
        if self._updates_cached is not None:
            return self._updates_cached

        hotfixes: List[str] = []
        if os.name == "nt":
            try:
                import winreg

                # Fast registry inspection of CBS packages
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\Packages",
                ) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for i in range(count):
                        try:
                            pkg_name = winreg.EnumKey(key, i)
                            if "Package_for_KB" in pkg_name or "Package_for_RollupFix" in pkg_name:
                                parts = pkg_name.split("~")
                                kb = parts[0].replace("Package_for_", "")
                                if kb not in hotfixes:
                                    hotfixes.append(kb)
                        except OSError:
                            pass
            except Exception as ex:
                logger.debug(f"Fast hotfix registry scan exception: {ex}")

        if not hotfixes:
            hotfixes = ["KB5126052", "KB5054156", "KB5071430", "KB5129195", "KB5124007"]

        info = WindowsUpdateInfo(
            status="Up to date (Актуально)",
            installed_kb_count=len(hotfixes),
            recent_hotfixes=hotfixes[:10],
            latest_installed_on="Недавние исправления установлены",
        )
        self._updates_cached = info
        return info

    def get_ms_office_info(self) -> OfficeSuiteInfo:
        """Сбор информации об установленном пакете Microsoft Office / 365.

        Returns:
            OfficeSuiteInfo: Сведения о версии и статусе пакета Office.
        """
        if self._office_cached is not None:
            return self._office_cached

        installed = False
        product_name = None
        version = None
        publisher = None

        if os.name == "nt":
            try:
                import winreg

                # 1. ClickToRun Configuration
                ctr_keys = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration"),
                ]
                for root, subkey in ctr_keys:
                    try:
                        with winreg.OpenKey(root, subkey) as k:
                            for val_name in ("ProductVersion", "VersionToReport", "ClientVersionToReport"):
                                try:
                                    v, _ = winreg.QueryValueEx(k, val_name)
                                    if v:
                                        version = str(v)
                                        break
                                except OSError:
                                    pass
                            try:
                                prod_ids, _ = winreg.QueryValueEx(k, "ProductReleaseIds")
                                if prod_ids:
                                    product_name = str(prod_ids).replace("Volume", "").replace("Retail", "").strip()
                            except OSError:
                                pass
                            if version:
                                installed = True
                                publisher = "Microsoft Corporation"
                                break
                    except OSError:
                        pass

                # 2. Uninstall registry keys
                if not installed:
                    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                        for sub in (
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                        ):
                            try:
                                with winreg.OpenKey(root, sub) as key:
                                    count = winreg.QueryInfoKey(key)[0]
                                    for i in range(count):
                                        try:
                                            sk_name = winreg.EnumKey(key, i)
                                            with winreg.OpenKey(key, sk_name) as sk:
                                                dn, _ = winreg.QueryValueEx(sk, "DisplayName")
                                                dn_str = str(dn)
                                                if (
                                                    "microsoft office" in dn_str.lower()
                                                    or "microsoft 365" in dn_str.lower()
                                                    or "office 16" in dn_str.lower()
                                                    or "office 15" in dn_str.lower()
                                                ):
                                                    try:
                                                        dv, _ = winreg.QueryValueEx(sk, "DisplayVersion")
                                                        version = str(dv)
                                                    except OSError:
                                                        pass
                                                    try:
                                                        pub, _ = winreg.QueryValueEx(sk, "Publisher")
                                                        publisher = str(pub)
                                                    except OSError:
                                                        publisher = "Microsoft Corporation"
                                                    product_name = dn_str
                                                    installed = True
                                                    break
                                        except OSError:
                                            pass
                                    if installed:
                                        break
                            except OSError:
                                pass
                            if installed:
                                break
            except Exception as ex:
                logger.debug(f"Исключение при поиске MS Office: {ex}")

        if installed:
            ver_suffix = f" (v{version})" if version else ""
            summary = f"{product_name or 'Microsoft Office'}{ver_suffix}"
        else:
            summary = "Не установлен"

        res = OfficeSuiteInfo(
            installed=installed,
            product_name=product_name,
            version=version,
            publisher=publisher,
            status=summary,
        )
        self._office_cached = res
        return res

    def get_onedrive_info(self) -> CloudStorageInfo:
        """Сбор информации о синхронизированной папке и дисковом пространстве OneDrive.

        Returns:
            CloudStorageInfo: Сведения о локальном пути и емкости диска OneDrive.
        """
        import shutil

        od_paths: List[str] = []
        for env_var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            val = os.environ.get(env_var)
            if val and os.path.exists(val) and val not in od_paths:
                od_paths.append(val)

        if not od_paths:
            home = os.path.expanduser("~")
            candidate = os.path.join(home, "OneDrive")
            if os.path.exists(candidate):
                od_paths.append(candidate)

        if os.name == "nt":
            try:
                import winreg

                for subkey in (
                    r"Software\Microsoft\OneDrive\Accounts\Personal",
                    r"Software\Microsoft\OneDrive\Accounts\Business1",
                    r"Software\Microsoft\OneDrive",
                ):
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey) as k:
                            val, _ = winreg.QueryValueEx(k, "UserFolder")
                            if val and os.path.exists(val) and val not in od_paths:
                                od_paths.append(val)
                    except OSError:
                        pass
            except Exception:
                pass

        if not od_paths:
            return CloudStorageInfo(
                installed=False,
                name="OneDrive",
                path=None,
                status="Не настроено",
            )

        target_path = od_paths[0]
        try:
            usage = shutil.disk_usage(target_path)
            free_gb = round(usage.free / (1024**3), 1)
            total_gb = round(usage.total / (1024**3), 1)
            used_gb = round(usage.used / (1024**3), 1)
            pct = round((usage.used / max(usage.total, 1)) * 100.0, 1)

            summary = f"{free_gb} GB своб. ({target_path})"
            return CloudStorageInfo(
                installed=True,
                name="OneDrive",
                path=target_path,
                total_gb=total_gb,
                used_gb=used_gb,
                free_gb=free_gb,
                percent_used=pct,
                status=summary,
            )
        except Exception as ex:
            logger.debug(f"Ошибка проверки диска OneDrive: {ex}")
            return CloudStorageInfo(
                installed=True,
                name="OneDrive",
                path=target_path,
                status=f"Активен ({target_path})",
            )

    async def get_core_metrics(self) -> SystemCoreMetrics:
        """Сверхбыстрый сбор базовой телеметрии без вызова тяжелых внешних утилит (< 0.2с).

        Returns:
            SystemCoreMetrics: Мгновенные показатели загрузки процессора, памяти, дисков и видеокарты.
        """
        now = time.time()
        uptime = round(now - (psutil.boot_time() if PSUTIL_AVAILABLE else now - 3600), 1)
        _, disk_io = self.get_disk_metrics()
        mems = self.get_memory_metrics()
        gpus = self.get_gpu_metrics()
        batt = self.get_battery_metrics()
        cpu_metrics = await self.get_cpu_metrics()
        self._last_time = now

        return SystemCoreMetrics(
            cpu=cpu_metrics,
            memory=mems,
            gpus=gpus,
            disk_io=disk_io,
            battery=batt,
            uptime_seconds=uptime,
        )

    async def get_hardware_quick(self) -> SystemHardwareQuick:
        """Сбор сводки физических компонентов (диски, слоты памяти, порты, алерты).

        Returns:
            SystemHardwareQuick: Состояние накопителей, планок RAM и сетевых сокетов.
        """
        ram_sticks = await self.get_ram_sticks()
        phys_disks = self.get_physical_disks_health()
        ports = self.get_listening_ports()
        alerts = self.get_health_alerts()

        return SystemHardwareQuick(
            ram_sticks=ram_sticks,
            physical_disks=phys_disks,
            listening_ports=ports,
            alerts=alerts,
        )


    async def get_snapshot(self, process_limit: int = 20) -> SystemSnapshot:
        """Capture full point-in-time system telemetry snapshot without blocking event loop.

        Args:
            process_limit: Number of top active processes to include.

        Returns:
            SystemSnapshot: Consolidated system and hardware snapshot.
        """
        def _collect_sync_telemetry() -> Dict[str, Any]:
            now = time.time()
            uptime = round(now - (psutil.boot_time() if PSUTIL_AVAILABLE else now - 3600), 1)
            partitions, disk_io = self.get_disk_metrics()
            net_metrics = self.get_network_metrics()
            sensors = get_hardware_sensors()
            top_procs = self.get_top_processes(limit=process_limit)
            ident = self.get_system_identity()
            mems = self.get_memory_metrics()
            gpu_list = self.get_gpu_metrics()
            mon_list = self.get_monitors()
            upd_info = self.get_updates_info()
            off_info = self.get_ms_office_info()
            od_info = self.get_onedrive_info()
            phys_disks = self.get_physical_disks_health()
            ports = self.get_listening_ports()
            net_activity = self.get_process_network_activity(limit=40)
            batt = self.get_battery_metrics()
            alerts = self.get_health_alerts()
            self._last_time = now

            return {
                "now": now,
                "uptime": uptime,
                "partitions": partitions,
                "disk_io": disk_io,
                "net_metrics": net_metrics,
                "sensors": sensors,
                "top_procs": top_procs,
                "ident": ident,
                "memory": mems,
                "gpus": gpu_list,
                "monitors": mon_list,
                "updates": upd_info,
                "office": off_info,
                "onedrive": od_info,
                "physical_disks": phys_disks,
                "listening_ports": ports,
                "net_activity": net_activity,
                "battery": batt,
                "alerts": alerts,
            }

        # Асинхронно параллельно запускаем сбор CPU, RAM и тяжелых синхронных метрик
        cpu_task = asyncio.create_task(self.get_cpu_metrics())
        ram_task = asyncio.create_task(self.get_ram_sticks())
        sync_task = asyncio.create_task(asyncio.to_thread(_collect_sync_telemetry))

        cpu_metrics, ram_sticks, sync_data = await asyncio.gather(cpu_task, ram_task, sync_task)
        ident = sync_data["ident"]

        return SystemSnapshot(
            hostname=ident.get("hostname") or socket.gethostname(),
            username=ident.get("username") or "",
            os_name=f"{platform.system()} {platform.release()}",
            os_build=ident.get("os_build") or platform.version(),
            system_language=ident.get("system_language") or "",
            user_locale=ident.get("user_locale") or "",
            system_locale=ident.get("system_locale") or "",
            timezone=ident.get("timezone") or "",
            codepage=ident.get("codepage") or "",
            input_languages=ident.get("input_languages") or [],
            os_install_date=ident.get("os_install_date") or "",
            uptime_seconds=sync_data["uptime"],
            cpu=cpu_metrics,
            memory=sync_data["memory"],
            ram_sticks=ram_sticks,
            gpus=sync_data["gpus"],
            monitors=sync_data["monitors"],
            updates=sync_data["updates"],
            office=sync_data["office"],
            onedrive=sync_data["onedrive"],
            disks=sync_data["partitions"],
            physical_disks=sync_data["physical_disks"],
            disk_io=sync_data["disk_io"],
            network=sync_data["net_metrics"],
            listening_ports=sync_data["listening_ports"],
            network_activity=sync_data["net_activity"],
            battery=sync_data["battery"],
            alerts=sync_data["alerts"],
            sensors=sync_data["sensors"],
            top_processes=sync_data["top_procs"],
        )

    def get_hardware_sensors(self) -> List[HardwareSensor]:
        """Collect real-time hardware sensors readings.

        Returns:
            List[HardwareSensor]: Hardware sensors and temperatures.
        """
        return get_hardware_sensors()

    async def get_hardware_tree_async(self) -> List[HardwareNode]:
        """Generate AIDA64-like hierarchical component specification tree (Async).

        Returns:
            List[HardwareNode]: Hardware devices grouped by category.
        """
        if os.name == "nt":
            try:
                import pythoncom

                pythoncom.CoInitialize()
            except Exception as e:
                logger.debug(f"[HardwareTree] CoInitialize warning: {e}")

        nodes: List[HardwareNode] = []
        ident = self.get_system_identity()

        # 1. Компьютер и операционная система (System & OS)
        nodes.append(
            HardwareNode(
                category="System",
                name=f"{ident.get('hostname')} ({platform.system()} {platform.release()})",
                properties={
                    "Компьютер (Host)": ident.get("hostname", ""),
                    "Пользователь": ident.get("username", ""),
                    "Версия Windows": platform.version(),
                    "Номер сборки": ident.get("os_build", ""),
                    "Дата установки ОС": ident.get("os_install_date", ""),
                    "Язык системы": ident.get("system_language", ""),
                    "Локали": f"User: {ident.get('user_locale', '')} | Sys: {ident.get('system_locale', '')}",
                    "Часовой пояс": ident.get("timezone", ""),
                    "Кодировки": ident.get("codepage", ""),
                    "Языки ввода": ", ".join(ident.get("input_languages", [])),
                    "Архитектура": platform.machine(),
                    "Среда Python": platform.python_version(),
                },
            )
        )

        # 2. Процессор (CPU) с деталями кэша и сокета
        cpu = await self.get_cpu_metrics()
        cpu_props: Dict[str, Any] = {
            "Модель процессора": cpu.model,
            "Физические ядра": cpu.physical_cores,
            "Логические потоки": cpu.logical_cores,
            "Базовая частота": f"{cpu.frequency_mhz} MHz",
            "Архитектура": cpu.architecture,
        }

        # Дополнительный опрос WMI Win32_Processor для расширенных данных кэша и сокета
        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")
                for p in wmi_obj.InstancesOf("Win32_Processor"):
                    if getattr(p, "SocketDesignation", None):
                        cpu_props["Разъем (Socket)"] = p.SocketDesignation
                    if getattr(p, "L2CacheSize", None):
                        cpu_props["Кэш L2"] = f"{round(p.L2CacheSize / 1024, 1)} MB ({p.L2CacheSize} KB)"
                    if getattr(p, "L3CacheSize", None):
                        cpu_props["Кэш L3"] = f"{round(p.L3CacheSize / 1024, 1)} MB ({p.L3CacheSize} KB)"
                    if getattr(p, "MaxClockSpeed", None):
                        cpu_props["Макс. частота"] = f"{p.MaxClockSpeed} MHz"
                    if getattr(p, "Manufacturer", None):
                        cpu_props["Производитель"] = p.Manufacturer
                    break
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI Win32_Processor warning: {e}")

        nodes.append(
            HardwareNode(
                category="Processor (CPU)",
                name=cpu.model,
                properties=cpu_props,
            )
        )

        # 3. Системная плата и BIOS (Motherboard & BIOS)
        if os.name == "nt":
            mb_props: Dict[str, Any] = {}
            mb_name = ""
            mb_mfg = ""
            try:
                import winreg

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                    mb_mfg, _ = winreg.QueryValueEx(key, "BaseBoardManufacturer")
                    mb_name, _ = winreg.QueryValueEx(key, "BaseBoardProduct")
                    bios_ver, _ = winreg.QueryValueEx(key, "BIOSVersion")
                    if mb_mfg:
                        mb_props["Производитель платы"] = mb_mfg
                    if mb_name:
                        mb_props["Модель платы"] = mb_name
                    if bios_ver:
                        mb_props["Версия BIOS"] = bios_ver
            except Exception:
                pass

            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")
                for b in wmi_obj.InstancesOf("Win32_BaseBoard"):
                    if getattr(b, "Manufacturer", None):
                        mb_props["Производитель платы"] = b.Manufacturer
                    if getattr(b, "Product", None):
                        mb_props["Модель платы"] = b.Product
                    if getattr(b, "SerialNumber", None):
                        mb_props["Серийный номер платы"] = (b.SerialNumber or "").strip()
                    if getattr(b, "Version", None):
                        mb_props["Ревизия / Версия"] = b.Version
                    mb_name = mb_props.get("Модель платы", mb_name)
                    mb_mfg = mb_props.get("Производитель платы", mb_mfg)
                    break

                for bios in wmi_obj.InstancesOf("Win32_BIOS"):
                    if getattr(bios, "Manufacturer", None):
                        mb_props["Производитель BIOS"] = bios.Manufacturer
                    if getattr(bios, "SMBIOSBIOSVersion", None):
                        mb_props["Версия SMBIOS BIOS"] = bios.SMBIOSBIOSVersion
                    if getattr(bios, "ReleaseDate", None):
                        rel_date = str(bios.ReleaseDate)[:8]
                        if len(rel_date) == 8:
                            mb_props["Дата выпуска BIOS"] = f"{rel_date[6:8]}.{rel_date[4:6]}.{rel_date[0:4]}"
                        else:
                            mb_props["Дата выпуска BIOS"] = str(bios.ReleaseDate)
                    break
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI BaseBoard/BIOS warning: {e}")

            if mb_props:
                nodes.append(
                    HardwareNode(
                        category="Motherboard",
                        name=f"{mb_mfg} {mb_name}".strip() or "Motherboard",
                        properties=mb_props,
                    )
                )

        # 4. Общая память (System Memory RAM Overview)
        mem = self.get_memory_metrics()
        mem_overview_props: Dict[str, Any] = {
            "Общий объем RAM": f"{mem.total_gb} GB",
            "Доступная память": f"{mem.available_gb} GB",
            "Файл подкачки (Swap)": f"{mem.swap_total_gb} GB",
        }

        # 4.1 Физические планки памяти (Physical RAM DIMM Modules)
        ram_modules_found = 0
        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")

                # Количество слотов на плате и макс. поддерживаемый объем
                for arr in wmi_obj.InstancesOf("Win32_PhysicalMemoryArray"):
                    if getattr(arr, "MemoryDevices", None):
                        mem_overview_props["Слотов памяти на плате"] = arr.MemoryDevices
                    if getattr(arr, "MaxCapacity", None):
                        max_gb = round(int(arr.MaxCapacity) / (1024**2), 1)
                        mem_overview_props["Макс. поддерживаемый объем"] = f"{max_gb} GB"
                    break

                type_map = {
                    20: "DDR",
                    21: "DDR2",
                    22: "DDR2 FB-DIMM",
                    24: "DDR3",
                    26: "DDR4",
                    27: "LPDDR",
                    28: "LPDDR2",
                    29: "LPDDR3",
                    30: "LPDDR4",
                    34: "DDR5",
                    35: "LPDDR5",
                }
                form_map = {
                    8: "DIMM (Desktop)",
                    12: "SODIMM (Laptop)",
                    9: "TSOP",
                    10: "PGA",
                    11: "RIMM",
                }

                for idx, m in enumerate(wmi_obj.InstancesOf("Win32_PhysicalMemory")):
                    ram_modules_found += 1
                    cap_bytes = int(getattr(m, "Capacity", 0) or 0)
                    cap_gb = round(cap_bytes / (1024**3), 1)
                    smbios_type = int(getattr(m, "SMBIOSMemoryType", 0) or 0)
                    mem_type = type_map.get(smbios_type, f"DDR (Тип {smbios_type})" if smbios_type else "DDR")
                    form_code = int(getattr(m, "FormFactor", 0) or 0)
                    form_name = form_map.get(form_code, "DIMM")

                    mfg = (getattr(m, "Manufacturer", "") or "").strip()
                    if mfg == "04CB000080CE":
                        mfg_display = "ADATA / Micron (04CB)"
                    elif mfg:
                        mfg_display = mfg
                    else:
                        mfg_display = "Не определен"

                    sn = (getattr(m, "SerialNumber", "") or "").strip() or "N/A"
                    pn = (getattr(m, "PartNumber", "") or "").strip() or "N/A"
                    speed = getattr(m, "Speed", 0) or 0
                    clock = getattr(m, "ConfiguredClockSpeed", 0) or speed
                    locator = (getattr(m, "DeviceLocator", "") or f"DIMM {idx+1}").strip()
                    bank = (getattr(m, "BankLabel", "") or "").strip()

                    module_props: Dict[str, Any] = {
                        "Слот / Разъем (Locator)": locator,
                        "Объем планки": f"{cap_gb} GB ({cap_bytes:,} байт)",
                        "Производитель": mfg_display,
                        "Серийный номер (S/N)": sn,
                        "Парт-номер (P/N)": pn,
                        "Номинальная частота": f"{speed} MHz" if speed else "N/A",
                        "Текущая рабочая частота": f"{clock} MHz" if clock else "N/A",
                        "Тип памяти": f"{mem_type} (SMBIOS {smbios_type})",
                        "Форм-фактор": form_name,
                    }
                    if bank:
                        module_props["Банк памяти (Bank)"] = bank

                    nodes.append(
                        HardwareNode(
                            category="Memory Module (RAM)",
                            name=f"Планка {idx+1} ({locator}): {cap_gb} GB {mem_type}-{speed or clock}",
                            properties=module_props,
                        )
                    )
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI PhysicalMemory query warning: {e}")

        if ram_modules_found > 0:
            mem_overview_props["Установлено модулей"] = f"{ram_modules_found} шт."

        nodes.append(
            HardwareNode(
                category="System Memory",
                name=f"{mem.total_gb} GB Physical RAM",
                properties=mem_overview_props,
            )
        )

        # 5. Видеоадаптеры и ускорители (Display Adapters & GPUs)
        wmi_video_map: Dict[str, Dict[str, Any]] = {}
        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")
                for v in wmi_obj.InstancesOf("Win32_VideoController"):
                    v_name = (getattr(v, "Name", "") or "").strip()
                    v_pnp = (getattr(v, "PNPDeviceID", "") or "").strip()
                    v_mfg = (getattr(v, "AdapterCompatibility", "") or "").strip()
                    v_drv_ver = (getattr(v, "DriverVersion", "") or "").strip()
                    v_drv_date_raw = getattr(v, "DriverDate", None)
                    v_drv_date = ""
                    if v_drv_date_raw:
                        ds = str(v_drv_date_raw)[:8]
                        if len(ds) == 8 and ds.isdigit():
                            v_drv_date = f"{ds[6:8]}.{ds[4:6]}.{ds[0:4]}"
                    v_proc = (getattr(v, "VideoProcessor", "") or "").strip()
                    v_mode = (getattr(v, "VideoModeDescription", "") or "").strip()
                    v_refresh = getattr(v, "CurrentRefreshRate", None)
                    v_status = (getattr(v, "Status", "") or "OK").strip()

                    info_dict = {
                        "name": v_name,
                        "mfg": v_mfg,
                        "drv_ver": v_drv_ver,
                        "drv_date": v_drv_date,
                        "proc": v_proc,
                        "mode": v_mode,
                        "refresh": v_refresh,
                        "status": v_status,
                        "pnp": v_pnp,
                    }
                    if v_name:
                        wmi_video_map[v_name.lower()] = info_dict
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI VideoController query warning: {e}")

        gpus = self.get_gpu_metrics()
        for idx, gpu in enumerate(gpus):
            v_extra = wmi_video_map.get(gpu.name.lower(), {})
            gpu_mfg = v_extra.get("mfg") or ("NVIDIA" if "geforce" in gpu.name.lower() or "nvidia" in gpu.name.lower() else "Intel" if "intel" in gpu.name.lower() else "AMD" if "radeon" in gpu.name.lower() else "Unknown")
            drv_ver = v_extra.get("drv_ver")
            drv_date = v_extra.get("drv_date")
            vproc = v_extra.get("proc")
            vmode = v_extra.get("mode")

            gpu_props: Dict[str, Any] = {
                "Индекс устройства": idx,
                "Модель видеокарты": gpu.name,
                "Производитель (Вендор)": gpu_mfg,
                "Объем видеопамяти (VRAM)": f"{gpu.memory_total_gb} GB",
            }
            if vproc:
                gpu_props["Видеопроцессор"] = vproc
            if drv_ver:
                gpu_props["Версия драйвера"] = drv_ver
            if drv_date:
                gpu_props["Дата драйвера"] = drv_date
            if vmode:
                gpu_props["Текущий видеорежим"] = vmode
            elif v_extra.get("refresh"):
                gpu_props["Частота обновления"] = f"{v_extra['refresh']} Hz"

            gpu_props["Поддержка CUDA"] = "Да" if gpu.has_cuda else "Нет"
            gpu_props["Поддержка DirectML"] = "Да" if gpu.has_directml else "Нет"
            gpu_props["Статус устройства"] = v_extra.get("status", "OK (Активно)")
            if v_extra.get("pnp"):
                gpu_props["Идентификатор PnP"] = v_extra["pnp"]

            nodes.append(
                HardwareNode(
                    category="Display Adapter",
                    name=gpu.name,
                    properties=gpu_props,
                )
            )

        # 6. Дисплеи и мониторы (Monitors & Displays)
        for idx, mon in enumerate(self.get_monitors()):
            nodes.append(
                HardwareNode(
                    category="Monitors & Displays",
                    name=f"{mon.name} ({mon.width}x{mon.height} @ {mon.frequency_hz}Hz)",
                    properties={
                        "Устройство": mon.device,
                        "Название дисплея": mon.name,
                        "Подключенный видеоадаптер": mon.adapter or "Default Adapter",
                        "Разрешение экрана": f"{mon.width} x {mon.height}",
                        "Частота развертки": f"{mon.frequency_hz} Hz",
                        "Глубина цвета": f"{mon.bits_per_pixel}-bit",
                        "Основной монитор": "Да (Основной)" if mon.is_primary else "Нет (Вторичный)",
                    },
                )
            )

        # 7. Физические накопители (Physical Storage Drives)
        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")
                for d in wmi_obj.InstancesOf("Win32_DiskDrive"):
                    size_bytes = int(getattr(d, "Size", 0) or 0)
                    size_gb = round(size_bytes / (1024**3), 1)
                    model = (getattr(d, "Model", "") or "Hard Disk").strip()
                    iface = (getattr(d, "InterfaceType", "") or "SCSI/SATA").strip()
                    media = (getattr(d, "MediaType", "") or "Fixed hard disk media").strip()
                    sn = (getattr(d, "SerialNumber", "") or "").strip() or "N/A"
                    firmware = (getattr(d, "FirmwareRevision", "") or "").strip()
                    parts = getattr(d, "Partitions", 0) or 1
                    status = (getattr(d, "Status", "") or "OK").strip()

                    # Определение бренда производителя накопителя
                    model_l = model.lower()
                    if "samsung" in model_l:
                        disk_mfg = "Samsung"
                    elif "crucial" in model_l or model_l.startswith("ct"):
                        disk_mfg = "Crucial / Micron"
                    elif "toshiba" in model_l or model_l.startswith("hdwd") or model_l.startswith("dt01"):
                        disk_mfg = "Toshiba"
                    elif "wdc" in model_l or model_l.startswith("wd") or "western digital" in model_l:
                        disk_mfg = "Western Digital"
                    elif "kingston" in model_l or model_l.startswith("sa400") or model_l.startswith("skc"):
                        disk_mfg = "Kingston"
                    elif "seagate" in model_l or model_l.startswith("st"):
                        disk_mfg = "Seagate"
                    elif "sandisk" in model_l:
                        disk_mfg = "SanDisk"
                    elif "kioxia" in model_l:
                        disk_mfg = "Kioxia"
                    elif "intel" in model_l:
                        disk_mfg = "Intel"
                    elif "micron" in model_l:
                        disk_mfg = "Micron"
                    elif "sk hynix" in model_l or "hynix" in model_l:
                        disk_mfg = "SK Hynix"
                    else:
                        disk_mfg = "Универсальный накопитель"

                    disk_props: Dict[str, Any] = {
                        "Модель накопителя": model,
                        "Производитель (Бренд)": disk_mfg,
                        "Интерфейс подключения": iface,
                        "Тип носителя": media,
                        "Емкость": f"{size_gb} GB ({size_bytes:,} байт)",
                        "Серийный номер (S/N)": sn,
                    }
                    if firmware:
                        disk_props["Версия прошивки (Firmware)"] = firmware
                    disk_props["Число разделов"] = parts
                    disk_props["Статус S.M.A.R.T."] = status

                    nodes.append(
                        HardwareNode(
                            category="Physical Disk",
                            name=f"{model} ({size_gb} GB)",
                            properties=disk_props,
                        )
                    )
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI DiskDrive query warning: {e}")

        # 8. Логические разделы дисков (Logical Storage Volumes)
        partitions, _ = self.get_disk_metrics()
        for part in partitions:
            nodes.append(
                HardwareNode(
                    category="Storage Volume",
                    name=f"Раздел {part.device} ({part.total_gb} GB)",
                    properties={
                        "Дисковый том": part.device,
                        "Точка монтирования": part.mountpoint,
                        "Файловая система": part.fstype,
                        "Общий объем": f"{part.total_gb} GB",
                        "Свободное место": f"{part.free_gb} GB",
                        "Занято памяти": f"{part.used_gb} GB ({part.percent}%)",
                    },
                )
            )

        # 9. Сетевые адаптеры (Network Adapters) с полными параметрами WMI/psutil
        wmi_net_adapters: Dict[str, Dict[str, Any]] = {}
        wmi_net_configs: Dict[str, Any] = {}

        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")

                for cfg in wmi_obj.InstancesOf("Win32_NetworkAdapterConfiguration"):
                    cdesc = (getattr(cfg, "Description", "") or "").strip()
                    if cdesc:
                        wmi_net_configs[cdesc.lower()] = cfg

                for a in wmi_obj.InstancesOf("Win32_NetworkAdapter"):
                    net_id = (getattr(a, "NetConnectionID", "") or "").strip()
                    aname = (getattr(a, "Name", "") or "").strip()
                    adesc = (getattr(a, "Description", "") or "").strip()
                    apnp = (getattr(a, "PNPDeviceID", "") or "").strip()
                    amfg = (getattr(a, "Manufacturer", "") or "").strip()
                    amac = (getattr(a, "MACAddress", "") or "").strip()
                    aspeed = getattr(a, "Speed", None)
                    atype = (getattr(a, "AdapterType", "") or "").strip()
                    astatus_num = getattr(a, "NetConnectionStatus", None)
                    aphys = getattr(a, "PhysicalAdapter", False)

                    item = {
                        "net_id": net_id,
                        "name": aname,
                        "desc": adesc,
                        "pnp": apnp,
                        "mfg": amfg,
                        "mac": amac,
                        "speed": aspeed,
                        "ad_type": atype,
                        "status_num": astatus_num,
                        "is_phys": aphys,
                    }
                    if net_id:
                        wmi_net_adapters[net_id.lower()] = item
                    if aname:
                        wmi_net_adapters[aname.lower()] = item
                    if adesc:
                        wmi_net_adapters[adesc.lower()] = item
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI NetworkAdapter query warning: {e}")

        if PSUTIL_AVAILABLE:
            ps_addrs = psutil.net_if_addrs()
            ps_stats = psutil.net_if_stats()

            for if_name, addr_list in ps_addrs.items():
                stat = ps_stats.get(if_name)
                w_info = wmi_net_adapters.get(if_name.lower(), {})
                cfg = wmi_net_configs.get(w_info.get("desc", "").lower()) or wmi_net_configs.get(if_name.lower())

                # Физический MAC-адрес
                mac_addr = w_info.get("mac")
                if not mac_addr:
                    for a in addr_list:
                        fam_name = getattr(a.family, "name", "")
                        if fam_name == "AF_LINK" or a.family == -1 or a.family == getattr(psutil, "AF_LINK", -1):
                            if a.address and len(a.address) in (12, 17):
                                mac_addr = a.address.replace("-", ":").upper()
                                break

                # IP-адреса
                ipv4_list = [a.address for a in addr_list if a.family == socket.AF_INET]
                ipv6_list = [a.address.split("%")[0] for a in addr_list if hasattr(socket, "AF_INET6") and a.family == socket.AF_INET6]

                # Шлюзы, DHCP, DNS
                gateways = list(getattr(cfg, "DefaultIPGateway", []) or []) if cfg else []
                dhcp_server = getattr(cfg, "DHCPServer", None) if cfg else None
                dhcp_enabled = getattr(cfg, "DHCPEnabled", None) if cfg else None
                dns_servers = list(getattr(cfg, "DNSServerSearchOrder", []) or []) if cfg else []

                # Статус соединения
                is_up = stat.isup if stat else True
                status_num = w_info.get("status_num")
                if status_num == 2 or (status_num is None and is_up):
                    status_str = "Активно (Up)"
                elif status_num == 7:
                    status_str = "Кабель не подключен (Disconnected)"
                elif status_num == 0:
                    status_str = "Отключено (Disabled)"
                elif not is_up:
                    status_str = "Не активно (Down)"
                else:
                    status_str = "Активно (Up)"

                # Скорость соединения
                speed_mbps = 0
                if stat and stat.speed and stat.speed > 0 and stat.speed < 1000000:
                    speed_mbps = stat.speed
                elif w_info.get("speed"):
                    try:
                        raw_spd = int(w_info["speed"])
                        if raw_spd < 100_000_000_000:
                            speed_mbps = round(raw_spd / 1_000_000)
                    except Exception:
                        pass

                if speed_mbps > 0:
                    if speed_mbps >= 1000:
                        speed_str = f"{speed_mbps} Mbps ({round(speed_mbps / 1000, 1)} Gbps)"
                    else:
                        speed_str = f"{speed_mbps} Mbps"
                else:
                    speed_str = "Автоопределение (0 Mbps)" if not is_up else "1000 Mbps (Авто)"

                # Модель адаптера и производитель
                model_name = w_info.get("name") or w_info.get("desc") or if_name
                mfg_val = w_info.get("mfg")
                if not mfg_val:
                    if "intel" in if_name.lower() or "intel" in model_name.lower():
                        mfg_val = "Intel Corporation"
                    elif "realtek" in if_name.lower() or "realtek" in model_name.lower():
                        mfg_val = "Realtek"
                    elif "vethernet" in if_name.lower() or "hyper-v" in model_name.lower() or "microsoft" in model_name.lower() or "local area connection*" in if_name.lower():
                        mfg_val = "Microsoft Corporation"
                    else:
                        mfg_val = "Универсальный сетевой контроллер"

                # Тип адаптера
                name_l = if_name.lower()
                desc_l = (w_info.get("desc") or "").lower()
                if "local area connection*" in name_l:
                    adapter_type = "Виртуальный адаптер Wi-Fi Direct"
                    if model_name == if_name:
                        model_name = f"Microsoft Wi-Fi Direct Virtual Adapter ({if_name})"
                elif "wi-fi" in name_l or "wireless" in desc_l or "802.11" in desc_l:
                    adapter_type = "Беспроводной адаптер (Wi-Fi 802.11)"
                elif "bluetooth" in name_l or "bluetooth" in desc_l:
                    adapter_type = "Bluetooth PAN адаптер"
                elif "vethernet" in name_l or "virtual" in desc_l or "hyper-v" in desc_l:
                    adapter_type = "Виртуальный сетевой адаптер (Hyper-V / WSL)"
                elif "loopback" in name_l:
                    adapter_type = "Программный интерфейс Loopback"
                elif "tap" in name_l or "tun" in name_l or "vpn" in name_l:
                    adapter_type = "VPN / Туннельный адаптер"
                else:
                    adapter_type = "Сетевая карта Ethernet (LAN)"

                net_props: Dict[str, Any] = {
                    "Имя подключения": if_name,
                    "Модель адаптера": model_name,
                    "Производитель": mfg_val,
                    "Тип адаптера": adapter_type,
                    "Физический (MAC) адрес": mac_addr or "N/A",
                    "Состояние соединения": status_str,
                    "Скорость канала": speed_str,
                }
                if stat and getattr(stat, "duplex", None) is not None:
                    d_val = getattr(stat.duplex, "value", stat.duplex)
                    if d_val == 2:
                        net_props["Режим дуплекса"] = "Full Duplex (Полный)"
                    elif d_val == 1:
                        net_props["Режим дуплекса"] = "Half Duplex (Полудуплекс)"
                if stat and getattr(stat, "mtu", None):
                    net_props["Размер MTU"] = f"{stat.mtu} байт"

                net_props["IP-адреса (IPv4)"] = ", ".join(ipv4_list) or "N/A"
                if ipv6_list:
                    net_props["IP-адреса (IPv6)"] = ", ".join(ipv6_list[:3])
                if gateways:
                    net_props["Основной шлюз"] = ", ".join(gateways)
                if dhcp_server or dhcp_enabled is not None:
                    net_props["DHCP сервер"] = dhcp_server or ("Включен (DHCP)" if dhcp_enabled else "Статический IP / Отключен")
                if dns_servers:
                    net_props["DNS серверы"] = ", ".join(dns_servers)
                if w_info.get("pnp"):
                    net_props["Идентификатор PnP"] = w_info["pnp"]

                display_title = f"{if_name}: {model_name}" if model_name != if_name else if_name
                nodes.append(
                    HardwareNode(
                        category="Network Adapter",
                        name=display_title,
                        properties=net_props,
                    )
                )

        # 10. Аудиоустройства и звуковые карты (Audio Devices)
        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")
                for s in wmi_obj.InstancesOf("Win32_SoundDevice"):
                    snd_name = (getattr(s, "Caption", "") or getattr(s, "Name", "") or "").strip()
                    snd_mfg = (getattr(s, "Manufacturer", "") or "").strip() or "Аудиоустройство"
                    snd_status = (getattr(s, "Status", "") or "OK").strip()
                    snd_pnp = (getattr(s, "PNPDeviceID", "") or "").strip()

                    if snd_name:
                        nodes.append(
                            HardwareNode(
                                category="Audio Device",
                                name=snd_name,
                                properties={
                                    "Название устройства": snd_name,
                                    "Производитель": snd_mfg,
                                    "Состояние": f"{snd_status} (Работает)",
                                    "Идентификатор PnP": snd_pnp or "N/A",
                                },
                            )
                        )
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI SoundDevice query warning: {e}")

        # 11. USB-контроллеры (USB Controllers)
        if os.name == "nt":
            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject("winmgmts:")
                for u in wmi_obj.InstancesOf("Win32_USBController"):
                    usb_name = (getattr(u, "Caption", "") or getattr(u, "Name", "") or "").strip()
                    usb_mfg = (getattr(u, "Manufacturer", "") or "").strip() or "USB Контроллер"
                    usb_status = (getattr(u, "Status", "") or "OK").strip()
                    usb_pnp = (getattr(u, "PNPDeviceID", "") or "").strip()

                    if usb_name:
                        nodes.append(
                            HardwareNode(
                                category="USB Controller",
                                name=usb_name,
                                properties={
                                    "Название контроллера": usb_name,
                                    "Производитель": usb_mfg,
                                    "Состояние": f"{usb_status} (Работает)",
                                    "Идентификатор PnP": usb_pnp or "N/A",
                                },
                            )
                        )
            except Exception as e:
                logger.debug(f"[HardwareTree] WMI USBController query warning: {e}")

        # 12. Обновления Windows (Windows Updates & Servicing)
        upd = self.get_updates_info()
        nodes.append(
            HardwareNode(
                category="Windows Updates",
                name=f"{upd.status} ({upd.installed_kb_count} KBs)",
                properties={
                    "Статус обновлений": upd.status,
                    "Число установленных исправлений": upd.installed_kb_count,
                    "Последние KB пакеты": ", ".join(upd.recent_hotfixes) or "N/A",
                    "Дата последней установки": upd.latest_installed_on or "OK",
                },
            )
        )

        return nodes

    def get_hardware_tree(self) -> List[HardwareNode]:
        """Generate AIDA64-like hierarchical component specification tree.

        Returns:
            List[HardwareNode]: Hardware devices grouped by category.
        """
        import asyncio
        return asyncio.run(self.get_hardware_tree_async())

    def get_hardware_audit(self) -> HardwareAuditReport:
        """Collect deep hardware devices audit with drivers, install dates, and attached sensors.

        Returns:
            HardwareAuditReport: Complete hardware audit report.
        """
        return self.auditor.audit_hardware()

    def archive_hardware_state(self, auto_diff: bool = True) -> HardwareArchiveEntry:
        """Capture current hardware audit and save it to historical archive storage.

        Args:
            auto_diff: Automatically compute diff with previous archive.

        Returns:
            HardwareArchiveEntry: Persisted archive entry with detected changes.
        """
        report = self.get_hardware_audit()
        return self.history_manager.archive_report(report, auto_diff=auto_diff)

    def get_hardware_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve historical hardware archive snapshots metadata.

        Args:
            limit: Maximum count of archive entries.

        Returns:
            List[Dict[str, Any]]: Chronological list of archive entries.
        """
        return self.history_manager.get_history(limit=limit)

    def get_hardware_changes(self, limit: int = 100) -> List[HardwareChangeItem]:
        """Retrieve historical timeline of all hardware configuration changes.

        Args:
            limit: Maximum count of changes to return.

        Returns:
            List[HardwareChangeItem]: Historical changes timeline.
        """
        return self.history_manager.get_change_timeline(limit=limit)

    def save_snapshot_to_db(
        self,
        snapshot: Optional[SystemSnapshot] = None,
        top_n: int = 20,
    ) -> int:
        """Collect and save system telemetry snapshot directly into SQLite database.

        Args:
            snapshot: Optional existing SystemSnapshot (if None, collected synchronously).
            top_n: Top processes count.

        Returns:
            int: Created snapshot ID in database.
        """
        snap = snapshot
        if snap is None:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                snap = asyncio.run_coroutine_threadsafe(
                    self.get_snapshot(process_limit=top_n),
                    loop,
                ).result(timeout=5.0)
            else:
                snap = asyncio.run(self.get_snapshot(process_limit=top_n))

        return self.storage.save_snapshot(snap, top_n=top_n)

    def get_snapshots(
        self,
        limit: int = 60,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve persisted system snapshots from SQLite database.

        Args:
            limit: Maximum number of snapshots.
            since_epoch: Optional starting timestamp.

        Returns:
            List[Dict[str, Any]]: List of system snapshots from database.
        """
        return self.storage.get_snapshots(limit=limit, since_epoch=since_epoch)

    def get_process_history(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical process metrics from SQLite database.

        Args:
            name: Substring of process name.
            pid: Process identifier.
            limit: Record limit.

        Returns:
            List[Dict[str, Any]]: History of process metrics.
        """
        return self.storage.get_process_history(name=name, pid=pid, limit=limit)


