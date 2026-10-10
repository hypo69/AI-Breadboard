# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Focus Policy Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой управления фокусировкой Windows Focus Policy
#   (apps.windows.sdk.modules.focus_policy).
#   Сгруппированы по 3 логическим блокам:
#     1. Инспекция состояния и профилей фокусировки (windows_focus_status_profiles)
#     2. Запуск и остановка фокус-сессий по протоколу SafeOps (windows_focus_session_action)
#     3. Перехват и выборка подавленных тост-уведомлений (windows_focus_notifications)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.focus import windows_focus_status_profiles
#     res = await windows_focus_status_profiles(action="status")
#
# File: focus.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:40:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Focus Policy Engine для ИИ-агентов."""

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
# Блок 1: Состояние и профили фокусировки
# =============================================================================

@tool
async def windows_focus_status_profiles(
    action: str,
    profile_id: Optional[str] = None,
    name: Optional[str] = None,
    start_time: str = "09:00",
    end_time: str = "18:00",
    days: Optional[List[str]] = None,
) -> str:
    """Аудит состояния, просмотр и сохранение профилей фокусировки Windows Focus Policy Engine.

    Args:
        action: Операция работы с профилями и статусом:
            - 'status': получение текущего состояния сессии и перехватчика уведомлений
            - 'list_profiles': реестр всех созданных профилей фокусировки
            - 'get_profile': получение подробных параметров профиля по profile_id
            - 'save_profile': создание/обновление профиля фокусировки (с регистрацией в Task Scheduler)
        profile_id: Идентификатор профиля (например, 'prof-work-default'). Обязателен для 'get_profile' и 'save_profile'.
        name: Человекочитаемое имя профиля при сохранении.
        start_time: Время начала фокусировки в формате HH:MM (по умолчанию '09:00').
        end_time: Время завершения фокусировки в формате HH:MM (по умолчанию '18:00').
        days: Список дней недели (например, ['mon', 'tue', 'wed', 'thu', 'fri']).

    Returns:
        JSON с состоянием движка, списком или запрошенным профилем.
    """
    try:
        from apps.windows.sdk.modules.focus_policy.controller import WindowsFocusController
        from apps.windows.sdk.modules.focus_policy.models import FocusProfile, FocusSchedule

        ctrl = WindowsFocusController()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "status":
            res = await loop.run_in_executor(None, ctrl.status)
            return json.dumps({"status": "ok", "action": act, "focus_status": _to_serializable(res)}, ensure_ascii=False)
        elif act == "list_profiles":
            res = await loop.run_in_executor(None, ctrl.list_profiles)
            return json.dumps({"status": "ok", "action": act, "profiles": _to_serializable(res)}, ensure_ascii=False)
        elif act == "get_profile":
            if not profile_id:
                return json.dumps({"status": "error", "message": "Параметр profile_id обязателен для 'get_profile'"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, ctrl.get_profile, profile_id)
            return json.dumps({"status": "ok", "action": act, "profile_id": profile_id, "profile": _to_serializable(res)}, ensure_ascii=False)
        elif act == "save_profile":
            if not profile_id:
                return json.dumps({"status": "error", "message": "Параметр profile_id обязателен для 'save_profile'"}, ensure_ascii=False)
            prof_name = name or profile_id
            sch_days = days or ['mon', 'tue', 'wed', 'thu', 'fri']
            prof = FocusProfile(
                profile_id=profile_id,
                name=prof_name,
                schedule=FocusSchedule(start_time=start_time, end_time=end_time, days=sch_days),
            )
            res = await loop.run_in_executor(None, ctrl.save_profile, prof)
            return json.dumps({"status": "ok", "action": act, "profile_id": profile_id, "profile": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.focus] Ошибка выполнения focus_status_profiles ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление сессиями фокусировки (SafeOps)
# =============================================================================

@tool
async def windows_focus_session_action(
    action: str,
    profile_id: Optional[str] = None,
    triggered_by: str = "AI_AGENT",
    dry_run: bool = False,
) -> str:
    """Запуск и завершение фокус-сессий с применением системного режима Do Not Disturb по протоколу SafeOps.

    Args:
        action: Операция управления сессией ('start', 'stop').
        profile_id: Идентификатор профиля (обязателен при action='start').
        triggered_by: Источник вызова ('AI_AGENT', 'UI_MANUAL', 'TASK_SCHEDULER').
        dry_run: Безопасный режим симуляции без изменения состояния ОС (по умолчанию False).

    Returns:
        JSON с идентификатором сессии или итоговой сводкой SessionSummary.
    """
    try:
        from apps.windows.sdk.modules.focus_policy.controller import WindowsFocusController

        ctrl = WindowsFocusController()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": act,
                "profile_id": profile_id,
                "result": f"DRY_RUN: Симуляция действия '{act}' прошла успешно."
            }, ensure_ascii=False)

        if act == "start":
            if not profile_id:
                return json.dumps({"status": "error", "message": "Параметр profile_id обязателен при старте сессии"}, ensure_ascii=False)
            session_id = await loop.run_in_executor(None, ctrl.start_session, profile_id, triggered_by)
            return json.dumps({"status": "ok", "action": act, "profile_id": profile_id, "session_id": session_id}, ensure_ascii=False)
        elif act == "stop":
            summary = await loop.run_in_executor(None, ctrl.stop_session, triggered_by)
            return json.dumps({"status": "ok", "action": act, "summary": _to_serializable(summary)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.focus] Ошибка выполнения focus_session_action ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Перехват и архив тост-уведомлений
# =============================================================================

@tool
async def windows_focus_notifications(
    action: str,
    session_id: Optional[str] = None,
) -> str:
    """Опрос, подавление и получение архива перехваченных тост-уведомлений в режиме фокусировки.

    Args:
        action: Операция с уведомлениями:
            - 'poll': выполнение текущего опроса и подавления новых тост-уведомлений
            - 'list_suppressed': выборка архива подавленных уведомлений (по session_id или последней сессии)
            - 'request_access': запрос прав доступа к WinRT UserNotificationListener
        session_id: Фильтр по идентификатору сессии для 'list_suppressed'.

    Returns:
        JSON с количеством подавленных уведомлений, списком из архива или статусом прав WinRT.
    """
    try:
        from apps.windows.sdk.modules.focus_policy.controller import WindowsFocusController

        ctrl = WindowsFocusController()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "poll":
            count = await loop.run_in_executor(None, ctrl.poll_notifications)
            return json.dumps({"status": "ok", "action": act, "suppressed_count": count}, ensure_ascii=False)
        elif act == "list_suppressed":
            res = await loop.run_in_executor(None, ctrl.list_suppressed, session_id)
            return json.dumps({"status": "ok", "action": act, "session_id": session_id, "suppressed_notifications": _to_serializable(res)}, ensure_ascii=False)
        elif act == "request_access":
            access = await loop.run_in_executor(None, ctrl.request_listener_access)
            return json.dumps({"status": "ok", "action": act, "listener_access_status": access}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.focus] Ошибка выполнения focus_notifications ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_FOCUS_TOOLS = [
    windows_focus_status_profiles,
    windows_focus_session_action,
    windows_focus_notifications,
]
