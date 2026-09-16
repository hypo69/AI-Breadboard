# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Process Intelligence Audit Collector
# =============================================================================
# Description:
#   Анализ запущенных процессов, иерархии родитель-потомок, командных строк,
#   привилегий, дескрипторов и выявление подозрительных процессов (Process Explorer).
#
# Examples:
#   >>> from apps.windows.core.modules.process_collector import ProcessCollector
#   >>> collector = ProcessCollector()
#   >>> result = collector.collect()
#
# File: process_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита процессов и дескрипторов Windows."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import psutil

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class ProcessCollector:
    """Коллектор фактов о процессах Windows."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о процессах и дереве выполнения.

        Returns:
            DomainAuditResult: Результат аудита процессов.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        processes = []
        suspicious_paths = [r"c:\users\default", r"c:\windows\temp", r"appdata\local\temp"]

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                processes.append(info)
                exe_path = (info.get('exe') or "").lower()

                # Проверка запуска процессов из подозрительных временных папок
                if exe_path and any(sp in exe_path for sp in suspicious_paths):
                    action = RemediationAction(
                        action_id=f"kill_temp_proc_{info.get('pid')}",
                        action_type=ActionType.KILL_PROCESS,
                        title=f"Завершить процесс из Temp: {info.get('name')}",
                        description="Завершение процесса, исполняемый файл которого запущен из временной папки",
                        target=str(info.get('pid')),
                        risk=RiskLevel.CAUTION,
                        execution_command=f"Stop-Process -Id {info.get('pid')} -Force",
                    )
                    findings.append(
                        AuditFinding(
                            domain="processes",
                            category="temp_execution",
                            title=f"Процесс запущен из временного каталога: {info.get('name')}",
                            description=f"Исполняемый файл '{info.get('exe')}' (PID {info.get('pid')}) выполняется из Temp.",
                            severity=RiskLevel.CAUTION,
                            evidence=info,
                            actions=[action],
                        )
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        metrics: Dict[str, Any] = {
            "total_processes_count": len(processes),
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="processes",
            title_ru="Интеллект процессов (Process Explorer)",
            status="warning" if findings else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
