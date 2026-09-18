# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Task Scheduler 2.0 COM API Wrapper
# =============================================================================
# Description:
#   High-performance Task Scheduler 2.0 COM client (Schedule.Service).
#   Enumerates scheduled tasks recursively across all folders, extracts triggers,
#   actions, hidden arguments, and execution states without spawning PowerShell.
#
# Examples:
#   >>> from apps.windows.api.tasksched import TaskSchedulerAPI
#   >>> ts = TaskSchedulerAPI()
#   >>> tasks = ts.get_all_tasks()
#
# File: tasksched.py
# Project: AI-Breadboard
# Package: apps.windows.api
# Class: TaskSchedulerAPI
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Интерфейс к Task Scheduler 2.0 COM API Windows."""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from src.logger import logger

# TASK_STATE перечисление
TASK_STATE_UNKNOWN = 0
TASK_STATE_DISABLED = 1
TASK_STATE_QUEUED = 2
TASK_STATE_READY = 3
TASK_STATE_RUNNING = 4

TASK_STATE_MAP = {
    TASK_STATE_UNKNOWN: "Unknown",
    TASK_STATE_DISABLED: "Disabled",
    TASK_STATE_QUEUED: "Queued",
    TASK_STATE_READY: "Ready",
    TASK_STATE_RUNNING: "Running",
}

# TASK_ACTION_TYPE
TASK_ACTION_EXEC = 0
TASK_ACTION_COM_HANDLER = 5
TASK_ACTION_SEND_EMAIL = 6
TASK_ACTION_SHOW_MESSAGE = 7


class TaskSchedulerAPI:
    """Обертка над COM-интерфейсом Task Scheduler 2.0 (Schedule.Service)."""

    def __init__(self) -> None:
        """Инициализация COM-объекта планировщика."""
        self._service: Optional[Any] = None
        self._is_available = self._connect()

    def _connect(self) -> bool:
        """Подключение к локальной службе планировщика через COM."""
        try:
            import win32com.client  # type: ignore
            self._service = win32com.client.Dispatch("Schedule.Service")
            self._service.Connect()
            return True
        except Exception as ex:
            logger.debug(f"COM-интерфейс Schedule.Service недоступен: {ex}")
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
            root_folder = self._service.GetFolder("\\")
            self._scan_folder(root_folder, tasks, max_tasks)
        except Exception as ex:
            logger.debug(f"Ошибка при рекурсивном чтении задач планировщика COM: {ex}")

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
            # 1. Сбор задач в текущей папке
            folder_tasks = folder.GetTasks(0)  # 0 = TASK_ENUM_HIDDEN | TASK_ENUM_NORMAL
            for task in folder_tasks:
                if len(tasks) >= max_tasks:
                    break
                try:
                    task_info = self._parse_task(task)
                    if task_info:
                        tasks.append(task_info)
                except Exception:
                    continue

            # 2. Рекурсивный переход в подпапки
            subfolders = folder.GetFolders(0)
            for sub in subfolders:
                if len(tasks) >= max_tasks:
                    break
                self._scan_folder(sub, tasks, max_tasks)
        except Exception as ex:
            logger.debug(f"Ошибка при сканировании папки '{getattr(folder, 'Path', '')}': {ex}")

    def _parse_task(self, task: Any) -> Optional[Dict[str, Any]]:
        """Парсинг свойств зарегистрированной задачи (IRegisteredTask)."""
        name = getattr(task, "Name", "")
        path = getattr(task, "Path", "")
        state_code = getattr(task, "State", 0)
        state_name = TASK_STATE_MAP.get(state_code, "Unknown")
        enabled = getattr(task, "Enabled", True)

        actions_list: List[Dict[str, Any]] = []
        action_strs: List[str] = []

        try:
            definition = task.Definition
            actions = definition.Actions
            for act in actions:
                act_type = getattr(act, "Type", -1)
                if act_type == TASK_ACTION_EXEC:
                    exec_path = getattr(act, "Path", "") or ""
                    args = getattr(act, "Arguments", "") or ""
                    working_dir = getattr(act, "WorkingDirectory", "") or ""
                    full_cmd = f"{exec_path} {args}".strip()
                    actions_list.append({
                        "type": "Exec",
                        "path": exec_path,
                        "arguments": args,
                        "working_directory": working_dir,
                        "command": full_cmd,
                    })
                    action_strs.append(full_cmd)
                elif act_type == TASK_ACTION_COM_HANDLER:
                    clsid = getattr(act, "ClassId", "")
                    actions_list.append({"type": "ComHandler", "class_id": clsid})
                    action_strs.append(f"ComHandler:{clsid}")
        except Exception:
            pass

        return {
            "TaskName": name,
            "TaskPath": path,
            "State": state_name,
            "Enabled": enabled,
            "Actions": " ; ".join(action_strs) if action_strs else "",
            "ActionDetails": actions_list,
        }
