# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Identity Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой Accounts & Identity Windows
#   (apps.windows.modules.accounts_identity).
#   Сгруппированы по 5 логическим блокам:
#     1. Досье безопасности субъекта и процессов (Explain)
#     2. Аудит привилегированного доступа и аномалий (Audit Security)
#     3. Управление пользователями, группами и политиками (Manage Account)
#     4. Журнал событий безопасности входов и прав (Audit Events)
#     5. Построение графа связей доступов (Identity Graph)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.identity import windows_identity_explain
#     res = await windows_identity_explain(identifier="onela")
#
# File: identity.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 20:47:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Identity для ИИ-агентов."""

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
# Блок 1: Досье безопасности субъекта и процессов
# =============================================================================

@tool
async def windows_identity_explain(
    identifier: Optional[str] = None,
) -> str:
    """Формирует полное досье контекста безопасности по субъекту (пользователю, SID) или текущему токену.

    Args:
        identifier: Опциональное имя пользователя или SID (например, 'onela', 'Administrator', 'S-1-5-21-...').
                    Если не указано, возвращает контекст текущего процесса.

    Returns:
        JSON со статусом и полным досье безопасности (токен, группы, LSA-права, MIL).
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        loop = asyncio.get_running_loop()

        if identifier:
            res = await loop.run_in_executor(None, service.explain, identifier)
            return json.dumps({"status": "ok", "target": identifier, "principal": _to_serializable(res)}, ensure_ascii=False)
        else:
            res = await loop.run_in_executor(None, service.get_current_identity)
            return json.dumps({"status": "ok", "target": "current_identity", "identity": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.identity] Ошибка выполнения windows_identity_explain ('{identifier}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "identifier": identifier, "error": str(e)}, ensure_ascii=False)


@tool
async def windows_identity_explain_pid(
    pid: int,
) -> str:
    """Формирует подробный отчет безопасности по токену процесса (PID).

    Args:
        pid: Идентификатор процесса (PID).

    Returns:
        JSON с разбором безопасности процесса (аккаунт, группы, привилегии, Integrity Level, UAC Elevation).
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, service.explain_pid, int(pid))
        return json.dumps({"status": "ok", "pid": pid, "pid_analysis": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.identity] Ошибка выполнения windows_identity_explain_pid ({pid}): {e}", exc_info=True)
        return json.dumps({"status": "error", "pid": pid, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Аудит привилегированного доступа и аномалий
# =============================================================================

@tool
async def windows_identity_audit_security(
    mode: str = "all",
) -> str:
    """Проводит аудит административного доступа, прав служб, RDP и выявляет осиротевшие SID/профили.

    Args:
        mode: Режим аудита:
            - 'all': полный аудит (администраторы, RDP, службы, осиротевшие SID и профили)
            - 'admins': список всех аккаунтов с правами администратора
            - 'rdp': аккаунты с правом входа через Remote Desktop
            - 'services': аккаунты с правом SeServiceLogonRight
            - 'orphaned': поиск осиротевших SID и неиспользуемых профилей в C:\\Users

    Returns:
        JSON со сводкой результатов аудита безопасности.
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        loop = asyncio.get_running_loop()
        m = mode.strip().lower()

        result: Dict[str, Any] = {"status": "ok", "mode": m}

        if m in ("all", "admins"):
            result["admins"] = _to_serializable(await loop.run_in_executor(None, service.who_is_admin))
        if m in ("all", "rdp"):
            result["rdp_users"] = await loop.run_in_executor(None, service.who_can_rdp)
        if m in ("all", "services"):
            result["service_logon_users"] = await loop.run_in_executor(None, service.who_can_logon_as_service)
        if m in ("all", "orphaned"):
            result["orphaned_sids"] = await loop.run_in_executor(None, service.find_orphaned_sids)
            result["orphaned_profiles"] = await loop.run_in_executor(None, service.find_orphaned_profiles)

        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.identity] Ошибка аудита безопасности (mode='{mode}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "mode": mode, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Управление пользователями, группами и политиками
# =============================================================================

@tool
async def windows_identity_manage_account(
    action: str,
    target: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """Управление учетными записями локальных пользователей, группами и политикой паролей Windows.

    Args:
        action: Операция администрирования:
            - 'list_users': список всех локальных пользователей
            - 'get_user': информация о пользователе по имени или SID (target)
            - 'create_user': создание пользователя (target - имя, params: {'password': '...', 'full_name': '...'})
            - 'delete_user': удаление пользователя (target - имя)
            - 'list_groups': список всех локальных групп
            - 'get_group': детали группы и ее участников (target)
            - 'add_to_group': включение пользователя в группу (target - группа, params: {'username': '...'})
            - 'remove_from_group': исключение из группы (target - группа, params: {'username': '...'})
            - 'get_password_policy': получение политики паролей и порогов блокировки
        target: Имя пользователя или группы.
        params: Словарь дополнительных параметров (пароль, полное имя, описание, username).

    Returns:
        JSON с результатом выполнения операции.
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()
        p = params or {}

        if act == "list_users":
            res = await loop.run_in_executor(None, service.list_users)
            return json.dumps({"status": "ok", "action": act, "users": _to_serializable(res)}, ensure_ascii=False)
        elif act == "get_user":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя или SID) обязателен"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, service.get_user, target)
            return json.dumps({"status": "ok", "action": act, "user": _to_serializable(res)}, ensure_ascii=False)
        elif act == "create_user":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя нового пользователя) обязателен"}, ensure_ascii=False)
            pwd = p.get("password")
            full_name = p.get("full_name", "")
            desc = p.get("description", "")
            success = await loop.run_in_executor(None, service.create_user, target, pwd, full_name, desc)
            return json.dumps({"status": "ok" if success else "error", "action": act, "created": success, "username": target}, ensure_ascii=False)
        elif act == "delete_user":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя пользователя) обязателен"}, ensure_ascii=False)
            success = await loop.run_in_executor(None, service.delete_user, target)
            return json.dumps({"status": "ok" if success else "error", "action": act, "deleted": success, "username": target}, ensure_ascii=False)
        elif act == "list_groups":
            res = await loop.run_in_executor(None, service.list_groups)
            return json.dumps({"status": "ok", "action": act, "groups": _to_serializable(res)}, ensure_ascii=False)
        elif act == "get_group":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя группы) обязателен"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, service.get_group, target)
            return json.dumps({"status": "ok", "action": act, "group": _to_serializable(res)}, ensure_ascii=False)
        elif act == "add_to_group":
            username = p.get("username")
            if not target or not username:
                return json.dumps({"status": "error", "message": "Требуются target (имя группы) и params['username']"}, ensure_ascii=False)
            success = await loop.run_in_executor(None, service.add_user_to_group, target, username)
            return json.dumps({"status": "ok" if success else "error", "action": act, "added": success, "group": target, "username": username}, ensure_ascii=False)
        elif act == "remove_from_group":
            username = p.get("username")
            if not target or not username:
                return json.dumps({"status": "error", "message": "Требуются target (имя группы) и params['username']"}, ensure_ascii=False)
            success = await loop.run_in_executor(None, service.remove_user_from_group, target, username)
            return json.dumps({"status": "ok" if success else "error", "action": act, "removed": success, "group": target, "username": username}, ensure_ascii=False)
        elif act == "get_password_policy":
            res = await loop.run_in_executor(None, service.get_password_policy)
            return json.dumps({"status": "ok", "action": act, "password_policy": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.identity] Ошибка управления учетной записью ('{action}', '{target}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 4: Журнал событий безопасности входов и прав
# =============================================================================

@tool
async def windows_identity_audit_events(
    limit: int = 30,
    username: Optional[str] = None,
    event_id: Optional[int] = None,
) -> str:
    """Возвращает историю событий безопасности из журнала Windows (события входа, изменения прав, создание пользователей).

    Args:
        limit: Максимальное количество возвращаемых записей (по умолчанию 30).
        username: Опциональная фильтрация по имени конкретного пользователя.
        event_id: Опциональный код события безопасности (Event ID, например 4624 - вход, 4625 - сбой входа, 4720 - создан пользователь).

    Returns:
        JSON со списком отфильтрованных событий безопасности.
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        loop = asyncio.get_running_loop()

        if username:
            res = await loop.run_in_executor(None, service.get_user_audit_events, username, limit)
        else:
            res = await loop.run_in_executor(None, service.get_audit_events, limit, event_id)

        return json.dumps({"status": "ok", "limit": limit, "username": username, "event_id": event_id, "events": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.identity] Ошибка запроса аудита событий безопасности: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 5: Построение графа связей доступов (Identity Graph)
# =============================================================================

@tool
async def windows_identity_graph_build() -> str:
    """Строит полный граф отношений Windows Identity Graph (пользователи, группы, права, сессии и связующие узлы).

    Returns:
        JSON со всеми узлами (nodes) и ребрами (edges) графа безопасности Windows.
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, service.get_identity_graph)
        return json.dumps({"status": "ok", "graph": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.identity] Ошибка построения Identity Graph: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


WINDOWS_IDENTITY_TOOLS = [
    windows_identity_explain,
    windows_identity_explain_pid,
    windows_identity_audit_security,
    windows_identity_manage_account,
    windows_identity_audit_events,
    windows_identity_graph_build,
]
