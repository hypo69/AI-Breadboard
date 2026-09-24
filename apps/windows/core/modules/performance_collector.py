# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Performance & Startup Audit Collector
# =============================================================================
# Description:
#   Анализ автозагрузки, параметров электропитания, системных ресурсов,
#   очередей диска, фоновых задач и выявление замедлений запуска Windows.
#
# Examples:
#   >>> from apps.windows.core.modules.performance_collector import PerformanceCollector
#   >>> collector = PerformanceCollector()
#   >>> result = collector.collect()
#
# File: performance_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита производительности и автозагрузки Windows."""

from __future__ import annotations

import time
import winreg
from typing import Any, Dict, List

import psutil

from logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel
from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider


class PerformanceCollector(TelemetryProvider):
    """Коллектор фактов производительности и точек автозагрузки."""

    def __init__(self) -> None:
        self._last_result: Optional[DomainAuditResult] = None

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает показатели производительности как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_result and self._last_result.metrics:
            metrics = self._last_result.metrics
            sensors.append(HardwareSensor(
                sensor_id="perf_cpu_percent",
                name="Загрузка CPU (%)",
                category="performance",
                value=float(metrics.get("cpu_percent", 0.0)),
                unit="%"
            ))
            sensors.append(HardwareSensor(
                sensor_id="perf_memory_percent",
                name="Загрузка RAM (%)",
                category="performance",
                value=float(metrics.get("memory_percent", 0.0)),
                unit="%"
            ))
            sensors.append(HardwareSensor(
                sensor_id="perf_uptime_hours",
                name="Время работы системы (ч)",
                category="performance",
                value=float(metrics.get("uptime_hours", 0.0)),
                unit="hours"
            ))
        return sensors

    def collect(self) -> DomainAuditResult:
        """Сбор данных о производительности и автозапуске."""
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []

        # Сбор показателей CPU, памяти и времени работы
        try:
            cpu_pct = float(psutil.cpu_percent(interval=0.1))
        except Exception:
            cpu_pct = 0.0

        try:
            mem = psutil.virtual_memory()
            mem_pct = float(mem.percent)
            mem_used = round(mem.used / (1024 ** 3), 2)
            mem_total = round(mem.total / (1024 ** 3), 2)
        except Exception:
            mem_pct, mem_used, mem_total = 0.0, 0.0, 0.0

        try:
            swap = psutil.swap_memory()
            swap_pct = float(swap.percent)
        except Exception:
            swap_pct = 0.0

        try:
            boot_time = psutil.boot_time()
            uptime_hours = round((time.time() - boot_time) / 3600.0, 2)
        except Exception:
            uptime_hours = 0.0

        startup_items = self._get_registry_startup()

        # Анализ высокой нагрузки на процессор и память
        if cpu_pct >= 90.0:
            findings.append(AuditFinding(
                id="perf_cpu_high",
                domain="performance",
                title=f"Критическая загрузка процессора: {cpu_pct:.1f}%",
                description="Процессор загружен более чем на 90%, возможны зависания и задержки отклика.",
                severity=RiskLevel.CRITICAL,
                remediation=RemediationAction(
                    action_type=ActionType.KILL_PROCESS,
                    command="",
                    description="Завершите процессы, утилизирующие большую часть ресурсов процессора.",
                    risk=RiskLevel.CAUTION,
                ),
            ))
        elif cpu_pct >= 75.0:
            findings.append(AuditFinding(
                id="perf_cpu_elevated",
                domain="performance",
                title=f"Повышенная нагрузка CPU: {cpu_pct:.1f}%",
                description="Процессор загружен выше нормального рабочего диапазона.",
                severity=RiskLevel.CAUTION,
            ))

        if mem_pct >= 90.0:
            findings.append(AuditFinding(
                id="perf_ram_high",
                domain="performance",
                title=f"Критическое заполнение оперативной памяти: {mem_pct:.1f}% ({mem_used} GB / {mem_total} GB)",
                description="Оперативная память почти исчерпана, система может активно использовать файл подкачки.",
                severity=RiskLevel.CRITICAL,
            ))

        if len(startup_items) > 15:
            findings.append(AuditFinding(
                id="perf_startup_crowded",
                domain="performance",
                title=f"Большое количество программ в автозагрузке ({len(startup_items)})",
                description="Множество программ в реестре автозапуска замедляют старт Windows.",
                severity=RiskLevel.CAUTION,
            ))

        metrics: Dict[str, Any] = {
            "cpu_percent": cpu_pct,
            "memory_percent": mem_pct,
            "memory_used_gb": mem_used,
            "memory_total_gb": mem_total,
            "swap_percent": swap_pct,
            "uptime_hours": uptime_hours,
            "startup_items_count": len(startup_items),
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity == RiskLevel.CAUTION for f in findings):
            status = "warning"

        result = DomainAuditResult(
            domain_name="performance",
            title_ru="Производительность и автозагрузка",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
        self._last_result = result
        return result


    def _get_registry_startup(self) -> List[Dict[str, str]]:
        """Извлечение записей из веток Run (HKCU и HKLM)."""
        items: List[Dict[str, str]] = []
        paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, subkey in paths:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(key, i)
                            hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
                            items.append({"name": name, "command": str(val), "location": f"{hive_name}\\{subkey}"})
                            i += 1
                        except OSError:
                            break
            except (OSError, PermissionError):
                pass
        return items
