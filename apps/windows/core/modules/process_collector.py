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
from typing import Any, Dict, List, Optional

import psutil

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel
from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider
from apps.windows.core.process_audit_manager import ProcessAuditManager
from apps.windows.telemetry.service import TelemetryLoggerService


class ProcessCollector(TelemetryProvider):
    """Коллектор фактов о процессах Windows."""

    def __init__(self) -> None:
        self._last_result: Optional[DomainAuditResult] = None
        self._audit_manager: Optional[ProcessAuditManager] = None

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает показатели процессов как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_result and self._last_result.metrics:
            metrics = self._last_result.metrics
            sensors.append(HardwareSensor(
                sensor_id="proc_total",
                name="Всего процессов",
                category="processes",
                value=float(metrics.get("total_processes_count", 0)),
                unit="count"
            ))
            sensors.append(HardwareSensor(
                sensor_id="proc_new_last_hour",
                name="Новых процессов (последний час)",
                category="processes",
                value=float(metrics.get("new_processes_last_hour", 0)),
                unit="count"
            ))
            sensors.append(HardwareSensor(
                sensor_id="proc_handle_leaks",
                name="Кандидаты на утечку дескрипторов",
                category="processes",
                value=float(metrics.get("handle_leak_candidates_count", 0)),
                unit="count"
            ))
        return sensors

    def collect(self) -> DomainAuditResult:
        """Сбор данных о процессах и дереве выполнения."""
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        processes = []
        suspicious_paths = [r"c:\users\default", r"c:\windows\temp", r"appdata\local\temp"]
        handle_leak_candidates = []
        new_processes_last_hour = 0

        # Сбор событий запуска программ через ProcessAuditManager
        try:
            if self._audit_manager is None:
                from apps.windows.api.wevtapi import WevtAPI
                self._audit_manager = ProcessAuditManager(WevtAPI())
            
            # Получаем историю запусков за последний час
            history = self._audit_manager.get_process_execution_history(
                limit=100,
                filter_process=None,
                filter_user=None,
            )
            
            # Фильтруем события за последний час
            one_hour_ago = time.time() - 3600
            for ev in history:
                timestamp_str = ev.get("timestamp", "")
                if timestamp_str:
                    try:
                        # Парсим ISO формат времени
                        from datetime import datetime
                        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).timestamp()
                        if ts > one_hour_ago:
                            new_processes_last_hour += 1
                            # Записываем корреляцию запуска процесса
                            try:
                                telemetry_service = TelemetryLoggerService.get_instance()
                                telemetry_service.record_event(
                                    event_type="process_start",
                                    event_details={
                                        "process_name": ev.get("process_name", ""),
                                        "executable_path": ev.get("executable_path", ""),
                                        "command_line": ev.get("command_line", ""),
                                        "user": ev.get("user", ""),
                                        "pid": ev.get("process_id"),
                                    },
                                )
                            except Exception as ex:
                                logger.debug(f"Не удалось записать корреляцию процесса: {ex}")
                    except Exception:
                        pass
        except Exception as ex:
            logger.debug(f"Не удалось получить историю запусков процессов: {ex}")

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'cpu_percent', 'memory_percent', 'num_threads']):
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
                
                # Проверка утечки дескрипторов (handle leak) - процесс с аномально большим числом потоков
                num_threads = info.get('num_threads') or 0
                if num_threads > 500:
                    handle_leak_candidates.append({
                        "pid": info.get('pid'),
                        "name": info.get('name'),
                        "thread_count": num_threads,
                    })
                    findings.append(
                        AuditFinding(
                            domain="processes",
                            category="handle_leak_candidate",
                            title=f"Потенциальная утечка дескрипторов: {info.get('name')}",
                            description=f"Процесс {info.get('name')} (PID {info.get('pid')}) имеет аномально большое количество потоков: {num_threads}.",
                            severity=RiskLevel.CAUTION,
                            evidence=info,
                        )
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        metrics: Dict[str, Any] = {
            "total_processes_count": len(processes),
            "new_processes_last_hour": new_processes_last_hour,
            "handle_leak_candidates_count": len(handle_leak_candidates),
            "handle_leak_candidates": handle_leak_candidates,
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        result = DomainAuditResult(
            domain_name="processes",
            title_ru="Интеллект процессов (Process Explorer)",
            status="warning" if findings else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
        self._last_result = result
        return result

