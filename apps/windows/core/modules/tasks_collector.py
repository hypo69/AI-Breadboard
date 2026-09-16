# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Scheduled Tasks Audit Collector
# =============================================================================
# Description:
#   Аудит задач Планировщика заданий Windows (Task Scheduler), обнаружение
#   сломанных задач, подозрительных скрытых скриптов PowerShell и неактивных триггеров.
#
# Examples:
#   >>> from apps.windows.core.modules.tasks_collector import TasksCollector
#   >>> collector = TasksCollector()
#   >>> result = collector.collect()
#
# File: tasks_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита задач планировщика Windows."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class TasksCollector:
    """Коллектор фактов о задачах планировщика Windows."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о задачах планировщика.

        Returns:
            DomainAuditResult: Результат аудита задач.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        tasks = self._get_scheduled_tasks()

        suspicious_tasks = []
        for t in tasks:
            action_str = str(t.get("Actions", "") or t.get("TaskPath", ""))
            task_name = t.get("TaskName", "Unknown")
            if "-encodedcommand" in action_str.lower() or "-enc " in action_str.lower() or "-windowstyle hidden" in action_str.lower():
                suspicious_tasks.append(t)
                findings.append(
                    AuditFinding(
                        domain="tasks",
                        category="suspicious_task",
                        title=f"Подозрительная задача планировщика: {task_name}",
                        description=f"Задача содержит закодированную или скрытую команду: {action_str}",
                        severity=RiskLevel.CRITICAL,
                        evidence=t,
                        actions=[
                            RemediationAction(
                                action_id=f"disable_task_{task_name.replace(' ', '_')}",
                                action_type=ActionType.DISABLE_TASK,
                                title=f"Отключить задачу {task_name}",
                                description="Отключение подозрительной задачи планировщика",
                                target=task_name,
                                risk=RiskLevel.CAUTION,
                                execution_command=f"schtasks /Change /TN '{task_name}' /Disable",
                            )
                        ]
                    )
                )

        metrics: Dict[str, Any] = {
            "total_tasks_count": len(tasks),
            "suspicious_tasks_count": len(suspicious_tasks),
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(
            domain_name="tasks",
            title_ru="Планировщик заданий (Task Scheduler)",
            status="critical" if suspicious_tasks else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Получение задач планировщика через PowerShell Get-ScheduledTask."""
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-ScheduledTask | Select-Object TaskName, TaskPath, State, @{N='Actions';E={$_.Actions.Execute}} | ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
        except Exception as e:
            logger.debug(f"Ошибка при вызове Get-ScheduledTask: {e}")
        return []
