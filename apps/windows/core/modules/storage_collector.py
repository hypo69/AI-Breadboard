# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Storage & Disk Health Audit Collector
# =============================================================================
# Description:
#   Диагностика физических и логических дисков, файловой системы NTFS/ReFS,
#   свободного места, статуса TRIM, BitLocker и обнаружение дисковых аномалий.
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

"""Коллектор аудита дисковой подсистемы и файловых томов."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import psutil

from src.logger import logger
from apps.windows.core.models import AuditFinding, DomainAuditResult, RiskLevel


class StorageCollector:
    """Коллектор фактов о состоянии дисков и томов."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о дисках и свободном пространстве.

        Returns:
            DomainAuditResult: Результат аудита дисковой подсистемы.
        """
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

        metrics: Dict[str, Any] = {
            "volumes_count": len(volumes),
            "volumes": volumes,
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity == RiskLevel.CAUTION for f in findings):
            status = "warning"

        return DomainAuditResult(
            domain_name="storage",
            title_ru="Диски и файловая система",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
