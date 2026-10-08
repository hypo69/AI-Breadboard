# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Performance Tracing Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой счетчиков производительности и трассировки ETW
#   (apps.windows.modules.performance_tracing).
#   Сгруппированы по 2 логическим блокам:
#     1. Инспекция счетчиков производительности и сессий ETW (windows_performance_tracing_audit)
#     2. Безопасные действия со сборщиками трассировки ETW по SafeOps (windows_performance_collector_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.performance_tracing import windows_performance_tracing_audit
#     res = await windows_performance_tracing_audit(action="counters")
#
# File: performance_tracing.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:57:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Performance Tracing Manager для ИИ-агентов."""

import asyncio
import json
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
    """Вспомогательное преобразование объектов моделей в сериализуемый словарь."""
    if isinstance(obj, (int, float, bool, str)) or obj is None:
        return obj
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
# Блок 1: Аудит счетчиков производительности и сборщиков ETW
# =============================================================================

@tool
async def windows_performance_tracing_audit(
    action: str,
) -> str:
    """Аудит моментальных счетчиков производительности и сборщиков данных ETW (Data Collector Sets).

    Args:
        action: Операция аудита производительности:
            - 'counters': моментальные значения счетчиков (CPU%, Memory%, очереди дисков, процессы)
            - 'collectors': список наборов сборщиков данных ETW и сессий трассировки событий
            - 'report': сводный статистический отчёт о производительности хоста

    Returns:
        JSON с результатами замера счетчиков, списком сборщиков или сводным отчетом.
    """
    try:
        from apps.windows.modules.performance_tracing.core.manager import PerformanceTracingManager

        mgr = PerformanceTracingManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "counters":
            res = await loop.run_in_executor(None, mgr.get_counter_samples)
            return json.dumps({"status": "ok", "action": act, "counters": _to_serializable(res)}, ensure_ascii=False)
        elif act == "collectors":
            res = await loop.run_in_executor(None, mgr.list_collectors)
            return json.dumps({"status": "ok", "action": act, "collectors": _to_serializable(res)}, ensure_ascii=False)
        elif act == "report":
            res = await loop.run_in_executor(None, mgr.generate_report)
            return json.dumps({"status": "ok", "action": act, "report": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.performance_tracing] Ошибка аудита производительности ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление сборщиками трассировки ETW по SafeOps
# =============================================================================

@tool
async def windows_performance_collector_action(
    collector_name: str,
    action: str,
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Безопасное выполнение или симуляция действий со сборщиками трассировки ETW по протоколу SafeOps.

    Args:
        collector_name: Имя сборщика данных или сессии ETW (например, 'System Diagnostics', 'EventLog-Security').
        action: Тип операции над сборщиком ('start', 'stop', 'create', 'delete').
        dry_run: Режим безопасной симуляции без изменения состояния сборщика в ОС (по умолчанию True).
        confirmed_by_user: Явный флаг подтверждения операции пользователем.

    Returns:
        JSON с результатом выполнения или симуляции операции над сборщиком трассировки.
    """
    try:
        from apps.windows.modules.performance_tracing.core.manager import PerformanceTracingManager
        from apps.windows.modules.performance_tracing.core.models import CollectorActionRequest

        mgr = PerformanceTracingManager()
        req = CollectorActionRequest(
            collector_name=collector_name,
            action=action,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await mgr.execute_collector_action(req)
        return json.dumps({"status": "ok", "action": action, "collector": collector_name, "result": res}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.performance_tracing] Ошибка управления сборщиком '{collector_name}' ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "collector": collector_name, "error": str(e)}, ensure_ascii=False)


WINDOWS_PERFORMANCE_TRACING_TOOLS = [
    windows_performance_tracing_audit,
    windows_performance_collector_action,
]
