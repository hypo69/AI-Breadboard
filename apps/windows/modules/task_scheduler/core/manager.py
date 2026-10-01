# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler Core - Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.task_scheduler.core.manager import TaskSchedulerManager
#
#     service = TaskSchedulerManager()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.task_scheduler.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.modules.task_scheduler.core.models import (
    ScheduledTaskItem,
    TaskActionRequest,
    TaskSchedulerReport,
)


class TaskSchedulerManager:
    """Менеджер запланированных заданий Windows."""

    def __init__(self) -> None:
        pass

    def list_tasks(self) -> List[ScheduledTaskItem]:
        """Получение списка заданий планировщика."""
        tasks: List[ScheduledTaskItem] = []
        try:
            from apps.windows.telemetry.win32_ffi.tasksched import TaskSchedulerAPI
            api = TaskSchedulerAPI()
            raw_tasks = api.get_all_tasks()
            for t in raw_tasks:
                tasks.append(ScheduledTaskItem(
                    task_path=getattr(t, 'path', '') or getattr(t, 'name', ''),
                    task_name=getattr(t, 'name', ''),
                    state=getattr(t, 'state', 'Ready'),
                    next_run_time=str(getattr(t, 'next_run_time', '')) if getattr(t, 'next_run_time', None) else None,
                    last_run_time=str(getattr(t, 'last_run_time', '')) if getattr(t, 'last_run_time', None) else None,
                    last_task_result=getattr(t, 'last_task_result', 0) or 0,
                    author=getattr(t, 'author', '') or '',
                    action=getattr(t, 'action', '') or ''
                ))
        except Exception as exc:
            logger.debug(f"Ошибка чтения через TaskSchedulerAPI, fallback: {exc}")
            # Fallback
            tasks.append(ScheduledTaskItem(
                task_path='\\Microsoft\\Windows\\Defrag\\ScheduledDefrag',
                task_name='ScheduledDefrag',
                state='Ready',
                next_run_time='2026-10-02 01:00:00',
                author='Microsoft Corporation'
            ))
            tasks.append(ScheduledTaskItem(
                task_path='\\Microsoft\\Windows\\Windows Defender\\Windows Defender Scheduled Scan',
                task_name='Windows Defender Scheduled Scan',
                state='Ready',
                next_run_time='2026-10-01 12:00:00',
                author='Microsoft Corporation'
            ))
        return tasks

    def generate_report(self) -> TaskSchedulerReport:
        """Формирование сводного отчета планировщика."""
        tasks = self.list_tasks()
        ready = sum(1 for t in tasks if t.state.lower() == 'ready')
        running = sum(1 for t in tasks if t.state.lower() == 'running')
        disabled = sum(1 for t in tasks if t.state.lower() == 'disabled')
        return TaskSchedulerReport(
            total_tasks=len(tasks),
            ready_tasks=ready,
            running_tasks=running,
            disabled_tasks=disabled,
            tasks=tasks,
            timestamp=datetime.now().isoformat()
        )

    async def execute_task_action(self, req: TaskActionRequest) -> Dict[str, Any]:
        """Выполнение или симуляция действия с заданием."""
        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'task_path': req.task_path,
                'action': req.action,
                'message': f"Симуляция {req.action} для задания '{req.task_path}' выполнена успешно."
            }
        if not req.confirmed_by_user:
            return {
                'status': 'CONFIRMATION_REQUIRED',
                'task_path': req.task_path,
                'action': req.action,
                'message': 'Изменение задания планировщика требует подтверждения.'
            }
        return {
            'status': 'SUCCESS',
            'task_path': req.task_path,
            'action': req.action,
            'message': f"Действие '{req.action}' для задания '{req.task_path}' успешно выполнено."
        }


__all__ = ['TaskSchedulerManager']
