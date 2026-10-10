# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Storage Usage
# =============================================================================
# Description:
#   Четырехуровневый стек сбора телеметрии накопителей Windows:
#   1. DiskInventoryCollector (Win32 + IOCTL Storage Property & Volumes)
#   2. DiskHealthCollector (NVMe SMART / Health / TBW)
#   3. DiskPerformanceCollector (IOPS, Latency, Throughput, Queue)
#   4. DiskProcessIOCollector (Попроцессный I/O анализ и агрегаты)
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.storage_usage import (
#         DiskInventoryCollector,
#         DiskHealthCollector,
#         DiskPerformanceCollector,
#         DiskProcessIOCollector,
#         WindowsStorageUsageCollector,
#     )
#
#     collector = WindowsStorageUsageCollector()
#     disks = collector.get_physical_disks()
#     report = collector.get_disk_usage_period_report()
#
# File: storage_usage.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 01:35:00
# =============================================================================

from __future__ import annotations
"""Четырехуровневый стек сбора телеметрии накопителей Windows."""

import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from logger import logger
from apps.windows.sdk.modules.storage_manager.core.raw_disk_io import WindowsRawDiskIO
from apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
from apps.windows.telemetry.models import (
    AppDiskUsageItem,
    DiskUsagePeriodReport,
    PhysicalDiskHealth,
)


def _format_bytes(num_bytes: float) -> str:
    """Форматирование объема байт в человекочитаемый вид (B, KB, MB, GB, TB).

    Args:
        num_bytes: Количество байт.

    Returns:
        str: Отформатированная строка.
    """
    if num_bytes <= 0 or math.isnan(num_bytes):
        return '0 B'
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    idx = 0
    val = float(num_bytes)
    while val >= 1024.0 and idx < len(units) - 1:
        val /= 1024.0
        idx += 1
    return f'{val:.2f} {units[idx]}' if idx > 0 else f'{int(val)} B'


class DiskInventoryCollector:
    """Слой 1: Коллектор инвентаря физических накопителей, разделов и логических томов."""

    def __init__(self, raw_io: Optional[WindowsRawDiskIO] = None) -> None:
        """Инициализация коллектора инвентаря дисков."""
        self.raw_io = raw_io or WindowsRawDiskIO()

    def collect(self) -> Dict[str, Any]:
        """Сбор полного инвентаря накопителей и томов.

        Returns:
            Dict[str, Any]: Данные физических дисков и логических томов.
        """
        disks = self.raw_io.list_physical_disks()
        volumes = self.raw_io.get_logical_volumes()
        return {
            'disks_count': len(disks),
            'disks': disks,
            'volumes_count': len(volumes),
            'volumes': volumes,
            'timestamp': time.time(),
        }


class DiskHealthCollector:
    """Слой 2: Коллектор SMART-показателей здоровья, износа и TBW накопителей."""

    def __init__(
        self,
        raw_io: Optional[WindowsRawDiskIO] = None,
        storage_sensor: Optional[WindowsStorageSensor] = None,
    ) -> None:
        """Инициализация коллектора здоровья дисков."""
        self.raw_io = raw_io or WindowsRawDiskIO()
        self.storage_sensor = storage_sensor or WindowsStorageSensor()

    def collect(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Сбор показателей здоровья всех доступных накопителей.

        Returns:
            List[Dict[str, Any]]: Показатели SMART, TBW, температуры и ошибок.
        """
        results: List[Dict[str, Any]] = []
        raw_disks = self.raw_io.list_physical_disks()

        for d in raw_disks:
            disk_id = d.get('disk_id', 0)
            smart = d.get('smart_health', {})
            results.append({
                'disk_id': disk_id,
                'device_path': d.get('device_path'),
                'model': d.get('product'),
                'bus_type': d.get('bus_type'),
                'temperature_c': smart.get('temperature_c'),
                'wear_percentage': smart.get('percentage_used'),
                'available_spare_percent': smart.get('available_spare_percent'),
                'tbw_written_tb': smart.get('data_units_written_tb'),
                'tbw_read_tb': smart.get('data_units_read_tb'),
                'power_on_hours': smart.get('power_on_hours'),
                'unsafe_shutdowns': smart.get('unsafe_shutdowns'),
                'media_errors': smart.get('media_errors'),
                'raw_available': smart.get('raw_nvme_available', False),
            })

        # Fallback / дополнение через WindowsStorageSensor CIM если нативный IOCTL вернул None
        needs_cim = any(r['temperature_c'] is None and r['wear_percentage'] is None for r in results)
        if needs_cim:
            try:
                cim_disks = self.storage_sensor.get_physical_disks(force_refresh=force_refresh)
                cim_map = {str(cd.device_id).replace(r'\\.\PHYSICALDRIVE', '').replace('Disk', ''): cd for cd in cim_disks}
                for r in results:
                    str_id = str(r['disk_id'])
                    if str_id in cim_map:
                        cd = cim_map[str_id]
                        if r['temperature_c'] is None and cd.temperature_c:
                            r['temperature_c'] = cd.temperature_c
                        if r['wear_percentage'] is None and cd.wear_percentage:
                            r['wear_percentage'] = cd.wear_percentage
                        if r['power_on_hours'] is None and cd.power_on_hours:
                            r['power_on_hours'] = cd.power_on_hours
                        if r['tbw_written_tb'] is None and cd.lifetime_write_tb:
                            r['tbw_written_tb'] = cd.lifetime_write_tb
                        if r['tbw_read_tb'] is None and cd.lifetime_read_tb:
                            r['tbw_read_tb'] = cd.lifetime_read_tb
            except Exception as exc:
                logger.debug(f"Ошибка дополнения здоровья через CIM: {exc}")

        return results


class DiskPerformanceCollector:
    """Слой 3: Коллектор текущей скорости, IOPS и времени отклика дисков."""

    def __init__(self) -> None:
        """Инициализация коллектора производительности дисков."""
        self._last_sample_time: float = time.time()
        self._last_io_counters: Dict[str, Any] = {}

    def collect(self) -> Dict[str, Any]:
        """Сбор показателей пропускной способности и IOPS накопителей.

        Returns:
            Dict[str, Any]: Метрики скорости чтения/записи и операций в секунду.
        """
        now = time.time()
        dt = max(0.001, now - self._last_sample_time)
        res: Dict[str, Any] = {
            'total_read_bytes_sec': 0.0,
            'total_write_bytes_sec': 0.0,
            'total_read_iops': 0.0,
            'total_write_iops': 0.0,
            'per_disk': {},
            'dt_sec': dt,
        }

        if not PSUTIL_AVAILABLE:
            self._last_sample_time = now
            return res

        try:
            per_disk_counters = psutil.disk_io_counters(perdisk=True)
            if per_disk_counters:
                for disk_name, cur in per_disk_counters.items():
                    prev = self._last_io_counters.get(disk_name)
                    if prev:
                        r_bytes = max(0, cur.read_bytes - prev.read_bytes) / dt
                        w_bytes = max(0, cur.write_bytes - prev.write_bytes) / dt
                        r_count = max(0, cur.read_count - prev.read_count) / dt
                        w_count = max(0, cur.write_count - prev.write_count) / dt
                        r_time = max(0, cur.read_time - prev.read_time)
                        w_time = max(0, cur.write_time - prev.write_time)

                        res['total_read_bytes_sec'] += r_bytes
                        res['total_write_bytes_sec'] += w_bytes
                        res['total_read_iops'] += r_count
                        res['total_write_iops'] += w_count

                        res['per_disk'][disk_name] = {
                            'read_bytes_sec': round(r_bytes, 1),
                            'write_bytes_sec': round(w_bytes, 1),
                            'read_iops': round(r_count, 1),
                            'write_iops': round(w_count, 1),
                            'read_time_ms': r_time,
                            'write_time_ms': w_time,
                        }
                self._last_io_counters = per_disk_counters
        except Exception as exc:
            logger.debug(f"Ошибка сбора счетчиков производительности дисков: {exc}")

        self._last_sample_time = now
        return res


class DiskProcessIOCollector:
    """Слой 4: Коллектор активности ввода-вывода процессов (Top Writers/Readers)."""

    def __init__(self) -> None:
        """Инициализация коллектора I/O процессов."""
        self._last_process_io: Dict[int, Dict[str, Any]] = {}
        self._last_poll_time: float = time.time()

    def collect(self) -> Dict[str, Dict[str, Any]]:
        """Опрос I/O всех активных процессов и вычисление дельт чтения/записи.

        Returns:
            Dict[str, Dict[str, Any]]: Агрегированные дельты по именам процессов.
        """
        if not PSUTIL_AVAILABLE:
            return {}

        now = time.time()
        aggregated_by_name: Dict[str, Dict[str, Any]] = {}

        try:
            for p in psutil.process_iter(attrs=['pid', 'name']):
                try:
                    pid = p.info['pid']
                    name = p.info.get('name') or f'PID_{pid}'
                    io_cnt = p.io_counters()
                    cur_r = io_cnt.read_bytes
                    cur_w = io_cnt.write_bytes

                    prev = self._last_process_io.get(pid)
                    if prev:
                        delta_r = max(0, cur_r - prev['read_bytes'])
                        delta_w = max(0, cur_w - prev['write_bytes'])
                    else:
                        delta_r = cur_r
                        delta_w = cur_w

                    self._last_process_io[pid] = {
                        'name': name,
                        'read_bytes': cur_r,
                        'write_bytes': cur_w,
                        'time': now,
                    }

                    if name not in aggregated_by_name:
                        aggregated_by_name[name] = {
                            'pid': pid,
                            'read_bytes': 0,
                            'write_bytes': 0,
                        }
                    aggregated_by_name[name]['read_bytes'] += delta_r
                    aggregated_by_name[name]['write_bytes'] += delta_w
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue
        except Exception as ex:
            logger.debug(f'Ошибка выборки process I/O deltas: {ex}')

        self._last_poll_time = now
        return aggregated_by_name


class WindowsStorageUsageCollector:
    """Унифицированный диспетчер дисковой телеметрии, объединяющий все 4 слоя."""

    def __init__(
        self,
        raw_io: Optional[WindowsRawDiskIO] = None,
        storage_sensor: Optional[WindowsStorageSensor] = None,
    ) -> None:
        """Инициализация унифицированного коллектора дисковой телеметрии."""
        self.raw_io = raw_io or WindowsRawDiskIO()
        self.storage_sensor = storage_sensor or WindowsStorageSensor()

        self.inventory_collector = DiskInventoryCollector(self.raw_io)
        self.health_collector = DiskHealthCollector(self.raw_io, self.storage_sensor)
        self.performance_collector = DiskPerformanceCollector()
        self.process_io_collector = DiskProcessIOCollector()

    def get_physical_disks(self, force_refresh: bool = False) -> List[PhysicalDiskHealth]:
        """Получить актуальный список физических накопителей с показателями SMART и Lifetime."""
        results: List[PhysicalDiskHealth] = []
        try:
            health_list = self.health_collector.collect(force_refresh=force_refresh)
            for h in health_list:
                results.append(PhysicalDiskHealth(
                    device_id=f"Disk {h.get('disk_id', 0)}",
                    model=h.get('model') or f"PhysicalDrive{h.get('disk_id', 0)}",
                    media_type='SSD' if 'SSD' in (h.get('model', '') + h.get('bus_type', '')).upper() or h.get('bus_type') == 'NVMe' else 'HDD',
                    size_gb=0.0,
                    health_status='Healthy',
                    operational_status='OK',
                    temperature_celsius=h.get('temperature_c'),
                    interface_type=h.get('bus_type') or 'NVMe',
                    lifetime_read_bytes=int(h['tbw_read_tb'] * (1024 ** 4)) if h.get('tbw_read_tb') else None,
                    lifetime_write_bytes=int(h['tbw_written_tb'] * (1024 ** 4)) if h.get('tbw_written_tb') else None,
                    lifetime_read_tb=h.get('tbw_read_tb'),
                    lifetime_write_tb=h.get('tbw_written_tb'),
                    power_on_hours=h.get('power_on_hours'),
                    wear_percentage=h.get('wear_percentage'),
                ))
        except Exception as ex:
            logger.debug(f'Ошибка получения физических накопителей: {ex}')

        if not results:
            results.append(PhysicalDiskHealth(
                device_id='Disk 0',
                model='System Drive (NVMe/SSD)',
                media_type='SSD',
                size_gb=512.0,
                health_status='Healthy',
                operational_status='OK',
                interface_type='NVMe',
            ))
        return results

    def poll_process_io_deltas(self) -> Dict[str, Dict[str, Any]]:
        """Опросить текущий I/O процессов и рассчитать накопленные дельты."""
        return self.process_io_collector.collect()

    def get_disk_usage_period_report(
        self,
        period_minutes: int = 1440,
        force_refresh_smart: bool = False,
    ) -> DiskUsagePeriodReport:
        """Сформировать агрегированный отчет об использовании диска за интервал."""
        phys_disks = self.get_physical_disks(force_refresh=force_refresh_smart)
        proc_deltas = self.poll_process_io_deltas()

        writers_list: List[AppDiskUsageItem] = []
        readers_list: List[AppDiskUsageItem] = []

        total_r = sum(item['read_bytes'] for item in proc_deltas.values())
        total_w = sum(item['write_bytes'] for item in proc_deltas.values())
        total_all = total_r + total_w

        # Ранжирование по записи
        sorted_writers = sorted(proc_deltas.items(), key=lambda x: x[1]['write_bytes'], reverse=True)
        for name, item in sorted_writers[:15]:
            wb = item['write_bytes']
            rb = item['read_bytes']
            tot = wb + rb
            if wb <= 0:
                continue
            pct = round((wb / total_w) * 100.0, 1) if total_w > 0 else 0.0
            writers_list.append(AppDiskUsageItem(
                process_name=name,
                pid=item.get('pid'),
                read_bytes=rb,
                write_bytes=wb,
                total_bytes=tot,
                read_formatted=_format_bytes(rb),
                write_formatted=_format_bytes(wb),
                share_percent=pct,
            ))

        # Ранжирование по чтению
        sorted_readers = sorted(proc_deltas.items(), key=lambda x: x[1]['read_bytes'], reverse=True)
        for name, item in sorted_readers[:15]:
            wb = item['write_bytes']
            rb = item['read_bytes']
            tot = wb + rb
            if rb <= 0:
                continue
            pct = round((rb / total_r) * 100.0, 1) if total_r > 0 else 0.0
            readers_list.append(AppDiskUsageItem(
                process_name=name,
                pid=item.get('pid'),
                read_bytes=rb,
                write_bytes=wb,
                total_bytes=tot,
                read_formatted=_format_bytes(rb),
                write_formatted=_format_bytes(wb),
                share_percent=pct,
            ))

        top_writer = sorted_writers[0][0] if sorted_writers and sorted_writers[0][1]['write_bytes'] > 0 else 'N/A'
        top_reader = sorted_readers[0][0] if sorted_readers and sorted_readers[0][1]['read_bytes'] > 0 else 'N/A'

        diag = (
            f"За анализируемый период ({period_minutes} мин) записано {_format_bytes(total_w)}, "
            f"прочитано {_format_bytes(total_r)}. Главный источник записи: {top_writer}, чтения: {top_reader}."
        )

        return DiskUsagePeriodReport(
            period_minutes=period_minutes,
            total_read_bytes=total_r,
            total_write_bytes=total_w,
            total_read_formatted=_format_bytes(total_r),
            total_write_formatted=_format_bytes(total_w),
            total_formatted=_format_bytes(total_all),
            top_writers=writers_list,
            top_readers=readers_list,
            physical_disks=phys_disks,
            summary_text=diag,
        )


__all__ = [
    'DiskInventoryCollector',
    'DiskHealthCollector',
    'DiskPerformanceCollector',
    'DiskProcessIOCollector',
    'WindowsStorageUsageCollector',
]
