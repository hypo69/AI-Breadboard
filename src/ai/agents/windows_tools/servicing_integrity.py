# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Servicing Integrity Tools Module
# =============================================================================
# Description:
#   Инструменты аудита и обслуживания целостности системного образа Windows (SFC, DISM, DISM Features)
#   (apps.windows.sdk.modules.servicing_integrity).
#   Включают:
#     1. Инспекция целостности системных файлов и компонентов Windows (windows_servicing_integrity_audit)
#     2. Выполнение процедур сканирования и очистки DISM/SFC по протоколу SafeOps (windows_servicing_integrity_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.servicing_integrity import windows_servicing_integrity_audit
#     res = await windows_servicing_integrity_audit(action="report")
#
# File: servicing_integrity.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:15:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов обслуживания целостности Windows (SFC, DISM) для ИИ-агентов."""

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
    """Вспомогательное преобразование Pydantic моделей и объектов в словарь."""
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
# Блок 1: Аудит целостности системных файлов и DISM
# =============================================================================

@tool
async def windows_servicing_integrity_audit(
    action: str = "report",
) -> str:
    """Инспекция целостности системных файлов Windows (SFC), хранилища компонентов DISM и статуса опциональных компонентов.

    Args:
        action: Режим работы:
            - 'report': сводный отчёт о целостности системных файлов и хранилища WinSxS
            - 'features': список ключевых опциональных компонентов Windows (WSL, Hyper-V, SMB1)

    Returns:
        JSON со статусом целостности SFC/DISM и состоянием компонентов.
    """
    try:
        from apps.windows.sdk.modules.servicing_integrity.core.manager import ServicingIntegrityManager

        sim = ServicingIntegrityManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "report":
            report = await loop.run_in_executor(None, sim.generate_report)
            return json.dumps({"status": "ok", "action": act, "report": _to_serializable(report)}, ensure_ascii=False)

        elif act == "features":
            features = await loop.run_in_executor(None, sim.get_features)
            return json.dumps({"status": "ok", "action": act, "features": _to_serializable(features)}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.servicing_integrity] Ошибка аудита целостности ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Выполнение процедур восстановления целостности (SafeOps)
# =============================================================================

@tool
async def windows_servicing_integrity_action(
    tool_name: str = "sfc",
    action: str = "scannow",
    feature_name: Optional[str] = None,
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Запуск утилит восстановления целостности Windows (SFC /scannow, DISM /RestoreHealth) по протоколу SafeOps/dry_run.

    Args:
        tool_name: Утилита обслуживания ('sfc', 'dism', 'feature').
        action: Команда или операция ('scannow', 'checkhealth', 'scanhealth', 'restorehealth', 'enable', 'disable').
        feature_name: Имя опционального компонента (при tool_name='feature').
        dry_run: Режим симуляции (по умолчанию True для безопасности).
        confirmed_by_user: Явное подтверждение запуска системной утилиты.

    Returns:
        JSON с результатом выполнения операции обслуживания.
    """
    try:
        from apps.windows.sdk.modules.servicing_integrity.core.manager import ServicingIntegrityManager
        from apps.windows.sdk.modules.servicing_integrity.core.models import ServicingActionRequest

        sim = ServicingIntegrityManager()
        req = ServicingActionRequest(
            tool=tool_name,
            action=action,
            feature_name=feature_name,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await sim.execute_servicing_action(req)
        return json.dumps({"status": "ok", "tool": tool_name, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.servicing_integrity] Ошибка запуска утилиты '{tool_name}': {e}", exc_info=True)
        return json.dumps({"status": "error", "tool": tool_name, "error": str(e)}, ensure_ascii=False)


WINDOWS_SERVICING_INTEGRITY_TOOLS = [
    windows_servicing_integrity_audit,
    windows_servicing_integrity_action,
]
