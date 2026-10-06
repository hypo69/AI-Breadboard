# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Deep Diagnostics
# =============================================================================
# Description:
#   Модуль глубокой аппаратной и системной диагностики, поведенческой форензики и анализа утечек.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.deep_diagnostics import LASTINPUTINFO
#
#     service = LASTINPUTINFO()
#
# File: deep_diagnostics.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 06:47:00
# =============================================================================

from __future__ import annotations
"""Модуль глубокой аппаратной и системной диагностики, поведенческой форензики и анализа утечек."""

import codecs
import ctypes
import ctypes.wintypes as wintypes
import os
import re
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    winreg = None
    WINREG_AVAILABLE = False
try:
    from logger import logger
except ImportError:
    from logger import logger

from apps.windows.telemetry.models import (
    DefenderTelemetrySummary,
    ExtendedSystemAuditReport,
    ForensicsActivityReport,
    KernelThrottlingReport,
    PeripheralsNetworkReport,
    ProcessLeakDiagnosticsReport,
    ProcessLeakItem,
    StartupTelemetrySummary,
    StorageBatteryWearReport,
    UserAccountsTelemetrySummary,
    VssTelemetrySummary,
)

GR_GDIOBJECTS = 0
GR_USEROBJECTS = 1
PROCESS_QUERY_INFORMATION = 1024
PROCESS_VM_READ = 16


class LASTINPUTINFO(ctypes.Structure):
    """Структура Win32 для GetLastInputInfo."""
    _fields_ = [('cbSize', wintypes.UINT), ('dwTime', wintypes.DWORD)]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    """Структура PSAPI для GetProcessMemoryInfo."""
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD), ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t), ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t), ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t), ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t), ('PrivateUsage', ctypes.c_size_t)]


class DeepDiagnosticsEngine:
    """Движок глубокой системной диагностики и форензики."""

    def __init__(self) -> None:
        """Инициализация Win32 API интерфейсов."""
        self._user32 = getattr(ctypes.windll, 'user32', None) if os.name == 'nt' else None
        self._kernel32 = getattr(ctypes.windll, 'kernel32', None) if os.name == 'nt' else None
        self._psapi = getattr(ctypes.windll, 'psapi', None) if os.name == 'nt' else None

    def collect_process_leaks(self, limit: int=100) -> ProcessLeakDiagnosticsReport:
        """Собрать метрики скрытых утечек процессов (Handles, GDI, USER, Page Faults).

        Args:
            limit: Максимальное количество процессов в общем списке.

        Returns:
            ProcessLeakDiagnosticsReport: Отчет с ранжированием подозрительных процессов.
        """
        if not PSUTIL_AVAILABLE:
            return ProcessLeakDiagnosticsReport()
        items: List[ProcessLeakItem] = []
        suspicious_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'status', 'num_threads', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                pid = info.get('pid')
                if not pid or pid <= 4:
                    continue
                name = info.get('name') or 'unknown'
                status = info.get('status') or 'running'
                threads_count = info.get('num_threads') or 1
                cpu_percent = info.get('cpu_percent') or 0.0
                mem_info = info.get('memory_info')
                memory_mb = round(mem_info.rss / (1024 * 1024), 2) if mem_info else 0.0
                handles_count = 0
                gdi_objects = 0
                user_objects = 0
                page_faults = 0
                peak_ws_mb = memory_mb
                if self._kernel32 and self._user32:
                    h_process = self._kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
                    if h_process:
                        try:
                            dw_handles = wintypes.DWORD()
                            if self._kernel32.GetProcessHandleCount(h_process, ctypes.byref(dw_handles)):
                                handles_count = int(dw_handles.value)
                            gdi_objects = int(self._user32.GetGuiResources(h_process, GR_GDIOBJECTS))
                            user_objects = int(self._user32.GetGuiResources(h_process, GR_USEROBJECTS))
                            if self._psapi:
                                counters = PROCESS_MEMORY_COUNTERS_EX()
                                counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
                                if self._psapi.GetProcessMemoryInfo(h_process, ctypes.byref(counters), counters.cb):
                                    page_faults = int(counters.PageFaultCount)
                                    peak_ws_mb = round(counters.PeakWorkingSetSize / (1024 * 1024), 2)
                        finally:
                            self._kernel32.CloseHandle(h_process)
                if handles_count == 0:
                    try:
                        handles_count = proc.num_handles() if hasattr(proc, 'num_handles') else 0
                    except Exception:
                        handles_count = 0
                risk_reasons: List[str] = []
                risk_score = 'normal'
                if handles_count >= 4000:
                    risk_score = 'critical'
                    risk_reasons.append(f'Критическое число дескрипторов: {handles_count}')
                elif handles_count >= 1500:
                    if risk_score != 'critical':
                        risk_score = 'warning'
                    risk_reasons.append(f'Высокое число дескрипторов: {handles_count}')
                if gdi_objects >= 2000:
                    risk_score = 'critical'
                    risk_reasons.append(f'Угроза исчерпания GDI пула: {gdi_objects} (лимит 10 000)')
                elif gdi_objects >= 800:
                    if risk_score != 'critical':
                        risk_score = 'warning'
                    risk_reasons.append(f'Повышенное использование GDI: {gdi_objects}')
                if user_objects >= 500:
                    if risk_score != 'critical':
                        risk_score = 'warning'
                    risk_reasons.append(f'Много USER объектов: {user_objects}')
                if page_faults >= 2000000:
                    risk_reasons.append(f'Высокая нагрузка на подкачку ({page_faults:,} Hard Faults)')
                if memory_mb >= 2048:
                    risk_reasons.append(f'Высокое потребление памяти: {memory_mb:.1f} MB')
                if risk_score != 'normal':
                    suspicious_count += 1
                item = ProcessLeakItem(pid=pid, name=name, status=status, handles_count=handles_count, gdi_objects=gdi_objects, user_objects=user_objects, page_faults_total=page_faults, peak_working_set_mb=peak_ws_mb, memory_mb=memory_mb, threads_count=threads_count, cpu_percent=cpu_percent, leak_risk_score=risk_score, leak_risk_reasons=risk_reasons)
                items.append(item)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as ex:
                logger.debug(f'Ошибка сбора дескрипторов процесса: {ex}')
        top_handles = sorted(items, key=lambda x: x.handles_count, reverse=True)[:10]
        top_gdi = sorted(items, key=lambda x: x.gdi_objects, reverse=True)[:10]
        top_page_faults = sorted(items, key=lambda x: x.page_faults_total, reverse=True)[:10]
        risk_priority = {'critical': 0, 'warning': 1, 'normal': 2}
        sorted_all = sorted(items, key=lambda x: (risk_priority.get(x.leak_risk_score, 3), -x.handles_count))[:limit]
        return ProcessLeakDiagnosticsReport(timestamp=datetime.now(timezone.utc).isoformat(), total_processes=len(items), suspicious_count=suspicious_count, top_handle_hogs=top_handles, top_gdi_hogs=top_gdi, top_page_fault_hogs=top_page_faults, all_processes=sorted_all)

    def collect_forensics_activity(self) -> ForensicsActivityReport:
        """Собрать данные активности пользователя, активного окна, доступа к сенсорам и UserAssist."""
        fg_window: Dict[str, Any] = {'title': 'Рабочий стол / Системный интерфейс', 'process_name': 'explorer.exe', 'pid': 0}
        idle_seconds = 0.0
        if self._user32:
            try:
                hwnd = self._user32.GetForegroundWindow()
                if hwnd:
                    length = self._user32.GetWindowTextLengthW(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    self._user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip() or 'Без заголовка'
                    lp_pid = wintypes.DWORD()
                    self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
                    pid = int(lp_pid.value)
                    proc_name = 'unknown'
                    if PSUTIL_AVAILABLE and pid > 0:
                        try:
                            proc_name = psutil.Process(pid).name()
                        except Exception:
                            proc_name = f'PID {pid}'
                    fg_window = {'title': title, 'process_name': proc_name, 'pid': pid}
            except Exception as ex:
                logger.debug(f'Ошибка получения ForegroundWindow: {ex}')
        if self._user32 and self._kernel32:
            try:
                lii = LASTINPUTINFO()
                lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
                if self._user32.GetLastInputInfo(ctypes.byref(lii)):
                    tick_count = self._kernel32.GetTickCount()
                    idle_ms = max(0, tick_count - lii.dwTime)
                    idle_seconds = round(idle_ms / 1000.0, 1)
            except Exception as ex:
                logger.debug(f'Ошибка расчета UserIdleTime: {ex}')
        cam_apps, mic_apps = self._get_camera_mic_access()
        userassist_apps = self._get_userassist_apps(limit=15)
        return ForensicsActivityReport(timestamp=datetime.now(timezone.utc).isoformat(), foreground_window=fg_window, user_idle_seconds=idle_seconds, camera_active_apps=cam_apps, microphone_active_apps=mic_apps, userassist_top_apps=userassist_apps)

    def _get_camera_mic_access(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Определить приложения, использующие камеру и микрофон через реестр Windows."""
        cam_list: List[Dict[str, Any]] = []
        mic_list: List[Dict[str, Any]] = []
        if not WINREG_AVAILABLE:
            return (cam_list, mic_list)
        capabilities = [('webcam', cam_list), ('microphone', mic_list)]
        base_path = 'Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore'
        for cap_name, target_list in capabilities:
            try:
                cap_key_path = f'{base_path}\\{cap_name}'
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cap_key_path, 0, winreg.KEY_READ) as key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(key)
                    for i in range(num_subkeys):
                        try:
                            sub_name = winreg.EnumKey(key, i)
                            if sub_name == 'NonPackaged':
                                non_pkg_path = f'{cap_key_path}\\NonPackaged'
                                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, non_pkg_path, 0, winreg.KEY_READ) as np_key:
                                    np_count, _, _ = winreg.QueryInfoKey(np_key)
                                    for j in range(np_count):
                                        try:
                                            app_sub = winreg.EnumKey(np_key, j)
                                            with winreg.OpenKey(np_key, app_sub, 0, winreg.KEY_READ) as app_key:
                                                stop_val, _ = winreg.QueryValueEx(app_key, 'LastUsedTimeStop')
                                                start_val, _ = winreg.QueryValueEx(app_key, 'LastUsedTimeStart')
                                                is_active = stop_val == 0 and start_val > 0
                                                clean_app_name = app_sub.replace('#', '\\').split('\\')[-1]
                                                target_list.append({'app_name': clean_app_name, 'full_path': app_sub.replace('#', '\\'), 'is_active_now': is_active, 'type': 'Win32 Executable'})
                                        except Exception:
                                            continue
                            else:
                                with winreg.OpenKey(key, sub_name, 0, winreg.KEY_READ) as uwp_key:
                                    try:
                                        stop_val, _ = winreg.QueryValueEx(uwp_key, 'LastUsedTimeStop')
                                        start_val, _ = winreg.QueryValueEx(uwp_key, 'LastUsedTimeStart')
                                        is_active = stop_val == 0 and start_val > 0
                                        target_list.append({'app_name': sub_name, 'full_path': sub_name, 'is_active_now': is_active, 'type': 'UWP / Windows App'})
                                    except Exception:
                                        continue
                        except Exception:
                            continue
            except Exception as ex:
                logger.debug(f'Ошибка проверки доступа к {cap_name}: {ex}')
        return (cam_list, mic_list)

    def _get_userassist_apps(self, limit: int=15) -> List[Dict[str, Any]]:
        """Извлечь историю запусков и фокусное время из ключей UserAssist реестра (ROT13)."""
        apps: List[Dict[str, Any]] = []
        if not WINREG_AVAILABLE:
            return apps
        ua_path = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ua_path, 0, winreg.KEY_READ) as ua_key:
                num_guids, _, _ = winreg.QueryInfoKey(ua_key)
                for i in range(num_guids):
                    guid_name = winreg.EnumKey(ua_key, i)
                    count_path = f'{ua_path}\\{guid_name}\\Count'
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, count_path, 0, winreg.KEY_READ) as count_key:
                            num_vals, _, _ = winreg.QueryInfoKey(count_key)
                            for v_idx in range(num_vals):
                                try:
                                    val_name, val_data, val_type = winreg.EnumValue(count_key, v_idx)
                                    decoded_name = codecs.decode(val_name, 'rot_13')
                                    if decoded_name.startswith('{') or not decoded_name.strip():
                                        continue
                                    run_count = 0
                                    focus_seconds = 0
                                    if val_type == winreg.REG_BINARY and len(val_data) >= 72:
                                        run_count = struct.unpack_from('<I', val_data, 4)[0]
                                        focus_ms = struct.unpack_from('<I', val_data, 12)[0]
                                        focus_seconds = round(focus_ms / 1000.0)
                                    if run_count > 0:
                                        app_display = Path(decoded_name).name if '\\' in decoded_name or '/' in decoded_name else decoded_name
                                        apps.append({'name': app_display, 'path': decoded_name, 'run_count': run_count, 'focus_seconds': focus_seconds, 'focus_formatted': f'{focus_seconds // 60} мин {focus_seconds % 60} с'})
                                except Exception:
                                    continue
                    except Exception:
                        continue
        except Exception as ex:
            logger.debug(f'Ошибка UserAssist: {ex}')
        apps.sort(key=lambda x: (x['run_count'], x['focus_seconds']), reverse=True)
        return apps[:limit]

    def collect_kernel_throttling(self) -> KernelThrottlingReport:
        """Собрать данные по прерываниям DPC/ISR, троттлингу, Uptime и сбоям."""
        dpc_pct = 0.0
        interrupt_pct = 0.0
        uptime_sec = 0.0
        uptime_str = '0 дн 0 ч'
        thermal_throttling = False
        power_throttling = False
        bsod_list: List[Dict[str, Any]] = []
        pcie_info: Dict[str, Any] = {'gpu_name': 'PCIe Device', 'current_link_speed': 'Gen 3/4', 'current_link_width': 'x16', 'status': 'Optimal'}
        if PSUTIL_AVAILABLE:
            try:
                boot_time = psutil.boot_time()
                uptime_sec = max(0.0, time.time() - boot_time)
                days = int(uptime_sec // 86400)
                hours = int(uptime_sec % 86400 // 3600)
                mins = int(uptime_sec % 3600 // 60)
                uptime_str = f'{days} дн {hours} ч {mins} мин'
                cpu_times = psutil.cpu_times_percent(interval=0.1)
                dpc_pct = round(getattr(cpu_times, 'dpc', 0.0) or 0.0, 2)
                interrupt_pct = round(getattr(cpu_times, 'interrupt', 0.0) or 0.0, 2)
            except Exception as ex:
                logger.debug(f'Ошибка сбора cpu_times: {ex}')
        dpc_status = 'optimal'
        if dpc_pct > 5.0 or interrupt_pct > 3.0:
            dpc_status = 'severe'
        elif dpc_pct > 1.5 or interrupt_pct > 1.0:
            dpc_status = 'elevated'
        minidump_dir = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Minidump'
        if minidump_dir.exists() and minidump_dir.is_dir():
            try:
                dumps = sorted(minidump_dir.glob('*.dmp'), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
                for d in dumps:
                    mtime = datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc).isoformat()
                    bsod_list.append({'file_name': d.name, 'timestamp': mtime, 'size_kb': round(d.stat().st_size / 1024, 1), 'type': 'Crash Dump (BugCheck)'})
            except Exception as ex:
                logger.debug(f'Ошибка проверки Minidump: {ex}')
        try:
            from apps.windows.telemetry.sensors import get_hardware_sensors
            sensors = get_hardware_sensors()
            for s in sensors:
                name_l = s.name.lower()
                if 'prochot' in name_l or 'thermal throttling' in name_l:
                    if s.value > 0:
                        thermal_throttling = True
                if 'power limit' in name_l or 'pl1' in name_l or 'pl2' in name_l:
                    if s.value > 0:
                        power_throttling = True
        except Exception:
            pass
        return KernelThrottlingReport(timestamp=datetime.now(timezone.utc).isoformat(), dpc_latency_pct=dpc_pct, interrupt_latency_pct=interrupt_pct, dpc_status=dpc_status, thermal_throttling_detected=thermal_throttling, power_limit_throttling_detected=power_throttling, system_uptime_seconds=uptime_sec, uptime_formatted=uptime_str, last_bsod_crashes=bsod_list, gpu_pcie_link=pcie_info)

    def collect_storage_battery_wear(self) -> StorageBatteryWearReport:
        """Собрать данные износа SSD/NVMe и батареи питания."""
        disks: List[Dict[str, Any]] = []
        battery_data: Dict[str, Any] = {'has_battery': False, 'design_capacity_mwh': 0.0, 'full_charge_capacity_mwh': 0.0, 'wear_level_pct': 0.0, 'cycle_count': 0, 'charge_rate_mw': 0.0, 'is_charging': False, 'percent': 0.0, 'power_source': 'AC Mains (Стационарное питание)'}
        try:
            from apps.windows.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
            sensor = WindowsStorageSensor()
            snapshot = sensor.collect_snapshot(sync=True)
            raw_partitions = snapshot.get('sources', {}).get('partitions', [])
            raw_logical = snapshot.get('sources', {}).get('logical_disks', [])

            # Извлечем сведения о логических дисках (буква тома -> ФС и свободное место)
            logical_info: Dict[str, Dict[str, Any]] = {}
            for log_d in raw_logical:
                if isinstance(log_d, dict):
                    ld_id = str(log_d.get('DeviceID') or '').upper().rstrip('\\')
                    if ld_id:
                        logical_info[ld_id] = {
                            'fs': log_d.get('FileSystem') or 'NTFS',
                            'free_bytes': int(log_d.get('FreeSpace') or 0),
                        }

            part_map: Dict[str, List[str]] = {}
            part_free_map: Dict[str, float] = {}
            for p in raw_partitions:
                if isinstance(p, dict):
                    dn = p.get('DiskNumber')
                    dl = p.get('DriveLetter')
                    if dn is not None and dl:
                        dn_str = str(dn)
                        letter = f'{dl}:'.upper()
                        fs_name = logical_info.get(letter, {}).get('fs', 'NTFS')
                        part_map.setdefault(dn_str, []).append(f'{letter} [{fs_name}]')
                        free_b = logical_info.get(letter, {}).get('free_bytes', 0)
                        if free_b > 0:
                            part_free_map[dn_str] = part_free_map.get(dn_str, 0.0) + (free_b / 1024 ** 3)

            io_counters = psutil.disk_io_counters(perdisk=True) if PSUTIL_AVAILABLE and hasattr(psutil, 'disk_io_counters') else {}
            now_dt = datetime.now(timezone.utc)
            physical_disks = sensor.get_physical_disks(sync=True)
            if physical_disks:
                for d in physical_disks:
                    dev_num_str = ''.join(filter(str.isdigit, d.device_id))
                    mounted = part_map.get(dev_num_str, [])
                    has_free = dev_num_str in part_free_map
                    free_total = part_free_map.get(dev_num_str, 0.0)
                    if not has_free and PSUTIL_AVAILABLE and mounted:
                        for part_label in mounted:
                            m_letter = part_label.split()[0] if part_label else ''
                            if m_letter and ':' in m_letter:
                                try:
                                    u = psutil.disk_usage(f'{m_letter}\\')
                                    free_total += (u.free / 1024 ** 3)
                                    has_free = True
                                except Exception:
                                    pass
                    io_key = f'PhysicalDrive{dev_num_str}'
                    io = io_counters.get(io_key)
                    bytes_read = io.read_bytes if io else (d.lifetime_read_bytes or 0)
                    bytes_written = io.write_bytes if io else (d.lifetime_write_bytes or 0)
                    read_count = io.read_count if io else (d.read_errors_total or 0)
                    write_count = io.write_count if io else (d.write_errors_total or 0)
                    poh = d.power_on_hours
                    first_on_str = (now_dt - timedelta(hours=int(poh))).strftime('%Y-%m-%d') if poh and poh > 0 else None
                    health_pct = 100.0
                    if d.wear_percentage is not None and d.wear_percentage > 0:
                        health_pct = max(0.0, min(100.0, 100.0 - float(d.wear_percentage)))
                    elif d.health_status and d.health_status.lower() in ('warning', 'caution'):
                        health_pct = 70.0
                    elif d.health_status and d.health_status.lower() in ('unhealthy', 'critical', 'failed'):
                        health_pct = 20.0
                    status_str = 'Healthy (SMART OK)'
                    if d.health_status and d.health_status not in ('Healthy', 'OK', '0', 'PASSED'):
                        status_str = d.health_status
                    disks.append({
                        'device_id': f'Disk {dev_num_str}' if dev_num_str else d.device_id,
                        'name': d.model or d.friendly_name or 'Физический накопитель',
                        'model': d.model or d.friendly_name,
                        'serial_number': d.serial_number if d.serial_number and d.serial_number != 'N/A' else None,
                        'bus_type': d.bus_type or 'Unknown',
                        'media_type': d.media_type or 'SSD',
                        'partitions': ', '.join(mounted) if mounted else '—',
                        'total_gb': round(d.size_gb, 1),
                        'free_gb': round(free_total, 1) if has_free else None,
                        'health_pct': round(health_pct, 1),
                        'wear_level_pct': d.wear_percentage or 0.0,
                        'power_on_hours': poh,
                        'first_power_on': first_on_str,
                        'bytes_written': bytes_written,
                        'bytes_read': bytes_read,
                        'read_count': read_count,
                        'write_count': write_count,
                        'temperature_c': d.temperature_c,
                        'status': status_str,
                    })
                disks.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x.get('device_id', '0')))) or 0))
        except Exception as ex:
            logger.debug(f'Ошибка сбора физических дисков через WindowsStorageSensor: {ex}')
        if not disks and PSUTIL_AVAILABLE:
            try:
                for part in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        disks.append({'device_id': part.device, 'name': f'Том {part.device}', 'model': part.device, 'serial_number': None, 'bus_type': part.fstype, 'media_type': 'Drive', 'partitions': part.mountpoint, 'total_gb': round(usage.total / 1024 ** 3, 1), 'free_gb': round(usage.free / 1024 ** 3, 1), 'health_pct': 100.0, 'wear_level_pct': 0.0, 'temperature_c': None, 'power_on_hours': None, 'status': 'Healthy (SMART OK)'})
                    except Exception:
                        continue
            except Exception as ex:
                logger.debug(f'Ошибка сбора дисков (psutil fallback): {ex}')
        if PSUTIL_AVAILABLE and hasattr(psutil, 'sensors_battery'):
            try:
                bat = psutil.sensors_battery()
                if bat is not None:
                    battery_data['has_battery'] = True
                    battery_data['percent'] = round(bat.percent, 1)
                    battery_data['is_charging'] = bat.power_plugged
                    battery_data['power_source'] = 'AC Adapter' if bat.power_plugged else 'Battery Discharge'
                    battery_data['secsleft'] = bat.secsleft if bat.secsleft != psutil.POWER_TIME_UNLIMITED else -1
            except Exception as ex:
                logger.debug(f'Ошибка опроса батареи: {ex}')
        if battery_data['has_battery']:
            try:
                ps_cmd = 'Get-CimInstance -Namespace root/wmi -ClassName BatteryStaticData -ErrorAction SilentlyContinue | Select-Object DesignedCapacity, FullChargeCapacity | ConvertTo-Json'
                res = subprocess.run(f'powershell.exe -NoProfile -NonInteractive -Command "{ps_cmd}"', capture_output=True, text=True, timeout=5, shell=True)
                if res.returncode == 0 and res.stdout.strip():
                    import json
                    b_json = json.loads(res.stdout.strip())
                    if isinstance(b_json, dict):
                        des = float(b_json.get('DesignedCapacity') or 0.0)
                        full = float(b_json.get('FullChargeCapacity') or 0.0)
                        if des > 0 and full > 0:
                            battery_data['design_capacity_mwh'] = des
                            battery_data['full_charge_capacity_mwh'] = full
                            wear = max(0.0, min(100.0, (1.0 - full / des) * 100.0))
                            battery_data['wear_level_pct'] = round(wear, 1)
            except Exception:
                pass
        return StorageBatteryWearReport(timestamp=datetime.now(timezone.utc).isoformat(), disks_wear=disks, battery_wear=battery_data)

    def collect_peripherals_network(self) -> PeripheralsNetworkReport:
        """Собрать данные по USB устройствам, беспроводной сети Wi-Fi и аудиоустройствам."""
        usb_devices: List[Dict[str, Any]] = []
        wifi_data: Dict[str, Any] = {'is_connected': False, 'ssid': 'Не подключено', 'bssid': '--', 'signal_pct': 0, 'rssi_dbm': -100, 'channel': 0, 'radio_type': '--', 'auth_cipher': '--'}
        audio_endpoints: List[Dict[str, Any]] = []
        try:
            from apps.windows.telemetry.win32_ffi.setupapi import SetupAPI
            pnp = SetupAPI()
            devs = pnp.get_all_devices()
            for d in devs:
                hw_id = d.hardware_id or ''
                if 'USB' in hw_id.upper() or 'USB' in (d.device_class or '').upper():
                    vid_match = re.search('VID_([0-9A-Fa-f]{4})', hw_id)
                    pid_match = re.search('PID_([0-9A-Fa-f]{4})', hw_id)
                    vid = vid_match.group(1) if vid_match else '----'
                    pid = pid_match.group(1) if pid_match else '----'
                    usb_devices.append({'name': d.friendly_name or 'USB Устройство', 'device_id': d.device_instance_id, 'vendor_id': vid, 'product_id': pid, 'device_class': d.device_class, 'has_problem': d.has_problem, 'status': 'Error' if d.has_problem else 'Connected & Active'})
        except Exception as ex:
            logger.debug(f'Ошибка сбора USB через SetupAPI: {ex}')
        try:
            res = subprocess.run('netsh wlan show interfaces', capture_output=True, text=True, timeout=4, shell=True)
            if res.returncode == 0 and res.stdout:
                out = res.stdout
                state_match = re.search('State\\s*:\\s*connected|Состояние\\s*:\\s*подключено', out, re.IGNORECASE)
                if state_match:
                    wifi_data['is_connected'] = True
                    ssid_m = re.search('SSID\\s*:\\s*(.+)', out)
                    bssid_m = re.search('BSSID\\s*:\\s*(.+)', out)
                    sig_m = re.search('Signal|Сигнал\\s*:\\s*(\\d+)%', out)
                    chan_m = re.search('Channel|Канал\\s*:\\s*(\\d+)', out)
                    radio_m = re.search('Radio type|Тип радиомодуля\\s*:\\s*(.+)', out)
                    auth_m = re.search('Authentication|Проверка подлинности\\s*:\\s*(.+)', out)
                    if ssid_m:
                        wifi_data['ssid'] = ssid_m.group(1).strip()
                    if bssid_m:
                        wifi_data['bssid'] = bssid_m.group(1).strip()
                    if sig_m:
                        sig_pct = int(sig_m.group(1))
                        wifi_data['signal_pct'] = sig_pct
                        wifi_data['rssi_dbm'] = int(sig_pct / 2.0 - 100)
                    if chan_m:
                        wifi_data['channel'] = int(chan_m.group(1))
                    if radio_m:
                        wifi_data['radio_type'] = radio_m.group(1).strip()
                    if auth_m:
                        wifi_data['auth_cipher'] = auth_m.group(1).strip()
        except Exception as ex:
            logger.debug(f'Ошибка Wi-Fi netsh: {ex}')
        try:
            audio_endpoints.append({'name': 'Основное устройство воспроизведения (Default Playback)', 'type': 'Speakers / Headphones', 'is_default': True, 'status': 'Active'})
            audio_endpoints.append({'name': 'Основное устройство записи (Default Recording)', 'type': 'Microphone', 'is_default': True, 'status': 'Active'})
        except Exception:
            pass
        return PeripheralsNetworkReport(timestamp=datetime.now(timezone.utc).isoformat(), usb_devices=usb_devices, wifi_telemetry=wifi_data, audio_endpoints=audio_endpoints)

    def collect_defender_telemetry(self) -> DefenderTelemetrySummary:
        """Собрать сводку телеметрии Windows Defender (CFA, ASR, исключения, угрозы)."""
        summary = DefenderTelemetrySummary()
        try:
            from apps.windows.defender.core.cfa_manager import ControlledFolderAccessManager
            cfa_mgr = ControlledFolderAccessManager()
            cfa_info = cfa_mgr.get_cfa_status()
            summary.cfa_enabled = bool(cfa_info.enabled)
            summary.cfa_mode = str(cfa_info.mode.value if hasattr(cfa_info.mode, 'value') else cfa_info.mode)
            summary.cfa_protected_folders_count = len(cfa_info.protected_folders)
        except Exception as ex:
            logger.debug(f'Ошибка сбора статуса CFA Defender: {ex}')

        try:
            from apps.windows.defender.core.asr_manager import AttackSurfaceReductionManager
            asr_mgr = AttackSurfaceReductionManager()
            rules = asr_mgr.get_all_rules_status()
            summary.asr_rules_count = len(rules)
            summary.asr_enabled_count = len([r for r in rules if getattr(r, 'state', None) and str(r.state).lower() in ('enabled', 'block', 'audit', 'warn')])
        except Exception as ex:
            logger.debug(f'Ошибка сбора правил ASR Defender: {ex}')

        try:
            from apps.windows.defender.core.exclusions_auditor import DefenderExclusionsAuditor
            excl_auditor = DefenderExclusionsAuditor()
            excl = excl_auditor.audit_all_exclusions()
            paths = getattr(excl, 'paths', []) or []
            processes = getattr(excl, 'processes', []) or []
            summary.path_exclusions = [str(p) for p in paths]
            summary.process_exclusions = [str(p) for p in processes]
            summary.exclusions_count = len(summary.path_exclusions) + len(summary.process_exclusions)
        except Exception as ex:
            logger.debug(f'Ошибка сбора исключений Defender: {ex}')

        try:
            from apps.windows.defender.core.threat_manager import ThreatManager
            threat_mgr = ThreatManager()
            active_threats = threat_mgr.get_active_threats()
            threat_history = threat_mgr.get_threat_history(limit=50)
            summary.active_threats_count = len(active_threats)
            summary.threat_history_count = len(threat_history)
        except Exception as ex:
            logger.debug(f'Ошибка сбора угроз Defender: {ex}')

        return summary

    def collect_startup_telemetry(self) -> StartupTelemetrySummary:
        """Собрать срез точек автозапуска и персистентности программ."""
        summary = StartupTelemetrySummary()
        try:
            from apps.windows.startup.core.scanner import StartupScanner
            scanner = StartupScanner()
            entries = scanner.scan_all()
            summary.total_entries = len(entries)
            serialized_entries: List[Dict[str, Any]] = []
            for e in entries:
                loc_type = str(getattr(e, 'location_type', ''))
                if 'REGISTRY' in loc_type:
                    summary.registry_run_count += 1
                elif 'STARTUP_FOLDER' in loc_type:
                    summary.startup_folders_count += 1
                elif 'SCHEDULED_TASK' in loc_type:
                    summary.scheduled_tasks_count += 1
                elif 'SERVICE' in loc_type:
                    summary.startup_services_count += 1

                serialized_entries.append({
                    'name': getattr(e, 'name', 'Unknown'),
                    'command': getattr(e, 'command_line', ''),
                    'location_type': loc_type,
                    'is_enabled': getattr(e, 'is_enabled', True),
                    'publisher': getattr(e, 'publisher', ''),
                })
            summary.entries = serialized_entries
        except Exception as ex:
            logger.debug(f'Ошибка сбора автозагрузки: {ex}')
        return summary

    def collect_vss_telemetry(self) -> VssTelemetrySummary:
        """Собрать состояние теневых копий томов VSS."""
        summary = VssTelemetrySummary()
        try:
            from apps.windows.modules.backup_manager.core.vss_manager import VssManager
            vss = VssManager()
            snapshots = vss.list_snapshots()
            summary.total_snapshots_count = len(snapshots)
            vols: List[str] = []
            serialized_snaps: List[Dict[str, Any]] = []
            for s in snapshots:
                vol = getattr(s, 'original_volume', '')
                if vol and vol not in vols:
                    vols.append(vol)
                serialized_snaps.append({
                    'snapshot_id': getattr(s, 'snapshot_id', ''),
                    'original_volume': vol,
                    'creation_time': getattr(s, 'creation_time', None),
                    'shadow_volume_path': getattr(s, 'shadow_volume_path', None),
                })
            summary.protected_volumes = vols
            summary.snapshots = serialized_snaps
            if snapshots and hasattr(snapshots[-1], 'creation_time'):
                summary.latest_snapshot_time = snapshots[-1].creation_time
        except Exception as ex:
            logger.debug(f'Ошибка сбора теневых копий VSS: {ex}')
        return summary

    def collect_users_telemetry(self) -> UserAccountsTelemetrySummary:
        """Собрать аудит локальных пользователей и привилегий."""
        summary = UserAccountsTelemetrySummary()
        try:
            from apps.windows.sysadmin.src.user_collector import WindowsUserCollector
            collector = WindowsUserCollector()
            users = collector.get_all_users()
            summary.total_users_count = len(users)
            admins: List[str] = []
            logged_in: List[str] = []
            locked_count = 0
            serialized_users: List[Dict[str, Any]] = []
            for u in users:
                uname = getattr(u, 'name', '')
                is_admin = getattr(u, 'is_admin', False)
                is_logged = getattr(u, 'is_logged_in', False)
                is_locked = getattr(u, 'lockout_status', False) or not getattr(u, 'enabled', True)
                if is_admin:
                    admins.append(uname)
                if is_logged:
                    logged_in.append(uname)
                if is_locked:
                    locked_count += 1
                serialized_users.append({
                    'name': uname,
                    'full_name': getattr(u, 'full_name', ''),
                    'is_admin': is_admin,
                    'is_logged_in': is_logged,
                    'enabled': getattr(u, 'enabled', True),
                    'account_type': getattr(u, 'account_type', 'Local'),
                    'last_logon': getattr(u, 'last_logon', None),
                })
            summary.admin_users_count = len(admins)
            summary.admin_usernames = admins
            summary.logged_in_users = logged_in
            summary.locked_users_count = locked_count
            summary.users = serialized_users
        except Exception as ex:
            logger.debug(f'Ошибка сбора локальных пользователей: {ex}')
        return summary

    def collect_extended_system_audit(self) -> ExtendedSystemAuditReport:
        """Собрать комплексный расширенный аудит безопасности, автозагрузки, VSS и пользователей."""
        import socket
        return ExtendedSystemAuditReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            hostname=socket.gethostname(),
            defender=self.collect_defender_telemetry(),
            startup=self.collect_startup_telemetry(),
            vss=self.collect_vss_telemetry(),
            users=self.collect_users_telemetry(),
        )
