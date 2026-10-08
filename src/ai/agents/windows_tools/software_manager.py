# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Software Manager Tools Module
# =============================================================================
# Description:
#   Инструменты управления пакетами программного обеспечения Windows (WinGet, MSI)
#   (apps.windows.modules.software_manager).
#   Включают:
#     1. Список установленного ПО, поиск в репозитории WinGet и проверка обновлений (windows_software_list)
#     2. Установка, обновление и удаление пакетов ПО по протоколу SafeOps/dry_run (windows_software_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.software_manager import windows_software_list
#     res = await windows_software_list(action="report")
#
# File: software_manager.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:16:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления пакетами ПО (WinGet) для ИИ-агентов."""

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
# Блок 1: Список пакетов ПО и поиск в WinGet
# =============================================================================

@tool
async def windows_software_list(
    action: str = "report",
    search_query: Optional[str] = None,
) -> str:
    """Инспекция установленного ПО, поиск пакетов и доступных обновлений WinGet.

    Args:
        action: Режим инспекции:
            - 'report': сводный отчёт (всего пакетов, количество доступных обновлений, статус WinGet)
            - 'list': полный список всех установленных пакетов ПО
            - 'search': поиск пакета ПО по названию или ID (search_query)

    Returns:
        JSON со списком пакетов ПО или отчётом WinGet.
    """
    try:
        from apps.windows.modules.software_manager.core.manager import SoftwarePackagesManager

        spm = SoftwarePackagesManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "report":
            report = await loop.run_in_executor(None, spm.generate_report)
            return json.dumps({"status": "ok", "action": act, "report": _to_serializable(report)}, ensure_ascii=False)

        elif act == "list":
            pkgs = await loop.run_in_executor(None, spm.list_packages)
            return json.dumps({"status": "ok", "action": act, "total": len(pkgs), "packages": _to_serializable(pkgs)}, ensure_ascii=False)

        elif act == "search":
            if not search_query:
                return json.dumps({"status": "error", "message": "Параметр search_query обязателен для поиска"}, ensure_ascii=False)
            found = await loop.run_in_executor(None, spm.search_packages, search_query)
            return json.dumps({"status": "ok", "action": act, "query": search_query, "packages": _to_serializable(found)}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.software_manager] Ошибка работы с ПО ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Установка, обновление и удаление ПО (SafeOps)
# =============================================================================

@tool
async def windows_software_action(
    package_id: str,
    action: str = "upgrade",
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Управление пакетом программного обеспечения (install, upgrade, uninstall) по протоколу SafeOps/dry_run.

    Args:
        package_id: Уникальный идентификатор пакета WinGet/MSI (например: 'Python.Python.3.14', 'Git.Git', 'Google.Chrome').
        action: Операция ('install', 'upgrade', 'uninstall').
        dry_run: Режим симуляции (по умолчанию True для безопасности).
        confirmed_by_user: Явное подтверждение установки/удаления администратором.

    Returns:
        JSON с результатом выполнения операции над пакетом ПО.
    """
    try:
        from apps.windows.modules.software_manager.core.manager import SoftwarePackagesManager
        from apps.windows.modules.software_manager.core.models import PackageActionRequest

        spm = SoftwarePackagesManager()
        req = PackageActionRequest(
            package_id=package_id,
            action=action,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await spm.execute_package_action(req)
        return json.dumps({"status": "ok", "package_id": package_id, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.software_manager] Ошибка операции с пакетом '{package_id}': {e}", exc_info=True)
        return json.dumps({"status": "error", "package_id": package_id, "error": str(e)}, ensure_ascii=False)


WINDOWS_SOFTWARE_MANAGER_TOOLS = [
    windows_software_list,
    windows_software_action,
]
