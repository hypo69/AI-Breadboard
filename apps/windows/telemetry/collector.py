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

from src.ai.orchestration.hardware import probe_hardware
from src.logger import logger
from apps.windows.telemetry.models import (
    AnomalyItem,
    BatteryMetrics,
    CpuMetrics,
    DiskIoMetrics,
    DiskPartitionMetrics,
    GpuMetrics,
    HardwareNode,
    HardwareSensor,
    MemoryMetrics,
    NetworkInterfaceMetrics,
    NetworkPortMetrics,
    PhysicalDiskHealth,
    ProcessMetrics,
    RamStickInfo,
    SystemHealthAlerts,
    SystemSnapshot,
)
from apps.windows.telemetry.sensors import get_hardware_sensors


class SystemCollector:
    """Telemetry collector for system load, hardware devices, and processes."""

    def __init__(self) -> None:
        """Initialize telemetry collector with timing and I/O baseline state."""
        self._last_disk_io = psutil.disk_io_counters() if PSUTIL_AVAILABLE else None
        self._last_net_io = psutil.net_io_counters(pernic=True) if PSUTIL_AVAILABLE else None
        self._last_time = time.time()
        self._cpu_model_cached: Optional[str] = None
        self._identity_cached: Optional[Dict[str, Any]] = None

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

        self._identity_cached = {
            "hostname": hostname,
            "username": full_username,
            "os_build": os_build,
            "system_language": sys_lang_display,
            "user_locale": user_locale,
            "system_locale": system_locale,
            "timezone": timezone_str,
            "codepage": codepage,
            "input_languages": input_languages,
        }
        return self._identity_cached

    def _resolve_cpu_model(self) -> str:
        """Resolve CPU brand/model name from platform or WMI.

        Returns:
            str: Resolved CPU model name.
        """
        if self._cpu_model_cached:
            return self._cpu_model_cached

        model = platform.processor() or ""
        if os.name == "nt" and (not model or "Intel64" in model or "AMD64" in model):
            try:
                import wmi  # type: ignore

                w = wmi.WMI()
                cpus = w.Win32_Processor()
                if cpus:
                    model = str(cpus[0].Name).strip()
            except Exception:
                pass

        if not model:
            model = f"{platform.machine()} {os.cpu_count() or 1}-Core Processor"

        self._cpu_model_cached = model
        return model

    def get_cpu_metrics(self) -> CpuMetrics:
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
                model=self._resolve_cpu_model(),
                architecture=platform.machine(),
                physical_cores=physical,
                logical_cores=logical,
                total_percent=total,
                per_core_percent=per_core,
                frequency_mhz=freq_mhz,
            )

        return CpuMetrics(
            model=self._resolve_cpu_model(),
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
        except Exception as ex:
            logger.debug(f"Failed to probe GPUs via hardware module: {ex}")

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
                    partitions.append(
                        DiskPartitionMetrics(
                            device=part.device,
                            mountpoint=part.mountpoint,
                            fstype=part.fstype,
                            total_gb=round(usage.total / (1024**3), 2),
                            used_gb=round(usage.used / (1024**3), 2),
                            free_gb=round(usage.free / (1024**3), 2),
                            percent=round(usage.percent, 1),
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
            limit: Maximum processes to return.
            sort_by: Attribute to sort by ('cpu', 'memory').

        Returns:
            List[ProcessMetrics]: Ranked process metrics.
        """
        procs: List[ProcessMetrics] = []

        if PSUTIL_AVAILABLE:
            for p in psutil.process_iter(
                attrs=["pid", "name", "status", "cpu_percent", "memory_info", "memory_percent", "num_threads", "username"]
            ):
                try:
                    info = p.info
                    mem_info = info.get("memory_info")
                    rss_mb = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0.0
                    cpu_p = round(info.get("cpu_percent") or 0.0, 1)

                    procs.append(
                        ProcessMetrics(
                            pid=info["pid"],
                            name=info.get("name") or "unknown",
                            status=info.get("status") or "running",
                            cpu_percent=cpu_p,
                            memory_mb=rss_mb,
                            memory_percent=round(info.get("memory_percent") or 0.0, 1),
                            num_threads=info.get("num_threads") or 1,
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
                    username=os.getenv("USERNAME", "SYSTEM"),
                )
            )

        if sort_by == "memory":
            procs.sort(key=lambda x: x.memory_mb, reverse=True)
        else:
            procs.sort(key=lambda x: x.cpu_percent, reverse=True)

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
        """Collect physical drives SMART, media type and health status via WMI/Storage.

        Returns:
            List[PhysicalDiskHealth]: Detected physical drives.
        """
        disks: List[PhysicalDiskHealth] = []
        if os.name == "nt":
            try:
                import wmi  # type: ignore

                # Try Microsoft Storage namespace for NVMe/SSD Health
                try:
                    w_storage = wmi.WMI(namespace=r"root\Microsoft\Windows\Storage")
                    phys_disks = w_storage.MSFT_PhysicalDisk()
                    for d in phys_disks:
                        media_map = {3: "HDD", 4: "SSD", 5: "SCM"}
                        media_type = media_map.get(d.MediaType, "NVMe/SSD" if "NVMe" in str(d.Model) else "Disk")
                        health_map = {0: "Healthy", 1: "Warning", 2: "Unhealthy"}
                        health = health_map.get(d.HealthStatus, "Healthy")
                        size_gb = round(int(d.Size or 0) / (1024**3), 1)

                        temp_c: Optional[float] = None
                        if hasattr(d, "OperationalDetails") and d.OperationalDetails:
                            pass

                        disks.append(
                            PhysicalDiskHealth(
                                device_id=str(d.DeviceId or d.FriendlyName or "Disk"),
                                model=str(d.FriendlyName or d.Model or "Physical Drive").strip(),
                                media_type=media_type,
                                size_gb=size_gb,
                                health_status=health,
                                operational_status="OK" if health == "Healthy" else "Check",
                                temperature_celsius=temp_c,
                            )
                        )
                except Exception:
                    pass

                # Fallback to Win32_DiskDrive if Storage namespace is unavailable
                if not disks:
                    w = wmi.WMI()
                    for d in w.Win32_DiskDrive():
                        size_gb = round(int(d.Size or 0) / (1024**3), 1)
                        status = str(d.Status or "OK")
                        disks.append(
                            PhysicalDiskHealth(
                                device_id=str(d.DeviceID or d.Index or "Disk"),
                                model=str(d.Model or d.Caption or "Disk Drive").strip(),
                                media_type="NVMe/SSD" if "NVMe" in str(d.Model) or "SSD" in str(d.Model) else "HDD",
                                size_gb=size_gb,
                                health_status="Healthy" if status == "OK" else "Warning",
                                operational_status=status,
                            )
                        )
            except Exception as ex:
                logger.debug(f"Failed to query physical disk health: {ex}")

        if not disks:
            disks.append(
                PhysicalDiskHealth(
                    device_id="Disk 0",
                    model="System Drive (NVMe/SSD)",
                    media_type="SSD",
                    size_gb=512.0,
                    health_status="Healthy",
                    operational_status="OK",
                )
            )
        return disks

    def get_ram_sticks(self) -> List[RamStickInfo]:
        """Collect physical memory stick (SPD) details via WMI.

        Returns:
            List[RamStickInfo]: Installed physical RAM modules.
        """
        sticks: List[RamStickInfo] = []
        if os.name == "nt":
            try:
                import wmi  # type: ignore

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
                    sticks.append(
                        RamStickInfo(
                            bank_label=str(m.BankLabel or m.DeviceLocator or "DIMM").strip(),
                            capacity_gb=cap_gb,
                            speed_mhz=speed,
                            manufacturer=str(m.Manufacturer or "Generic").strip(),
                            part_number=str(m.PartNumber or "").strip(),
                            memory_type=m_type,
                        )
                    )
            except Exception as ex:
                logger.debug(f"Failed to query physical memory sticks: {ex}")

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

    def get_snapshot(self, process_limit: int = 20) -> SystemSnapshot:
        """Capture full point-in-time system telemetry snapshot.

        Args:
            process_limit: Number of top active processes to include.

        Returns:
            SystemSnapshot: Consolidated system and hardware snapshot.
        """
        now = time.time()
        uptime = round(now - (psutil.boot_time() if PSUTIL_AVAILABLE else now - 3600), 1)
        partitions, disk_io = self.get_disk_metrics()
        net_metrics = self.get_network_metrics()
        sensors = get_hardware_sensors()
        top_procs = self.get_top_processes(limit=process_limit)
        ident = self.get_system_identity()

        self._last_time = now

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
            uptime_seconds=uptime,
            cpu=self.get_cpu_metrics(),
            memory=self.get_memory_metrics(),
            ram_sticks=self.get_ram_sticks(),
            gpus=self.get_gpu_metrics(),
            disks=partitions,
            physical_disks=self.get_physical_disks_health(),
            disk_io=disk_io,
            network=net_metrics,
            listening_ports=self.get_listening_ports(),
            battery=self.get_battery_metrics(),
            alerts=self.get_health_alerts(),
            sensors=sensors,
            top_processes=top_procs,
        )

    def get_hardware_sensors(self) -> List[HardwareSensor]:
        """Collect real-time hardware sensors readings.

        Returns:
            List[HardwareSensor]: Hardware sensors and temperatures.
        """
        return get_hardware_sensors()

    def get_hardware_tree(self) -> List[HardwareNode]:
        """Generate AIDA64-like hierarchical component specification tree.

        Returns:
            List[HardwareNode]: Hardware devices grouped by category.
        """
        nodes: List[HardwareNode] = []
        ident = self.get_system_identity()

        # 1. Computer & Operating System Node
        nodes.append(
            HardwareNode(
                category="System",
                name=f"{ident.get('hostname')} ({platform.system()} {platform.release()})",
                properties={
                    "Computer Name": ident.get("hostname", ""),
                    "Current User": ident.get("username", ""),
                    "OS Version": platform.version(),
                    "OS Build": ident.get("os_build", ""),
                    "System Language": ident.get("system_language", ""),
                    "User Locale": ident.get("user_locale", ""),
                    "System Locale": ident.get("system_locale", ""),
                    "Timezone": ident.get("timezone", ""),
                    "Codepages": ident.get("codepage", ""),
                    "Input Languages": ", ".join(ident.get("input_languages", [])),
                    "Architecture": platform.machine(),
                    "Python Runtime": platform.python_version(),
                },
            )
        )

        # 2. Processor Node
        cpu = self.get_cpu_metrics()
        nodes.append(
            HardwareNode(
                category="Processor (CPU)",
                name=cpu.model,
                properties={
                    "Physical Cores": cpu.physical_cores,
                    "Logical Threads": cpu.logical_cores,
                    "Base Frequency": f"{cpu.frequency_mhz} MHz",
                    "Architecture": cpu.architecture,
                },
            )
        )

        # 3. Motherboard & BIOS (via Registry or WMI on Windows)
        if os.name == "nt":
            mb_name = ""
            mb_mfg = ""
            bios_ver = ""
            try:
                import winreg

                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                    mb_mfg, _ = winreg.QueryValueEx(key, "BaseBoardManufacturer")
                    mb_name, _ = winreg.QueryValueEx(key, "BaseBoardProduct")
                    bios_ver, _ = winreg.QueryValueEx(key, "BIOSVersion")
            except Exception:
                pass

            if not mb_name:
                try:
                    import wmi  # type: ignore

                    w = wmi.WMI()
                    board = w.Win32_BaseBoard()
                    bios = w.Win32_BIOS()
                    mb_name = board[0].Product if board else ""
                    mb_mfg = board[0].Manufacturer if board else ""
                    bios_ver = bios[0].SMBIOSBIOSVersion if bios else ""
                except Exception:
                    pass

            if mb_name or mb_mfg:
                nodes.append(
                    HardwareNode(
                        category="Motherboard",
                        name=f"{mb_mfg} {mb_name}".strip() or "Motherboard",
                        properties={
                            "Manufacturer": mb_mfg or "Unknown",
                            "Product": mb_name or "Unknown",
                            "BIOS Version": bios_ver or "Unknown",
                        },
                    )
                )

        # 4. Memory (RAM)
        mem = self.get_memory_metrics()
        nodes.append(
            HardwareNode(
                category="System Memory",
                name=f"{mem.total_gb} GB Physical RAM",
                properties={
                    "Total RAM": f"{mem.total_gb} GB",
                    "Available RAM": f"{mem.available_gb} GB",
                    "Swap Capacity": f"{mem.swap_total_gb} GB",
                },
            )
        )

        # 5. Display & Graphics (GPU)
        for idx, gpu in enumerate(self.get_gpu_metrics()):
            nodes.append(
                HardwareNode(
                    category="Display Adapter",
                    name=gpu.name,
                    properties={
                        "Device Index": idx,
                        "VRAM": f"{gpu.memory_total_gb} GB",
                        "CUDA Accelerated": gpu.has_cuda,
                        "DirectML Accelerated": gpu.has_directml,
                    },
                )
            )

        # 6. Storage Drives
        partitions, _ = self.get_disk_metrics()
        for part in partitions:
            nodes.append(
                HardwareNode(
                    category="Storage Drive",
                    name=f"Disk Volume {part.device} ({part.total_gb} GB)",
                    properties={
                        "Device": part.device,
                        "Mountpoint": part.mountpoint,
                        "Filesystem": part.fstype,
                        "Total Space": f"{part.total_gb} GB",
                        "Free Space": f"{part.free_gb} GB",
                    },
                )
            )

        # 7. Network Adapters
        for net in self.get_network_metrics():
            nodes.append(
                HardwareNode(
                    category="Network Adapter",
                    name=net.name,
                    properties={
                        "Status": "Up" if net.is_up else "Down",
                        "Link Speed": f"{net.speed_mbps} Mbps",
                        "IP Addresses": ", ".join(net.ip_addresses) or "N/A",
                    },
                )
            )

        return nodes
