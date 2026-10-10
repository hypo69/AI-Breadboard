# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Services Manager Tools Module
# =============================================================================
# Description:
#   Инструменты прямого аудита, поиска и управления службами Windows
#   (apps.windows.sdk.modules.services_manager).
#   Включают:
#     1. Инспекцию списка служб Windows, статусов и фильтрацию (windows_services_list)
#     2. Управление состоянием служб (запуск, остановка, перезапуск) SafeOps (windows_services_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.services_manager import windows_services_list
#     res = await windows_services_list(action="summary")
#
# File: services_manager.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:13:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления службами Windows для ИИ-агентов."""

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
# Блок 1: Аудит и списки служб Windows
# =============================================================================

@tool
async def windows_services_list(
    action: str = "summary",
    status_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 50,
) -> str:
    """Инспекция, поиск и аудит системных служб Windows.

    Args:
        action: Режим работы:
            - 'summary': сводная статистика (всего, работающих, остановленных, автозапуск)
            - 'list': полученние списка всех служб с фильтрацией по status_filter
            - 'refresh': принудительный опрос SCM и обновление снимка в SQLite
            - 'search': поиск службы по имени или отображаемому названию (search_query)
        status_filter: Опциональный фильтр статуса ('RUNNING', 'STOPPED', 'PAUSED').
        search_query: Подстрока для поиска по имени или описанию службы.
        limit: Ограничение выдачи записей (по умолчанию 50).

    Returns:
        JSON со списком или сводным отчетом по службам Windows.
    """
    try:
        from apps.windows.sdk.modules.services_manager.core.manager import ServicesManager

        sm = ServicesManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            report = await loop.run_in_executor(None, sm.generate_report)
            summary_data = {
                "total_services": report.total_services,
                "running_services": report.running_services,
                "stopped_services": report.stopped_services,
                "auto_start_services": report.auto_start_services,
                "orphaned_services_count": report.orphaned_services_count,
                "timestamp": report.timestamp,
                "sample_services": _to_serializable(report.services[:10]),
            }
            return json.dumps({"status": "ok", "action": act, "summary": summary_data}, ensure_ascii=False)

        elif act == "refresh":
            report = await loop.run_in_executor(None, sm.refresh_and_save)
            return json.dumps({"status": "ok", "action": act, "refreshed_total": report.total_services}, ensure_ascii=False)

        elif act in ("list", "search"):
            svcs = await loop.run_in_executor(None, sm.list_services, status_filter, 500)
            if search_query:
                sq = search_query.strip().lower()
                svcs = [
                    s for s in svcs
                    if sq in s.name.lower() or sq in s.display_name.lower()
                ]
            return json.dumps({"status": "ok", "action": act, "count": len(svcs), "services": _to_serializable(svcs[:limit])}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.services_manager] Ошибка работы со службам ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление состоянием служб (SafeOps)
# =============================================================================

@tool
async def windows_services_action(
    name: str,
    action: str = "start",
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Управление состоянием службы Windows (start, stop, restart, pause, resume) по протоколу SafeOps/dry_run.

    Args:
        name: Системное имя службы (например: 'wuauserv', 'WinDefend', 'Spooler').
        action: Операция ('start', 'stop', 'restart', 'pause', 'resume').
        dry_run: Режим симуляции (по умолчанию True для защиты от сбоев).
        confirmed_by_user: Подтверждение действия администратором.

    Returns:
        JSON с результатом выполнения операции над службой.
    """
    try:
        from apps.windows.sdk.modules.services_manager.core.manager import ServicesManager
        from apps.windows.sdk.modules.services_manager.core.models import ServiceActionRequest

        sm = ServicesManager()
        req = ServiceActionRequest(
            name=name,
            action=action,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await sm.execute_service_action(req)
        return json.dumps({"status": "ok", "name": name, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.services_manager] Ошибка выполнения действия со службой '{name}': {e}", exc_info=True)
        return json.dumps({"status": "error", "name": name, "error": str(e)}, ensure_ascii=False)


WINDOWS_SERVICES_MANAGER_TOOLS = [
    windows_services_list,
    windows_services_action,
]
