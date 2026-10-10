# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Boot & Recovery Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой Windows Boot & Recovery Manager
#   (apps.windows.sdk.modules.boot_recovery).
#   Сгруппированы по 2 логическим блокам:
#     1. Аудит конфигурации загрузчика BCD и среды WinRE (Audit)
#     2. Безопасное управление параметрами BCD и WinRE по протоколу SafeOps (Action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.boot import windows_boot_recovery_audit
#     res = await windows_boot_recovery_audit()
#
# File: boot.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:10:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Boot & Recovery для ИИ-агентов."""

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
# Блок 1: Аудит загрузчика BCD и среды WinRE
# =============================================================================

@tool
async def windows_boot_recovery_audit() -> str:
    """Проводит аудит конфигурации загрузчика Windows BCD, таймаута, Secure Boot и среды восстановления WinRE.

    Returns:
        JSON со сводным отчетом: список BCD записей, таймаут загрузки, статус Secure Boot и путь к образу WinRE.
    """
    try:
        from apps.windows.sdk.modules.boot_recovery.core.manager import BootRecoveryManager

        mgr = BootRecoveryManager()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, mgr.generate_report)
        return json.dumps({"status": "ok", "boot_report": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.boot] Ошибка аудита BCD и WinRE: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Безопасное управление параметрами BCD и WinRE (SafeOps Action)
# =============================================================================

@tool
async def windows_boot_recovery_action(
    action: str,
    target: Optional[str] = None,
    value: Optional[Any] = None,
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Выполняет или симулирует (dry_run) управляющие действия над диспетчером загрузки BCD и WinRE по протоколу SafeOps.

    Args:
        action: Тип действия ('set_timeout', 'toggle_winre', 'set_safemode', 'set_default_os').
        target: Целевой объект или идентификатор записи BCD (например, '{current}' или 'WinRE').
        value: Новое значение параметра (например, таймаут 10 секунд).
        dry_run: Если True, выполняется безопасная симуляция без изменения BCD/WinRE (по умолчанию True).
        confirmed_by_user: Явный флаг подтверждения операции пользователем.

    Returns:
        JSON с результатом выполнения или симуляции действия SafeOps.
    """
    try:
        from apps.windows.sdk.modules.boot_recovery.core.manager import BootRecoveryManager
        from apps.windows.sdk.modules.boot_recovery.core.models import BootActionRequest

        mgr = BootRecoveryManager()
        req = BootActionRequest(
            action=action,
            target=target,
            value=value,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await mgr.execute_action(req)
        return json.dumps({"status": "ok", "action_result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.boot] Ошибка выполнения boot_action ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_BOOT_TOOLS = [
    windows_boot_recovery_audit,
    windows_boot_recovery_action,
]
