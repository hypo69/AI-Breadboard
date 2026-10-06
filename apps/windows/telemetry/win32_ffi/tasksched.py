# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi - Tasksched
# =============================================================================
# Description:
#   Интерфейс к Task Scheduler 2.0 COM API Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.win32_ffi.tasksched import TaskSchedulerAPI
#
#     service = TaskSchedulerAPI()
#
# File: tasksched.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:35:00
# =============================================================================

from __future__ import annotations
"""Интерфейс к Task Scheduler 2.0 COM API Windows."""

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from logger import logger

TASK_STATE_UNKNOWN = 0
TASK_STATE_DISABLED = 1
TASK_STATE_QUEUED = 2
TASK_STATE_READY = 3
TASK_STATE_RUNNING = 4
TASK_STATE_MAP = {
    TASK_STATE_UNKNOWN: 'Unknown',
    TASK_STATE_DISABLED: 'Disabled',
    TASK_STATE_QUEUED: 'Queued',
    TASK_STATE_READY: 'Ready',
    TASK_STATE_RUNNING: 'Running'
}

TASK_ACTION_EXEC = 0
TASK_ACTION_COM_HANDLER = 5
TASK_ACTION_SEND_EMAIL = 6
TASK_ACTION_SHOW_MESSAGE = 7

TASK_TRIGGER_TYPE_MAP = {
    0: 'On event',
    1: 'Time',
    2: 'Daily',
    3: 'Weekly',
    4: 'Monthly',
    5: 'Monthly DOW',
    6: 'On idle',
    7: 'On registration',
    8: 'At startup',
    9: 'At logon',
    11: 'Session state change',
}


def _format_com_date(dt_obj: Any) -> Optional[str]:
    """Форматирует дату из COM API в читаемую строку.

    Args:
        dt_obj: COM объект даты или datetime.

    Returns:
        Optional[str]: Отформатированная дата или None.
    """
    if dt_obj is None:
        return None
    try:
        # COM дата 1899 года означает отсутствие даты
        if hasattr(dt_obj, 'year'):
            if dt_obj.year < 1910 or dt_obj.year > 2100:
                return None
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        s = str(dt_obj).strip()
        if '1899' in s or s == '' or s == 'None':
            return None
        return s
    except Exception:
        return None


class TaskSchedulerAPI:
    """Обертка над COM-интерфейсом Task Scheduler 2.0 (Schedule.Service)."""

    def __init__(self) -> None:
        """Инициализация COM-объекта планировщика."""
        self._service: Optional[Any] = None
        self._is_available = self._connect()

    def _connect(self) -> bool:
        """Подключение к локальной службе планировщика через COM."""
        try:
            import win32com.client
            self._service = win32com.client.Dispatch('Schedule.Service')
            self._service.Connect()
            return True
        except Exception as ex:
            logger.debug(f'COM-интерфейс Schedule.Service недоступен: {ex}')
            self._service = None
            return False

    @property
    def is_available(self) -> bool:
        """Доступность нативного COM-интерфейса планировщика."""
        return self._is_available and self._service is not None

    def get_all_tasks(self, max_tasks: int = 500) -> List[Dict[str, Any]]:
        """Рекурсивный сбор всех задач планировщика из всех папок.

        Args:
            max_tasks: Максимальное количество задач для выборки.

        Returns:
            List[Dict[str, Any]]: Список задач с путями, действиями и статусами.
        """
        if not self.is_available or self._service is None:
            return []
        tasks: List[Dict[str, Any]] = []
        try:
            root_folder = self._service.GetFolder('\\')
            self._scan_folder(root_folder, tasks, max_tasks)
        except Exception as ex:
            logger.debug(f'Ошибка при рекурсивном чтении задач планировщика COM: {ex}')
        return tasks

    def _scan_folder(self, folder: Any, tasks: List[Dict[str, Any]], max_tasks: int) -> None:
        """Рекурсивный обход папки планировщика.

        Args:
            folder: COM-объект ITaskFolder.
            tasks: Результирующий список задач.
            max_tasks: Лимит задач.
        """
        if len(tasks) >= max_tasks:
            return
        try:
            folder_tasks = folder.GetTasks(0)
            for task in folder_tasks:
                if len(tasks) >= max_tasks:
                    break
                try:
                    task_info = self._parse_task(task)
                    if task_info:
                        tasks.append(task_info)
                except Exception:
                    continue
            subfolders = folder.GetFolders(0)
            for sub in subfolders:
                if len(tasks) >= max_tasks:
                    break
                self._scan_folder(sub, tasks, max_tasks)
        except Exception as ex:
            logger.debug(f"Ошибка при сканировании папки '{getattr(folder, 'Path', '')}': {ex}")

    def _parse_task(self, task: Any) -> Optional[Dict[str, Any]]:
        """Парсинг свойств зарегистрированной задачи (IRegisteredTask)."""
        name = getattr(task, 'Name', '') or ''
        path = getattr(task, 'Path', '') or ''
        state_code = getattr(task, 'State', 0)
        state_name = TASK_STATE_MAP.get(state_code, 'Unknown')
        enabled = getattr(task, 'Enabled', True)
        next_run_raw = getattr(task, 'NextRunTime', None)
        last_run_raw = getattr(task, 'LastRunTime', None)
        last_result = getattr(task, 'LastTaskResult', 0) or 0

        next_run_str = _format_com_date(next_run_raw)
        last_run_str = _format_com_date(last_run_raw)

        actions_list: List[Dict[str, Any]] = []
        action_strs: List[str] = []
        author = ''
        triggers_list: List[str] = []

        try:
            definition = task.Definition
            if hasattr(definition, 'RegistrationInfo') and definition.RegistrationInfo:
                author = getattr(definition.RegistrationInfo, 'Author', '') or ''

            if hasattr(definition, 'Triggers') and definition.Triggers:
                for trig in definition.Triggers:
                    t_type = getattr(trig, 'Type', -1)
                    t_label = TASK_TRIGGER_TYPE_MAP.get(t_type, 'Custom')
                    if t_label not in triggers_list:
                        triggers_list.append(t_label)

            if hasattr(definition, 'Actions') and definition.Actions:
                for act in definition.Actions:
                    act_type = getattr(act, 'Type', -1)
                    if act_type == TASK_ACTION_EXEC:
                        exec_path = getattr(act, 'Path', '') or ''
                        args = getattr(act, 'Arguments', '') or ''
                        working_dir = getattr(act, 'WorkingDirectory', '') or ''
                        full_cmd = f'{exec_path} {args}'.strip()
                        actions_list.append({
                            'type': 'Exec',
                            'path': exec_path,
                            'arguments': args,
                            'working_directory': working_dir,
                            'command': full_cmd
                        })
                        action_strs.append(full_cmd)
                    elif act_type == TASK_ACTION_COM_HANDLER:
                        clsid = getattr(act, 'ClassId', '')
                        actions_list.append({'type': 'ComHandler', 'class_id': clsid})
                        action_strs.append(f'ComHandler:{clsid}')
        except Exception:
            pass

        schedule_type = ', '.join(triggers_list) if triggers_list else 'Custom'
        action_summary = ' ; '.join(action_strs) if action_strs else ''

        return {
            'TaskName': name,
            'task_name': name,
            'name': name,
            'TaskPath': path,
            'task_path': path,
            'State': state_name,
            'state': state_name,
            'status': state_name,
            'Enabled': enabled,
            'enabled': enabled,
            'NextRunTime': next_run_str,
            'next_run_time': next_run_str,
            'LastRunTime': last_run_str,
            'last_run_time': last_run_str,
            'LastTaskResult': last_result,
            'last_task_result': last_result,
            'Author': author,
            'author': author,
            'ScheduleType': schedule_type,
            'schedule_type': schedule_type,
            'Actions': action_summary,
            'action': action_summary,
            'ActionDetails': actions_list,
        }