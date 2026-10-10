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
#     python -m apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor
#
#     sensor = WindowsStorageSensor()
#     disks = sensor.get_physical_disks()
#
# File: windows_storage_sensor.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 03:18:00
# =============================================================================

from __future__ import annotations
"""Сенсор диагностики накопителей Windows без сторонних утилит."""

import argparse
import base64
import json
import os
import platform
import re
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
$ProgressPreference = 'SilentlyContinue'
$ErrorActionPreference = 'SilentlyContinue'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$errWriter = New-Object System.IO.StreamWriter([System.Console]::OpenStandardError(), $utf8NoBom)
$errWriter.AutoFlush = $true
[System.Console]::SetError($errWriter)

$outWriter = New-Object System.IO.StreamWriter([System.Console]::OpenStandardOutput(), $utf8NoBom)
$outWriter.AutoFlush = $true
[System.Console]::SetOut($outWriter)

[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[System.Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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

function Get-SafeWmiSmartData {
    $res = @()
    try {
        $rawSmart = @(Get-CimInstance -Namespace 'root/wmi' -ClassName 'MSStorageDriver_FailurePredictData' -ErrorAction Stop)
        foreach ($it in $rawSmart) {
            $b64 = if ($it.VendorSpecific) { [System.Convert]::ToBase64String($it.VendorSpecific) } else { $null }
            $res += [PSCustomObject]@{
                InstanceName = $it.InstanceName
                PredictFailure = $it.PredictFailure
                VendorSpecificB64 = $b64
            }
        }
    }
    catch { }
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

Trace-Step "5. Опрос WMI SMART атрибутов накопителей (MSStorageDriver_FailurePredictData)"
$smart_data = @(Get-SafeWmiSmartData)

Trace-Step "6. Опрос счетчиков производительности дисков (Get-Counter PhysicalDisk)"
$performance_counters = @(Get-SafePerformanceCounters)

Trace-Step "7. Опрос журналов событий Windows Storage (Get-WinEvent System/Storport/Partition/Ntfs)"
$event_log = @(Get-SafeEventLog)

Trace-Step "8. Формирование структуры результата"
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
    smart_data = $smart_data
    performance_counters = $performance_counters
    event_log = $event_log
}

Trace-Step "9. Сериализация в JSON (ConvertTo-Json -Depth 8)"
$json = $result | ConvertTo-Json -Depth 8 -Compress

Trace-Step "10. Завершено успешно"
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


def parse_smart_vendor_data(raw_b64: str) -> Dict[int, Dict[str, Any]]:
    """Парсинг 512-байтного буфера SMART (структура ATA атрибутов).

    Args:
        raw_b64: Строка в кодировке Base64, содержащая байты VendorSpecific.

    Returns:
        Dict[int, Dict[str, Any]]: Словарь разобранных SMART-атрибутов (ID -> {id, val, worst, raw}).
    """
    if not raw_b64:
        return {}
    try:
        raw = base64.b64decode(raw_b64)
        if len(raw) < 362:
            return {}
        attrs: Dict[int, Dict[str, Any]] = {}
        for i in range(2, min(len(raw), 362), 12):
            attr_id = raw[i]
            if attr_id == 0:
                continue
            val = raw[i + 3]
            worst = raw[i + 4]
            raw_val = int.from_bytes(raw[i + 5:i + 11], byteorder='little')
            attrs[attr_id] = {
                'id': attr_id,
                'val': val,
                'worst': worst,
                'raw': raw_val
            }
        return attrs
    except Exception:
        return {}


def _enrich_disks_with_lhm(disks: List[StorageDiskHealthInfo], sensors: List[Dict[str, Any]]) -> None:
    """Обогащает объекты StorageDiskHealthInfo данными SMART/LHM (наработка, температура, износ, запись).

    Args:
        disks: Список дисков для обогащения.
        sensors: Плоский список сенсоров из LibreHardwareMonitor.
    """
    if not disks or not sensors:
        return

    lhm_by_hardware: Dict[str, Dict[str, Any]] = {}
    for s in sensors:
        htype = str(s.get("hardware_type", "")).lower()
        if not any(k in htype for k in ("storage", "disk", "hdd", "ssd", "nvme")):
            continue
        hname = str(s.get("hardware_name", "")).strip()
        if not hname:
            continue
        if hname not in lhm_by_hardware:
            lhm_by_hardware[hname] = {
                "power_on_hours": None,
                "power_on_count": None,
                "temperature_c": None,
                "life_pct": None,
                "wear_pct": None,
                "data_written_gb": None,
                "data_read_gb": None,
                "total_space_gb": None,
            }

        cat = str(s.get("sensor_category", "")).lower()
        sname = str(s.get("sensor_name", "")).lower()
        v_num = s.get("value_num") if s.get("value_num") is not None else s.get("value_numeric")
        if v_num is None:
            continue

        if "factor" in cat:
            if "power on hours" in sname:
                lhm_by_hardware[hname]["power_on_hours"] = int(v_num)
            elif "power on count" in sname:
                lhm_by_hardware[hname]["power_on_count"] = int(v_num)
        elif "temp" in cat:
            if 5 < v_num < 120:
                lhm_by_hardware[hname]["temperature_c"] = float(v_num)
        elif "level" in cat:
            if "life" in sname or "remaining" in sname:
                lhm_by_hardware[hname]["life_pct"] = float(v_num)
                lhm_by_hardware[hname]["wear_pct"] = max(0.0, min(100.0, 100.0 - float(v_num)))
            elif "wear" in sname:
                lhm_by_hardware[hname]["wear_pct"] = float(v_num)
        elif "data" in cat:
            if "data written" in sname:
                lhm_by_hardware[hname]["data_written_gb"] = float(v_num)
            elif "data read" in sname:
                lhm_by_hardware[hname]["data_read_gb"] = float(v_num)
            elif "total space" in sname:
                lhm_by_hardware[hname]["total_space_gb"] = float(v_num)

    if not lhm_by_hardware:
        return

    matched_lhm_names: set[str] = set()

    for d in disks:
        m_lower = (d.model or "").lower().strip()
        fn_lower = (d.friendly_name or "").lower().strip()
        matched_data: Optional[Dict[str, Any]] = None
        best_name: Optional[str] = None

        # 1. Прямой поиск по подстроке имени/модели
        for hname, metrics in lhm_by_hardware.items():
            h_lower = hname.lower().strip()
            if (h_lower in m_lower) or (m_lower and m_lower in h_lower) or (h_lower in fn_lower) or (fn_lower and fn_lower in h_lower):
                matched_data = metrics
                best_name = hname
                break

        # 2. Поиск по ключевым словам модели
        if not matched_data:
            m_words = [w for w in re.split(r"[\s\-_/]+", f"{m_lower} {fn_lower}") if len(w) >= 4 and w not in ("disk", "drive", "generic", "storage", "device")]
            for hname, metrics in lhm_by_hardware.items():
                h_lower = hname.lower().strip()
                if any(w in h_lower for w in m_words):
                    matched_data = metrics
                    best_name = hname
                    break

        # 3. Fallback: сопоставление по близкому объему для внешних накопителей (USB bridges), если остался неиспользованный
        if not matched_data and d.size_gb > 0:
            for hname, metrics in lhm_by_hardware.items():
                if hname in matched_lhm_names:
                    continue
                tot_gb = metrics.get("total_space_gb")
                if tot_gb and abs(tot_gb - d.size_gb) / max(d.size_gb, 1.0) < 0.15:
                    matched_data = metrics
                    best_name = hname
                    break

        if matched_data and best_name:
            matched_lhm_names.add(best_name)
            # Обогащаем отсутствующие или нулевые метрики
            if (d.power_on_hours is None or d.power_on_hours == 0) and matched_data.get("power_on_hours") is not None:
                d.power_on_hours = matched_data["power_on_hours"]

            if (d.temperature_c is None or d.temperature_c == 0.0) and matched_data.get("temperature_c") is not None:
                d.temperature_c = matched_data["temperature_c"]

            if (d.wear_percentage is None or d.wear_percentage == 0.0) and matched_data.get("wear_pct") is not None:
                d.wear_percentage = matched_data["wear_pct"]

            if (d.lifetime_write_bytes is None or d.lifetime_write_bytes == 0) and matched_data.get("data_written_gb") is not None:
                d.lifetime_write_bytes = int(matched_data["data_written_gb"] * (1024 ** 3))
                d.lifetime_write_tb = round(matched_data["data_written_gb"] / 1024.0, 2)

            if (d.lifetime_read_bytes is None or d.lifetime_read_bytes == 0) and matched_data.get("data_read_gb") is not None:
                d.lifetime_read_bytes = int(matched_data["data_read_gb"] * (1024 ** 3))
                d.lifetime_read_tb = round(matched_data["data_read_gb"] / 1024.0, 2)


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

        # Загрузка сохраненного снимка с диска, если память еще пуста
        if not WindowsStorageSensor._CACHE_SNAPSHOT:
            snap_file = _PROJECT_ROOT / "storage_snapshot.json"
            if snap_file.is_file():
                try:
                    with open(snap_file, "r", encoding="utf-8") as f:
                        WindowsStorageSensor._CACHE_SNAPSHOT = json.load(f)
                        WindowsStorageSensor._CACHE_TIME = time.time()
                except Exception as ex:
                    logger.debug(f"[WindowsStorageSensor] Ошибка загрузки storage_snapshot.json: {ex}")

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
        encoded_script = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encoded_script],
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

        По умолчанию выполняется асинхронно в фоне без блокировки вызывающего потока,
        но при отсутствии кэша или явном sync/force_refresh выполняет опрос синхронно.

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

        if sync or force_refresh or not WindowsStorageSensor._CACHE_SNAPSHOT:
            return self._perform_collection_and_cache()

        # Запуск фонового обновления при наличии устаревшего кэша
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
        smart_data = _ensure_list(raw_data.get('smart_data'))
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
                'smart_data': smart_data,
                'performance_counters': performance_counters,
                'event_log': event_log
            },
            'summary': {
                'physical_disk_count': len(physical_disks),
                'storage_disk_count': len(physical_storage),
                'reliability_counter_count': len(storage_reliability),
                'smart_device_count': len(smart_data),
                'event_count': len(event_log)
            }
        }
        return snapshot

    def get_physical_disks(self, force_refresh: bool = False, sync: bool = False) -> List[StorageDiskHealthInfo]:
        """Извлекает детальные нормализованные сведения о каждом физическом накопителе.

        Объединяет данные Win32_DiskDrive, MSFT_PhysicalDisk, StorageReliabilityCounter и WMI SMART.

        Args:
            force_refresh: Принудительное обновление данных.
            sync: Выполнить опрос синхронно.

        Returns:
            List[StorageDiskHealthInfo]: Список объектов StorageDiskHealthInfo.
        """
        snapshot = self.collect_snapshot(force_refresh=force_refresh, sync=sync)
        sources = snapshot.get('sources', {})
        storage_disks = sources.get('physical_storage', [])
        wmi_disks = sources.get('physical_disks', [])
        reliabilities = sources.get('storage_reliability', [])
        raw_smart = sources.get('smart_data', [])

        reliability_map: Dict[str, Dict[str, Any]] = {}
        for r in reliabilities:
            dev_id = str(r.get('DeviceId', '') or r.get('DeviceID', '') or '')
            if dev_id:
                reliability_map[dev_id] = r

        # Разбор WMI SMART данных
        smart_by_pnp: Dict[str, Dict[int, Dict[str, Any]]] = {}
        for s in raw_smart:
            inst = str(s.get('InstanceName', '') or '').strip()
            b64 = s.get('VendorSpecificB64', '')
            if b64:
                parsed = parse_smart_vendor_data(b64)
                if parsed:
                    norm_inst = inst.rstrip('_0').lower()
                    smart_by_pnp[norm_inst] = parsed

        wmi_by_index: Dict[str, Dict[str, Any]] = {}
        wmi_by_serial: Dict[str, Dict[str, Any]] = {}
        for w in wmi_disks:
            idx_str = str(w.get('Index', ''))
            if idx_str:
                wmi_by_index[idx_str] = w
            sn = str(w.get('SerialNumber', '') or '').strip().lower()
            if sn and sn != 'n/a':
                wmi_by_serial[sn] = w

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
                
                # Уточнение типа и интерфейса
                model_lower = model.lower()
                if bus_type == 'RAID':
                    if any(kw in model_lower for kw in ('nvme', '990', '980', '970', 'pcie')):
                        bus_type = 'NVMe'
                    elif any(kw in model_lower for kw in ('mx500', 'sata', 'hdwd', 'wd20', 'barracuda')):
                        bus_type = 'SATA'
                if media_type == 'Unspecified':
                    if bus_type == 'USB':
                        media_type = 'External'
                    elif any(kw in model_lower for kw in ('ssd', 'nvme')):
                        media_type = 'SSD'
                    else:
                        media_type = 'HDD'
                        
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

                # Поиск соответствующих SMART-атрибутов
                smart_attrs: Dict[int, Dict[str, Any]] = {}
                w_disk = wmi_by_index.get(dev_id)
                if not w_disk and serial and serial != 'N/A':
                    w_disk = wmi_by_serial.get(serial.lower())

                if w_disk:
                    pnp = str(w_disk.get('PNPDeviceID') or '').lower()
                    for norm_inst, attrs in smart_by_pnp.items():
                        if norm_inst in pnp or pnp in norm_inst or any(part in norm_inst for part in pnp.split('\\') if len(part) > 6):
                            smart_attrs = attrs
                            break

                if not smart_attrs and model:
                    for norm_inst, attrs in smart_by_pnp.items():
                        if any(w.lower() in norm_inst for w in model.split() if len(w) > 3):
                            smart_attrs = attrs
                            break

                # Дополнение метрик из SMART если Get-StorageReliabilityCounter вернул 0/None
                if (poh == 0 or poh is None) and smart_attrs:
                    if 9 in smart_attrs:
                        poh = int(smart_attrs[9]['raw'])

                if (temp_c == 0.0 or temp_c is None) and smart_attrs:
                    if 194 in smart_attrs:
                        temp_c = float(smart_attrs[194]['raw'] & 0xFF)
                    elif 190 in smart_attrs:
                        temp_c = float(smart_attrs[190]['raw'] & 0xFF)

                if (wear == 0.0 or wear is None) and smart_attrs:
                    if 202 in smart_attrs:  # Percentage used / remaining
                        wear = max(0.0, min(100.0, 100.0 - float(smart_attrs[202]['val'])))
                    elif 231 in smart_attrs:  # SSD Life Left
                        wear = max(0.0, min(100.0, 100.0 - float(smart_attrs[231]['val'])))
                    elif 232 in smart_attrs:  # Available Spare
                        wear = max(0.0, min(100.0, 100.0 - float(smart_attrs[232]['val'])))

                if (read_errors == 0 or read_errors is None) and smart_attrs:
                    if 5 in smart_attrs:
                        read_errors = int(smart_attrs[5]['raw'])

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

                # Поиск соответствующих SMART-атрибутов
                smart_attrs = {}
                pnp = str(w_disk.get('PNPDeviceID') or '').lower()
                for norm_inst, attrs in smart_by_pnp.items():
                    if norm_inst in pnp or pnp in norm_inst or any(part in norm_inst for part in pnp.split('\\') if len(part) > 6):
                        smart_attrs = attrs
                        break

                if not smart_attrs and model:
                    for norm_inst, attrs in smart_by_pnp.items():
                        if any(w.lower() in norm_inst for w in model.split() if len(w) > 3):
                            smart_attrs = attrs
                            break

                if (poh == 0 or poh is None) and smart_attrs:
                    if 9 in smart_attrs:
                        poh = int(smart_attrs[9]['raw'])

                if (temp_c == 0.0 or temp_c is None) and smart_attrs:
                    if 194 in smart_attrs:
                        temp_c = float(smart_attrs[194]['raw'] & 0xFF)
                    elif 190 in smart_attrs:
                        temp_c = float(smart_attrs[190]['raw'] & 0xFF)

                if (wear == 0.0 or wear is None) and smart_attrs:
                    if 202 in smart_attrs:
                        wear = max(0.0, min(100.0, 100.0 - float(smart_attrs[202]['val'])))
                    elif 231 in smart_attrs:
                        wear = max(0.0, min(100.0, 100.0 - float(smart_attrs[231]['val'])))
                    elif 232 in smart_attrs:
                        wear = max(0.0, min(100.0, 100.0 - float(smart_attrs[232]['val'])))

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

        # Обогащение данными из LibreHardwareMonitor (LhmService)
        try:
            from apps.windows.sdk.modules.hardware.lhm_service import LhmService
            lhm = LhmService()
            if lhm.is_running():
                lhm_sensors = lhm.get_flattened_sensors()
                if lhm_sensors:
                    _enrich_disks_with_lhm(result_disks, lhm_sensors)
        except Exception as lhm_err:
            logger.debug(f'Обогащение через LHM пропущено: {lhm_err}')

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
