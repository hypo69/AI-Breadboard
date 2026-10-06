# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage Manager Core - Windows Storage Sensor
# =============================================================================
# Description:
#   Сенсор диагностики накопителей Windows без сторонних утилит.
#   Прямой опрос Win32, MSFT Storage CIM и SMART через PowerShell.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.modules.storage_manager.core.windows_storage_sensor
#   Python API:
#     from apps.windows.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
#
#     sensor = WindowsStorageSensor()
#     disks = sensor.get_physical_disks()
#
# File: windows_storage_sensor.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 03:08:00
# =============================================================================

from __future__ import annotations
"""Сенсор диагностики накопителей Windows без сторонних утилит."""

import argparse
import json
import os
import platform
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from logger import logger

POWERSHELL_STORAGE_SCRIPT = """
$ErrorActionPreference = 'SilentlyContinue'
$sw = [System.Diagnostics.Stopwatch]::StartNew()

function Trace-Step {
    param([string]$StepName)
    $elapsed = $sw.Elapsed.TotalSeconds
    [System.Console]::Error.WriteLine(("[STORAGE-DIAG] [{0:N2}s] {1}" -f $elapsed, $StepName))
}

function Get-SafeCimInstances {
    param([string]$ClassName, [string]$Namespace = 'root/cimv2')
    try {
        @(Get-CimInstance -Namespace $Namespace -ClassName $ClassName -ErrorAction Stop | Select-Object *)
    }
    catch { @() }
}

function Get-SafeStorageReliability {
    $res = @()
    try {
        $res = @(Get-PhysicalDisk -ErrorAction Stop | Get-StorageReliabilityCounter -ErrorAction Stop | Select-Object *)
    }
    catch { }
    if (-not $res -or $res.Count -eq 0) {
        try {
            $res = @(Get-CimInstance -Namespace 'root/Microsoft/Windows/Storage' -ClassName 'MSFT_StorageReliabilityCounter' -ErrorAction Stop | Select-Object *)
        }
        catch { @() }
    }
    return $res
}

function Get-SafePerformanceCounters {
    $paths = @(
        '\\PhysicalDisk(*)\\Disk Read Bytes/sec',
        '\\PhysicalDisk(*)\\Disk Write Bytes/sec',
        '\\PhysicalDisk(*)\\% Disk Time',
        '\\PhysicalDisk(*)\\Avg. Disk sec/Read',
        '\\PhysicalDisk(*)\\Avg. Disk sec/Write',
        '\\PhysicalDisk(*)\\Current Disk Queue Length'
    )
    try {
        @(Get-Counter -Counter $paths -MaxSamples 1 -ErrorAction Stop |
            Select-Object -ExpandProperty CounterSamples |
            Select-Object Path, InstanceName, CookedValue, Timestamp)
    }
    catch { @() }
}

function Get-SafeEventLog {
    $logs = @(
        'System',
        'Microsoft-Windows-Storage-Storport/Operational',
        'Microsoft-Windows-Partition/Diagnostic',
        'Microsoft-Windows-Ntfs/Operational'
    )
    $result = @()
    foreach ($log in $logs) {
        try {
            $result += @(Get-WinEvent -LogName $log -MaxEvents 15 -ErrorAction Stop |
                Select-Object LogName, Id, LevelDisplayName, TimeCreated, ProviderName, Message)
        }
        catch { }
    }
    return $result
}

Trace-Step "1. Инициализация и опрос базовых системных классов Win32 (Win32_ComputerSystem, Win32_OperatingSystem)"
$computer_system = @(Get-SafeCimInstances -ClassName 'Win32_ComputerSystem')
$operating_system = @(Get-SafeCimInstances -ClassName 'Win32_OperatingSystem')

Trace-Step "2. Опрос Win32 дисков, разделов и томов (Win32_DiskDrive, Win32_DiskPartition, Win32_LogicalDisk, Win32_Volume)"
$physical_disks = @(Get-SafeCimInstances -ClassName 'Win32_DiskDrive')
$disk_partitions = @(Get-SafeCimInstances -ClassName 'Win32_DiskPartition')
$logical_disks = @(Get-SafeCimInstances -ClassName 'Win32_LogicalDisk')
$volumes = @(Get-SafeCimInstances -ClassName 'Win32_Volume')

Trace-Step "3. Опрос MSFT Storage CIM (MSFT_PhysicalDisk, MSFT_VirtualDisk, MSFT_StoragePool, MSFT_Disk, MSFT_Partition)"
$physical_storage = @(Get-SafeCimInstances -ClassName 'MSFT_PhysicalDisk' -Namespace 'root/Microsoft/Windows/Storage')
$virtual_disks = @(Get-SafeCimInstances -ClassName 'MSFT_VirtualDisk' -Namespace 'root/Microsoft/Windows/Storage')
$storage_pools = @(Get-SafeCimInstances -ClassName 'MSFT_StoragePool' -Namespace 'root/Microsoft/Windows/Storage')
$disk_drives = @(Get-SafeCimInstances -ClassName 'MSFT_Disk' -Namespace 'root/Microsoft/Windows/Storage')
$partitions = @(Get-SafeCimInstances -ClassName 'MSFT_Partition' -Namespace 'root/Microsoft/Windows/Storage')

Trace-Step "4. Опрос SMART и счетчиков надежности (Get-PhysicalDisk | Get-StorageReliabilityCounter)"
$storage_reliability = @(Get-SafeStorageReliability)

Trace-Step "5. Опрос счетчиков производительности дисков (Get-Counter PhysicalDisk)"
$performance_counters = @(Get-SafePerformanceCounters)

Trace-Step "6. Опрос журналов событий Windows Storage (Get-WinEvent System/Storport/Partition/Ntfs)"
$event_log = @(Get-SafeEventLog)

Trace-Step "7. Формирование структуры результата"
$result = [ordered]@{
    computer_system = $computer_system
    operating_system = $operating_system
    physical_disks = $physical_disks
    disk_partitions = $disk_partitions
    logical_disks = $logical_disks
    volumes = $volumes
    physical_storage = $physical_storage
    virtual_disks = $virtual_disks
    storage_pools = $storage_pools
    disk_drives = $disk_drives
    partitions = $partitions
    storage_reliability = $storage_reliability
    performance_counters = $performance_counters
    event_log = $event_log
}

Trace-Step "8. Сериализация в JSON (ConvertTo-Json -Depth 8)"
$json = $result | ConvertTo-Json -Depth 8 -Compress

Trace-Step "9. Завершено успешно"
$json
"""


@dataclass
class StorageDiskHealthInfo:
    """Структурированные данные о здоровье и характеристиках физического диска."""
    device_id: str = ""
    friendly_name: str = ""
    model: str = ""
    serial_number: str = ""
    bus_type: str = ""
    media_type: str = ""
    size_gb: float = 0.0
    health_status: str = ""
    operational_status: str = ""
    size_bytes: Optional[int] = 0
    temperature_c: Optional[float] = 0.0
    wear_percentage: Optional[float] = 0.0
    power_on_hours: Optional[int] = 0
    read_errors_total: Optional[int] = 0
    write_errors_total: Optional[int] = 0
    read_latency_max_ms: Optional[float] = 0.0
    write_latency_max_ms: Optional[float] = 0.0
    lifetime_read_bytes: Optional[int] = 0
    lifetime_write_bytes: Optional[int] = 0
    lifetime_read_tb: Optional[float] = 0.0
    lifetime_write_tb: Optional[float] = 0.0
    raw_storage_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование информации о накопителе в словарь."""
        return asdict(self)


class WindowsStorageSensor:
    """Сенсор дисковой подсистемы на базе нативных интерфейсов Windows и PowerShell."""
    _CACHE_SNAPSHOT: Dict[str, Any] = {}
    _CACHE_TIME: float = 0.0
    _DEFAULT_TTL: float = 43200.0  # 12 часов (2 раза в день)
    _BG_LOCK: threading.Lock = threading.Lock()
    _IS_FETCHING: bool = False

    def __init__(self, timeout_sec: int = 30, ttl_sec: float = 43200.0) -> None:
        """Инициализация сенсора дисков Windows.

        Args:
            timeout_sec: Таймаут сбора данных через PowerShell в секундах (по умолчанию 30с).
            ttl_sec: Время жизни кэша снимка в секундах (по умолчанию 43200с = 12 часов / 2 раза в день).
        """
        self.timeout_sec = timeout_sec
        self.ttl_sec = ttl_sec

    @property
    def is_windows(self) -> bool:
        """Проверка, выполняется ли код на платформе Windows."""
        return platform.system().lower() == 'windows' or os.name == 'nt'

    def _render_storage_diagnostics(
        self,
        stderr_output: str,
        duration: float,
        is_timeout: bool = False,
        timeout_limit: int = 0,
        return_code: Optional[int] = 0
    ) -> None:
        """Отрисовывает выделенный блок диагностики выполнения PowerShell-скрипта в консоль/лог.

        Args:
            stderr_output: Текст стандартного потока ошибок от PowerShell.
            duration: Общая продолжительность выполнения в секундах.
            is_timeout: Флаг прерывания по таймауту.
            timeout_limit: Установленный лимит времени в секундах.
            return_code: Код возврата процесса PowerShell.
        """
        lines = [line.strip() for line in (stderr_output or '').splitlines() if line.strip()]
        diag_lines = [line for line in lines if '[STORAGE-DIAG]' in line]

        border = "=" * 80
        inner_div = "-" * 80
        title = "❌ [POWERSHELL STORAGE DIAGNOSTICS] ПРЕВЫШЕН ТАЙМАУТ" if is_timeout else "📊 [POWERSHELL STORAGE DIAGNOSTICS] ЭТАПЫ СБОРА ХРАНИЛИЩА"

        out: List[str] = [
            "",
            border,
            f"  {title}",
            border,
        ]

        if diag_lines:
            for d in diag_lines:
                clean_d = d.replace('[STORAGE-DIAG]', '').strip()
                out.append(f"  ▶ {clean_d}")
        elif lines:
            for line in lines:
                out.append(f"  ℹ {line}")
        else:
            out.append("  (нет вывода промежуточных шагов)")

        out.append(inner_div)
        if is_timeout:
            last_step = diag_lines[-1].replace('[STORAGE-DIAG]', '').strip() if diag_lines else 'Инициализация PowerShell'
            out.append(f"  ❌ СТАТУС: Превышен лимит {timeout_limit} сек. (прервано через {duration:.2f} сек.)")
            out.append(f"  ⚠️  ПОСЛЕДНИЙ ВЫПОЛНЯВШИЙСЯ ЭТАП: {last_step}")
        elif return_code != 0:
            out.append(f"  ⚠️ СТАТУС: Ошибка выполнения (код {return_code}) за {duration:.2f} сек.")
        else:
            out.append(f"  ✅ СТАТУС: Успешно завершено за {duration:.2f} сек.")
        out.append(border)
        out.append("")

        rendered_block = "\n".join(out)
        if is_timeout:
            logger.warning(rendered_block)
        else:
            logger.info(rendered_block)

    def run_powershell(self, script: str, timeout: Optional[int] = 0) -> Dict[str, Any]:
        """Выполняет PowerShell-скрипт и разбирает JSON-результат.

        Args:
            script: Текст PowerShell-скрипта.
            timeout: Максимальное время выполнения в секундах.

        Returns:
            Dict[str, Any]: Декодированный JSON-объект.
        """
        effective_timeout = timeout if timeout and timeout > 0 else self.timeout_sec
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        t_start = time.perf_counter()
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', script],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=effective_timeout,
                creationflags=creationflags,
                check=False
            )
            duration = time.perf_counter() - t_start
            self._render_storage_diagnostics(result.stderr, duration, is_timeout=False, return_code=result.returncode)
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - t_start
            stderr_captured = (exc.stderr or '') if isinstance(exc.stderr, str) else ''
            self._render_storage_diagnostics(stderr_captured, duration, is_timeout=True, timeout_limit=effective_timeout)
            logger.warning(f'PowerShell скрипт сбора хранилища превысил таймаут {effective_timeout} сек.')
            return {}

        if result.returncode != 0:
            logger.warning(f'PowerShell завершился с кодом {result.returncode}: {result.stderr.strip()}')
            if not result.stdout.strip():
                raise RuntimeError(f'PowerShell завершился с кодом {result.returncode}: {result.stderr.strip()}')

        stdout_clean = result.stdout.strip()
        if not stdout_clean:
            return {}
        try:
            return json.loads(stdout_clean)
        except json.JSONDecodeError as error:
            logger.error(f'Некорректный JSON от PowerShell: {stdout_clean[:500]}')
            raise ValueError(f'Некорректный JSON от PowerShell: {stdout_clean[:500]}') from error

    def _perform_collection_and_cache(self) -> Dict[str, Any]:
        """Выполняет сбор снимка через PowerShell и обновляет кэш."""
        try:
            logger.debug(f'Windows Storage Sensor: сбор снимка накопителей через CIM/WMI (интервал кэша: {self.ttl_sec / 60:.1f} мин)...')
            try:
                raw_data = self.run_powershell(POWERSHELL_STORAGE_SCRIPT)
            except Exception as ex:
                logger.error(f'Ошибка выполнения скрипта сбора хранилища: {ex}')
                raw_data = {}

            snapshot = self.normalize_snapshot(raw_data)
            WindowsStorageSensor._CACHE_SNAPSHOT = snapshot
            WindowsStorageSensor._CACHE_TIME = time.time()
            return snapshot
        finally:
            with WindowsStorageSensor._BG_LOCK:
                WindowsStorageSensor._IS_FETCHING = False

    def trigger_async_refresh(self) -> None:
        """Запускает фоновый опрос накопителей без блокировки вызывающего потока."""
        with WindowsStorageSensor._BG_LOCK:
            if WindowsStorageSensor._IS_FETCHING:
                return
            WindowsStorageSensor._IS_FETCHING = True

        thread = threading.Thread(
            target=self._perform_collection_and_cache,
            name="WindowsStorageSensorWorker",
            daemon=True
        )
        thread.start()

    def collect_snapshot(self, force_refresh: bool = False, sync: bool = False) -> Dict[str, Any]:
        """Собирает полный доступный снимок Windows Storage с кэшированием (раз в 12 часов).

        По умолчанию выполняется асинхронно в фоне без блокировки вызывающего потока.

        Args:
            force_refresh: Принудительное обновление без использования кэша.
            sync: Выполнить опрос синхронно с блокировкой потока.

        Returns:
            Dict[str, Any]: Нормализованный диагностический снимок.
        """
        if not self.is_windows:
            logger.debug('Windows Storage Sensor поддерживается только в среде Windows.')
            return self._empty_snapshot()

        now = time.time()
        if not force_refresh and WindowsStorageSensor._CACHE_SNAPSHOT and (now - WindowsStorageSensor._CACHE_TIME < self.ttl_sec):
            return WindowsStorageSensor._CACHE_SNAPSHOT

        if sync:
            return self._perform_collection_and_cache()

        # Запуск фонового обновления
        self.trigger_async_refresh()

        if WindowsStorageSensor._CACHE_SNAPSHOT:
            return WindowsStorageSensor._CACHE_SNAPSHOT

        return self._empty_snapshot()

    def normalize_snapshot(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Формирует нормализованный снимок диагностических данных.

        Args:
            raw_data: Сырые данные от Windows-провайдеров.

        Returns:
            Dict[str, Any]: Структурированный снимок для хранения и анализа.
        """
        def _ensure_list(val: Any) -> List[Any]:
            if val is None:
                return []
            if isinstance(val, list):
                return val
            if isinstance(val, dict):
                return [val]
            return []

        physical_disks = _ensure_list(raw_data.get('physical_disks'))
        physical_storage = _ensure_list(raw_data.get('physical_storage'))
        storage_reliability = _ensure_list(raw_data.get('storage_reliability'))
        event_log = _ensure_list(raw_data.get('event_log'))
        performance_counters = _ensure_list(raw_data.get('performance_counters'))

        snapshot = {
            'schema_version': '1.0',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine()
            },
            'sources': {
                'computer_system': _ensure_list(raw_data.get('computer_system')),
                'operating_system': _ensure_list(raw_data.get('operating_system')),
                'physical_disks': physical_disks,
                'disk_partitions': _ensure_list(raw_data.get('disk_partitions')),
                'logical_disks': _ensure_list(raw_data.get('logical_disks')),
                'volumes': _ensure_list(raw_data.get('volumes')),
                'physical_storage': physical_storage,
                'virtual_disks': _ensure_list(raw_data.get('virtual_disks')),
                'storage_pools': _ensure_list(raw_data.get('storage_pools')),
                'disk_drives': _ensure_list(raw_data.get('disk_drives')),
                'partitions': _ensure_list(raw_data.get('partitions')),
                'storage_reliability': storage_reliability,
                'performance_counters': performance_counters,
                'event_log': event_log
            },
            'summary': {
                'physical_disk_count': len(physical_disks),
                'storage_disk_count': len(physical_storage),
                'reliability_counter_count': len(storage_reliability),
                'event_count': len(event_log)
            }
        }
        return snapshot

    def get_physical_disks(self, force_refresh: bool = False) -> List[StorageDiskHealthInfo]:
        """Извлекает детальные нормализованные сведения о каждом физическом накопителе.

        Объединяет данные Win32_DiskDrive, MSFT_PhysicalDisk и StorageReliabilityCounter.

        Args:
            force_refresh: Принудительное обновление данных.

        Returns:
            List[StorageDiskHealthInfo]: Список объектов StorageDiskHealthInfo.
        """
        snapshot = self.collect_snapshot(force_refresh=force_refresh)
        sources = snapshot.get('sources', {})
        storage_disks = sources.get('physical_storage', [])
        wmi_disks = sources.get('physical_disks', [])
        reliabilities = sources.get('storage_reliability', [])

        reliability_map: Dict[str, Dict[str, Any]] = {}
        for r in reliabilities:
            dev_id = str(r.get('DeviceId', '') or r.get('DeviceID', '') or '')
            if dev_id:
                reliability_map[dev_id] = r

        bus_type_map = {
            0: 'Unknown', 1: 'SCSI', 2: 'ATAPI', 3: 'ATA', 4: '1394', 5: 'SSA',
            6: 'Fibre Channel', 7: 'USB', 8: 'RAID', 9: 'iSCSI', 10: 'SAS',
            11: 'SATA', 12: 'SD', 13: 'MMC', 14: 'MAX', 15: 'File Backed Virtual',
            16: 'Storage Spaces', 17: 'NVMe', 18: 'SCM', 19: 'UFS'
        }
        media_type_map = {0: 'Unspecified', 3: 'HDD', 4: 'SSD', 5: 'SCM'}
        health_status_map = {0: 'Healthy', 1: 'Warning', 2: 'Unhealthy', 5: 'Unknown'}

        result_disks: List[StorageDiskHealthInfo] = []
        if storage_disks:
            for s_disk in storage_disks:
                dev_id = str(s_disk.get('DeviceId', '') or s_disk.get('DeviceID', '') or '')
                friendly_name = str(s_disk.get('FriendlyName', '') or s_disk.get('Model', 'Physical Disk'))
                model = str(s_disk.get('Model', friendly_name))
                serial = str(s_disk.get('SerialNumber', '') or 'N/A').strip()
                size_bytes = int(s_disk.get('Size', 0) or 0)
                size_gb = round(size_bytes / (1024 ** 3), 2) if size_bytes else 0.0
                raw_bus = s_disk.get('BusType')
                bus_type = bus_type_map.get(raw_bus, str(raw_bus or 'Unknown'))
                raw_media = s_disk.get('MediaType')
                media_type = media_type_map.get(raw_media, 'SSD' if 'nvme' in model.lower() or 'ssd' in model.lower() else 'HDD')
                raw_health = s_disk.get('HealthStatus')
                health_str = health_status_map.get(raw_health, 'Healthy' if raw_health == 0 else 'Warning')
                op_status = str(s_disk.get('OperationalStatus', 'OK'))

                rel = reliability_map.get(dev_id, {})
                temp_c = float(rel.get('Temperature') or 0.0)
                wear = float(rel.get('Wear') or 0.0)
                poh = int(rel.get('PowerOnHours') or 0)
                read_errors = int(rel.get('ReadErrorsTotal') or 0)
                write_errors = int(rel.get('WriteErrorsTotal') or 0)
                read_latency_max = float(rel.get('ReadLatencyMax') or 0.0)
                write_latency_max = float(rel.get('WriteLatencyMax') or 0.0)

                read_bytes = int(rel.get('BytesRead') or rel.get('DataUnitsRead') or 0)
                write_bytes = int(rel.get('BytesWritten') or rel.get('DataUnitsWritten') or 0)
                read_tb = round(float(read_bytes) / (1024 ** 4), 2) if read_bytes else 0.0
                write_tb = round(float(write_bytes) / (1024 ** 4), 2) if write_bytes else 0.0

                result_disks.append(StorageDiskHealthInfo(
                    device_id=f'Disk{dev_id}' if dev_id else 'Disk',
                    friendly_name=friendly_name,
                    model=model,
                    serial_number=serial,
                    bus_type=bus_type,
                    media_type=media_type,
                    size_gb=size_gb,
                    health_status=health_str,
                    operational_status=op_status,
                    size_bytes=size_bytes,
                    temperature_c=temp_c,
                    wear_percentage=wear,
                    power_on_hours=poh,
                    read_errors_total=read_errors,
                    write_errors_total=write_errors,
                    read_latency_max_ms=read_latency_max,
                    write_latency_max_ms=write_latency_max,
                    lifetime_read_bytes=read_bytes,
                    lifetime_write_bytes=write_bytes,
                    lifetime_read_tb=read_tb,
                    lifetime_write_tb=write_tb,
                    raw_storage_data=s_disk,
                ))
        elif wmi_disks:
            for w_disk in wmi_disks:
                dev_id = str(w_disk.get('Index', '') or w_disk.get('DeviceID', 'Disk'))
                model = str(w_disk.get('Model', 'Generic Disk'))
                serial = str(w_disk.get('SerialNumber', 'N/A')).strip()
                size_bytes = int(w_disk.get('Size', 0) or 0)
                size_gb = round(size_bytes / (1024 ** 3), 2) if size_bytes else 0.0
                status_str = str(w_disk.get('Status', 'OK'))
                rel = reliability_map.get(str(dev_id), {})
                temp_c = float(rel.get('Temperature') or 0.0)
                wear = float(rel.get('Wear') or 0.0)
                poh = int(rel.get('PowerOnHours') or 0)
                read_bytes = int(rel.get('BytesRead') or rel.get('DataUnitsRead') or 0)
                write_bytes = int(rel.get('BytesWritten') or rel.get('DataUnitsWritten') or 0)
                read_tb = round(float(read_bytes) / (1024 ** 4), 2) if read_bytes else 0.0
                write_tb = round(float(write_bytes) / (1024 ** 4), 2) if write_bytes else 0.0

                result_disks.append(StorageDiskHealthInfo(
                    device_id=str(w_disk.get('DeviceID', f'\\\\.\\PHYSICALDRIVE{dev_id}')),
                    friendly_name=model,
                    model=model,
                    serial_number=serial,
                    bus_type=str(w_disk.get('InterfaceType', 'WMI')),
                    media_type='SSD' if 'ssd' in model.lower() or 'nvme' in model.lower() else 'HDD',
                    size_gb=size_gb,
                    health_status='Healthy' if status_str.upper() == 'OK' else 'Warning',
                    operational_status=status_str,
                    size_bytes=size_bytes,
                    temperature_c=temp_c,
                    wear_percentage=wear,
                    power_on_hours=poh,
                    lifetime_read_bytes=read_bytes,
                    lifetime_write_bytes=write_bytes,
                    lifetime_read_tb=read_tb,
                    lifetime_write_tb=write_tb,
                    raw_storage_data=w_disk,
                ))
        return result_disks

    def _empty_snapshot(self) -> Dict[str, Any]:
        """Возвращает пустой снимок для не-Windows платформ."""
        return {
            'schema_version': '1.0',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'platform': {'system': platform.system()},
            'sources': {},
            'summary': {
                'physical_disk_count': 0,
                'storage_disk_count': 0,
                'reliability_counter_count': 0,
                'event_count': 0
            }
        }


def collect_storage_snapshot() -> Dict[str, Any]:
    """Собирает полный снимок Windows Storage через глобальный экземпляр сенсора.

    Returns:
        Dict[str, Any]: Нормализованный диагностический снимок.
    """
    sensor = WindowsStorageSensor()
    return sensor.collect_snapshot()


def save_snapshot(snapshot: Dict[str, Any], output_path: Path) -> None:
    """Сохраняет диагностический снимок в UTF-8 JSON файл.

    Args:
        snapshot: Диагностический снимок.
        output_path: Путь к выходному JSON-файлу.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    logger.info(f'Снимок сохранен: {output_path}')


def main() -> int:
    """Запускает сбор диагностической информации из командной строки.

    Returns:
        int: Код завершения процесса.
    """
    parser = argparse.ArgumentParser(description='Windows Storage Sensor без Smartmontools.')
    parser.add_argument('--output', type=Path, default=Path('storage_snapshot.json'))
    parser.add_argument('--log-level', default='INFO', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR'))
    arguments = parser.parse_args()
    try:
        snapshot = collect_storage_snapshot()
        save_snapshot(snapshot, arguments.output)
    except Exception as error:
        logger.error(f'Ошибка сбора снимка накопителей: {error}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
