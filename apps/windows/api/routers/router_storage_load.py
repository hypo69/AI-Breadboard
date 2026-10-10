# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Storage Load
# =============================================================================
# Description:
#   GET /api/v1/panel/storage-load — детальные параметры и метрики всех дисков
#   и накопителей (NVMe, SSD, HDD, USB) без жесткого кодирования (Zero-Hardcode):
#   динамическое слияние Windows CIM/WMI (WindowsStorageSensor), LibreHardwareMonitor
#   и системных разделов psutil.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_storage_load import init_router
#     app.include_router(init_router())
#
# File: router_storage_load.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 13:56:00
# =============================================================================

from __future__ import annotations
"""Роутер панели «Параметры накопителей (Диски SSD/HDD/NVMe)»: метрики хранилища."""

import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

try:
    import psutil
except ImportError:
    psutil = None

from logger import logger
from apps.windows.sdk.modules.hardware.lhm_service import LhmService
from apps.windows.sdk.modules.storage_manager.core.windows_storage_sensor import WindowsStorageSensor



class DiskDriveMetric(BaseModel):
    """Метрика физического накопителя (SSD, HDD, NVMe)."""
    id: str = Field(default="", description="Идентификатор накопителя (напр. Disk0)")
    name: str = Field(..., description="Модель или наименование диска")
    media_type: str = Field(default="SSD", description="Тип носителя: NVMe, SSD, HDD, External")
    interface_type: Optional[str] = Field(default=None, description="Интерфейс: SATA, NVMe, USB, PCIe")
    serial_number: Optional[str] = Field(default=None, description="Серийный номер диска")
    health_status: Optional[str] = Field(default="Healthy", description="Состояние здоровья (SMART)")
    total_gb: Optional[float] = Field(default=None, description="Полный объем накопителя, GB")
    used_gb: Optional[float] = Field(default=None, description="Занятый объем, GB")
    free_gb: Optional[float] = Field(default=None, description="Свободный объем, GB")
    used_percent: Optional[float] = Field(default=None, description="Заполненность накопителя, %")
    temperature_c: Optional[float] = Field(default=None, description="Температура накопителя, °C")
    activity_percent: Optional[float] = Field(default=None, description="Общая интенсивность обращений (активность), %")
    read_activity_percent: Optional[float] = Field(default=None, description="Активность чтения, %")
    write_activity_percent: Optional[float] = Field(default=None, description="Активность записи, %")
    read_rate_raw: Optional[str] = Field(default=None, description="Скорость чтения")
    write_rate_raw: Optional[str] = Field(default=None, description="Скорость записи")
    data_written_gb: Optional[float] = Field(default=None, description="Объем записанных данных, GB")
    data_written_raw: Optional[str] = Field(default=None, description="Форматированный объем записанных данных")
    data_read_gb: Optional[float] = Field(default=None, description="Объем прочитанных данных, GB")
    data_read_raw: Optional[str] = Field(default=None, description="Форматированный объем прочитанных данных")
    read_bytes: Optional[int] = Field(default=None, description="Байт прочитано")
    write_bytes: Optional[int] = Field(default=None, description="Байт записано")
    read_count: Optional[int] = Field(default=None, description="Количество операций чтения")
    write_count: Optional[int] = Field(default=None, description="Количество операций записи")
    life_percent: Optional[float] = Field(default=None, description="Остаточный ресурс SSD (Life), %")
    power_on_hours: Optional[float] = Field(default=None, description="Время наработки (Power-on Hours)")
    power_on_count: Optional[float] = Field(default=None, description="Количество циклов включения")
    partitions: List[str] = Field(default_factory=list, description="Связанные буквы дисков / разделы")


class DiskPartitionMetric(BaseModel):
    """Метрика логического диска / раздела."""
    device: str = Field(..., description="Устройство (буква диска, напр. C:\\)")
    mountpoint: str = Field(..., description="Точка монтирования")
    fstype: str = Field(default="", description="Файловая система (NTFS, FAT32)")
    total_gb: float = Field(default=0.0, description="Полный объем раздела, GB")
    used_gb: float = Field(default=0.0, description="Занятый объем раздела, GB")
    free_gb: float = Field(default=0.0, description="Свободный объем раздела, GB")
    used_percent: float = Field(default=0.0, description="Процент заполнения раздела, %")


class StorageSummary(BaseModel):
    """Сводка по всему хранилищу."""
    total_gb: float = Field(default=0.0, description="Суммарный объем всех дисков, GB")
    used_gb: float = Field(default=0.0, description="Суммарно занятый объем, GB")
    free_gb: float = Field(default=0.0, description="Суммарно свободный объем, GB")
    used_percent: float = Field(default=0.0, description="Общий процент занятого пространства, %")
    max_temperature_c: Optional[float] = Field(default=None, description="Максимальная температура среди дисков, °C")
    avg_temperature_c: Optional[float] = Field(default=None, description="Средняя температура дисков, °C")


class StorageLoadResponse(BaseModel):
    """Ответ GET /api/v1/panel/storage-load."""
    status: str = Field(default="ok", description="Статус ответа")
    summary: StorageSummary = Field(default_factory=StorageSummary, description="Общая сводка хранилища")
    drives: List[DiskDriveMetric] = Field(default_factory=list, description="Физические накопители")
    partitions: List[DiskPartitionMetric] = Field(default_factory=list, description="Логические разделы")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные ответа")


def _detect_media_type(name: str) -> str:
    """Определяет тип диска (NVMe, SSD, HDD) по названию модели."""
    n = name.lower()
    if "nvme" in n or "990" in n or "980" in n or "970" in n or "optane" in n:
        return "NVMe"
    if "ssd" in n or "flash" in n or "solid" in n or "crucial" in n:
        return "SSD"
    return "HDD"


def _find_matching_key(drives_map: Dict[str, Dict[str, Any]], name: str) -> Optional[str]:
    """Находит ключ накопителя в словаре по частичному совпадению модели."""
    nl = name.lower().strip()
    for k in drives_map:
        kl = k.lower().strip()
        if nl in kl or kl in nl:
            return k
    return None


def build_storage_load(
    sensors: Optional[List[Dict[str, Any]]] = None,
    physical_disks: Optional[List[Any]] = None,
    partitions_data: Optional[List[Dict[str, Any]]] = None,
) -> StorageLoadResponse:
    """Собирает структурированные данные о всех дисках и разделах без хардкода.

    Args:
        sensors: Список показаний сенсоров LHM.
        physical_disks: Список физических дисков из WindowsStorageSensor (CIM/WMI).
        partitions_data: Опциональный список готовых данных по разделам для тестов.

    Returns:
        StorageLoadResponse: Структура с физическими накопителями и разделами.
    """
    drives_map: Dict[str, Dict[str, Any]] = {}

    # 1. Загрузка физических дисков из WindowsStorageSensor (CIM/WMI)
    if physical_disks:
        for cd in physical_disks:
            m = getattr(cd, "model", None) or getattr(cd, "friendly_name", None) or "Physical Drive"
            dev_id = getattr(cd, "device_id", None) or f"Disk{len(drives_map)}"
            media_type = getattr(cd, "media_type", None)
            detected = _detect_media_type(m)
            if not media_type or media_type.lower() in ("unspecified", "ssd") and detected == "NVMe":
                media_type = "NVMe"
            elif not media_type or media_type.lower() == "unspecified":
                media_type = detected

            temp = getattr(cd, "temperature_c", None)
            if temp is None:
                temp = getattr(cd, "temperature_celsius", None)
            if temp is not None and (temp <= 5 or temp > 120):
                temp = None

            wear = getattr(cd, "wear_percentage", None)
            life = None
            if wear is not None and wear >= 0:
                life = max(0.0, 100.0 - float(wear))

            lifetime_w_tb = getattr(cd, "lifetime_write_tb", None)
            lifetime_r_tb = getattr(cd, "lifetime_read_tb", None)
            lifetime_w_b = getattr(cd, "lifetime_write_bytes", None)
            lifetime_r_b = getattr(cd, "lifetime_read_bytes", None)

            drives_map[m] = {
                "id": dev_id,
                "name": m,
                "media_type": media_type,
                "interface_type": getattr(cd, "interface_type", None) or ("NVMe" if media_type == "NVMe" else "SATA"),
                "serial_number": getattr(cd, "serial_number", None),
                "health_status": getattr(cd, "health_status", "Healthy") or "Healthy",
                "total_gb": round(float(cd.size_gb), 1) if getattr(cd, "size_gb", None) else None,
                "temperature_c": round(float(temp), 1) if temp is not None else None,
                "power_on_hours": round(float(cd.power_on_hours), 0) if getattr(cd, "power_on_hours", None) else None,
                "life_percent": life,
                "data_written_gb": round(float(lifetime_w_tb) * 1024.0, 1) if lifetime_w_tb else None,
                "data_read_gb": round(float(lifetime_r_tb) * 1024.0, 1) if lifetime_r_tb else None,
                "write_bytes": int(lifetime_w_b) if lifetime_w_b else None,
                "read_bytes": int(lifetime_r_b) if lifetime_r_b else None,
                "partitions": [],
            }

    # 2. Обогащение и добавление из сенсоров LibreHardwareMonitor
    if sensors:
        for s in sensors:
            htype = str(s.get("hardware_type", "")).lower()
            if "storage" not in htype and "disk" not in htype and "hdd" not in htype:
                continue

            hname = s.get("hardware_name") or "Storage Drive"
            matched_key = _find_matching_key(drives_map, hname)
            if not matched_key:
                matched_key = hname
                drives_map[matched_key] = {
                    "id": f"drive-{len(drives_map) + 1}",
                    "name": hname,
                    "media_type": _detect_media_type(hname),
                    "partitions": [],
                }

            cat = str(s.get("sensor_category", "")).lower()
            sname = str(s.get("sensor_name", "")).lower()
            val_num = s.get("value_num") if s.get("value_num") is not None else s.get("value_numeric")
            val_raw = s.get("value_raw")

            if "temp" in cat:
                if val_num is not None and val_num > 5:
                    drives_map[matched_key]["temperature_c"] = round(float(val_num), 1)
            elif "load" in cat:
                if "used space" in sname and val_num is not None:
                    drives_map[matched_key]["used_percent"] = round(float(val_num), 1)
                elif "total activity" in sname and val_num is not None:
                    drives_map[matched_key]["activity_percent"] = round(float(val_num), 1)
                elif "read activity" in sname and val_num is not None:
                    drives_map[matched_key]["read_activity_percent"] = round(float(val_num), 1)
                elif "write activity" in sname and val_num is not None:
                    drives_map[matched_key]["write_activity_percent"] = round(float(val_num), 1)
            elif "data" in cat:
                if "total space" in sname and val_num is not None:
                    drives_map[matched_key]["total_gb"] = round(float(val_num), 1)
                elif "free space" in sname and val_num is not None:
                    drives_map[matched_key]["free_gb"] = round(float(val_num), 1)
                elif "data written" in sname and val_num is not None:
                    drives_map[matched_key]["data_written_gb"] = round(float(val_num), 1)
                elif "data read" in sname and val_num is not None:
                    drives_map[matched_key]["data_read_gb"] = round(float(val_num), 1)
            elif "throughput" in cat:
                if "read rate" in sname:
                    drives_map[matched_key]["read_rate_raw"] = str(val_raw or "")
                elif "write rate" in sname:
                    drives_map[matched_key]["write_rate_raw"] = str(val_raw or "")
            elif "levels" in cat:
                if "life" in sname and val_num is not None:
                    drives_map[matched_key]["life_percent"] = round(float(val_num), 1)
            elif "factors" in cat:
                if "power on hours" in sname and val_num is not None:
                    drives_map[matched_key]["power_on_hours"] = round(float(val_num), 0)
                elif "power on count" in sname and val_num is not None:
                    drives_map[matched_key]["power_on_count"] = round(float(val_num), 0)

    # 3. psutil disk_io_counters для операций и байтов чтения/записи
    io_counters = {}
    if psutil is not None:
        try:
            io_counters = psutil.disk_io_counters(perdisk=True) or {}
        except Exception as io_err:
            logger.debug(f"[router_storage_load] Ошибка сбора psutil.disk_io_counters: {io_err}")

    for k, d in drives_map.items():
        dev_id = str(d.get("id", ""))
        digits = re.findall(r"\d+", dev_id)
        if digits:
            phys_key = f"PhysicalDrive{digits[0]}"
            if phys_key in io_counters:
                io_stat = io_counters[phys_key]
                if d.get("read_bytes") is None or d.get("read_bytes") == 0:
                    d["read_bytes"] = io_stat.read_bytes
                if d.get("write_bytes") is None or d.get("write_bytes") == 0:
                    d["write_bytes"] = io_stat.write_bytes
                d["read_count"] = io_stat.read_count
                d["write_count"] = io_stat.write_count

        # Форматирование data_written_raw
        w_gb = d.get("data_written_gb")
        w_b = d.get("write_bytes")
        if w_gb and w_gb > 0:
            if w_gb >= 1000:
                d["data_written_raw"] = f"{w_gb / 1024.0:.2f} TB"
            else:
                d["data_written_raw"] = f"{w_gb:,.0f} GB"
        elif w_b and w_b > 0:
            if w_b >= 1024**4:
                d["data_written_raw"] = f"{w_b / (1024**4):.2f} TB"
            elif w_b >= 1024**3:
                d["data_written_raw"] = f"{w_b / (1024**3):.2f} GB"
            else:
                d["data_written_raw"] = f"{w_b / (1024**2):.1f} MB"

        # Форматирование data_read_raw
        r_gb = d.get("data_read_gb")
        r_b = d.get("read_bytes")
        if r_gb and r_gb > 0:
            if r_gb >= 1000:
                d["data_read_raw"] = f"{r_gb / 1024.0:.2f} TB"
            else:
                d["data_read_raw"] = f"{r_gb:,.0f} GB"
        elif r_b and r_b > 0:
            if r_b >= 1024**4:
                d["data_read_raw"] = f"{r_b / (1024**4):.2f} TB"
            elif r_b >= 1024**3:
                d["data_read_raw"] = f"{r_b / (1024**3):.2f} GB"
            else:
                d["data_read_raw"] = f"{r_b / (1024**2):.1f} MB"

    # 4. Сбор логических разделов
    partitions_list: List[DiskPartitionMetric] = []
    if partitions_data is not None:
        for p in partitions_data:
            if isinstance(p, dict):
                p_dev = p.get("device") or p.get("mountpoint") or ""
                p_mount = p.get("mountpoint") or p.get("device") or ""
                p_fstype = str(p.get("fstype", "") or "")
                p_tot = float(p.get("total_gb", 0.0) or 0.0)
                p_used = float(p.get("used_gb", 0.0) or 0.0)
                p_free = float(p.get("free_gb", 0.0) or 0.0)
                p_pct = float(p.get("used_percent") if p.get("used_percent") is not None else (p.get("percent", 0.0) or 0.0))
                partitions_list.append(
                    DiskPartitionMetric(
                        device=p_dev,
                        mountpoint=p_mount,
                        fstype=p_fstype,
                        total_gb=p_tot,
                        used_gb=p_used,
                        free_gb=p_free,
                        used_percent=round(p_pct, 1),
                    )
                )
            elif isinstance(p, DiskPartitionMetric):
                partitions_list.append(p)
    elif psutil is not None:
        try:
            parts = psutil.disk_partitions(all=False)
            for p in parts:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    tot_gb = round(usage.total / (1024 ** 3), 1)
                    used_gb = round(usage.used / (1024 ** 3), 1)
                    free_gb = round(usage.free / (1024 ** 3), 1)
                    partitions_list.append(
                        DiskPartitionMetric(
                            device=p.device,
                            mountpoint=p.mountpoint,
                            fstype=p.fstype,
                            total_gb=tot_gb,
                            used_gb=used_gb,
                            free_gb=free_gb,
                            used_percent=round(usage.percent, 1),
                        )
                    )
                except Exception:
                    continue
        except Exception as exc:
            logger.debug(f"[router_storage_load] Ошибка сбора разделов через psutil: {exc}")

    # 4. Довычисляем used_gb / used_percent для физических дисков
    drives_list: List[DiskDriveMetric] = []
    for d in drives_map.values():
        tot = d.get("total_gb")
        free = d.get("free_gb")
        if tot is not None and free is not None and "used_gb" not in d:
            d["used_gb"] = round(max(tot - free, 0.0), 1)
        if tot is not None and d.get("used_gb") is not None and d.get("used_percent") is None:
            if tot > 0:
                d["used_percent"] = round((d["used_gb"] / tot) * 100.0, 1)

        # Если диск не получил used_percent из LHM, ищем соответствующий раздел по объему
        if d.get("used_percent") is None and tot is not None and partitions_list:
            for part in partitions_list:
                if abs(part.total_gb - tot) <= 5.0:  # совпадение объема раздела и диска
                    d["used_percent"] = part.used_percent
                    d["used_gb"] = part.used_gb
                    d["free_gb"] = part.free_gb
                    break

        drives_list.append(DiskDriveMetric(**d))

    # 5. Расчет суммарной сводки по хранилищу
    if partitions_list:
        sum_total = sum(p.total_gb for p in partitions_list)
        sum_used = sum(p.used_gb for p in partitions_list)
        sum_free = sum(p.free_gb for p in partitions_list)
    elif drives_list:
        sum_total = sum(d.total_gb for d in drives_list if d.total_gb is not None)
        sum_used = sum(d.used_gb for d in drives_list if d.used_gb is not None)
        sum_free = sum(d.free_gb for d in drives_list if d.free_gb is not None)
    else:
        sum_total = 0.0
        sum_used = 0.0
        sum_free = 0.0

    sum_pct = round((sum_used / sum_total * 100.0), 1) if sum_total > 0 else 0.0

    temps = [d.temperature_c for d in drives_list if d.temperature_c is not None]
    max_temp = max(temps) if temps else None
    avg_temp = round(sum(temps) / len(temps), 1) if temps else None

    summary = StorageSummary(
        total_gb=round(sum_total, 1),
        used_gb=round(sum_used, 1),
        free_gb=round(sum_free, 1),
        used_percent=sum_pct,
        max_temperature_c=max_temp,
        avg_temperature_c=avg_temp,
    )

    return StorageLoadResponse(
        summary=summary,
        drives=drives_list,
        partitions=partitions_list,
        meta={
            "drives_count": len(drives_list),
            "partitions_count": len(partitions_list),
            "source": "cim+lhm+psutil",
        },
    )


def init_router(
    lhm_service: Optional[LhmService] = None,
    storage_sensor: Optional[WindowsStorageSensor] = None,
) -> APIRouter:
    """Создаёт роутер /api/v1/panel/storage-load.

    Args:
        lhm_service: Сервис LibreHardwareMonitor.
        storage_sensor: Сенсор дисков WindowsStorageSensor (CIM/WMI).

    Returns:
        APIRouter: Роутер с эндпоинтом GET /api/v1/panel/storage-load.
    """
    router = APIRouter(tags=["Storage Load Panel"])
    lhm = lhm_service or LhmService()

    @router.get("/api/v1/panel/storage-load", response_model=StorageLoadResponse)
    async def get_panel_storage_load() -> StorageLoadResponse:
        """Возвращает детальную загрузку, температуру и емкость всех накопителей из телеметрии БД."""
        try:
            sensors = lhm.get_flattened_sensors() if lhm.is_running() else []
            physical_disks: List[Any] = []
            partitions_data: Optional[List[Dict[str, Any]]] = None

            # 1. Попытка прочитать актуальные данные дисков из SQLite телеметрии
            try:
                from apps.windows.telemetry.sqlite import TelemetryStorage
                storage = TelemetryStorage.get_instance(read_only=True)
                storage_data = storage.get_latest_storage_data()
                if storage_data.get("physical_disks"):
                    physical_disks = storage_data["physical_disks"]
                if storage_data.get("partitions"):
                    partitions_data = storage_data["partitions"]
            except Exception as db_err:
                logger.debug(f"[router_storage_load] Не удалось прочитать накопители из SQLite: {db_err}")

            # 2. Fallback при отсутствии снимков в базе данных (без живого вызова WMI/CIM в tc.ps1)
            if not physical_disks:
                from apps.windows.telemetry.collector import SystemCollector
                collector = SystemCollector()
                physical_disks = collector.get_physical_disks_health(force=False)

            return build_storage_load(
                sensors=sensors,
                physical_disks=physical_disks,
                partitions_data=partitions_data,
            )
        except Exception as exc:
            logger.error(f"[router_storage_load] Ошибка опроса накопителей: {exc}", exc_info=True)
            return build_storage_load(sensors=[], physical_disks=[])

    return router


__all__ = [
    "init_router",
    "build_storage_load",
    "DiskDriveMetric",
    "DiskPartitionMetric",
    "StorageSummary",
    "StorageLoadResponse",
]
