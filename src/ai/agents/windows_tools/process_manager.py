# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Process Manager Tools Module
# =============================================================================
# Description:
#   Инструменты инспекции, категоризации и управления процессами Windows
#   (apps.windows.modules.process_manager).
#   Включают в себя:
#     1. Обзор процессов, топ по CPU/памяти и категоризацию (windows_process_list)
#     2. Завершение процесса/дерева процессов с поддержкой SafeOps/dry_run (windows_process_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.process_manager import windows_process_list
#     res = await windows_process_list(action="summary")
#
# File: process_manager.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:06:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления процессами Windows для ИИ-агентов."""

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
    """Вспомогательное преобразование объектов Pydantic и dataclass в словарь."""
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
# Блок 1: Инспекция и категоризация процессов
# =============================================================================

@tool
async def windows_process_list(
    action: str = "summary",
    limit: int = 10,
) -> str:
    """Инспекция активных процессов Windows, их ресурсов и категоризации.

    Args:
        action: Режим инспекции процессов:
            - 'summary': краткая сводка системных ресурсов и топ-5 по CPU/памяти
            - 'categorized': отчёт по группам (Apps, Background, Windows processes)
            - 'top_cpu': топ процессов по загрузке CPU
            - 'top_memory': топ процессов по использованию ОЗУ (в МБ)
            - 'full': полный список всех активных процессов
        limit: Ограничение количества записей для топов или списков (по умолчанию 10).

    Returns:
        JSON со списком или сводкой процессов Windows.
    """
    try:
        from apps.windows.modules.process_manager.core.manager import ProcessManager

        pm = ProcessManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            report = await loop.run_in_executor(None, pm.generate_report)
            summary_data = {
                "total_processes": report.total_processes,
                "total_threads": report.total_threads,
                "total_memory_used_mb": report.total_memory_used_mb,
                "apps_count": report.apps_count,
                "background_count": report.background_count,
                "windows_count": report.windows_count,
                "top_cpu_processes": _to_serializable(report.top_cpu_processes[:limit]),
                "top_memory_processes": _to_serializable(report.top_memory_processes[:limit]),
            }
            return json.dumps({"status": "ok", "action": act, "summary": summary_data}, ensure_ascii=False)

        elif act == "categorized":
            report = await loop.run_in_executor(None, pm.generate_categorized_report)
            return json.dumps({"status": "ok", "action": act, "categorized": _to_serializable(report)}, ensure_ascii=False)

        elif act in ("top_cpu", "top_memory"):
            report = await loop.run_in_executor(None, pm.generate_report)
            target = report.top_cpu_processes if act == "top_cpu" else report.top_memory_processes
            return json.dumps({"status": "ok", "action": act, "processes": _to_serializable(target[:limit])}, ensure_ascii=False)

        elif act == "full":
            procs = await loop.run_in_executor(None, pm.list_processes)
            return json.dumps({"status": "ok", "action": act, "total": len(procs), "processes": _to_serializable(procs[:limit])}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.process_manager] Ошибка выполнения process_list ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Завершение процессов (Kill Process)
# =============================================================================

@tool
async def windows_process_action(
    pid: int,
    kill_tree: bool = False,
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Принудительное завершение процесса Windows по PID (с поддержкой SafeOps/dry_run).

    Args:
        pid: Идентификатор процесса (PID).
        kill_tree: Завершать ли также дочерние процессы (дерево процессов).
        dry_run: Режим симуляции (по умолчанию True для безопасности).
        confirmed_by_user: Подтверждено ли действие пользователем при отключенном dry_run.

    Returns:
        JSON с результатом операции завершения процесса.
    """
    try:
        from apps.windows.modules.process_manager.core.manager import ProcessManager
        from apps.windows.modules.process_manager.core.models import ProcessKillRequest

        pm = ProcessManager()
        req = ProcessKillRequest(
            pid=pid,
            kill_tree=kill_tree,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await pm.kill_process(req)
        return json.dumps({"status": "ok", "pid": pid, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.process_manager] Ошибка выполнения process_action (PID={pid}): {e}", exc_info=True)
        return json.dumps({"status": "error", "pid": pid, "error": str(e)}, ensure_ascii=False)


WINDOWS_PROCESS_TOOLS = [
    windows_process_list,
    windows_process_action,
]
