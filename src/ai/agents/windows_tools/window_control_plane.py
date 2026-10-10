# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Window Control Plane Tools Module
# =============================================================================
# Description:
#   Инструменты прямого управления 295 параметрами окон, жесткой фокусировки,
#   прилипания (Snap Layouts), анимаций и виртуальных рабочих столов Windows
#   (apps.windows.sdk.modules.window_control_plane).
#   Включают:
#     1. Поиск и аудит параметров управления окнами (windows_control_plane_audit)
#     2. Изменение и настройка параметров окон SafeOps (windows_control_plane_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.window_control_plane import windows_control_plane_audit
#     res = await windows_control_plane_audit(action="summary")
#
# File: window_control_plane.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:43:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Window Management Control Plane для ИИ-агентов."""

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
# Блок 1: Поиск и аудит параметров Control Plane
# =============================================================================

@tool
async def windows_control_plane_audit(
    action: str = "summary",
    query: str = "",
    limit: int = 50,
) -> str:
    """Аудит и глобальный поиск по 295 параметрам подсистемы управления окнами Windows.

    Args:
        action: Режим аудита:
            - 'summary': сводная аналитика каталога параметров (всего настроек, распределение по риску)
            - 'categories': перечень 15 категорий настроек окон (Snap Assist, виртуальные столы, фокусировка)
            - 'search': поиск настроек по ключевым словам или категориям (параметр query)
            - 'read_value': чтение текущего живого значения параметра из реестра/WinAPI (query=setting_id)
        query: Ключевое слово для поиска или ID параметра (setting_id).
        limit: Ограничение количества выводимых настроек (по умолчанию 50).

    Returns:
        JSON с результатами аудита параметров подсистемы окон.
    """
    try:
        from apps.windows.sdk.modules.window_control_plane.manager import WindowManagementControlPlane

        plane = WindowManagementControlPlane()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            summary = await loop.run_in_executor(None, plane.get_summary)
            return json.dumps({
                "status": "ok",
                "action": act,
                "summary": _to_serializable(summary),
            }, ensure_ascii=False)

        elif act == "categories":
            cats = await loop.run_in_executor(None, plane.get_categories_overview)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_categories": len(cats),
                "categories": _to_serializable(cats),
            }, ensure_ascii=False)

        elif act == "search":
            results = await loop.run_in_executor(None, lambda: plane.search_settings(query=query if query else None, limit=limit))
            return json.dumps({
                "status": "ok",
                "action": act,
                "query": query,
                "total_found": len(results),
                "settings": _to_serializable(results),
            }, ensure_ascii=False)

        elif act == "read_value":
            if not query:
                return json.dumps({"status": "error", "message": "Параметр query (setting_id) обязателен для чтения живого значения"}, ensure_ascii=False)
            val = await loop.run_in_executor(None, plane.get_live_value, query)
            if not val:
                return json.dumps({"status": "error", "message": f"Параметр '{query}' не найден или недоступен для чтения"}, ensure_ascii=False)
            return json.dumps({
                "status": "ok",
                "action": act,
                "setting_id": query,
                "value": _to_serializable(val),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.window_control_plane] Ошибка аудита параметров окон ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Выполнение настройки параметров окон SafeOps
# =============================================================================

@tool
async def windows_control_plane_action(
    setting_id: str,
    value: Any,
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Изменение параметров управления окнами, прилипанием и фокусировкой SafeOps.

    Args:
        setting_id: Уникальный идентификатор параметра (например: 'snap_assist_001', 'focus_activation_002').
        value: Новое устанавливаемое значение параметра (число, булево флаг или строка).
        dry_run: Режим симуляции (по умолчанию True).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом применения или симуляции настройки подсистемы окон.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "setting_id": setting_id,
                "new_value": value,
                "dry_run": True,
                "message": f"Симуляция изменения параметра '{setting_id}' в значение '{value}' прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        from apps.windows.sdk.modules.window_control_plane.manager import WindowManagementControlPlane
        from apps.windows.sdk.modules.window_control_plane.models import SettingApplyRequest

        plane = WindowManagementControlPlane()
        loop = asyncio.get_running_loop()

        req = SettingApplyRequest(new_value=value, operator=operator)
        res = await loop.run_in_executor(None, plane.apply_setting, setting_id, req)
        return json.dumps({
            "status": "ok",
            "setting_id": setting_id,
            "result": _to_serializable(res),
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.window_control_plane] Ошибка изменения параметра '{setting_id}': {e}", exc_info=True)
        return json.dumps({"status": "error", "setting_id": setting_id, "error": str(e)}, ensure_ascii=False)


WINDOWS_WINDOW_CONTROL_PLANE_TOOLS = [
    windows_control_plane_audit,
    windows_control_plane_action,
]
