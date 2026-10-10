# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core Audits - Tasks Collector
# =============================================================================
# Description:
#   Коллектор аудита задач планировщика Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.audits.tasks_collector import TasksCollector
#
#     service = TasksCollector()
#
# File: tasks_collector.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core.audits
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Коллектор аудита задач планировщика Windows."""

import json
import subprocess
import time
from typing import Any, Dict, List
from logger import logger
from apps.windows.telemetry.win32_ffi.tasksched import TaskSchedulerAPI
from apps.windows.sdk.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel

class TasksCollector:
    """Коллектор фактов о задачах планировщика Windows с поддержкой COM API."""

    def __init__(self) -> None:
        """Инициализация коллектора с поддержкой COM API."""
        self._com_api = TaskSchedulerAPI()

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
            action_str = str(t.get('Actions', '') or t.get('TaskPath', ''))
            task_name = t.get('TaskName', 'Unknown')
            action_lower = action_str.lower()
            if '-encodedcommand' in action_lower or '-enc ' in action_lower or '-windowstyle hidden' in action_lower:
                suspicious_tasks.append(t)
                findings.append(AuditFinding(domain='tasks', category='suspicious_task', title=f'Подозрительная задача планировщика: {task_name}', description=f'Задача содержит закодированную или скрытую команду: {action_str}', severity=RiskLevel.CRITICAL, evidence=t, actions=[RemediationAction(action_id=f"disable_task_{task_name.replace(' ', '_')}", action_type=ActionType.DISABLE_TASK, title=f'Отключить задачу {task_name}', description='Отключение подозрительной задачи планировщика', target=task_name, risk=RiskLevel.CAUTION, execution_command=f"schtasks /Change /TN '{task_name}' /Disable")]))
        metrics: Dict[str, Any] = {'total_tasks_count': len(tasks), 'suspicious_tasks_count': len(suspicious_tasks), 'engine': 'Task Scheduler 2.0 COM API' if self._com_api.is_available else 'PowerShell Fallback'}
        duration_ms = (time.perf_counter() - start_t) * 1000
        return DomainAuditResult(domain_name='tasks', title_ru='Планировщик заданий (Task Scheduler)', status='critical' if suspicious_tasks else 'ok', findings=findings, metrics=metrics, scan_duration_ms=round(duration_ms, 2))

    def _get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Получение задач планировщика через каскад: COM API -> PowerShell."""
        if self._com_api.is_available:
            try:
                tasks = self._com_api.get_all_tasks(max_tasks=500)
                if tasks:
                    return tasks
            except Exception as ex:
                logger.debug(f'Сбой COM сбора задач, fallback на PowerShell: {ex}')
        cmd = ['powershell', '-NoProfile', '-Command', "Get-ScheduledTask | Select-Object TaskName, TaskPath, State, @{N='Actions';E={$_.Actions.Execute}} | ConvertTo-Json -Compress"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
        except Exception as e:
            logger.debug(f'Ошибка при вызове Get-ScheduledTask: {e}')
        return []
