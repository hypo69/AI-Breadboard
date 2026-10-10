# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Programs History Tools Module
# =============================================================================
# Description:
#   Инструменты глубокого анализа истории программ и артефактов исполнения Windows
#   (apps.windows.sdk.modules.programms_history_deep_researh).
#   Включают:
#     1. Сводный отчёт об установленном ПО и ассоциированных артефактах (windows_programs_history_report)
#     2. Быстрый аудит установленных программ из реестра Windows (windows_programs_history_audit)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.programms_history import windows_programs_history_audit
#     res = await windows_programs_history_audit(action="registry")
#
# File: programms_history.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:07:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов глубокого анализа программ и артефактов Windows для ИИ-агентов."""

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
    """Вспомогательное преобразование объектов в сериализуемый словарь."""
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
# Блок 1: Сводный отчёт об артефактах программ
# =============================================================================

@tool
async def windows_programs_history_report(
    action: str = "summary",
    limit: int = 20,
) -> str:
    """Глубокий отчёт о приложениях Windows и их артефактах в профилях пользователей.

    Args:
        action: Режим генерации отчёта:
            - 'summary': краткая сводка количества программ, сопоставленных и неизвестных артефактов
            - 'installed': список установленных приложений с их версиями и издателями
            - 'mapped': список сопоставленных артефактов и файлов программ
            - 'full': полный сопоставленный отчёт в JSON формате
        limit: Ограничение числа выводимых элементов (по умолчанию 20).

    Returns:
        JSON с отчётом по артефактам и программам Windows.
    """
    try:
        from apps.windows.sdk.modules.programms_history_deep_researh.report import generate_report

        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        report_data = await loop.run_in_executor(None, generate_report)

        if act == "summary":
            summary = {
                "generated_at": report_data.get("generated_at"),
                "total_installed_programs": len(report_data.get("installed_programs", [])),
                "total_detected_artifacts": len(report_data.get("detected_artifacts", [])),
                "total_mapped_artifacts": len(report_data.get("mapped_artifacts", [])),
                "total_unknown_artifacts": len(report_data.get("unknown_artifacts", [])),
                "sample_installed": report_data.get("installed_programs", [])[:limit],
            }
            return json.dumps({"status": "ok", "action": act, "summary": summary}, ensure_ascii=False)

        elif act == "installed":
            progs = report_data.get("installed_programs", [])
            return json.dumps({"status": "ok", "action": act, "total": len(progs), "installed_programs": progs[:limit]}, ensure_ascii=False)

        elif act == "mapped":
            mapped = report_data.get("mapped_artifacts", [])
            return json.dumps({"status": "ok", "action": act, "total": len(mapped), "mapped_artifacts": mapped[:limit]}, ensure_ascii=False)

        elif act == "full":
            return json.dumps({"status": "ok", "action": act, "report": _to_serializable(report_data)}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.programms_history] Ошибка выполнения programs_history_report ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Быстрый аудит программ из реестра Windows
# =============================================================================

@tool
async def windows_programs_history_audit(
    query_name: Optional[str] = None,
    limit: int = 50,
) -> str:
    """Быстрый аудит установленных программ из реестра Windows (HKLM/HKCU Uninstall).

    Args:
        query_name: Фильтр по названию программы или издателю (регистронезависимый подстроковый поиск).
        limit: Ограничение количества результатов (по умолчанию 50).

    Returns:
        JSON со списком установленного ПО из реестра Windows.
    """
    try:
        from apps.windows.sdk.modules.programms_history_deep_researh.registry_extractor import get_installed_programs

        loop = asyncio.get_running_loop()
        programs = await loop.run_in_executor(None, get_installed_programs)

        if query_name:
            q_lower = query_name.strip().lower()
            programs = [
                p for p in programs
                if q_lower in str(p.get("displayname", "")).lower()
                or q_lower in str(p.get("publisher", "")).lower()
            ]

        return json.dumps({
            "status": "ok",
            "query": query_name,
            "count": len(programs),
            "programs": programs[:limit],
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.programms_history] Ошибка выполнения programs_history_audit: {e}", exc_info=True)
        return json.dumps({"status": "error", "query": query_name, "error": str(e)}, ensure_ascii=False)


WINDOWS_PROGRAMS_HISTORY_TOOLS = [
    windows_programs_history_report,
    windows_programs_history_audit,
]
