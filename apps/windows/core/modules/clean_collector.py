# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Clean & Cache Audit Collector
# =============================================================================
# Description:
#   Анализ и поиск временных файлов, кэшей Windows Update, минидампов,
#   корзины, больших файлов и остатков установщиков с расчётом безопасности.
#
# Examples:
#   >>> from apps.windows.core.modules.clean_collector import CleanCollector
#   >>> collector = CleanCollector()
#   >>> result = collector.collect()
#
# File: clean_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита очистки системы и временных файлов."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List

from logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class CleanCollector:
    """Коллектор фактов для очистки кэшей и временных данных."""

    def __init__(self) -> None:
        """Инициализация путей для аудита очистки."""
        self.user_temp = Path(os.environ.get("TEMP", "C:/Users/Default/AppData/Local/Temp"))
        self.sys_temp = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "Temp"
        self.software_dist = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "SoftwareDistribution" / "Download"
        self.minidump_dir = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "Minidump"
        self.memory_dmp = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "MEMORY.DMP"

    def collect(self) -> DomainAuditResult:
        """Сбор данных о временных файлах и мусоре.

        Returns:
            DomainAuditResult: Результат аудита домена очистки.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        metrics: Dict[str, Any] = {
            "total_cleanable_bytes": 0,
            "total_cleanable_mb": 0.0,
            "locations_scanned": 0,
        }

        # 1. Проверка пользовательского %TEMP%
        user_temp_bytes, user_temp_count = self._scan_directory(self.user_temp)
        metrics["locations_scanned"] += 1
        if user_temp_bytes > 50 * 1024 * 1024:  # > 50 MB
            action = RemediationAction(
                action_id="clean_user_temp",
                action_type=ActionType.CLEAN_DIRECTORY,
                title="Очистка пользовательского каталога Temp",
                description=f"Удаление {user_temp_count} временных файлов ({user_temp_bytes // (1024 * 1024)} MB)",
                target=str(self.user_temp),
                risk=RiskLevel.SAFE,
                releasable_bytes=user_temp_bytes,
                execution_command=f"Remove-Item -Path '{self.user_temp}\\*' -Recurse -Force -ErrorAction SilentlyContinue",
            )
            findings.append(
                AuditFinding(
                    domain="clean",
                    category="temp_files",
                    title="Большой объем файлов в пользовательском Temp",
                    description=f"В каталоге {self.user_temp} обнаружено {user_temp_count} файлов на сумму {user_temp_bytes // (1024 * 1024)} MB.",
                    severity=RiskLevel.SAFE,
                    evidence={"path": str(self.user_temp), "size_bytes": user_temp_bytes, "file_count": user_temp_count},
                    actions=[action],
                )
            )
            metrics["total_cleanable_bytes"] += user_temp_bytes

        # 2. Проверка системного Temp
        sys_temp_bytes, sys_temp_count = self._scan_directory(self.sys_temp)
        metrics["locations_scanned"] += 1
        if sys_temp_bytes > 50 * 1024 * 1024:
            action = RemediationAction(
                action_id="clean_sys_temp",
                action_type=ActionType.CLEAN_DIRECTORY,
                title="Очистка системного каталога C:\\Windows\\Temp",
                description=f"Удаление {sys_temp_count} системных временных файлов ({sys_temp_bytes // (1024 * 1024)} MB)",
                target=str(self.sys_temp),
                risk=RiskLevel.SAFE,
                releasable_bytes=sys_temp_bytes,
                execution_command=f"Remove-Item -Path '{self.sys_temp}\\*' -Recurse -Force -ErrorAction SilentlyContinue",
            )
            findings.append(
                AuditFinding(
                    domain="clean",
                    category="temp_files",
                    title="Временные файлы в системном каталоге Windows\\Temp",
                    description=f"В каталоге {self.sys_temp} обнаружено {sys_temp_count} файлов на сумму {sys_temp_bytes // (1024 * 1024)} MB.",
                    severity=RiskLevel.SAFE,
                    evidence={"path": str(self.sys_temp), "size_bytes": sys_temp_bytes, "file_count": sys_temp_count},
                    actions=[action],
                )
            )
            metrics["total_cleanable_bytes"] += sys_temp_bytes

        # 3. Проверка кэша Windows Update Download
        wu_bytes, wu_count = self._scan_directory(self.software_dist)
        metrics["locations_scanned"] += 1
        if wu_bytes > 100 * 1024 * 1024:  # > 100 MB
            action = RemediationAction(
                action_id="clean_wu_cache",
                action_type=ActionType.CLEAN_DIRECTORY,
                title="Очистка кэша загрузок Windows Update",
                description=f"Удаление устаревших загрузок обновлений ({wu_bytes // (1024 * 1024)} MB)",
                target=str(self.software_dist),
                risk=RiskLevel.SAFE,
                releasable_bytes=wu_bytes,
                execution_command="net stop wuauserv; Remove-Item -Path 'C:\\Windows\\SoftwareDistribution\\Download\\*' -Recurse -Force -ErrorAction SilentlyContinue; net start wuauserv",
            )
            findings.append(
                AuditFinding(
                    domain="clean",
                    category="update_cache",
                    title="Кэш загрузок Windows Update",
                    description=f"В SoftwareDistribution\\Download обнаружено {wu_count} файлов ({wu_bytes // (1024 * 1024)} MB).",
                    severity=RiskLevel.SAFE,
                    evidence={"path": str(self.software_dist), "size_bytes": wu_bytes, "file_count": wu_count},
                    actions=[action],
                )
            )
            metrics["total_cleanable_bytes"] += wu_bytes

        # 4. Crash dumps & Minidumps
        md_bytes, md_count = self._scan_directory(self.minidump_dir)
        metrics["locations_scanned"] += 1
        if md_count > 0:
            action = RemediationAction(
                action_id="clean_minidumps",
                action_type=ActionType.CLEAN_DIRECTORY,
                title="Очистка дампов аварийного завершения (Minidump)",
                description=f"Удаление {md_count} дампов памяти BSOD ({md_bytes // (1024 * 1024)} MB)",
                target=str(self.minidump_dir),
                risk=RiskLevel.CAUTION,
                releasable_bytes=md_bytes,
                execution_command=f"Remove-Item -Path '{self.minidump_dir}\\*' -Force -ErrorAction SilentlyContinue",
            )
            findings.append(
                AuditFinding(
                    domain="clean",
                    category="crash_dumps",
                    title="Обнаружены дампы памяти BSOD",
                    description=f"В каталоге {self.minidump_dir} найдено {md_count} дампов сбоев.",
                    severity=RiskLevel.CAUTION,
                    evidence={"path": str(self.minidump_dir), "count": md_count, "size_bytes": md_bytes},
                    actions=[action],
                )
            )
            metrics["total_cleanable_bytes"] += md_bytes

        metrics["total_cleanable_mb"] = round(metrics["total_cleanable_bytes"] / (1024 * 1024), 2)
        duration_ms = (time.perf_counter() - start_t) * 1000

        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity in (RiskLevel.CAUTION, RiskLevel.SAFE) for f in findings):
            status = "warning"

        return DomainAuditResult(
            domain_name="clean",
            title_ru="Очистка системы и кэшей",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _scan_directory(self, path: Path) -> tuple[int, int]:
        """Рекурсивный подсчет размера и количества файлов."""
        if not path.exists():
            return 0, 0
        total_size = 0
        count = 0
        try:
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        p = Path(root) / f
                        total_size += p.stat().st_size
                        count += 1
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total_size, count
