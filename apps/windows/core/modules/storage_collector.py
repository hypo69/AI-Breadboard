# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Storage & Disk Health Audit Collector
# =============================================================================
# Description:
#   Диагностика физических и логических дисков, файловой системы NTFS/ReFS,
#   свободного места, статуса VSS (Volume Shadow Storage) и точек восстановления.
#
# Examples:
#   >>> from apps.windows.core.modules.storage_collector import StorageCollector
#   >>> collector = StorageCollector()
#   >>> result = collector.collect()
#
# File: storage_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита дисковой подсистемы, VSS и файловых томов."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import psutil

from logger import logger
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel
from apps.windows.core.system_restore import WindowsSystemRestoreManager
from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider


class StorageCollector(TelemetryProvider):
    """Коллектор фактов о состоянии дисков, томов и теневых хранилищ VSS."""

    def __init__(self) -> None:
        """Инициализация коллектора с менеджером System Restore & VSS."""
        self._restore_mgr = WindowsSystemRestoreManager(timeout_seconds=10)
        self._last_result: Optional[DomainAuditResult] = None

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает показатели дисковой подсистемы как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_result and self._last_result.metrics:
            volumes = self._last_result.metrics.get("volumes", [])
            for vol in volumes:
                mount = vol.get("mountpoint", "unknown").replace(":", "").replace("\\", "_")
                sensors.append(HardwareSensor(
                    sensor_id=f"disk_usage_{mount}",
                    name=f"Заполнение диска {vol.get('mountpoint')}",
                    category="storage",
                    value=float(vol.get("percent_used", 0.0)),
                    unit="%"
                ))
        return sensors

    def collect(self) -> DomainAuditResult:
        """Сбор данных о дисках, свободном пространстве и теневом хранилище VSS."""
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        volumes = []

        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                free_gb = round(usage.free / (1024**3), 2)
                total_gb = round(usage.total / (1024**3), 2)
                vol_info = {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total_gb": total_gb,
                    "free_gb": free_gb,
                    "percent_used": usage.percent,
                }
                volumes.append(vol_info)

                # Предупреждение при низком свободном месте
                if usage.percent >= 90.0:
                    findings.append(
                        AuditFinding(
                            domain="storage",
                            category="low_disk_space",
                            title=f"Критически мало места на диске {part.mountpoint}",
                            description=f"Диск {part.mountpoint} заполнен на {usage.percent}% (осталось {free_gb} GB из {total_gb} GB).",
                            severity=RiskLevel.CRITICAL if usage.percent >= 95.0 else RiskLevel.CAUTION,
                            evidence=vol_info,
                        )
                    )
            except (PermissionError, OSError):
                continue

        # Проверка состояния теневого хранилища VSS и System Protection
        vss_storage = self._restore_mgr.get_shadow_storage_info()
        protection_status = self._restore_mgr.check_protection_status()

        if vss_storage.get("at_risk_of_eviction", False):
            findings.append(
                AuditFinding(
                    domain="storage",
                    category="vss_storage_pressure",
                    title="Переполнение хранилища теневых копий VSS",
                    description=f"Хранилище теневых копий VSS заполнено на {vss_storage.get('usage_percent')}%, что создает риск вытеснения точек восстановления.",
                    severity=RiskLevel.CAUTION,
                    evidence=vss_storage,
                )
            )

        # Диагностика физических накопителей через WindowsStorageSensor
        physical_disks_data: List[Dict[str, Any]] = []
        try:
            from apps.windows.storage_sensors.windows_storage_sensor import WindowsStorageSensor
            sensor = WindowsStorageSensor(timeout_sec=10)
            disks = sensor.get_physical_disks()
            for d in disks:
                disk_dict = d.to_dict()
                physical_disks_data.append(disk_dict)

                # Проверка критического статуса здоровья
                if d.health_status.upper() in ("UNHEALTHY", "FAILING", "CRITICAL"):
                    findings.append(
                        AuditFinding(
                            domain="storage",
                            category="disk_hardware_failure",
                            title=f"Угроза отказа диска {d.friendly_name}",
                            description=f"Накопитель {d.friendly_name} сообщает о сбое здоровья ({d.health_status}, статус: {d.operational_status}).",
                            severity=RiskLevel.CRITICAL,
                            evidence=disk_dict,
                        )
                    )
                elif d.health_status.upper() == "WARNING":
                    findings.append(
                        AuditFinding(
                            domain="storage",
                            category="disk_health_warning",
                            title=f"Предупреждение о здоровье диска {d.friendly_name}",
                            description=f"Накопитель {d.friendly_name} находится в состоянии предупреждения ({d.health_status}).",
                            severity=RiskLevel.CAUTION,
                            evidence=disk_dict,
                        )
                    )

                # Проверка износа SSD/NVMe
                if d.wear_percentage is not None and d.wear_percentage >= 95.0:
                    findings.append(
                        AuditFinding(
                            domain="storage",
                            category="ssd_wear_critical",
                            title=f"Критический износ накопителя {d.friendly_name}",
                            description=f"Процент износа SSD/NVMe {d.friendly_name} достиг {d.wear_percentage}%. Рекомендуется замена накопителя.",
                            severity=RiskLevel.CRITICAL if d.wear_percentage >= 99.0 else RiskLevel.CAUTION,
                            evidence=disk_dict,
                        )
                    )
        except Exception as e:
            logger.debug(f"Ошибка сбора физических дисков в StorageCollector: {e}")

        metrics: Dict[str, Any] = {
            "volumes_count": len(volumes),
            "volumes": volumes,
            "physical_disks_count": len(physical_disks_data),
            "physical_disks": physical_disks_data,
            "vss_shadow_storage": vss_storage,
            "system_protection": protection_status,
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity == RiskLevel.CAUTION for f in findings):
            status = "warning"

        result = DomainAuditResult(
            domain_name="storage",
            title_ru="Диски, VSS и файловая система",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
        self._last_result = result
        return result

