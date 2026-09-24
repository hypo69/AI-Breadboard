# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Native Storage Sensor
# =============================================================================
# Description:
#   Сенсор дисковой подсистемы Windows. Выполняет глубокую диагностику
#   физических дисков (NVMe, SATA SSD, HDD), пулов хранения, счетчиков
#   надежности (StorageReliabilityCounter), счетчиков производительности и
#   событий журнала дисковой подсистемы без использования Smartmontools.
#
# Examples:
#   >>> from apps.windows.storage_sensors.windows_storage_sensor import WindowsStorageSensor
#   >>> sensor = WindowsStorageSensor()
#   >>> disks = sensor.get_physical_disks()
#   >>> for disk in disks:
#   ...     print(disk["model"], disk["health_status"], disk.get("temperature_c"))
#
# File: windows_storage_sensor.py
# Project: ai-breadboard
# Package: apps.windows.storage_sensors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сенсор диагностики накопителей Windows без сторонних утилит."""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from logger import logger
except ImportError:
    try:
        from src.logger import logger  # type: ignore
    except ImportError:
        logger = logging.getLogger("windows_storage_sensor")

POWERSHELL_STORAGE_SCRIPT = r'''
$ErrorActionPreference = 'SilentlyContinue'

function Get-SafeCimInstances {
    param([string]$ClassName, [string]$Namespace = 'root/cimv2')
    try {
        @(Get-CimInstance -Namespace $Namespace -ClassName $ClassName -ErrorAction Stop | Select-Object *)
    }
    catch { @() }
}

function Get-SafeStorageReliability {
    try {
        @(Get-CimInstance -Namespace 'root/Microsoft/Windows/Storage' -ClassName 'MSFT_StorageReliabilityCounter' -ErrorAction Stop | Select-Object *)
    }
    catch {
        try { @(Get-PhysicalDisk -ErrorAction Stop | Get-StorageReliabilityCounter -ErrorAction Stop | Select-Object *) }
        catch { @() }
    }
}

function Get-SafePerformanceCounters {
    $paths = @(
        '\\PhysicalDisk(*)\Disk Read Bytes/sec',
        '\\PhysicalDisk(*)\Disk Write Bytes/sec',
        '\\PhysicalDisk(*)\% Disk Time',
        '\\PhysicalDisk(*)\Avg. Disk sec/Read',
        '\\PhysicalDisk(*)\Avg. Disk sec/Write',
        '\\PhysicalDisk(*)\Current Disk Queue Length'
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

$result = [ordered]@{
    computer_system = @(Get-SafeCimInstances -ClassName 'Win32_ComputerSystem')
    operating_system = @(Get-SafeCimInstances -ClassName 'Win32_OperatingSystem')
    physical_disks = @(Get-SafeCimInstances -ClassName 'Win32_DiskDrive')
    disk_partitions = @(Get-SafeCimInstances -ClassName 'Win32_DiskPartition')
    logical_disks = @(Get-SafeCimInstances -ClassName 'Win32_LogicalDisk')
    volumes = @(Get-SafeCimInstances -ClassName 'Win32_Volume')
    physical_storage = @(Get-SafeCimInstances -ClassName 'MSFT_PhysicalDisk' -Namespace 'root/Microsoft/Windows/Storage')
    virtual_disks = @(Get-SafeCimInstances -ClassName 'MSFT_VirtualDisk' -Namespace 'root/Microsoft/Windows/Storage')
    storage_pools = @(Get-SafeCimInstances -ClassName 'MSFT_StoragePool' -Namespace 'root/Microsoft/Windows/Storage')
    disk_drives = @(Get-SafeCimInstances -ClassName 'MSFT_Disk' -Namespace 'root/Microsoft/Windows/Storage')
    partitions = @(Get-SafeCimInstances -ClassName 'MSFT_Partition' -Namespace 'root/Microsoft/Windows/Storage')
    storage_reliability = @(Get-SafeStorageReliability)
    performance_counters = @(Get-SafePerformanceCounters)
    event_log = @(Get-SafeEventLog)
}

$result | ConvertTo-Json -Depth 8 -Compress
'''


@dataclass
class StorageDiskHealthInfo:
    """Структурированные данные о здоровье и характеристиках физического диска."""
    device_id: str
    friendly_name: str
    model: str
    serial_number: str
    bus_type: str
    media_type: str
    size_gb: float
    health_status: str
    operational_status: str
    temperature_c: Optional[float] = None
    wear_percentage: Optional[float] = None
    power_on_hours: Optional[int] = None
    read_errors_total: Optional[int] = None
    write_errors_total: Optional[int] = None
    read_latency_max_ms: Optional[float] = None
    write_latency_max_ms: Optional[float] = None
    raw_storage_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование информации о накопителе в словарь."""
        return asdict(self)


class WindowsStorageSensor:
    """Сенсор дисковой подсистемы на базе нативных интерфейсов Windows и PowerShell."""

    _CACHE_SNAPSHOT: Optional[Dict[str, Any]] = None
    _CACHE_TIME: float = 0.0
    _DEFAULT_TTL: float = 600.0  # 10 минут между полными вызовами PowerShell WMI/CIM

    def __init__(self, timeout_sec: int = 30, ttl_sec: float = 600.0) -> None:
        """Инициализация сенсора дисков Windows.

        :param timeout_sec: Таймаут сбора данных через PowerShell в секундах (по умолчанию 30с).
        :param ttl_sec: Время жизни кэша снимка в секундах (по умолчанию 600с = 10 мин).
        """
        self.timeout_sec = timeout_sec
        self.ttl_sec = ttl_sec

    @property
    def is_windows(self) -> bool:
        """Проверка, выполняется ли код на платформе Windows."""
        return platform.system().lower() == "windows" or os.name == "nt"

    def run_powershell(self, script: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Выполняет PowerShell-скрипт и разбирает JSON-результат.

        :param script: Текст PowerShell-скрипта.
        :param timeout: Максимальное время выполнения в секундах.
        :return: Декодированный JSON-объект.
        """
        effective_timeout = timeout or self.timeout_sec
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            result = subprocess.run(
                [
                    "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                    "-ExecutionPolicy", "Bypass", "-Command", script,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=effective_timeout,
                creationflags=creationflags,
                check=False,
            )
        except subprocess.TimeoutExpired:
            logger.warning(
                f"PowerShell скрипт сбора хранилища превысил таймаут {effective_timeout} сек."
            )
            return {}

        if result.returncode != 0:
            logger.warning(
                f"PowerShell завершился с кодом {result.returncode}: {result.stderr.strip()}"
            )
            if not result.stdout.strip():
                raise RuntimeError(
                    f"PowerShell завершился с кодом {result.returncode}: {result.stderr.strip()}"
                )

        stdout_clean = result.stdout.strip()
        if not stdout_clean:
            return {}

        try:
            return json.loads(stdout_clean)
        except json.JSONDecodeError as error:
            logger.error(f"Некорректный JSON от PowerShell: {stdout_clean[:500]}")
            raise ValueError(
                f"Некорректный JSON от PowerShell: {stdout_clean[:500]}"
            ) from error

    def collect_snapshot(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Собирает полный доступный снимок Windows Storage с кэшированием (раз в 10 минут).

        :param force_refresh: Принудительное обновление без использования кэша.
        :return: Нормализованный диагностический снимок.
        """
        if not self.is_windows:
            logger.debug("Windows Storage Sensor поддерживается только в среде Windows.")
            return self._empty_snapshot()

        now = time.time()
        if (
            not force_refresh
            and WindowsStorageSensor._CACHE_SNAPSHOT is not None
            and (now - WindowsStorageSensor._CACHE_TIME < self.ttl_sec)
        ):
            return WindowsStorageSensor._CACHE_SNAPSHOT

        logger.info(
            f"Windows Storage Sensor: запуск периодического сбора данных накопителей через Windows CIM/WMI (интервал: {self.ttl_sec / 60:.1f} мин)..."
        )
        try:
            raw_data = self.run_powershell(POWERSHELL_STORAGE_SCRIPT)
        except Exception as ex:
            logger.error(f"Ошибка выполнения скрипта сбора хранилища: {ex}")
            raw_data = {}

        snapshot = self.normalize_snapshot(raw_data)
        WindowsStorageSensor._CACHE_SNAPSHOT = snapshot
        WindowsStorageSensor._CACHE_TIME = now
        return snapshot

    def normalize_snapshot(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Формирует нормализованный снимок диагностических данных.

        :param raw_data: Сырые данные от Windows-провайдеров.
        :return: Структурированный снимок для хранения и анализа.
        """
        def _ensure_list(val: Any) -> List[Any]:
            if val is None:
                return []
            if isinstance(val, list):
                return val
            if isinstance(val, dict):
                return [val]
            return []

        physical_disks = _ensure_list(raw_data.get("physical_disks"))
        physical_storage = _ensure_list(raw_data.get("physical_storage"))
        storage_reliability = _ensure_list(raw_data.get("storage_reliability"))
        event_log = _ensure_list(raw_data.get("event_log"))
        performance_counters = _ensure_list(raw_data.get("performance_counters"))

        snapshot = {
            "schema_version": "1.0",
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
            },
            "sources": {
                "computer_system": _ensure_list(raw_data.get("computer_system")),
                "operating_system": _ensure_list(raw_data.get("operating_system")),
                "physical_disks": physical_disks,
                "disk_partitions": _ensure_list(raw_data.get("disk_partitions")),
                "logical_disks": _ensure_list(raw_data.get("logical_disks")),
                "volumes": _ensure_list(raw_data.get("volumes")),
                "physical_storage": physical_storage,
                "virtual_disks": _ensure_list(raw_data.get("virtual_disks")),
                "storage_pools": _ensure_list(raw_data.get("storage_pools")),
                "disk_drives": _ensure_list(raw_data.get("disk_drives")),
                "partitions": _ensure_list(raw_data.get("partitions")),
                "storage_reliability": storage_reliability,
                "performance_counters": performance_counters,
                "event_log": event_log,
            },
            "summary": {
                "physical_disk_count": len(physical_disks),
                "storage_disk_count": len(physical_storage),
                "reliability_counter_count": len(storage_reliability),
                "event_count": len(event_log),
            },
        }
        return snapshot

    def get_physical_disks(self, force_refresh: bool = False) -> List[StorageDiskHealthInfo]:
        """Извлекает детальные нормализованные сведения о каждом физическом накопителе.

        Объединяет данные Win32_DiskDrive, MSFT_PhysicalDisk и StorageReliabilityCounter.

        :param force_refresh: Принудительное обновление данных.
        :return: Список объектов StorageDiskHealthInfo.
        """
        snapshot = self.collect_snapshot(force_refresh=force_refresh)
        sources = snapshot.get("sources", {})

        storage_disks = sources.get("physical_storage", [])
        wmi_disks = sources.get("physical_disks", [])
        reliabilities = sources.get("storage_reliability", [])

        # Словарь reliability по DeviceId / UniqueId
        reliability_map: Dict[str, Dict[str, Any]] = {}
        for r in reliabilities:
            dev_id = str(r.get("DeviceId", "") or r.get("DeviceID", "") or "")
            if dev_id:
                reliability_map[dev_id] = r

        bus_type_map = {
            0: "Unknown", 1: "SCSI", 2: "ATAPI", 3: "ATA", 4: "1394", 5: "SSA",
            6: "Fibre Channel", 7: "USB", 8: "RAID", 9: "iSCSI", 10: "SAS",
            11: "SATA", 12: "SD", 13: "MMC", 14: "MAX", 15: "File Backed Virtual",
            16: "Storage Spaces", 17: "NVMe", 18: "SCM", 19: "UFS"
        }

        media_type_map = {
            0: "Unspecified", 3: "HDD", 4: "SSD", 5: "SCM"
        }

        health_status_map = {
            0: "Healthy", 1: "Warning", 2: "Unhealthy", 5: "Unknown"
        }

        result_disks: List[StorageDiskHealthInfo] = []

        # 1. Если доступны данные MSFT_PhysicalDisk
        if storage_disks:
            for s_disk in storage_disks:
                dev_id = str(s_disk.get("DeviceId", "") or s_disk.get("DeviceID", "") or "")
                friendly_name = str(s_disk.get("FriendlyName", "") or s_disk.get("Model", "Physical Disk"))
                model = str(s_disk.get("Model", friendly_name))
                serial = str(s_disk.get("SerialNumber", "") or "N/A").strip()
                size_bytes = int(s_disk.get("Size", 0) or 0)
                size_gb = round(size_bytes / (1024**3), 2) if size_bytes else 0.0

                raw_bus = s_disk.get("BusType")
                bus_type = bus_type_map.get(raw_bus, str(raw_bus or "Unknown"))

                raw_media = s_disk.get("MediaType")
                media_type = media_type_map.get(raw_media, "SSD" if "nvme" in model.lower() or "ssd" in model.lower() else "HDD")

                raw_health = s_disk.get("HealthStatus")
                health_str = health_status_map.get(raw_health, "Healthy" if raw_health == 0 else "Warning")

                op_status = str(s_disk.get("OperationalStatus", "OK"))

                rel = reliability_map.get(dev_id, {})
                temp_c = rel.get("Temperature")
                wear = rel.get("Wear")
                poh = rel.get("PowerOnHours")
                read_errors = rel.get("ReadErrorsTotal")
                write_errors = rel.get("WriteErrorsTotal")
                read_latency_max = rel.get("ReadLatencyMax")
                write_latency_max = rel.get("WriteLatencyMax")

                result_disks.append(
                    StorageDiskHealthInfo(
                        device_id=f"Disk{dev_id}" if dev_id else "Disk",
                        friendly_name=friendly_name,
                        model=model,
                        serial_number=serial,
                        bus_type=bus_type,
                        media_type=media_type,
                        size_gb=size_gb,
                        health_status=health_str,
                        operational_status=op_status,
                        temperature_c=float(temp_c) if temp_c is not None else None,
                        wear_percentage=float(wear) if wear is not None else None,
                        power_on_hours=int(poh) if poh is not None else None,
                        read_errors_total=int(read_errors) if read_errors is not None else None,
                        write_errors_total=int(write_errors) if write_errors is not None else None,
                        read_latency_max_ms=float(read_latency_max) if read_latency_max is not None else None,
                        write_latency_max_ms=float(write_latency_max) if write_latency_max is not None else None,
                        raw_storage_data=s_disk,
                    )
                )

        # 2. Фолбэк на Win32_DiskDrive, если MSFT_PhysicalDisk пуст
        elif wmi_disks:
            for w_disk in wmi_disks:
                dev_id = str(w_disk.get("Index", "") or w_disk.get("DeviceID", "Disk"))
                model = str(w_disk.get("Model", "Generic Disk"))
                serial = str(w_disk.get("SerialNumber", "N/A")).strip()
                size_bytes = int(w_disk.get("Size", 0) or 0)
                size_gb = round(size_bytes / (1024**3), 2) if size_bytes else 0.0
                status_str = str(w_disk.get("Status", "OK"))

                rel = reliability_map.get(str(dev_id), {})
                temp_c = rel.get("Temperature")
                wear = rel.get("Wear")
                poh = rel.get("PowerOnHours")

                result_disks.append(
                    StorageDiskHealthInfo(
                        device_id=str(w_disk.get("DeviceID", f"\\\\.\\PHYSICALDRIVE{dev_id}")),
                        friendly_name=model,
                        model=model,
                        serial_number=serial,
                        bus_type=str(w_disk.get("InterfaceType", "WMI")),
                        media_type="SSD" if "ssd" in model.lower() or "nvme" in model.lower() else "HDD",
                        size_gb=size_gb,
                        health_status="Healthy" if status_str.upper() == "OK" else "Warning",
                        operational_status=status_str,
                        temperature_c=float(temp_c) if temp_c is not None else None,
                        wear_percentage=float(wear) if wear is not None else None,
                        power_on_hours=int(poh) if poh is not None else None,
                        raw_storage_data=w_disk,
                    )
                )

        return result_disks

    def _empty_snapshot(self) -> Dict[str, Any]:
        """Возвращает пустой снимок для не-Windows платформ."""
        return {
            "schema_version": "1.0",
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "platform": {"system": platform.system()},
            "sources": {},
            "summary": {
                "physical_disk_count": 0,
                "storage_disk_count": 0,
                "reliability_counter_count": 0,
                "event_count": 0,
            },
        }


def collect_storage_snapshot() -> Dict[str, Any]:
    """Собирает полный снимок Windows Storage через глобальный экземпляр сенсора.

    :return: Нормализованный диагностический снимок.
    """
    sensor = WindowsStorageSensor()
    return sensor.collect_snapshot()


def save_snapshot(snapshot: Dict[str, Any], output_path: Path) -> None:
    """Сохраняет диагностический снимок в UTF-8 JSON файл.

    :param snapshot: Диагностический снимок.
    :param output_path: Путь к выходному JSON-файлу.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info(f"Снимок сохранен: {output_path}")


def main() -> int:
    """Запускает сбор диагностической информации из командной строки.

    :return: Код завершения процесса.
    """
    parser = argparse.ArgumentParser(
        description="Windows Storage Sensor без Smartmontools."
    )
    parser.add_argument(
        "--output", type=Path, default=Path("storage_snapshot.json")
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR")
    )
    arguments = parser.parse_args()

    try:
        snapshot = collect_storage_snapshot()
        save_snapshot(snapshot, arguments.output)
    except Exception as error:
        logger.error(f"Ошибка сбора снимка накопителей: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
