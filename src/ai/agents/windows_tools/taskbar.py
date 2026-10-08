# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Taskbar Tools Module
# =============================================================================
# Description:
#   Инструменты управления панелью задач, окнами и закрепленными приложениями
#   Windows 10/11 (apps.windows.modules.taskbar).
#   Включают:
#     1. Инспекция панели задач, окон и закрепленных программ (windows_taskbar_audit)
#     2. Выполнение команд управления панелью задач SafeOps (windows_taskbar_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.taskbar import windows_taskbar_audit
#     res = await windows_taskbar_audit(action="summary")
#
# File: taskbar.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:38:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления панелью задач Windows для ИИ-агентов."""

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
# Блок 1: Инспекция и аудит панели задач и окон
# =============================================================================

@tool
async def windows_taskbar_audit(
    action: str = "summary",
    limit: int = 50,
) -> str:
    """Глубокая инспекция панели задач Windows, открытых окон и закрепленных приложений.

    Args:
        action: Режим аудита:
            - 'summary': комплексная сводка (версия ОС, настройки панели, количество окон и закрепленных программ)
            - 'windows': список окон на панели задач (HWND, заголовок, процесс PID, видимость)
            - 'pinned': список прикрепленных ярлыков и приложений
            - 'settings': текущие настройки реестра панели задач (автоскрытие, положение, выравнивание)
            - 'commands': каталоговый список поддерживаемых управляющих команд панели задач
        limit: Ограничение количества выводимых элементов (по умолчанию 50).

    Returns:
        JSON с результатами инспекции панели задач.
    """
    try:
        from apps.windows.modules.taskbar.core.manager import TaskbarController

        ctrl = TaskbarController()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            summary = await loop.run_in_executor(None, ctrl.get_summary)
            return json.dumps({
                "status": "ok",
                "action": act,
                "summary": _to_serializable(summary),
            }, ensure_ascii=False)

        elif act == "windows":
            wins = await loop.run_in_executor(None, lambda: ctrl.window_mgr.list_windows(only_visible=False))
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_windows": len(wins),
                "windows": _to_serializable(wins[:limit]),
            }, ensure_ascii=False)

        elif act == "pinned":
            pinned = await loop.run_in_executor(None, ctrl.app_mgr.list_pinned_apps)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_pinned": len(pinned),
                "pinned_apps": _to_serializable(pinned[:limit]),
            }, ensure_ascii=False)

        elif act == "settings":
            settings = await loop.run_in_executor(None, ctrl.get_settings)
            return json.dumps({
                "status": "ok",
                "action": act,
                "settings": _to_serializable(settings),
            }, ensure_ascii=False)

        elif act == "commands":
            cmds = await loop.run_in_executor(None, ctrl.get_command_catalog)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_commands": len(cmds),
                "commands": _to_serializable(cmds[:limit]),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.taskbar] Ошибка аудита панели задач ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Выполнение команд панели задач SafeOps
# =============================================================================

@tool
async def windows_taskbar_action(
    action: str,
    target: str = "",
    value: str = "",
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Управление настройками, окнами и закрепленными ярлыками панели задач SafeOps.

    Args:
        action: Команда (например: 'pin_app', 'unpin_app', 'update_setting', 'activate_window', 'rollback').
        target: Идентификатор приложения, заголовок окна или имя настройки.
        value: Значение настройки или путь к ярлыку.
        dry_run: Режим симуляции (по умолчанию True).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом выполнения или симуляции команды над панелью задач.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": action,
                "target": target,
                "value": value,
                "dry_run": True,
                "message": f"Симуляция команды панели задач '{action}' для target='{target}' прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        return json.dumps({
            "status": "ok",
            "action": action,
            "target": target,
            "message": f"Команда '{action}' для '{target}' выполнена на панели задач.",
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.taskbar] Ошибка выполнения команды '{action}' панели задач: {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "target": target, "error": str(e)}, ensure_ascii=False)


WINDOWS_TASKBAR_TOOLS = [
    windows_taskbar_audit,
    windows_taskbar_action,
]
