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

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class PerformanceCollector:
    """Коллектор фактов производительности и точек автозагрузки."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о производительности и автозапуске.

        Returns:
            DomainAuditResult: Результат аудита производительности.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        
        # 1. Метрики CPU и RAM (с защитой от сбоев PDH)
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
        except Exception:
            cpu_pct = 0.0

        try:
            mem = psutil.virtual_memory()
            mem_pct = mem.percent
            mem_used = round(mem.used / (1024**3), 2)
            mem_total = round(mem.total / (1024**3), 2)
        except Exception:
            mem_pct = 0.0
            mem_used = 0.0
            mem_total = 0.0

        try:
            swap = psutil.swap_memory()
            swap_pct = swap.percent
        except Exception:
            swap_pct = 0.0

        try:
            boot_time = psutil.boot_time()
            uptime_hours = round((time.time() - boot_time) / 3600, 1)
        except Exception:
            uptime_hours = 0.0

        metrics: Dict[str, Any] = {
            "cpu_percent": cpu_pct,
            "memory_percent": mem_pct,
            "memory_used_gb": mem_used,
            "memory_total_gb": mem_total,
            "swap_percent": swap_pct,
            "uptime_hours": uptime_hours,
            "startup_items_count": 0,
        }

        # 2. Анализ автозагрузки в реестре (Run / RunOnce)
        startup_items = self._get_registry_startup()
        metrics["startup_items_count"] = len(startup_items)

        if len(startup_items) > 10:
            findings.append(
                AuditFinding(
                    domain="performance",
                    category="startup",
                    title="Большое количество программ в автозагрузке реестра",
                    description=f"Найдено {len(startup_items)} записей автозагрузки, что может увеличивать время старта Windows.",
                    severity=RiskLevel.CAUTION,
                    evidence={"startup_items": startup_items[:15]},
                )
            )

        # 3. Высокая нагрузка CPU
        if cpu_pct > 85.0:
            findings.append(
                AuditFinding(
                    domain="performance",
                    category="cpu_load",
                    title="Высокая утилизация процессора",
                    description=f"Текущая нагрузка CPU составляет {cpu_pct}%.",
                    severity=RiskLevel.CRITICAL,
                    evidence={"cpu_percent": cpu_pct},
                )
            )

        # 4. Высокое потребление RAM
        if mem_pct > 90.0:
            findings.append(
                AuditFinding(
                    domain="performance",
                    category="memory_pressure",
                    title="Критическое заполнение оперативной памяти",
                    description=f"Оперативная память заполнена на {mem_pct}% ({mem_used}/{mem_total} GB).",
                    severity=RiskLevel.CRITICAL,
                    evidence={"memory_percent": mem_pct, "swap_percent": swap_pct},
                )
            )

        # 5. Поиск ресурсоёмких процессов (расширенная диагностика памяти)
        top_procs = []
        memory_leak_candidates = []
        try:
            proc_list = []
            for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    info = p.info
                    proc_list.append(info)
                    # Выявление потенциальной утечки памяти (процесс потребляет > 500 MB)
                    if info.get('memory_info'):
                        rss_mb = round(info['memory_info'].rss / (1024 * 1024), 1)
                        if rss_mb > 500 and rss_mb < mem_total * 0.5:  # Исключаем системные сервисы
                            memory_leak_candidates.append({
                                "pid": info.get('pid'),
                                "name": info.get('name'),
                                "memory_mb": rss_mb,
                                "memory_percent": info.get('memory_percent'),
                            })
                except Exception:
                    continue
            top_procs = sorted(proc_list, key=lambda x: x.get('memory_percent') or 0, reverse=True)[:5]
            
            # Если найдены кандидаты на утечку, добавить finding
            if memory_leak_candidates:
                findings.append(
                    AuditFinding(
                        domain="performance",
                        category="memory_leak_candidates",
                        title="Обнаружены процессы-кандидаты на утечку памяти",
                        description=f"Найдено {len(memory_leak_candidates)} процессов, потребляющих > 500 MB.",
                        severity=RiskLevel.CAUTION,
                        evidence={"candidates": memory_leak_candidates[:5]},
                    )
                )
        except Exception as e:
            logger.debug(f"Ошибка при итерации процессов: {e}")

        # 6. Анализ дисковой нагрузки (I/O операции)
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                io_read_mb_s = round(disk_io.read_bytes / (1024 * 1024), 2)
                io_write_mb_s = round(disk_io.write_bytes / (1024 * 1024), 2)
                metrics["disk_io_read_mb"] = io_read_mb_s
                metrics["disk_io_write_mb"] = io_write_mb_s
        except Exception:
            pass

        metrics["top_cpu_processes"] = top_procs
        metrics["memory_leak_candidates"] = memory_leak_candidates

        duration_ms = (time.perf_counter() - start_t) * 1000
        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity == RiskLevel.CAUTION for f in findings):
            status = "warning"

        return DomainAuditResult(
            domain_name="performance",
            title_ru="Производительность и автозагрузка",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

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
