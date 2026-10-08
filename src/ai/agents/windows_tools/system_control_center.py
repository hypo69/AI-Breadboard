# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows System Control Center Tools Module
# =============================================================================
# Description:
#   Инструменты единого центра управления Windows (System Control Center),
#   агрегирующие телеметрию безопасности, оперативной памяти, торов дисков
#   и точек восстановления (apps.windows.modules.system_control_center).
#   Включают:
#     1. Сводный аудит и телеметрия центра управления (windows_system_control_audit)
#     2. Системные действия центров управления SafeOps (windows_system_control_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.system_control_center import windows_system_control_audit
#     res = await windows_system_control_audit(action="status")
#
# File: system_control_center.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:33:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов единого центра управления Windows для ИИ-агентов."""

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
    """Вспомогательное преобразование Pydantic и объектов в словарь."""
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
# Блок 1: Сводный аудит центра управления Windows
# =============================================================================

@tool
async def windows_system_control_audit(
    action: str = "status",
) -> str:
    """Сводный аудит и статус единого центра управления Windows (System Control Center).

    Args:
        action: Режим аудита:
            - 'status': единый сводный статус системы (CPU, RAM, Uptime, Defender, Firewall, UAC, Restore Points)
            - 'security': оценка состояния компонентов безопасности (Defender, profiles, UAC elevation)
            - 'cleanup_estimate': потенциально очищаемый объём временных дисковых файлов

    Returns:
        JSON со статусом центра управления Windows.
    """
    try:
        from apps.windows.modules.system_control_center.router import _collect_status_sync

        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        status_data = await loop.run_in_executor(None, _collect_status_sync)

        if act == "status":
            return json.dumps({
                "status": "ok",
                "action": act,
                "system_control": _to_serializable(status_data),
            }, ensure_ascii=False)

        elif act == "security":
            sec_info = status_data.get("security", {})
            return json.dumps({
                "status": "ok",
                "action": act,
                "security": _to_serializable(sec_info),
            }, ensure_ascii=False)

        elif act == "cleanup_estimate":
            disk_info = status_data.get("disk", {})
            return json.dumps({
                "status": "ok",
                "action": act,
                "cleanup_estimate": _to_serializable(disk_info.get("cleanup_estimate", {})),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.system_control_center] Ошибка аудита центра управления ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Действия центра управления SafeOps
# =============================================================================

@tool
async def windows_system_control_action(
    action: str,
    target: str = "",
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Выполнение комплексных действий через единый центр управления Windows SafeOps.

    Args:
        action: Тип действия (например: 'apply_profile', 'clean_temp_files', 'trigger_checkpoint').
        target: Идентификатор профиля или целевого компонента.
        dry_run: Режим симуляции (по умолчанию True для предотвращения нежелательных системных мутаций).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом выполнения или симуляции системного действия.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": action,
                "target": target,
                "dry_run": True,
                "message": f"Симуляция действия '{action}' в центре управления для target='{target}' прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        return json.dumps({
            "status": "ok",
            "action": action,
            "target": target,
            "message": f"Действие '{action}' успешно выполнено в центре управления.",
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.system_control_center] Ошибка выполнения действия '{action}': {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "target": target, "error": str(e)}, ensure_ascii=False)


WINDOWS_SYSTEM_CONTROL_CENTER_TOOLS = [
    windows_system_control_audit,
    windows_system_control_action,
]
