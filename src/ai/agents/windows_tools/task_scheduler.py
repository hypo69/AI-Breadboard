# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Task Scheduler Tools Module
# =============================================================================
# Description:
#   Инструменты аудита и управления задачами планировщика Windows Task Scheduler
#   (apps.windows.modules.task_scheduler).
#   Включают:
#     1. Инспекция и аудит запланированных задач (windows_task_scheduler_audit)
#     2. Выполнение действий над задачами планировщика SafeOps (windows_task_scheduler_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.task_scheduler import windows_task_scheduler_audit
#     res = await windows_task_scheduler_audit(action="summary")
#
# File: task_scheduler.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:36:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления планировщиком задач Windows для ИИ-агентов."""

import asyncio
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from logger import logger

try:
    from langchain_core.tools import tool
except ImportError:
    class DummyTool:
        def __init__(self, func):
            self.func = func
            self.__name__ = getattr(func, '__name__', 'DummyTool')
            self.__doc__ = getattr(func, '__doc__', '')

        def invoke(self, input_data=None, **kwargs):
            if isinstance(input_data, dict):
                return self.func(**input_data)
            elif input_data is not None:
                return self.func(input_data, **kwargs)
            return self.func(**kwargs)

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    def tool(func=None, *args, **kwargs):
        if func is not None:
            return DummyTool(func)
        return lambda f: DummyTool(f)


def _to_serializable(obj: Any) -> Any:
    """Вспомогательное преобразование Pydantic и dataclass объектов в словарь."""
    if isinstance(obj, (int, float, bool, str)) or obj is None:
        return obj
    if is_dataclass(obj):
        return _to_serializable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: _to_serializable(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    return str(obj)


# =============================================================================
# Блок 1: Инспекция задач планировщика Windows
# =============================================================================

@tool
async def windows_task_scheduler_audit(
    action: str = "summary",
    limit: int = 50,
) -> str:
    """Глубокий аудит и инспекция задач планировщика Windows Task Scheduler.

    Args:
        action: Режим аудита:
            - 'summary': сводный статус планировщика (всего задач, активных, отключенных, упавших с ошибкой)
            - 'list': список всех задач (путь, название, статус, время следующего/прошлого запуска, авторы)
            - 'report': полный структурированный отчёт планировщика задач
        limit: Ограничение выдачи количества задач (по умолчанию 50).

    Returns:
        JSON с результатами аудита планировщика задач.
    """
    try:
        from apps.windows.modules.task_scheduler.core.manager import TaskSchedulerManager

        mgr = TaskSchedulerManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            report = await loop.run_in_executor(None, mgr.generate_report)
            return json.dumps({
                "status": "ok",
                "action": act,
                "summary": _to_serializable(getattr(report, "summary", report)),
            }, ensure_ascii=False)

        elif act == "list":
            tasks = await loop.run_in_executor(None, mgr.list_tasks)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_tasks": len(tasks),
                "tasks": _to_serializable(tasks[:limit]),
            }, ensure_ascii=False)

        elif act == "report":
            report = await loop.run_in_executor(None, mgr.generate_report)
            return json.dumps({
                "status": "ok",
                "action": act,
                "report": _to_serializable(report),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.task_scheduler] Ошибка аудита планировщика задач ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление задачами планировщика SafeOps
# =============================================================================

@tool
async def windows_task_scheduler_action(
    task_path: str,
    action: str = "run",
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Управление состоянием и запуск заданий планировщика Windows SafeOps.

    Args:
        task_path: Полный путь к задаче (например: '\\Microsoft\\Windows\\Defrag\\ScheduledDefrag').
        action: Тип действия ('run', 'enable', 'disable', 'delete').
        dry_run: Режим симуляции (по умолчанию True для защиты системных задач).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом выполнения или симуляции операции над задачей.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "task_path": task_path,
                "action": action,
                "dry_run": True,
                "message": f"Симуляция выполнения действия '{action}' для задачи '{task_path}' прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        from apps.windows.modules.task_scheduler.core.manager import TaskSchedulerManager
        from apps.windows.modules.task_scheduler.core.models import TaskActionRequest

        mgr = TaskSchedulerManager()
        loop = asyncio.get_running_loop()

        req = TaskActionRequest(task_path=task_path, action=action)
        res = await loop.run_in_executor(None, mgr.execute_task_action, req)
        return json.dumps({
            "status": "ok",
            "task_path": task_path,
            "action": action,
            "result": _to_serializable(res),
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.task_scheduler] Ошибка вызова операции '{action}' над задачей '{task_path}': {e}", exc_info=True)
        return json.dumps({"status": "error", "task_path": task_path, "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_TASK_SCHEDULER_TOOLS = [
    windows_task_scheduler_audit,
    windows_task_scheduler_action,
]
