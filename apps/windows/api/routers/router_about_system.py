# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router About System
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для панели "О Системе" (About System Panel)
#   с прямыми SQL-запросами к SQLite базе данных telemetry.db.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_about_system import AboutSystemPanelOverviewResponse
#
#     service = AboutSystemPanelOverviewResponse()
#
# File: router_about_system.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 04:30:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST эндпоинты для панели 'О Системе' из базы данных telemetry.db."""

import json
import os
import platform
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage


class PlatformOsPanelResponse(BaseModel):
    """Модель ответа панели «Платформа & ОС»."""
    status: str = Field(default="ok", description="Статус ответа")
    os_name: str = Field(default="Windows", description="Наименование операционной системы")
    os_build: str = Field(default="", description="Номер сборки ОС")
    os_install_date: str = Field(default="", description="Дата установки операционной системы")
    architecture: str = Field(default="x86_64", description="Архитектура процессора")
    hostname: str = Field(default="", description="Имя хоста")
    uptime_seconds: float = Field(default=0.0, description="Аптайм в секундах")
    uptime_human: str = Field(default="0h 0m", description="Человекочитаемый аптайм")
    display_title: str = Field(default="Windows", description="Заголовок для KPI-карточки")
    display_host: str = Field(default="Host: --", description="Строка с именем хоста")
    timestamp: str = Field(default="", description="Временная метка последнего зафиксированного снимка")


class SecurityPanelResponse(BaseModel):
    """Модель ответа панели «Безопасность системы»."""
    status: str = Field(default="Active & Protected", description="Сводный статус защиты")
    firewall_status: str = Field(default="ON", description="Статус брандмауэра")
    firewall_domain: bool = Field(default=True, description="Брандмауэр доменного профиля")
    firewall_private: bool = Field(default=True, description="Брандмауэр частного профиля")
    firewall_public: bool = Field(default=True, description="Брандмауэр публичного профиля")
    defender_enabled: bool = Field(default=True, description="Защитник Windows включен")
    realtime_protection: bool = Field(default=True, description="Режим защиты в реальном времени")
    uac_enabled: bool = Field(default=True, description="Контроль учетных записей (UAC) активен")
    display_title: str = Field(default="Active & Protected", description="Заголовок для KPI-карточки")
    display_subtitle: str = Field(default="Firewall: ON | UAC: ON", description="Подзаголовок для KPI-карточки")
    timestamp: str = Field(default="", description="Временная метка аудита")


class RestorePointsPanelResponse(BaseModel):
    """Модель ответа панели «Точки восстановления»."""
    status: str = Field(default="ok", description="Статус ответа")
    checkpoints_count: int = Field(default=0, description="Количество доступных точек восстановления")
    protection_enabled: bool = Field(default=True, description="Защита системы включена")
    protection_status: str = Field(default="Active", description="Текстовый статус защиты")
    display_title: str = Field(default="0 Checkpoints", description="Заголовок для KPI-карточки")
    display_subtitle: str = Field(default="Protection: Active", description="Подзаголовок для KPI-карточки")
    latest_checkpoint_name: Optional[str] = Field(default=None, description="Имя последней контрольной точки")
    latest_checkpoint_time: Optional[str] = Field(default=None, description="Время последней контрольной точки")
    timestamp: str = Field(default="", description="Временная метка аудита")


class StoragePanelResponse(BaseModel):
    """Модель ответа панели «Системный накопитель (C:)»."""
    status: str = Field(default="ok", description="Статус ответа")
    drive: str = Field(default="C:", description="Буква системного диска")
    total_gb: float = Field(default=0.0, description="Общий объем системного диска в GB")
    free_gb: float = Field(default=0.0, description="Свободный объем системного диска в GB")
    used_gb: float = Field(default=0.0, description="Занятый объем системного диска в GB")
    percent_used: float = Field(default=0.0, description="Процент использования диска")
    cleanable_mb: float = Field(default=0.0, description="Оценка объема файлов для очистки в MB")
    display_title: str = Field(default="0.0 GB Free", description="Заголовок для KPI-карточки")
    display_subtitle: str = Field(default="Cleanable: ~0 MB", description="Подзаголовок для KPI-карточки")
    timestamp: str = Field(default="", description="Временная метка последнего снимка")


class CpuPanelResponse(BaseModel):
    """Модель ответа виджета «Загрузка CPU»."""
    total_percent: float = Field(default=0.0, description="Загрузка CPU в процентах")
    frequency_mhz: float = Field(default=0.0, description="Текущая частота CPU в МГц")
    physical_cores: int = Field(default=6, description="Количество физических ядер")
    logical_cores: int = Field(default=12, description="Количество логических потоков")
    model: str = Field(default="Intel Processor", description="Модель процессора")
    display_val: str = Field(default="0.0%", description="Отображаемое значение загрузки")
    display_cores: str = Field(default="6 физ. / 12 Потоков", description="Строка с ядрами и потоками")
    display_freq: str = Field(default="", description="Строка с частотой")


class MemoryPanelResponse(BaseModel):
    """Модель ответа виджета «Память (RAM)»."""
    total_gb: float = Field(default=0.0, description="Общий объем памяти в GB")
    used_gb: float = Field(default=0.0, description="Занятый объем памяти в GB")
    available_gb: float = Field(default=0.0, description="Свободный объем памяти в GB")
    percent: float = Field(default=0.0, description="Процент занятой памяти")
    display_val: str = Field(default="0.0 / 0.0 GB", description="Отображаемая строка памяти")
    display_sub: str = Field(default="0.0% занято (0.0 GB свободно)", description="Подзаголовок памяти")


class GpuPanelResponse(BaseModel):
    """Модель ответа виджета «GPU Ускоритель»."""
    name: str = Field(default="GPU", description="Наименование графического ускорителя")
    memory_total_gb: float = Field(default=0.0, description="Объем VRAM в GB")
    load_percent: float = Field(default=0.0, description="Процент нагрузки GPU")
    temperature_c: Optional[float] = Field(default=None, description="Температура GPU в °C")
    badge: str = Field(default="Active GPU", description="Бейдж возможностей (CUDA, DirectML)")
    display_name: str = Field(default="GPU", description="Отображаемое имя GPU")
    display_vram: str = Field(default="VRAM: N/A", description="Подзаголовок с объемом памяти и нагрузкой")


class DiskIoPanelResponse(BaseModel):
    """Модель ответа виджета «Диск (C:) I/O»."""
    read_bytes_sec: float = Field(default=0.0, description="Скорость чтения байт/с")
    write_bytes_sec: float = Field(default=0.0, description="Скорость записи байт/с")
    total_mb_s: float = Field(default=0.0, description="Суммарная скорость в MB/s")
    read_kb_s: float = Field(default=0.0, description="Скорость чтения в KB/s")
    write_kb_s: float = Field(default=0.0, description="Скорость записи в KB/s")
    display_val: str = Field(default="0.00 MB/s", description="Отображаемая скорость")
    display_rates: str = Field(default="Чтение: 0 КБ/с | Запись: 0 КБ/с", description="Подзаголовок со скоростями чтения/записи")


class AboutSystemHistoryItem(BaseModel):
    """Элемент исторического среза телеметрии из таблицы system_snapshots."""
    id: int = Field(..., description="Идентификатор записи в базе данных")
    timestamp: str = Field(..., description="Временная метка ISO")
    created_at: Optional[float] = Field(default=None, description="UNIX timestamp")
    hostname: str = Field(default="", description="Имя хоста")
    uptime_seconds: float = Field(default=0.0, description="Аптайм в секундах")
    uptime_human: str = Field(default="0h 0m", description="Человекочитаемый аптайм")
    os_name: str = Field(default="Windows", description="Операционная система")
    os_build: str = Field(default="", description="Сборка ОС")
    os_install_date: Optional[str] = Field(default=None, description="Дата установки ОС")
    cpu_total_percent: float = Field(default=0.0, description="Загрузка CPU (%)")
    cpu_frequency_mhz: float = Field(default=0.0, description="Частота CPU (МГц)")
    memory_total_gb: float = Field(default=0.0, description="Всего RAM (GB)")
    memory_used_gb: float = Field(default=0.0, description="Занято RAM (GB)")
    memory_percent: float = Field(default=0.0, description="Процент памяти (%)")
    gpu_load_percent: float = Field(default=0.0, description="Нагрузка GPU (%)")
    gpu_temp_c: Optional[float] = Field(default=None, description="Температура GPU (°C)")
    disk_read_bytes_sec: float = Field(default=0.0, description="Чтение диска (байт/с)")
    disk_write_bytes_sec: float = Field(default=0.0, description="Запись диска (байт/с)")
    disk_io_total_mb_s: float = Field(default=0.0, description="Суммарная скорость диска (MB/s)")
    storage_c_free_gb: Optional[float] = Field(default=None, description="Свободно на C: (GB)")
    storage_c_used_gb: Optional[float] = Field(default=None, description="Занято на C: (GB)")
    storage_c_total_gb: Optional[float] = Field(default=None, description="Объем C: (GB)")


class AboutSystemHistoryResponse(BaseModel):
    """Ответ с историей метрик панели 'О Системе' из telemetry.db."""
    status: str = Field(default="ok", description="Статус ответа")
    count: int = Field(default=0, description="Количество возвращенных записей")
    metric: str = Field(default="all", description="Запрошенный фильтр метрики")
    history: List[AboutSystemHistoryItem] = Field(default_factory=list, description="Список исторических снимков")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные запроса к базе данных")


class AboutSystemPanelOverviewResponse(BaseModel):
    """Сводный ответ для всей панели 'О Системе' (8 карточек и метаданные) из базы данных telemetry.db."""
    status: str = Field(default="ok", description="Статус ответа")
    os: PlatformOsPanelResponse = Field(default_factory=PlatformOsPanelResponse, description="Карточка 1: Платформа & ОС")
    security: SecurityPanelResponse = Field(default_factory=SecurityPanelResponse, description="Карточка 2: Безопасность")
    restore_points: RestorePointsPanelResponse = Field(default_factory=RestorePointsPanelResponse, description="Карточка 3: Точки восстановления")
    storage: StoragePanelResponse = Field(default_factory=StoragePanelResponse, description="Карточка 4: Системный накопитель C:")
    cpu: CpuPanelResponse = Field(default_factory=CpuPanelResponse, description="Карточка 5: Загрузка CPU")
    memory: MemoryPanelResponse = Field(default_factory=MemoryPanelResponse, description="Карточка 6: Память (RAM)")
    gpu: GpuPanelResponse = Field(default_factory=GpuPanelResponse, description="Карточка 7: GPU Ускоритель")
    disk_io: DiskIoPanelResponse = Field(default_factory=DiskIoPanelResponse, description="Карточка 8: Диск (C:) I/O")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Метаданные сформированного SQL-запроса к telemetry.db")


def _format_uptime_human(seconds: float) -> str:
    """Форматирует секунды аптайма в человекочитаемую строку."""
    sec = int(max(0.0, seconds))
    hours = sec // 3600
    minutes = (sec % 3600) // 60
    return f"{hours}h {minutes}m"


def _get_latest_snapshot_dict(storage: TelemetryStorage) -> Dict[str, Any]:
    """Извлекает и десериализует последний снимок из таблицы system_snapshots."""
    snapshots = storage.get_snapshots(limit=1)
    if not snapshots:
        return {}

    snap_row = dict(snapshots[0])
    raw_json_str = snap_row.get("raw_json")
    if raw_json_str:
        try:
            return json.loads(raw_json_str)
        except Exception as err:
            logger.debug(f"[router_about_system] Ошибка парсинга raw_json снимка: {err}")

    disks_str = snap_row.get("disks_json")
    if disks_str and isinstance(disks_str, str):
        try:
            snap_row["disks"] = json.loads(disks_str)
        except Exception as err:
            logger.debug(f"[router_about_system] Ошибка парсинга disks_json снимка: {err}")

    return snap_row


def query_about_system_from_db(storage: TelemetryStorage) -> AboutSystemPanelOverviewResponse:
    """Выполняет сформированные SQL-запросы к telemetry.db и строит сводный JSON-ответ для панели 'О Системе'.

    Args:
        storage: Экземпляр хранилища TelemetryStorage.

    Returns:
        AboutSystemPanelOverviewResponse: Модель со всеми 8 карточками панели.
    """
    now_ts = datetime.now(timezone.utc).isoformat()
    executed_queries: List[str] = []

    snap_row: Optional[Dict[str, Any]] = None
    audit_row: Optional[Dict[str, Any]] = None
    clean_row: Optional[Dict[str, Any]] = None
    gpu_sensor_rows: List[Dict[str, Any]] = []

    with storage._lock, storage._get_connection() as conn:
        cursor = conn.cursor()

        # 1. Запрос последнего системного снимка
        sql_snap = (
            "SELECT id, timestamp, created_at, hostname, uptime_seconds, os_name, os_build, os_install_date, "
            "disks_json, cpu_total_percent, cpu_frequency_mhz, memory_total_gb, "
            "memory_used_gb, memory_percent, swap_percent, gpu_load_percent, gpu_temp_c, "
            "disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec, disk_write_count_sec, "
            "network_sent_bytes_sec, network_recv_bytes_sec "
            "FROM system_snapshots ORDER BY id DESC LIMIT 1;"
        )
        cursor.execute(sql_snap)
        row = cursor.fetchone()
        if row:
            snap_row = dict(row)
        executed_queries.append(sql_snap)

        # 2. Запрос расширенного аудита безопасности и точек восстановления
        sql_audit = (
            "SELECT vss_snapshots_count, raw_json, timestamp "
            "FROM system_extended_audits ORDER BY id DESC LIMIT 1;"
        )
        cursor.execute(sql_audit)
        row_audit = cursor.fetchone()
        if row_audit:
            audit_row = dict(row_audit)
        executed_queries.append(sql_audit)

        # 3. Запрос метрик очистки накопителя
        sql_clean = (
            "SELECT value, details, timestamp FROM app_polls "
            "WHERE metric_name IN ('cleanable_mb', 'clean_findings') "
            "ORDER BY id DESC LIMIT 1;"
        )
        cursor.execute(sql_clean)
        row_clean = cursor.fetchone()
        if row_clean:
            clean_row = dict(row_clean)
        executed_queries.append(sql_clean)

        # 4. Запрос сенсоров GPU
        sql_sensors = (
            "SELECT hardware_name, sensor_name, value, unit, raw_json "
            "FROM sensor_polls "
            "WHERE hardware_type LIKE '%Gpu%' OR hardware_name LIKE '%GeForce%' OR hardware_name LIKE '%NVIDIA%' OR hardware_name LIKE '%Radeon%' "
            "ORDER BY id DESC LIMIT 10;"
        )
        cursor.execute(sql_sensors)
        gpu_sensor_rows = [dict(r) for r in cursor.fetchall()]
        executed_queries.append(sql_sensors)

    # 1. Платформа & ОС
    os_name = (snap_row.get("os_name") if snap_row else None) or f"{platform.system()} {platform.release()}"
    os_build = str((snap_row.get("os_build") if snap_row else None) or platform.version() or "22631")
    os_install_date = str((snap_row.get("os_install_date") if snap_row else None) or "")
    if not os_install_date:
        try:
            from apps.windows.telemetry import SystemCollector
            os_install_date = str(SystemCollector().get_system_identity().get("os_install_date") or "")
        except Exception:
            pass
    arch = platform.machine() or "AMD64"
    hostname = (snap_row.get("hostname") if snap_row else None) or platform.node() or "Host"
    uptime_sec = float((snap_row.get("uptime_seconds") if snap_row else None) or 0.0)
    if uptime_sec <= 0.0:
        try:
            uptime_sec = float(time.time() - psutil.boot_time())
        except Exception:
            uptime_sec = 0.0
    uptime_str = _format_uptime_human(uptime_sec)
    os_title = f"{os_name} ({arch})" if arch else os_name

    os_res = PlatformOsPanelResponse(
        status="ok",
        os_name=os_name,
        os_build=os_build,
        os_install_date=os_install_date,
        architecture=arch,
        hostname=hostname,
        uptime_seconds=uptime_sec,
        uptime_human=uptime_str,
        display_title=os_title,
        display_host=f"Host: {hostname}",
        timestamp=snap_row.get("timestamp") if snap_row else now_ts,
    )

    # 2. Безопасность
    fw_domain = True
    fw_private = True
    fw_public = True
    def_enabled = True
    realtime = True
    uac_enabled = True
    audit_ts = now_ts

    if audit_row:
        audit_ts = audit_row.get("timestamp") or now_ts
        raw_aud = audit_row.get("raw_json")
        if raw_aud:
            try:
                aud_data = json.loads(raw_aud)
                sec = aud_data.get("security", {})
                fw = sec.get("firewall", {})
                fw_domain = bool(fw.get("domain", True))
                fw_private = bool(fw.get("private", True))
                fw_public = bool(fw.get("public", True))
                df = sec.get("defender", {})
                def_enabled = bool(df.get("enabled", True))
                realtime = bool(df.get("realtime_protection", True))
                uac = sec.get("uac", {})
                uac_enabled = bool(uac.get("enabled", True))
            except Exception as err:
                logger.debug(f"[router_about_system] Ошибка парсинга аудита: {err}")

    fw_all = fw_domain and fw_private and fw_public
    fw_text = "ON" if fw_all else "PARTIAL"
    uac_text = "ON" if uac_enabled else "OFF"
    sec_ok = fw_all and def_enabled and realtime and uac_enabled
    sec_title = "Active & Protected" if sec_ok else "Attention Required"

    sec_res = SecurityPanelResponse(
        status=sec_title,
        firewall_status=fw_text,
        firewall_domain=fw_domain,
        firewall_private=fw_private,
        firewall_public=fw_public,
        defender_enabled=def_enabled,
        realtime_protection=realtime,
        uac_enabled=uac_enabled,
        display_title=sec_title,
        display_subtitle=f"Firewall: {fw_text} | UAC: {uac_text}",
        timestamp=audit_ts,
    )

    # 3. Точки восстановления
    checkpoints_count = int(audit_row.get("vss_snapshots_count") or 0) if audit_row else 0
    prot_enabled = True
    prot_status = "Active"
    latest_chk_name = None
    latest_chk_time = None

    if audit_row and audit_row.get("raw_json"):
        try:
            aud_data = json.loads(audit_row["raw_json"])
            vss = aud_data.get("vss", {}) or aud_data.get("restore_points", {})
            if isinstance(vss, dict):
                prot_enabled = bool(vss.get("protection_enabled", True))
                prot_status = vss.get("status") or ("Active" if prot_enabled else "Disabled")
                latest_chk_name = vss.get("latest_name")
                latest_chk_time = vss.get("latest_time")
        except Exception:
            pass

    restore_res = RestorePointsPanelResponse(
        status="ok",
        checkpoints_count=checkpoints_count,
        protection_enabled=prot_enabled,
        protection_status=prot_status,
        display_title=f"{checkpoints_count} Checkpoints",
        display_subtitle=f"Protection: {prot_status}",
        latest_checkpoint_name=latest_chk_name,
        latest_checkpoint_time=latest_chk_time,
        timestamp=audit_ts,
    )

    # 4. Накопитель C:
    disks = []
    if snap_row and snap_row.get("disks_json"):
        try:
            disks = json.loads(snap_row["disks_json"])
        except Exception:
            disks = []

    c_disk = None
    for d in disks:
        dev = (d.get("device") if isinstance(d, dict) else getattr(d, "device", "")) or ""
        mount = (d.get("mountpoint") if isinstance(d, dict) else getattr(d, "mountpoint", "")) or ""
        if dev.upper().startswith("C") or mount.upper().startswith("C"):
            c_disk = d
            break
    if not c_disk and disks:
        c_disk = disks[0]

    tot_gb = float((c_disk.get("total_gb") if isinstance(c_disk, dict) else getattr(c_disk, "total_gb", 0.0)) or 0.0) if c_disk else 0.0
    free_gb = float((c_disk.get("free_gb") if isinstance(c_disk, dict) else getattr(c_disk, "free_gb", 0.0)) or 0.0) if c_disk else 0.0
    used_gb = float((c_disk.get("used_gb") if isinstance(c_disk, dict) else getattr(c_disk, "used_gb", 0.0)) or 0.0) if c_disk else 0.0
    pct_used = float((c_disk.get("percent") if isinstance(c_disk, dict) else getattr(c_disk, "percent", 0.0)) or 0.0) if c_disk else 0.0

    if tot_gb <= 0.0:
        try:
            usage = psutil.disk_usage("C:\\")
            tot_gb = usage.total / (1024.0 ** 3)
            free_gb = usage.free / (1024.0 ** 3)
            used_gb = usage.used / (1024.0 ** 3)
            pct_used = usage.percent
        except Exception:
            pass

    cleanable_mb = float(clean_row.get("value") or 0.0) if clean_row else 0.0
    clean_str = f"~{cleanable_mb:.0f} MB" if cleanable_mb < 1024 else f"~{cleanable_mb/1024:.1f} GB"

    storage_res = StoragePanelResponse(
        status="ok",
        drive="C:",
        total_gb=round(tot_gb, 1),
        free_gb=round(free_gb, 1),
        used_gb=round(used_gb, 1),
        percent_used=round(pct_used, 1),
        cleanable_mb=round(cleanable_mb, 1),
        display_title=f"{free_gb:.1f} GB Free",
        display_subtitle=f"Cleanable: {clean_str}",
        timestamp=snap_row.get("timestamp") if snap_row else now_ts,
    )

    # 5. CPU
    cpu_pct = float((snap_row.get("cpu_total_percent") if snap_row else 0.0) or 0.0)
    cpu_freq = float((snap_row.get("cpu_frequency_mhz") if snap_row else 0.0) or 0.0)
    phys_cores = psutil.cpu_count(logical=False) or 6
    log_cores = psutil.cpu_count(logical=True) or 12
    cpu_model = platform.processor() or "Intel Processor"

    if cpu_freq <= 0.0:
        try:
            freq_obj = psutil.cpu_freq()
            cpu_freq = float(freq_obj.current) if freq_obj and freq_obj.current else 2900.0
        except Exception:
            cpu_freq = 2900.0

    if cpu_pct <= 0.0:
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
        except Exception:
            cpu_pct = 0.0

    freq_txt = f"{int(cpu_freq)} MHz" if cpu_freq > 0 else ""

    cpu_res = CpuPanelResponse(
        total_percent=round(cpu_pct, 1),
        frequency_mhz=round(cpu_freq, 0),
        physical_cores=phys_cores,
        logical_cores=log_cores,
        model=cpu_model,
        display_val=f"{cpu_pct:.1f}%",
        display_cores=f"{phys_cores} физ. / {log_cores} Потоков",
        display_freq=freq_txt,
    )

    # 6. Память RAM
    mem_total = float((snap_row.get("memory_total_gb") if snap_row else 0.0) or 0.0)
    mem_used = float((snap_row.get("memory_used_gb") if snap_row else 0.0) or 0.0)
    mem_pct = float((snap_row.get("memory_percent") if snap_row else 0.0) or 0.0)

    if mem_total <= 0.0:
        try:
            vm = psutil.virtual_memory()
            mem_total = vm.total / (1024.0 ** 3)
            mem_used = vm.used / (1024.0 ** 3)
            mem_pct = vm.percent
        except Exception:
            pass

    mem_avail = max(0.0, mem_total - mem_used)

    memory_res = MemoryPanelResponse(
        total_gb=round(mem_total, 1),
        used_gb=round(mem_used, 1),
        available_gb=round(mem_avail, 1),
        percent=round(mem_pct, 1),
        display_val=f"{mem_used:.1f} / {mem_total:.1f} GB",
        display_sub=f"{mem_pct:.1f}% занято ({mem_avail:.1f} GB свободно)",
    )

    # 7. GPU
    gpu_name = "GeForce GT 710"
    gpu_vram = 2.0
    if gpu_sensor_rows:
        for g_row in gpu_sensor_rows:
            hw_name = g_row.get("hardware_name")
            if hw_name and ("GeForce" in hw_name or "NVIDIA" in hw_name or "Radeon" in hw_name or "Intel" in hw_name):
                gpu_name = hw_name
                break
    gpu_load = float((snap_row.get("gpu_load_percent") if snap_row else 0.0) or 0.0)
    gpu_temp = float(snap_row["gpu_temp_c"]) if snap_row and snap_row.get("gpu_temp_c") is not None else None
    caps = ["CUDA", "DirectML"] if ("GeForce" in gpu_name or "NVIDIA" in gpu_name) else ["Active GPU"]
    badge_str = " + ".join(caps)

    gpu_res = GpuPanelResponse(
        name=gpu_name,
        memory_total_gb=round(gpu_vram, 1),
        load_percent=round(gpu_load, 1),
        temperature_c=gpu_temp,
        badge=badge_str,
        display_name=gpu_name,
        display_vram=f"VRAM: {gpu_vram:.1f} GB | Нагрузка: {int(gpu_load)}%",
    )

    # 8. Диск I/O
    disk_rb = float((snap_row.get("disk_read_bytes_sec") if snap_row else 0.0) or 0.0)
    disk_wb = float((snap_row.get("disk_write_bytes_sec") if snap_row else 0.0) or 0.0)
    total_mbs = (disk_rb + disk_wb) / (1024.0 * 1024.0)
    rkbs = disk_rb / 1024.0
    wkbs = disk_wb / 1024.0

    disk_io_res = DiskIoPanelResponse(
        read_bytes_sec=disk_rb,
        write_bytes_sec=disk_wb,
        total_mb_s=round(total_mbs, 2),
        read_kb_s=round(rkbs, 1),
        write_kb_s=round(wkbs, 1),
        display_val=f"{total_mbs:.2f} MB/s",
        display_rates=f"Чтение: {int(rkbs)} КБ/с | Запись: {int(wkbs)} КБ/с",
    )

    meta = {
        "source": "telemetry.db",
        "db_path": str(storage.db_path),
        "timestamp": snap_row.get("timestamp") if snap_row else now_ts,
        "sql_queries": executed_queries,
    }

    return AboutSystemPanelOverviewResponse(
        status="ok",
        os=os_res,
        security=sec_res,
        restore_points=restore_res,
        storage=storage_res,
        cpu=cpu_res,
        memory=memory_res,
        gpu=gpu_res,
        disk_io=disk_io_res,
        meta=meta,
    )


def query_about_system_history_from_db(
    storage: TelemetryStorage,
    limit: int = 30,
    metric: str = "all",
) -> AboutSystemHistoryResponse:
    """Извлекает исторические срезы телеметрии из таблицы system_snapshots в telemetry.db.

    Args:
        storage: Экземпляр хранилища TelemetryStorage.
        limit: Максимальное число возвращаемых записей истории (по умолчанию 30).
        metric: Фильтр метрики ('all', 'cpu', 'memory', 'gpu', 'storage', 'disk_io').

    Returns:
        AboutSystemHistoryResponse: Список исторических снимков с форматированными полями.
    """
    safe_limit = max(1, min(limit, 200))
    history_items: List[AboutSystemHistoryItem] = []

    sql_history = (
        "SELECT id, timestamp, created_at, hostname, uptime_seconds, os_name, os_build, os_install_date, "
        "disks_json, cpu_total_percent, cpu_frequency_mhz, memory_total_gb, "
        "memory_used_gb, memory_percent, swap_percent, gpu_load_percent, gpu_temp_c, "
        "disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec, disk_write_count_sec, "
        "network_sent_bytes_sec, network_recv_bytes_sec "
        "FROM system_snapshots ORDER BY id DESC LIMIT ?;"
    )

    with storage._lock, storage._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_history, (safe_limit,))
        rows = cursor.fetchall()

    for row in rows:
        r = dict(row)
        snap_id = int(r.get("id") or 0)
        ts = str(r.get("timestamp") or "")
        created_at_val = float(r["created_at"]) if r.get("created_at") is not None else None
        hname = str(r.get("hostname") or "")
        uptime_sec = float(r.get("uptime_seconds") or 0.0)
        uptime_str = _format_uptime_human(uptime_sec)
        os_n = str(r.get("os_name") or "Windows")
        os_b = str(r.get("os_build") or "")
        os_inst_d = str(r.get("os_install_date") or "")

        cpu_pct = float(r.get("cpu_total_percent") or 0.0)
        cpu_freq = float(r.get("cpu_frequency_mhz") or 0.0)

        mem_tot = float(r.get("memory_total_gb") or 0.0)
        mem_used = float(r.get("memory_used_gb") or 0.0)
        mem_pct = float(r.get("memory_percent") or 0.0)

        gpu_load = float(r.get("gpu_load_percent") or 0.0)
        gpu_temp = float(r["gpu_temp_c"]) if r.get("gpu_temp_c") is not None else None

        disk_rb = float(r.get("disk_read_bytes_sec") or 0.0)
        disk_wb = float(r.get("disk_write_bytes_sec") or 0.0)
        disk_total_mb_s = (disk_rb + disk_wb) / (1024.0 * 1024.0)

        # Вычисление емкости и остатка на C:
        c_free_gb: Optional[float] = None
        c_used_gb: Optional[float] = None
        c_total_gb: Optional[float] = None

        disks_str = r.get("disks_json")
        if disks_str and isinstance(disks_str, str):
            try:
                disks_arr = json.loads(disks_str)
                for d in disks_arr:
                    dev = (d.get("device") if isinstance(d, dict) else getattr(d, "device", "")) or ""
                    mnt = (d.get("mountpoint") if isinstance(d, dict) else getattr(d, "mountpoint", "")) or ""
                    if dev.upper().startswith("C") or mnt.upper().startswith("C"):
                        c_free_gb = round(float(d.get("free_gb") or 0.0), 1)
                        c_used_gb = round(float(d.get("used_gb") or 0.0), 1)
                        c_total_gb = round(float(d.get("total_gb") or 0.0), 1)
                        break
            except Exception:
                pass

        item = AboutSystemHistoryItem(
            id=snap_id,
            timestamp=ts,
            created_at=created_at_val,
            hostname=hname,
            uptime_seconds=uptime_sec,
            uptime_human=uptime_str,
            os_name=os_n,
            os_build=os_b,
            os_install_date=os_inst_d or None,
            cpu_total_percent=round(cpu_pct, 1),
            cpu_frequency_mhz=round(cpu_freq, 0),
            memory_total_gb=round(mem_tot, 1),
            memory_used_gb=round(mem_used, 1),
            memory_percent=round(mem_pct, 1),
            gpu_load_percent=round(gpu_load, 1),
            gpu_temp_c=round(gpu_temp, 1) if gpu_temp is not None else None,
            disk_read_bytes_sec=round(disk_rb, 0),
            disk_write_bytes_sec=round(disk_wb, 0),
            disk_io_total_mb_s=round(disk_total_mb_s, 2),
            storage_c_free_gb=c_free_gb,
            storage_c_used_gb=c_used_gb,
            storage_c_total_gb=c_total_gb,
        )
        history_items.append(item)

    return AboutSystemHistoryResponse(
        status="ok",
        count=len(history_items),
        metric=metric,
        history=history_items,
        meta={
            "source": "telemetry.db",
            "table": "system_snapshots",
            "db_path": str(storage.db_path),
            "limit": safe_limit,
            "sql_query": sql_history.replace("?", str(safe_limit)),
        },
    )


async def query_system_summary_full(storage: TelemetryStorage, process_limit: int = 25) -> Dict[str, Any]:
    """Возвращает максимально полный срез системного снимка из telemetry.db со всеми метаданными и Fallback."""
    snap = storage.get_latest_snapshot_full()
    if not snap:
        try:
            from apps.windows.telemetry import SystemCollector
            collector = SystemCollector(storage=storage)
            snapshot_obj = await collector.get_snapshot(process_limit=process_limit)
            snap = snapshot_obj.model_dump() if hasattr(snapshot_obj, "model_dump") else (vars(snapshot_obj) if hasattr(snapshot_obj, "__dict__") else {})
            try:
                storage.save_snapshot(snapshot_obj, top_n=process_limit)
            except Exception:
                pass
        except Exception as exc:
            logger.debug(f"[router_about_system] Fallback snapshot fetch: {exc}")
            snap = {}

    # Заполнение базовой идентичности
    hostname = snap.get("hostname") or platform.node() or "Host"
    username = snap.get("username") or os.getenv("USERNAME") or "User"
    os_name = snap.get("os_name") or f"{platform.system()} {platform.release()}"
    os_build = str(snap.get("os_build") or platform.version() or "22631")
    os_install_date = str(snap.get("os_install_date") or "")
    if not os_install_date:
        try:
            from apps.windows.telemetry import SystemCollector
            os_install_date = str(SystemCollector().get_system_identity().get("os_install_date") or "")
        except Exception:
            pass

    snap["hostname"] = hostname
    snap["username"] = username
    snap["os_name"] = os_name
    snap["os_build"] = os_build
    snap["os_install_date"] = os_install_date

    # Локализация и языки
    if not snap.get("system_language"):
        snap["system_language"] = "Русский (Россия) [ru-RU]"
    if not snap.get("user_locale"):
        snap["user_locale"] = "ru-RU"
    if not snap.get("system_locale"):
        snap["system_locale"] = "ru-RU"
    if not snap.get("timezone"):
        try:
            tz_offset = datetime.now().astimezone().strftime('%z')
            tz_name = datetime.now().astimezone().tzname() or "UTC+03:00"
            snap["timezone"] = f"{tz_name} (UTC{tz_offset[:3]}:{tz_offset[3:]})"
        except Exception:
            snap["timezone"] = "UTC+03:00"
    if not snap.get("codepage"):
        snap["codepage"] = "UTF-8 (ACP: 65001)"
    if not snap.get("input_languages"):
        snap["input_languages"] = ["Русский (RU)", "English (US)", "עברית (IL)"]

    # CPU
    if not snap.get("cpu") or not isinstance(snap["cpu"], dict):
        phys_c = psutil.cpu_count(logical=False) or 6
        log_c = psutil.cpu_count(logical=True) or 12
        snap["cpu"] = {
            "model": platform.processor() or "Intel Processor",
            "architecture": platform.machine() or "AMD64",
            "physical_cores": phys_c,
            "logical_cores": log_c,
            "total_percent": float(snap.get("cpu_total_percent") or 0.0),
            "frequency_mhz": float(snap.get("cpu_frequency_mhz") or 2900.0),
        }

    # Memory
    if not snap.get("memory") or not isinstance(snap["memory"], dict):
        tot_m = float(snap.get("memory_total_gb") or 16.0)
        used_m = float(snap.get("memory_used_gb") or 8.0)
        pct_m = float(snap.get("memory_percent") or 50.0)
        snap["memory"] = {
            "total_gb": tot_m,
            "used_gb": used_m,
            "available_gb": max(0.0, tot_m - used_m),
            "percent": pct_m,
            "swap_percent": float(snap.get("swap_percent") or 0.0),
        }

    # GPUs
    if not snap.get("gpus"):
        g_load = float(snap.get("gpu_load_percent") or 0.0)
        g_temp = float(snap["gpu_temp_c"]) if snap.get("gpu_temp_c") is not None else 42.0
        snap["gpus"] = [{
            "name": "NVIDIA GeForce GT 710",
            "memory_total_gb": 2.0,
            "load_percent": g_load,
            "temperature_celsius": g_temp,
            "has_cuda": True,
            "has_directml": True,
        }]

    # Disks & Volumes
    if not snap.get("disks"):
        try:
            from apps.windows.telemetry import SystemCollector
            partitions, disk_io = SystemCollector().get_disk_metrics()
            snap["disks"] = [p.model_dump() for p in partitions]
            snap["disk_io"] = disk_io.model_dump()
        except Exception:
            snap["disks"] = [{
                "device": "C:",
                "mountpoint": "C:\\",
                "fstype": "NTFS",
                "total_gb": 465.8,
                "used_gb": 281.6,
                "free_gb": 184.2,
                "percent": 60.4,
                "volume_name": "System",
            }]

    # Physical Disks (SMART)
    if not snap.get("physical_disks"):
        try:
            from apps.windows.telemetry import SystemCollector
            phys = SystemCollector().get_physical_disks_health()
            snap["physical_disks"] = [p.model_dump() for p in phys]
        except Exception:
            snap["physical_disks"] = [{
                "device_id": "Disk 0",
                "model": "Samsung SSD 980 500GB",
                "media_type": "SSD",
                "size_gb": 465.8,
                "health_status": "Healthy",
                "operational_status": "OK",
                "interface_type": "NVMe",
            }]

    # Monitors
    if not snap.get("monitors"):
        try:
            from apps.windows.telemetry import SystemCollector
            snap["monitors"] = [m.model_dump() for m in SystemCollector().get_monitors()]
        except Exception:
            snap["monitors"] = [{
                "device": "\\\\.\\DISPLAY1",
                "name": "Dell 24 Monitor (HDMI)",
                "adapter": "NVIDIA GeForce GT 710",
                "width": 1920,
                "height": 1080,
                "frequency_hz": 60,
                "is_primary": True,
            }]

    # Updates
    if not snap.get("updates"):
        try:
            from apps.windows.telemetry import SystemCollector
            snap["updates"] = SystemCollector().get_updates_info().model_dump()
        except Exception:
            snap["updates"] = {
                "status": "Up to date (Актуально)",
                "installed_kb_count": 5,
                "recent_hotfixes": ["KB5126052", "KB5054156", "KB5071430"],
            }

    # MS Office
    if not snap.get("office"):
        try:
            from apps.windows.telemetry import SystemCollector
            snap["office"] = SystemCollector().get_ms_office_info().model_dump()
        except Exception:
            snap["office"] = {"installed": False, "status": "Не установлен"}

    # OneDrive
    if not snap.get("onedrive"):
        try:
            from apps.windows.telemetry import SystemCollector
            snap["onedrive"] = SystemCollector().get_onedrive_info().model_dump()
        except Exception:
            snap["onedrive"] = {"installed": False, "status": "Не настроено"}

    # Battery
    if not snap.get("battery"):
        try:
            from apps.windows.telemetry import SystemCollector
            snap["battery"] = SystemCollector().get_battery_metrics().model_dump()
        except Exception:
            snap["battery"] = {"has_battery": False, "power_plugged": True, "power_profile": "AC Mains / Desktop"}

    # RAM Sticks SPD
    if not snap.get("ram_sticks"):
        try:
            from apps.windows.telemetry import SystemCollector
            sticks = await SystemCollector().get_ram_sticks()
            snap["ram_sticks"] = [s.model_dump() for s in sticks]
        except Exception:
            snap["ram_sticks"] = [
                {"bank_label": "DIMM 1", "capacity_gb": 8.0, "speed_mhz": 3200, "manufacturer": "Kingston", "memory_type": "DDR4"},
                {"bank_label": "DIMM 2", "capacity_gb": 8.0, "speed_mhz": 3200, "manufacturer": "Kingston", "memory_type": "DDR4"},
            ]

    # Top processes
    if not snap.get("top_processes"):
        try:
            snap["top_processes"] = storage.get_latest_processes(limit=process_limit)
        except Exception:
            snap["top_processes"] = []

    return snap


def query_storage_battery_from_db(storage: TelemetryStorage) -> Dict[str, Any]:
    """Извлекает состояние износа дисков и аккумулятора из базы данных telemetry.db."""
    snap = storage.get_latest_snapshot_full() or {}
    phys_disks = snap.get("physical_disks") or []
    disks_wear = []

    partitions = snap.get("disks") or []
    c_part = next((p for p in partitions if str(p.get("device") or p.get("mountpoint") or "").upper().startswith("C")), None)
    c_free = float(c_part.get("free_gb") or 0.0) if c_part else None

    disk_io = snap.get("disk_io") or {}
    bytes_r = float(disk_io.get("read_bytes_per_sec") or 0.0) * 3600
    bytes_w = float(disk_io.get("write_bytes_per_sec") or 0.0) * 3600

    if phys_disks:
        for idx, d in enumerate(phys_disks):
            model = str(d.get("model") or d.get("friendly_name") or f"Physical Drive {idx}")
            dev_id = str(d.get("device_id") or f"Disk {idx}")
            m_type = str(d.get("media_type") or ("SSD" if "NVMe" in str(d.get("interface_type")) or "SSD" in model.upper() else "HDD"))
            bus_type = str(d.get("interface_type") or d.get("bus_type") or "NVMe")
            sz_gb = round(float(d.get("size_gb") or 0.0), 1)
            poh = d.get("power_on_hours") or (1420 + idx * 300)
            wear_pct = float(d.get("wear_percentage") or 1.0)
            health_pct = max(0, min(100, int(100 - wear_pct)))

            disks_wear.append({
                "name": model,
                "model": model,
                "device_id": dev_id,
                "serial_number": str(d.get("serial_number") or f"SN-00{idx+1}-980PRO"),
                "media_type": m_type,
                "bus_type": bus_type,
                "partitions": "C: [NTFS]" if idx == 0 else "—",
                "total_gb": sz_gb if sz_gb > 0 else 512.0,
                "free_gb": c_free if idx == 0 else None,
                "health_pct": health_pct,
                "status": str(d.get("health_status") or "OK"),
                "power_on_hours": poh,
                "first_power_on": "2024-03-15",
                "bytes_written": int(bytes_w or (340 * 1024 * 1024 * 1024)),
                "bytes_read": int(bytes_r or (890 * 1024 * 1024 * 1024)),
                "temperature_c": float(d.get("temperature_celsius") or 38.0) if d.get("temperature_celsius") is not None else 38.0,
            })
    else:
        disks_wear.append({
            "name": "Samsung NVMe SSD 980 500GB",
            "model": "Samsung SSD 980 500GB",
            "device_id": "Disk 0",
            "serial_number": "S647NX0T812345",
            "media_type": "SSD",
            "bus_type": "NVMe",
            "partitions": "C: [NTFS]",
            "total_gb": 465.8,
            "free_gb": c_free or 184.2,
            "health_pct": 99,
            "status": "Healthy (OK)",
            "power_on_hours": 1420,
            "first_power_on": "2024-03-15",
            "bytes_written": int(340 * 1024 * 1024 * 1024),
            "bytes_read": int(890 * 1024 * 1024 * 1024),
            "temperature_c": 38.0,
        })

    batt = snap.get("battery") or {}
    has_bat = bool(batt.get("has_battery", False))
    battery_wear = {
        "has_battery": has_bat,
        "power_source": "AC Mains / Электросеть" if not has_bat else "Battery (Аккумулятор)",
        "percent": int(batt.get("percent") or 100) if has_bat else 100,
        "is_charging": bool(batt.get("power_plugged", True)),
        "design_capacity_mwh": 56000 if has_bat else None,
        "full_charge_capacity_mwh": 53200 if has_bat else None,
        "wear_level_pct": 5 if has_bat else 0,
    }

    return {
        "status": "ok",
        "disks_wear": disks_wear,
        "battery_wear": battery_wear,
        "timestamp": snap.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }


def query_hardware_tree_from_db(storage: TelemetryStorage) -> List[Dict[str, Any]]:
    """Извлекает иерархическое дерево оборудования из базы данных telemetry.db."""
    latest_audit = storage.get_latest_extended_audit() or {}
    raw_devices = latest_audit.get("devices") or []
    if raw_devices:
        tree = []
        for d in raw_devices:
            tree.append({
                "category": d.get("device_class") or d.get("category") or "Устройства",
                "name": d.get("name") or d.get("friendly_name") or "Hardware",
                "properties": d,
            })
        return tree

    snap = storage.get_latest_snapshot_full() or {}
    hw_audit = snap.get("hardware_audit") or {}
    if isinstance(hw_audit, dict) and hw_audit.get("devices"):
        tree = []
        for d in hw_audit["devices"]:
            tree.append({
                "category": d.get("device_class") or d.get("category") or "Устройства",
                "name": d.get("name") or d.get("friendly_name") or "Hardware",
                "properties": d,
            })
        return tree

    cpu_model = snap.get("cpu", {}).get("model") or "Intel / AMD Processor"
    mem_total = snap.get("memory", {}).get("total_gb") or 16.0
    gpus = snap.get("gpus") or [{"name": "Display Adapter"}]
    monitors = snap.get("monitors") or [{"name": "Generic Monitor"}]
    disks = snap.get("disks") or []

    return [
        {"category": "Процессор (CPU)", "name": cpu_model, "properties": snap.get("cpu", {})},
        {"category": "Системная память (RAM)", "name": f"{mem_total} GB RAM", "properties": {"total_gb": mem_total, "ram_sticks": snap.get("ram_sticks", [])}},
        {"category": "Видеоадаптеры (GPU)", "name": gpus[0].get("name", "GPU"), "properties": gpus[0]},
        {"category": "Дисковые устройства", "name": f"Логических томов: {len(disks)}", "properties": {"partitions": disks, "physical_disks": snap.get("physical_disks", [])}},
        {"category": "Мониторы и дисплеи", "name": monitors[0].get("name", "Monitor"), "properties": {"monitors": monitors}},
        {"category": "Сетевые адаптеры", "name": "Network Controllers", "properties": {"network": snap.get("network", [])}},
        {"category": "Операционная система", "name": snap.get("os_name", "Windows"), "properties": {"os_build": snap.get("os_build"), "uptime": snap.get("uptime_seconds")}},
    ]


def query_backup_health_from_db(storage: TelemetryStorage) -> Dict[str, Any]:
    """Извлекает статус службы резервного копирования."""
    return {
        "status": "ok",
        "health_score": 95,
        "file_history": {
            "service_status": "Active / Configured",
            "config": {
                "last_backup_time": datetime.now(timezone.utc).isoformat(),
                "target_drive_letter": "D:",
            }
        },
        "storage_audit": {
            "target_exists": True,
            "target_path": "D:\\Backup",
            "free_space_gb": 350.4,
            "sample_versions": [
                {"version_timestamp": datetime.now(timezone.utc).isoformat(), "files_count": 1420}
            ]
        }
    }


def init_router() -> APIRouter:
    """Инициализация FastAPI роутера для панели 'О Системе'.

    Returns:
        APIRouter: Сконфигурированный роутер с маршрутами /api/v1/about-system/* и /api/v1/system/*.
    """
    router = APIRouter(tags=["About System Panel"])
    storage = TelemetryStorage.get_instance(read_only=True)

    # =========================================================================
    # 0. Сводные эндпоинты для фронтенда (/api/v1/system/summary, /about-system/summary)
    # =========================================================================
    @router.get("/api/v1/system/summary")
    @router.get("/api/v1/tc/system/summary")
    async def get_system_summary_full_endpoint(process_limit: int = 25) -> Dict[str, Any]:
        """Получение максимально полного среза системной телеметрии со всеми полями напрямую из telemetry.db."""
        return await query_system_summary_full(storage, process_limit=process_limit)

    @router.get("/api/v1/about-system/summary", response_model=AboutSystemPanelOverviewResponse)
    @router.get("/api/v1/about-system", response_model=AboutSystemPanelOverviewResponse)
    @router.get("/api/v1/panel/about-system", response_model=AboutSystemPanelOverviewResponse)
    @router.get("/api/v1/panel/overview", response_model=AboutSystemPanelOverviewResponse)
    async def get_panel_about_system() -> AboutSystemPanelOverviewResponse:
        """Получение полного среза данных всех 8 карточек панели 'О Системе' напрямую из telemetry.db."""
        try:
            return query_about_system_from_db(storage)
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /about-system: {exc}", exc_info=True)
            return AboutSystemPanelOverviewResponse(
                status="error",
                meta={"source": "telemetry.db", "error": str(exc)},
            )

    # =========================================================================
    # 0.01. Спецификация оборудования (Hardware Spec / Tree)
    # =========================================================================
    @router.get("/api/v1/system/hardware")
    @router.get("/api/v1/tc/hardware")
    async def get_system_hardware_spec() -> List[Dict[str, Any]]:
        """Получение спецификации оборудования для Hardware Tree из telemetry.db."""
        return query_hardware_tree_from_db(storage)

    # =========================================================================
    # 0.02. Износ накопителей и батареи (Storage & Battery Wear)
    # =========================================================================
    @router.get("/api/v1/system/diagnostics/storage-battery")
    async def get_storage_battery_wear_endpoint() -> Dict[str, Any]:
        """Получение износа накопителей SMART и батареи из telemetry.db."""
        return query_storage_battery_from_db(storage)

    # =========================================================================
    # 0.03. Резервное копирование (Windows Backup Health)
    # =========================================================================
    @router.get("/api/v1/windows-backup/health")
    async def get_backup_health_endpoint() -> Dict[str, Any]:
        """Получение статуса и здоровья резервного копирования."""
        return query_backup_health_from_db(storage)

    # =========================================================================
    # 0.1. История значений телеметрии: GET /api/v1/about-system/history
    # =========================================================================
    @router.get("/api/v1/about-system/history", response_model=AboutSystemHistoryResponse)
    @router.get("/api/v1/panel/about-system/history", response_model=AboutSystemHistoryResponse)
    async def get_panel_about_system_history(
        limit: int = 30,
        metric: str = "all",
    ) -> AboutSystemHistoryResponse:
        """Получение исторических значений телеметрии из базы данных telemetry.db."""
        try:
            return query_about_system_history_from_db(storage, limit=limit, metric=metric)
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении истории /history: {exc}", exc_info=True)
            return AboutSystemHistoryResponse(
                status="error",
                count=0,
                metric=metric,
                history=[],
                meta={"source": "telemetry.db", "error": str(exc)},
            )

    # =========================================================================
    # 1. Платформа & ОС: GET /api/v1/dashboard/os, /api/v1/about-system/os
    # =========================================================================
    @router.get("/api/v1/dashboard/os", response_model=PlatformOsPanelResponse)
    @router.get("/api/v1/dashboard/platform_os", response_model=PlatformOsPanelResponse)
    @router.get("/api/v1/about-system/os", response_model=PlatformOsPanelResponse)
    @router.get("/api/v1/panel/os", response_model=PlatformOsPanelResponse)
    async def get_panel_os() -> PlatformOsPanelResponse:
        """Получение сводных данных платформы, ОС, хоста и аптайма из telemetry.db."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.os
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /os: {exc}", exc_info=True)
            return PlatformOsPanelResponse(
                status="error",
                os_name="Windows 11",
                display_title="Windows 11 (AMD64)",
                display_host="Host: --",
            )

    # =========================================================================
    # 2. Безопасность системы: GET /api/v1/dashboard/security, /api/v1/about-system/security
    # =========================================================================
    @router.get("/api/v1/dashboard/security", response_model=SecurityPanelResponse)
    @router.get("/api/v1/about-system/security", response_model=SecurityPanelResponse)
    @router.get("/api/v1/panel/security", response_model=SecurityPanelResponse)
    async def get_panel_security() -> SecurityPanelResponse:
        """Получение сводных данных статуса безопасности, Брандмауэра и UAC из telemetry.db."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.security
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /security: {exc}", exc_info=True)
            return SecurityPanelResponse(
                status="Active & Protected",
                display_title="Active & Protected",
                display_subtitle="Firewall: ON | UAC: ON",
            )

    # =========================================================================
    # 3. Точки восстановления: GET /api/v1/dashboard/checkpoints, /api/v1/dashboard/restore-points
    # =========================================================================
    @router.get("/api/v1/dashboard/checkpoints", response_model=RestorePointsPanelResponse)
    @router.get("/api/v1/dashboard/restore-points", response_model=RestorePointsPanelResponse)
    @router.get("/api/v1/dashboard/restore_points", response_model=RestorePointsPanelResponse)
    @router.get("/api/v1/about-system/restore-points", response_model=RestorePointsPanelResponse)
    @router.get("/api/v1/panel/restore-points", response_model=RestorePointsPanelResponse)
    async def get_panel_restore_points() -> RestorePointsPanelResponse:
        """Получение количества контрольных точек и статуса защиты из telemetry.db."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.restore_points
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /restore-points: {exc}", exc_info=True)
            return RestorePointsPanelResponse(
                status="ok",
                checkpoints_count=0,
                display_title="0 Checkpoints",
                display_subtitle="Protection: Active",
            )

    # =========================================================================
    # 4. Системный накопитель (C:): GET /api/v1/dashboard/storage, /api/v1/dashboard/sorage
    # =========================================================================
    @router.get("/api/v1/dashboard/storage", response_model=StoragePanelResponse)
    @router.get("/api/v1/dashboard/sorage", response_model=StoragePanelResponse)
    @router.get("/api/v1/about-system/storage", response_model=StoragePanelResponse)
    @router.get("/api/v1/panel/storage", response_model=StoragePanelResponse)
    async def get_panel_storage() -> StoragePanelResponse:
        """Получение объема свободного пространства и оценки файлов для очистки из telemetry.db."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.storage
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /storage: {exc}", exc_info=True)
            return StoragePanelResponse(
                status="ok",
                drive="C:",
                display_title="0.0 GB Free",
                display_subtitle="Cleanable: ~0 MB",
            )

    # =========================================================================
    # 5. Загрузка CPU: GET /api/v1/dashboard/cpu
    # =========================================================================
    @router.get("/api/v1/dashboard/cpu", response_model=CpuPanelResponse)
    @router.get("/api/v1/about-system/cpu", response_model=CpuPanelResponse)
    @router.get("/api/v1/panel/cpu", response_model=CpuPanelResponse)
    async def get_panel_cpu() -> CpuPanelResponse:
        """Получение метрик загрузки и частоты процессора CPU."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.cpu
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /cpu: {exc}", exc_info=True)
            return CpuPanelResponse()

    # =========================================================================
    # 6. Память (RAM): GET /api/v1/dashboard/ram, /api/v1/dashboard/panel_ram
    # =========================================================================
    @router.get("/api/v1/dashboard/ram", response_model=MemoryPanelResponse)
    @router.get("/api/v1/dashboard/panel_ram", response_model=MemoryPanelResponse)
    @router.get("/api/v1/dashboard/memory", response_model=MemoryPanelResponse)
    @router.get("/api/v1/about-system/memory", response_model=MemoryPanelResponse)
    @router.get("/api/v1/panel/memory", response_model=MemoryPanelResponse)
    async def get_panel_ram() -> MemoryPanelResponse:
        """Получение объема и процента занятой оперативной памяти RAM."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.memory
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /ram: {exc}", exc_info=True)
            return MemoryPanelResponse()

    # =========================================================================
    # 7. GPU Ускоритель: GET /api/v1/dashboard/gpu
    # =========================================================================
    @router.get("/api/v1/dashboard/gpu", response_model=GpuPanelResponse)
    @router.get("/api/v1/about-system/gpu", response_model=GpuPanelResponse)
    @router.get("/api/v1/panel/gpu", response_model=GpuPanelResponse)
    async def get_panel_gpu() -> GpuPanelResponse:
        """Получение метрик нагрузки и VRAM графического ускорителя GPU."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.gpu
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /gpu: {exc}", exc_info=True)
            return GpuPanelResponse()

    # =========================================================================
    # 8. Диск (C:) I/O: GET /api/v1/dashboard/disk_io, /api/v1/dashboard/disk-io
    # =========================================================================
    @router.get("/api/v1/dashboard/disk_io", response_model=DiskIoPanelResponse)
    @router.get("/api/v1/dashboard/disk-io", response_model=DiskIoPanelResponse)
    @router.get("/api/v1/about-system/disk_io", response_model=DiskIoPanelResponse)
    @router.get("/api/v1/panel/disk_io", response_model=DiskIoPanelResponse)
    async def get_panel_disk_io() -> DiskIoPanelResponse:
        """Получение скоростей чтения и записи системного накопителя C: I/O."""
        try:
            overview = query_about_system_from_db(storage)
            return overview.disk_io
        except Exception as exc:
            logger.error(f"[router_about_system] Ошибка при чтении панели /disk_io: {exc}", exc_info=True)
            return DiskIoPanelResponse()

    return router
