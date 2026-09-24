# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Grouped Telemetry Builder
# =============================================================================
# Description:
#   Модуль разделения полного среза телеметрии хоста (SystemSnapshot)
#   на изолированные функциональные группы для поэтапной AI-диагностики.
#
# Examples:
#   >>> from src.ai.observability.grouped_telemetry import GroupedTelemetryBuilder
#   >>> builder = GroupedTelemetryBuilder()
#   >>> groups = builder.build_groups(snapshot)
#
# File: grouped_telemetry.py
# Project: ai-breadboard
# Package: src.ai.observability
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Разбиение телеметрии хоста на специализированные доменные группы для LLM-анализа."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from apps.windows.telemetry.models import SystemSnapshot


class TelemetryGroupInfo(BaseModel):
    """Описание и структурированные данные одной диагностической группы."""

    group_id: str = Field(..., description="Уникальный идентификатор группы")
    title: str = Field(..., description="Человекочитаемый заголовок домена")
    icon: str = Field(default="bi-cpu", description="Bootstrap-иконка")
    description: str = Field(..., description="Краткое описание охватываемых подсистем")
    order: int = Field(default=1, description="Порядковый номер выполнения в цепочке")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Срез данных телеметрии и сенсоров")


class GroupedTelemetryBuilder:
    """Генератор изолированных пакетов телеметрии по функциональным группам."""

    @staticmethod
    def build_compute_thermals_group(snapshot: SystemSnapshot) -> TelemetryGroupInfo:
        """Формирует группу 1: Вычислительные ресурсы (CPU/GPU) и тепловой режим."""
        try:
            sensors = snapshot.sensors or []
            temps = {
                s.name: s.value for s in sensors
                if s.name and (s.category == "temperature" or ("temp" in (s.sensor_id or "").lower()))
            }
            fans = {
                s.name: f"{s.value} {s.unit}" for s in sensors
                if s.name and (s.category == "fan" or ("fan" in (s.sensor_id or "").lower()))
            }
            voltages = {
                s.name: f"{s.value} {s.unit}" for s in sensors
                if s.name and (s.category == "voltage" or ("voltage" in (s.sensor_id or "").lower()))
            }
            powers = {
                s.name: f"{s.value} {s.unit}" for s in sensors
                if s.name and (s.category == "power" or ("power" in (s.sensor_id or "").lower()))
            }

            gpus_data = [
                {
                    "name": g.name or "GPU",
                    "load_percent": g.load_percent,
                    "memory_total_gb": g.memory_total_gb,
                    "memory_used_gb": g.memory_used_gb,
                    "memory_free_gb": g.memory_free_gb,
                    "temperature_celsius": g.temperature_celsius,
                }
                for g in (snapshot.gpus or [])
            ]

            cpu = snapshot.cpu
            cpu_model = cpu.model if cpu else ""
            cpu_arch = cpu.architecture if cpu else "x86_64"
            cpu_load = round(cpu.total_percent, 1) if (cpu and cpu.total_percent is not None) else 0.0
            p_cores = cpu.physical_cores if cpu else 1
            l_cores = cpu.logical_cores if cpu else 1
            freq = cpu.frequency_mhz if cpu else 0.0
            pkg_temp = cpu.temperature_celsius if cpu else None
            per_core = [round(c, 1) for c in (cpu.per_core_percent or []) if c is not None] if cpu else []

            payload: Dict[str, Any] = {
                "cpu": {
                    "model": cpu_model,
                    "architecture": cpu_arch,
                    "load_percent": cpu_load,
                    "physical_cores": p_cores,
                    "logical_cores": l_cores,
                    "frequency_mhz": freq,
                    "package_temperature_celsius": pkg_temp,
                    "per_core_percent": per_core,
                },
                "gpus": gpus_data,
                "sensors": {
                    "temperatures_celsius": temps,
                    "fans_speed": fans,
                    "voltages": voltages,
                    "powers_watt": powers,
                },
            }
        except Exception:
            payload = {
                "cpu": {"model": "CPU", "load_percent": 0.0, "physical_cores": 1, "logical_cores": 1},
                "gpus": [],
                "sensors": {"temperatures_celsius": {}, "fans_speed": {}, "voltages": {}, "powers_watt": {}},
            }

        return TelemetryGroupInfo(
            group_id="compute_thermals",
            title="CPU, GPU и Охлаждение",
            icon="bi-fire",
            description="Анализ загрузки процессора, ядер, видеокарт, температурных датчиков и кулеров",
            order=1,
            payload=payload,
        )

    @staticmethod
    def build_memory_processes_group(snapshot: SystemSnapshot) -> TelemetryGroupInfo:
        """Формирует группу 2: Оперативная память, Swap и активные процессы."""
        try:
            ignored_processes = {"system idle process", "system", "idle"}
            procs = snapshot.top_processes or []
            active_processes = [
                {
                    "pid": p.pid,
                    "name": p.name or "process",
                    "cpu_percent": round(p.cpu_percent, 1) if p.cpu_percent is not None else 0.0,
                    "memory_mb": round(p.memory_mb, 1) if p.memory_mb is not None else 0.0,
                    "memory_percent": round(p.memory_percent, 1) if p.memory_percent is not None else 0.0,
                }
                for p in procs
                if p.pid not in [0, 4] and (p.name or "").lower() not in ignored_processes
            ][:12]

            mem = snapshot.memory
            ram_total = mem.total_gb if mem else 0.0
            ram_used = mem.used_gb if mem else 0.0
            ram_avail = mem.available_gb if mem else 0.0
            ram_pct = mem.percent if mem else 0.0
            swap_total = mem.swap_total_gb if mem else 0.0
            swap_used = mem.swap_used_gb if mem else 0.0
            swap_pct = mem.swap_percent if mem else 0.0

            ram_modules = [
                {
                    "bank_label": r.bank_label,
                    "capacity_gb": r.capacity_gb,
                    "speed_mhz": r.speed_mhz,
                    "manufacturer": r.manufacturer,
                }
                for r in (snapshot.ram_sticks or [])
            ]

            payload: Dict[str, Any] = {
                "ram": {
                    "total_gb": ram_total,
                    "used_gb": ram_used,
                    "available_gb": ram_avail,
                    "used_percent": ram_pct,
                },
                "swap_paging_file": {
                    "total_gb": swap_total,
                    "used_gb": swap_used,
                    "used_percent": swap_pct,
                },
                "ram_modules": ram_modules,
                "top_active_processes": active_processes,
            }
        except Exception:
            payload = {
                "ram": {"total_gb": 0.0, "used_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0},
                "swap_paging_file": {"total_gb": 0.0, "used_gb": 0.0, "used_percent": 0.0},
                "ram_modules": [],
                "top_active_processes": [],
            }

        return TelemetryGroupInfo(
            group_id="memory_processes",
            title="Память и Процессы",
            icon="bi-memory",
            description="Анализ объема и утилизации RAM, Swap-файла и топ-процессов потребителей ресурсов",
            order=2,
            payload=payload,
        )

    @staticmethod
    def build_storage_smart_group(snapshot: SystemSnapshot) -> TelemetryGroupInfo:
        """Формирует группу 3: Дисковые разделы, SMART-здоровье и Disk I/O."""
        try:
            partitions = [
                {
                    "device": d.device or "",
                    "mountpoint": d.mountpoint or "",
                    "fstype": d.fstype or "",
                    "total_gb": round(d.total_gb, 2) if d.total_gb is not None else 0.0,
                    "used_gb": round(d.used_gb, 2) if d.used_gb is not None else 0.0,
                    "free_gb": round(d.free_gb, 2) if d.free_gb is not None else 0.0,
                    "used_percent": round(d.percent, 1) if d.percent is not None else 0.0,
                }
                for d in (snapshot.disks or [])
            ]

            physical_disks = [
                {
                    "model": p.model or "Disk",
                    "media_type": p.media_type or "SSD",
                    "size_gb": p.size_gb or 0.0,
                    "smart_health": p.health_status or "Healthy",
                    "temperature_celsius": p.temperature_celsius,
                    "interface_type": getattr(p, "interface_type", None) or "Unknown",
                }
                for p in (snapshot.physical_disks or [])
            ]

            dio = snapshot.disk_io
            r_mb = round((dio.read_bytes_per_sec or 0.0) / (1024 * 1024), 2) if dio else 0.0
            w_mb = round((dio.write_bytes_per_sec or 0.0) / (1024 * 1024), 2) if dio else 0.0
            r_iops = round(dio.read_count_per_sec or 0.0, 1) if dio else 0.0
            w_iops = round(dio.write_count_per_sec or 0.0, 1) if dio else 0.0

            payload: Dict[str, Any] = {
                "storage_partitions": partitions,
                "physical_drives_smart": physical_disks,
                "disk_io_rates": {
                    "read_mb_per_sec": r_mb,
                    "write_mb_per_sec": w_mb,
                    "read_iops": r_iops,
                    "write_iops": w_iops,
                },
            }
        except Exception:
            payload = {
                "storage_partitions": [],
                "physical_drives_smart": [],
                "disk_io_rates": {"read_mb_per_sec": 0.0, "write_mb_per_sec": 0.0, "read_iops": 0.0, "write_iops": 0.0},
            }

        return TelemetryGroupInfo(
            group_id="storage_smart",
            title="Диски и Хранилище",
            icon="bi-hdd",
            description="Оценка свободного места на томах, SMART-состояния накопителей и дискового I/O",
            order=3,
            payload=payload,
        )

    @staticmethod
    def build_system_network_group(snapshot: SystemSnapshot) -> TelemetryGroupInfo:
        """Формирует группу 4: Сеть, обновления Windows и точки восстановления."""
        try:
            backup_info: Dict[str, Any] = {
                "system_protection": "Enabled",
                "restore_points_count": 0,
                "latest_restore_point": "None",
            }
            try:
                from apps.windows.core.system_restore import WindowsSystemRestoreManager
                restore_mgr = WindowsSystemRestoreManager(timeout_seconds=3)
                prot = restore_mgr.check_protection_status()
                backup_info["system_protection"] = "Enabled" if prot.get("system_protection_enabled") else "Disabled"
                points = restore_mgr.list_restore_points()
                backup_info["restore_points_count"] = len(points)
                if points:
                    backup_info["latest_restore_point"] = points[0].get("creation_time") or points[0].get("description", "")
            except Exception:
                pass

            networks = [
                {
                    "name": n.name or "Adapter",
                    "is_up": n.is_up,
                    "speed_mbps": n.speed_mbps or 0,
                    "recv_kb_per_sec": round((n.bytes_recv_per_sec or 0.0) / 1024, 1),
                    "sent_kb_per_sec": round((n.bytes_sent_per_sec or 0.0) / 1024, 1),
                }
                for n in (snapshot.network or [])
            ]

            ports = [
                {
                    "port": p.port,
                    "process_name": p.process_name or "",
                    "protocol": p.protocol or "TCP",
                    "pid": p.pid,
                }
                for p in (snapshot.listening_ports or [])[:15]
            ]

            payload: Dict[str, Any] = {
                "host_info": {
                    "hostname": snapshot.hostname or "localhost",
                    "os": f"{snapshot.os_name or 'Windows'} {snapshot.os_build or ''}".strip(),
                    "uptime_hours": round((snapshot.uptime_seconds or 0.0) / 3600, 1),
                },
                "system_updates": {
                    "reboot_pending": bool(snapshot.alerts and snapshot.alerts.reboot_pending),
                    "status": snapshot.updates.status if snapshot.updates else "Up to date",
                    "installed_kb_count": snapshot.updates.installed_kb_count if snapshot.updates else 0,
                },
                "backup_and_restore": backup_info,
                "network_adapters": networks,
                "listening_ports_sample": ports,
            }
        except Exception:
            payload = {
                "host_info": {"hostname": "localhost", "os": "Windows", "uptime_hours": 0.0},
                "system_updates": {"reboot_pending": False, "status": "Up to date", "installed_kb_count": 0},
                "backup_and_restore": {"system_protection": "Enabled", "restore_points_count": 0, "latest_restore_point": "None"},
                "network_adapters": [],
                "listening_ports_sample": [],
            }

        return TelemetryGroupInfo(
            group_id="system_network",
            title="Сеть и Стабильность ОС",
            icon="bi-shield-check",
            description="Проверка сети, обновлений ОС, отложенных перезагрузок и точек восстановления",
            order=4,
            payload=payload,
        )

    def build_all_groups(self, snapshot: SystemSnapshot) -> List[TelemetryGroupInfo]:
        """Формирует полный упорядоченный список диагностических групп."""
        return [
            self.build_compute_thermals_group(snapshot),
            self.build_memory_processes_group(snapshot),
            self.build_storage_smart_group(snapshot),
            self.build_system_network_group(snapshot),
        ]


class GroupDiagnoseRequest(BaseModel):
    """Запрос на AI-диагностику одной конкретной группы телеметрии."""

    group_id: str = Field(..., description="Идентификатор группы (compute_thermals, memory_processes, storage_smart, system_network)")
    title: Optional[str] = Field(default="", description="Опциональный заголовок группы")
    payload: Dict[str, Any] = Field(..., description="Данные телеметрии группы")


class GroupDiagnosticResult(BaseModel):
    """Результат AI-анализа одной специализированной группы."""

    group_id: str = Field(..., description="Идентификатор группы")
    title: str = Field(..., description="Заголовок группы")
    icon: str = Field(default="bi-cpu", description="Bootstrap-иконка")
    status: str = Field(default="ok", description="Статус: ok, warning, critical")
    summary: str = Field(default="", description="Экспертное заключение AI-модели по данной группе")
    anomalies: List[str] = Field(default_factory=list, description="Выявленные отклонения и узкие места")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации по оптимизации домена")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Ключевые метрики для карточки UI")
    raw_response: Optional[str] = Field(default=None, description="Сырой ответ языковой модели")
    ai_model_used: str = Field(default="AI Model", description="Использованный AI-провайдер/модель")


class SynthesisRequest(BaseModel):
    """Запрос на синтез итогового вердикта по всем завершенным группам."""

    groups: List[GroupDiagnosticResult] = Field(..., description="Результаты анализа всех 4 групп")


class SynthesisDiagnosticResult(BaseModel):
    """Итоговый синтез состояния всей системы с интегральным Health Score."""

    health_score: int = Field(default=100, ge=0, le=100, description="Интегральный индекс здоровья (0-100)")
    status_label: str = Field(default="Отличное", description="Метка статуса (Отличное, Внимание, Критическое)")
    executive_summary: str = Field(..., description="Итоговое резюме инженера по всей системе")
    critical_actions: List[str] = Field(default_factory=list, description="Приоритизированные шаги для администратора")
    ai_model_used: str = Field(default="AI Model", description="Использованный провайдер для синтеза")
    groups_evaluated: int = Field(default=4, description="Количество оцененных доменов")

