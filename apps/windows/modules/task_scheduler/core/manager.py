# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler Core - Manager
# =============================================================================
# Description:
#   Менеджер управления и сбора телеметрии задач Windows Task Scheduler.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.task_scheduler.core.manager import TaskSchedulerManager
#
#     service = TaskSchedulerManager()
#     report = service.generate_report()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.task_scheduler.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:35:00
# =============================================================================

from __future__ import annotations
"""Менеджер управления и сбора телеметрии задач Windows Task Scheduler."""

import asyncio
import csv
import io
import subprocess
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
        """Инициализация менеджера планировщика задач."""
        pass

    def list_tasks(self) -> List[ScheduledTaskItem]:
        """Получение списка заданий планировщика.

        Returns:
            List[ScheduledTaskItem]: Список объектов задач.
        """
        tasks: List[ScheduledTaskItem] = []
        try:
            from apps.windows.telemetry.win32_ffi.tasksched import TaskSchedulerAPI
            api = TaskSchedulerAPI()
            raw_tasks = api.get_all_tasks()
            for t in raw_tasks:
                if isinstance(t, dict):
                    task_name = t.get('task_name') or t.get('TaskName') or ''
                    task_path = t.get('task_path') or t.get('TaskPath') or task_name
                    state = t.get('state') or t.get('State') or 'Ready'
                    enabled = t.get('enabled', True)
                    next_run = t.get('next_run_time') or t.get('NextRunTime')
                    last_run = t.get('last_run_time') or t.get('LastRunTime')
                    last_res = t.get('last_task_result') or t.get('LastTaskResult') or 0
                    author = t.get('author') or t.get('Author') or ''
                    action = t.get('action') or t.get('Actions') or ''
                    sched_type = t.get('schedule_type') or t.get('ScheduleType') or 'Custom'
                else:
                    task_name = getattr(t, 'name', '') or getattr(t, 'task_name', '')
                    task_path = getattr(t, 'path', '') or getattr(t, 'task_path', '') or task_name
                    state = getattr(t, 'state', 'Ready')
                    enabled = getattr(t, 'enabled', True)
                    next_run = str(getattr(t, 'next_run_time', '')) if getattr(t, 'next_run_time', None) else None
                    last_run = str(getattr(t, 'last_run_time', '')) if getattr(t, 'last_run_time', None) else None
                    last_res = getattr(t, 'last_task_result', 0) or 0
                    author = getattr(t, 'author', '') or ''
                    action = getattr(t, 'action', '') or ''
                    sched_type = getattr(t, 'schedule_type', 'Custom') or 'Custom'

                display_name = task_name or (task_path.split('\\')[-1] if task_path else 'Task')

                tasks.append(ScheduledTaskItem(
                    task_path=task_path,
                    task_name=display_name,
                    name=display_name,
                    state=state,
                    status=state,
                    enabled=enabled,
                    next_run_time=next_run,
                    last_run_time=last_run,
                    last_task_result=last_res,
                    author=author,
                    action=action,
                    schedule_type=sched_type
                ))
        except Exception as exc:
            logger.debug(f"[TaskSchedulerManager] Ошибка чтения через TaskSchedulerAPI: {exc}")

        if not tasks:
            tasks = self._list_tasks_via_cli()

        return tasks

    def _list_tasks_via_cli(self) -> List[ScheduledTaskItem]:
        """Резервный сбор задач через утилиту schtasks.exe."""
        tasks: List[ScheduledTaskItem] = []
        try:
            res = subprocess.run(
                ['schtasks.exe', '/Query', '/FO', 'CSV', '/V'],
                capture_output=True,
                text=True,
                timeout=15,
                encoding='cp866',
                errors='replace'
            )
            if res.returncode == 0 and res.stdout:
                reader = csv.DictReader(io.StringIO(res.stdout))
                for row in reader:
                    task_path = row.get('TaskName') or row.get('Имя задачи') or ''
                    if not task_path:
                        continue
                    task_name = task_path.split('\\')[-1] if task_path else 'Task'
                    status = row.get('Status') or row.get('Состояние') or 'Ready'
                    next_run = row.get('Next Run Time') or row.get('Время следующего запуска') or None
                    last_run = row.get('Last Run Time') or row.get('Время прошлого запуска') or None
                    author = row.get('Author') or row.get('Автор') or ''
                    action = row.get('Task To Run') or row.get('Запускаемая задача') or ''
                    sched_type = row.get('Schedule Type') or row.get('Тип расписания') or 'Custom'

                    tasks.append(ScheduledTaskItem(
                        task_path=task_path,
                        task_name=task_name,
                        name=task_name,
                        state=status,
                        status=status,
                        enabled=not ('disable' in status.lower() or 'отключ' in status.lower()),
                        next_run_time=next_run if next_run != 'N/A' else None,
                        last_run_time=last_run if last_run != 'N/A' else None,
                        author=author,
                        action=action,
                        schedule_type=sched_type
                    ))
        except Exception as exc:
            logger.warning(f"[TaskSchedulerManager] Резервный сбор schtasks.exe не удался: {exc}")

        return tasks

    def generate_report(self) -> TaskSchedulerReport:
        """Формирование сводного отчета планировщика.

        Returns:
            TaskSchedulerReport: Сводка по задачам и их состояниям.
        """
        tasks = self.list_tasks()
        ready = sum(1 for t in tasks if 'ready' in t.state.lower() or 'готов' in t.state.lower())
        running = sum(1 for t in tasks if 'run' in t.state.lower() or 'работ' in t.state.lower() or 'выполн' in t.state.lower())
        disabled = sum(1 for t in tasks if 'disable' in t.state.lower() or 'отключ' in t.state.lower())
        return TaskSchedulerReport(
            total_tasks=len(tasks),
            ready_tasks=ready,
            running_tasks=running,
            disabled_tasks=disabled,
            tasks=tasks,
            timestamp=datetime.now().isoformat()
        )

    async def execute_task_action(self, req: TaskActionRequest) -> Dict[str, Any]:
        """Выполнение действия с заданием планировщика Windows.

        Args:
            req: Параметры запроса (task_path, action, dry_run).

        Returns:
            Dict[str, Any]: Результат выполнения операции.
        """
        task_target = req.task_path or req.task_name or ''
        if not task_target:
            return {
                'status': 'ERROR',
                'task_path': '',
                'action': req.action,
                'message': 'Не указано имя или путь задачи планировщика.'
            }

        act_norm = req.action.lower().replace('schtasks_', '')

        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'task_path': task_target,
                'action': req.action,
                'message': f"Симуляция {req.action} для задания '{task_target}' выполнена успешно."
            }

        return await asyncio.to_thread(self._run_cli_action, task_target, act_norm)

    def _run_cli_action(self, task_target: str, action: str) -> Dict[str, Any]:
        """Запуск команды schtasks.exe для выполнения действия.

        Args:
            task_target: Имя или путь задачи.
            action: Нормализованное действие (run, enable, disable, stop, delete).

        Returns:
            Dict[str, Any]: Результат выполнения.
        """
        cmd: List[str] = ['schtasks.exe']
        if action in ('run', 'start'):
            cmd.extend(['/Run', '/TN', task_target])
        elif action in ('enable', 'on'):
            cmd.extend(['/Change', '/TN', task_target, '/Enable'])
        elif action in ('disable', 'off'):
            cmd.extend(['/Change', '/TN', task_target, '/Disable'])
        elif action in ('stop', 'end'):
            cmd.extend(['/End', '/TN', task_target])
        elif action in ('delete', 'remove'):
            cmd.extend(['/Delete', '/TN', task_target, '/F'])
        else:
            return {
                'status': 'ERROR',
                'task_path': task_target,
                'action': action,
                'message': f"Неизвестное действие: {action}"
            }

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='cp866',
                errors='replace'
            )
            out = (res.stdout or '').strip()
            err = (res.stderr or '').strip()
            success = res.returncode == 0

            return {
                'status': 'SUCCESS' if success else 'ERROR',
                'task_path': task_target,
                'action': action,
                'message': out or err or ('Операция выполнена успешно' if success else 'Сбой выполнения'),
                'returncode': res.returncode
            }
        except Exception as exc:
            logger.error(f"[TaskSchedulerManager] Ошибка выполнения {cmd}: {exc}")
            return {
                'status': 'ERROR',
                'task_path': task_target,
                'action': action,
                'message': str(exc),
                'returncode': -1
            }


__all__ = ['TaskSchedulerManager']
