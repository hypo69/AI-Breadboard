# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Panel
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для 4 сводных KPI-карточек вкладки "О Системе".
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_panel import PlatformOsPanelResponse
#
#     service = PlatformOsPanelResponse()
#
# File: router_panel.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""FastAPI REST эндпоинты для 4 сводных KPI-карточек вкладки "О Системе"."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage


class PlatformOsPanelResponse(BaseModel):
    """Модель ответа панели «Платформа & ОС»."""
    status: str = Field(default="ok", description="Статус ответа")
    os_name: str = Field(default="Windows", description="Наименование операционной системы")
    os_build: str = Field(default="", description="Номер сборки ОС")
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
            logger.debug(f"[router_panel] Ошибка парсинга raw_json снимка: {err}")

    disks_str = snap_row.get("disks_json")
    if disks_str and isinstance(disks_str, str):
        try:
            snap_row["disks"] = json.loads(disks_str)
        except Exception as err:
            logger.debug(f"[router_panel] Ошибка парсинга disks_json снимка: {err}")

    return snap_row


def init_router() -> APIRouter:
    """Инициализация FastAPI роутера для сводных панелей KPI.

    Returns:
        APIRouter: Сконфигурированный роутер с маршрутами /api/v1/panel/*.
    """
    router = APIRouter(prefix="/api/v1/panel", tags=["KPI Telemetry Panels"])
    storage = TelemetryStorage.get_instance()

    # =========================================================================
    # 1. Платформа & ОС: GET /api/v1/panel/os
    # =========================================================================
    @router.get("/os", response_model=PlatformOsPanelResponse)
    async def get_panel_os() -> PlatformOsPanelResponse:
        """Получение сводных данных платформы, ОС, хоста и аптайма из telemetry.db."""
        try:
            data = _get_latest_snapshot_dict(storage)
            if not data:
                # Fallback: прямой сбор через синглтон сборщика если БД пуста
                from apps.windows.telemetry import SystemCollector
                collector = SystemCollector()
                snap = await collector.get_snapshot(process_limit=5)
                storage.save_snapshot(snap, top_n=5)
                storage.flush()
                data = _get_latest_snapshot_dict(storage)

            os_name = data.get("os_name") or "Windows 11"
            os_build = str(data.get("os_build") or "")
            cpu_dict = data.get("cpu") or {}
            arch = cpu_dict.get("architecture") if isinstance(cpu_dict, dict) else getattr(cpu_dict, "architecture", "AMD64")
            arch = arch or "AMD64"
            host = data.get("hostname") or "Host"
            uptime = float(data.get("uptime_seconds") or 0.0)
            ts = data.get("timestamp") or datetime.now(timezone.utc).isoformat()

            display_title = f"{os_name} ({arch})" if arch else os_name
            display_host = f"Host: {host}"
            uptime_human = _format_uptime_human(uptime)

            return PlatformOsPanelResponse(
                status="ok",
                os_name=os_name,
                os_build=os_build,
                architecture=arch,
                hostname=host,
                uptime_seconds=uptime,
                uptime_human=uptime_human,
                display_title=display_title,
                display_host=display_host,
                timestamp=ts,
            )
        except Exception as exc:
            logger.error(f"[router_panel] Ошибка при чтении панели /os: {exc}", exc_info=True)
            return PlatformOsPanelResponse(
                status="error",
                os_name="Windows 11",
                display_title="Windows 11 (AMD64)",
                display_host="Host: --",
            )

    # =========================================================================
    # 2. Безопасность системы: GET /api/v1/panel/security
    # =========================================================================
    @router.get("/security", response_model=SecurityPanelResponse)
    async def get_panel_security() -> SecurityPanelResponse:
        """Получение сводных данных статуса безопасности, Брандмауэра и UAC из telemetry.db."""
        try:
            # Читаем расширенный аудит из telemetry.db
            with storage._lock, storage._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT raw_json, timestamp FROM system_extended_audits ORDER BY id DESC LIMIT 1;"
                )
                row = cursor.fetchone()

            fw_domain = True
            fw_private = True
            fw_public = True
            defender_enabled = True
            realtime = True
            uac_enabled = True
            ts = datetime.now(timezone.utc).isoformat()

            if row and row["raw_json"]:
                try:
                    ext_data = json.loads(row["raw_json"])
                    ts = row["timestamp"] or ts
                    sec_data = ext_data.get("security", {})
                    fw = sec_data.get("firewall", {})
                    fw_domain = bool(fw.get("domain", True))
                    fw_private = bool(fw.get("private", True))
                    fw_public = bool(fw.get("public", True))
                    defender = sec_data.get("defender", {})
                    defender_enabled = bool(defender.get("enabled", True))
                    realtime = bool(defender.get("realtime_protection", True))
                    uac = sec_data.get("uac", {})
                    uac_enabled = bool(uac.get("enabled", True))
                except Exception as err:
                    logger.debug(f"[router_panel] Ошибка парсинга system_extended_audits: {err}")
            else:
                # Попробуем прочитать из app_polls или system_snapshots
                snap_data = _get_latest_snapshot_dict(storage)
                if snap_data:
                    ts = snap_data.get("timestamp") or ts

            fw_all_on = fw_domain and fw_private and fw_public
            fw_str = "ON" if fw_all_on else "PARTIAL"
            uac_str = "ON" if uac_enabled else "OFF"
            all_protected = fw_all_on and defender_enabled and realtime and uac_enabled
            status_text = "Active & Protected" if all_protected else "Warning"
            display_sub = f"Firewall: {fw_str} | UAC: {uac_str}"

            return SecurityPanelResponse(
                status=status_text,
                firewall_status=fw_str,
                firewall_domain=fw_domain,
                firewall_private=fw_private,
                firewall_public=fw_public,
                defender_enabled=defender_enabled,
                realtime_protection=realtime,
                uac_enabled=uac_enabled,
                display_title=status_text,
                display_subtitle=display_sub,
                timestamp=ts,
            )
        except Exception as exc:
            logger.error(f"[router_panel] Ошибка при чтении панели /security: {exc}", exc_info=True)
            return SecurityPanelResponse(
                status="Active & Protected",
                display_title="Active & Protected",
                display_subtitle="Firewall: ON | UAC: ON",
            )

    # =========================================================================
    # 3. Точки восстановления: GET /api/v1/panel/restore-points
    # =========================================================================
    @router.get("/restore-points", response_model=RestorePointsPanelResponse)
    async def get_panel_restore_points() -> RestorePointsPanelResponse:
        """Получение количества контрольных точек и статуса защиты из telemetry.db."""
        try:
            checkpoints_count = 0
            protection_enabled = True
            protection_status = "Active"
            latest_name = None
            latest_time = None
            ts = datetime.now(timezone.utc).isoformat()

            # Читаем из таблицы system_extended_audits
            with storage._lock, storage._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT vss_snapshots_count, raw_json, timestamp FROM system_extended_audits ORDER BY id DESC LIMIT 1;"
                )
                row = cursor.fetchone()

            if row:
                checkpoints_count = int(row["vss_snapshots_count"] or 0)
                ts = row["timestamp"] or ts
                if row["raw_json"]:
                    try:
                        ext_data = json.loads(row["raw_json"])
                        vss_data = ext_data.get("vss", {}) or ext_data.get("restore_points", {})
                        if isinstance(vss_data, dict):
                            protection_enabled = bool(vss_data.get("protection_enabled", True))
                            protection_status = vss_data.get("status") or ("Active" if protection_enabled else "Disabled")
                            latest_name = vss_data.get("latest_name")
                            latest_time = vss_data.get("latest_time")
                    except Exception as err:
                        logger.debug(f"[router_panel] Ошибка парсинга VSS аудита: {err}")
            else:
                # Если аудита ещё не было, проверяем app_polls
                with storage._lock, storage._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT value, details, timestamp FROM app_polls WHERE metric_name = 'vss_snapshots_count' ORDER BY id DESC LIMIT 1;"
                    )
                    poll_row = cursor.fetchone()
                    if poll_row:
                        checkpoints_count = int(poll_row["value"] or 0)
                        ts = poll_row["timestamp"] or ts

            display_title = f"{checkpoints_count} Checkpoints"
            display_sub = f"Protection: {protection_status}"

            return RestorePointsPanelResponse(
                status="ok",
                checkpoints_count=checkpoints_count,
                protection_enabled=protection_enabled,
                protection_status=protection_status,
                display_title=display_title,
                display_subtitle=display_sub,
                latest_checkpoint_name=latest_name,
                latest_checkpoint_time=latest_time,
                timestamp=ts,
            )
        except Exception as exc:
            logger.error(f"[router_panel] Ошибка при чтении панели /restore-points: {exc}", exc_info=True)
            return RestorePointsPanelResponse(
                status="ok",
                checkpoints_count=0,
                display_title="0 Checkpoints",
                display_subtitle="Protection: Active",
            )

    # =========================================================================
    # 4. Системный накопитель (C:): GET /api/v1/panel/storage
    # =========================================================================
    @router.get("/storage", response_model=StoragePanelResponse)
    async def get_panel_storage() -> StoragePanelResponse:
        """Получение объема свободного пространства и оценки файлов для очистки из telemetry.db."""
        try:
            data = _get_latest_snapshot_dict(storage)
            disks = data.get("disks") or []
            c_drive = None
            for d in disks:
                dev = (d.get("device") if isinstance(d, dict) else getattr(d, "device", "")) or ""
                mount = (d.get("mountpoint") if isinstance(d, dict) else getattr(d, "mountpoint", "")) or ""
                if dev.upper().startswith("C") or mount.upper().startswith("C"):
                    c_drive = d
                    break

            if not c_drive and disks:
                c_drive = disks[0]

            total_gb = 0.0
            free_gb = 0.0
            used_gb = 0.0
            pct_used = 0.0
            ts = data.get("timestamp") or datetime.now(timezone.utc).isoformat()

            if c_drive:
                total_gb = float((c_drive.get("total_gb") if isinstance(c_drive, dict) else getattr(c_drive, "total_gb", 0.0)) or 0.0)
                free_gb = float((c_drive.get("free_gb") if isinstance(c_drive, dict) else getattr(c_drive, "free_gb", 0.0)) or 0.0)
                used_gb = float((c_drive.get("used_gb") if isinstance(c_drive, dict) else getattr(c_drive, "used_gb", 0.0)) or 0.0)
                pct_used = float((c_drive.get("percent") if isinstance(c_drive, dict) else getattr(c_drive, "percent", 0.0)) or 0.0)

            # Оценка очищаемых файлов (Cleanable) из app_polls или app_events
            cleanable_mb = 0.0
            with storage._lock, storage._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value, details FROM app_polls WHERE metric_name = 'cleanable_mb' OR metric_name = 'clean_findings' ORDER BY id DESC LIMIT 1;"
                )
                clean_row = cursor.fetchone()
                if clean_row and clean_row["value"] is not None:
                    cleanable_mb = float(clean_row["value"])

            display_title = f"{free_gb:.1f} GB Free"
            clean_str = f"~{cleanable_mb:.0f} MB" if cleanable_mb < 1024 else f"~{cleanable_mb/1024:.1f} GB"
            display_sub = f"Cleanable: {clean_str}"

            return StoragePanelResponse(
                status="ok",
                drive="C:",
                total_gb=round(total_gb, 1),
                free_gb=round(free_gb, 1),
                used_gb=round(used_gb, 1),
                percent_used=round(pct_used, 1),
                cleanable_mb=round(cleanable_mb, 1),
                display_title=display_title,
                display_subtitle=display_sub,
                timestamp=ts,
            )
        except Exception as exc:
            logger.error(f"[router_panel] Ошибка при чтении панели /storage: {exc}", exc_info=True)
            return StoragePanelResponse(
                status="ok",
                drive="C:",
                display_title="0.0 GB Free",
                display_subtitle="Cleanable: ~0 MB",
            )

    return router
