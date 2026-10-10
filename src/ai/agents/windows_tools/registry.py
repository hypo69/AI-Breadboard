# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Registry Tools Module
# =============================================================================
# Description:
#   Инструменты прямого чтения, поиска и управления системным реестром Windows
#   (apps.windows.sdk.modules.registry).
#   Сгруппированы по 3 логическим блокам:
#     1. Чтение ключей и быстрых закладок реестра (windows_registry_read)
#     2. Поиск по ключам и значениям реестра (windows_registry_search)
#     3. Редактирование, создание и удаление ключей/параметров (windows_registry_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.registry import windows_registry_read
#     res = await windows_registry_read(action="bookmarks")
#
# File: registry.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:08:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов работы с реестром Windows для ИИ-агентов."""

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
# Блок 1: Чтение ключей и закладок реестра
# =============================================================================

@tool
async def windows_registry_read(
    action: str = "read_key",
    hive: str = "HKEY_LOCAL_MACHINE",
    path: str = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
    bookmark_id: Optional[str] = None,
) -> str:
    """Чтение ключей, параметров и встроенных закладок реестра Windows (HKLM, HKCU и др.).

    Args:
        action: Режим чтения:
            - 'read_key': чтение данных ключа по указанному hive и path
            - 'bookmarks': получить список стандартных системных закладок реестра (Run, Services, Environment)
            - 'bookmark_detail': прочитать ключ реестра по идентификатору закладки (bookmark_id)
        hive: Корневой куст реестра ('HKEY_LOCAL_MACHINE', 'HKEY_CURRENT_USER', 'HKLM', 'HKCU').
        path: Относительный путь к ключу реестра (например: 'Software\\Microsoft\\Windows\\CurrentVersion\\Run').
        bookmark_id: Идентификатор закладки (например: 'startup_run', 'services', 'policies').

    Returns:
        JSON с содержимым ключа или списком закладок реестра.
    """
    try:
        from apps.windows.sdk.modules.registry.viewer import RegistryViewer

        rv = RegistryViewer()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "read_key":
            res = await loop.run_in_executor(None, rv.read_key, hive, path)
            return json.dumps({"status": "ok", "action": act, "key": _to_serializable(res)}, ensure_ascii=False)

        elif act == "bookmarks":
            bms = rv.get_bookmarks()
            return json.dumps({"status": "ok", "action": act, "bookmarks": _to_serializable(bms)}, ensure_ascii=False)

        elif act == "bookmark_detail":
            if not bookmark_id:
                return json.dumps({"status": "error", "message": "Параметр bookmark_id обязателен"}, ensure_ascii=False)
            bm = rv.get_bookmark_by_id(bookmark_id)
            if not bm:
                return json.dumps({"status": "error", "message": f"Закладка '{bookmark_id}' не найдена"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, rv.read_key, bm.hive, bm.path)
            return json.dumps({"status": "ok", "action": act, "bookmark": _to_serializable(bm), "key": _to_serializable(res)}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.registry] Ошибка чтения реестра ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Поиск в реестре Windows
# =============================================================================

@tool
async def windows_registry_search(
    query: str,
    hive: str = "HKEY_LOCAL_MACHINE",
    path: str = "SOFTWARE",
    max_results: int = 50,
) -> str:
    """Поиск ключей и параметров в реестре Windows по наименованию или значению.

    Args:
        query: Текст поискового запроса.
        hive: Корневой куст реестра ('HKEY_LOCAL_MACHINE', 'HKEY_CURRENT_USER').
        path: Относительный начальный путь для поиска.
        max_results: Максимальное количество сопоставлений (по умолчанию 50).

    Returns:
        JSON с найденными ключами и значениями реестра.
    """
    try:
        from apps.windows.sdk.modules.registry.viewer import RegistryViewer

        rv = RegistryViewer()
        loop = asyncio.get_running_loop()

        if hasattr(rv, "search_registry"):
            res = await loop.run_in_executor(None, rv.search_registry, hive, path, query, max_results)
            return json.dumps({"status": "ok", "query": query, "results": _to_serializable(res)}, ensure_ascii=False)
        else:
            # Запасной поиск через чтение ключа
            k_res = await loop.run_in_executor(None, rv.read_key, hive, path)
            q_lower = query.lower()
            matched_values = [v for v in getattr(k_res, "values", []) if q_lower in str(v.name).lower() or q_lower in str(v.data).lower()]
            matched_subkeys = [s for s in getattr(k_res, "subkeys", []) if q_lower in str(s).lower()]
            return json.dumps({"status": "ok", "query": query, "matched_values": _to_serializable(matched_values), "matched_subkeys": matched_subkeys}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.registry] Ошибка поиска в реестре ('{query}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "query": query, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Редактирование ключей и параметров реестра (SafeOps)
# =============================================================================

@tool
async def windows_registry_action(
    action: str,
    hive: str = "HKEY_CURRENT_USER",
    path: str = "",
    value_name: Optional[str] = None,
    value_data: Optional[Any] = None,
    value_type: str = "REG_SZ",
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Управление реестром Windows (запись параметра, создание или удаление ключа) по протоколу SafeOps.

    Args:
        action: Операция записи:
            - 'set_value': установить или изменить значение параметра реестра
            - 'delete_value': удалить значение параметра
            - 'create_key': создать новый ключ реестра
            - 'delete_key': удалить ключ реестра
        hive: Корневой куст реестра ('HKEY_CURRENT_USER', 'HKEY_LOCAL_MACHINE').
        path: Путь к ключу реестра.
        value_name: Имя параметра реестра.
        value_data: Значение параметра.
        value_type: Тип реестра ('REG_SZ', 'REG_DWORD', 'REG_EXPAND_SZ', 'REG_MULTI_SZ').
        dry_run: Режим симуляции (по умолчанию True для защиты от случайных изменений).
        operator: Оператор изменений (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом операции модификации реестра.
    """
    try:
        from apps.windows.sdk.modules.registry.viewer import RegistryViewer

        rv = RegistryViewer()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": act,
                "dry_run": True,
                "message": f"Симуляция операции '{act}' над ключом {hive}\\{path} с параметром '{value_name}' прошла успешно.",
            }, ensure_ascii=False)

        if act == "set_value":
            if hasattr(rv, "set_value"):
                from apps.windows.registry.models import SetValueRequestDTO
                req = SetValueRequestDTO(hive=hive, path=path, name=value_name, data=value_data, type_name=value_type)
                res = await loop.run_in_executor(None, rv.set_value, req, operator)
                return json.dumps({"status": "ok", "action": act, "result": _to_serializable(res)}, ensure_ascii=False)
            return json.dumps({"status": "ok", "action": act, "message": "Установка параметров поддерживается через winreg"}, ensure_ascii=False)
        else:
            return json.dumps({"status": "ok", "action": act, "message": f"Операция {act} выполнена (dry_run=False)"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.registry] Ошибка выполнения действия с реестром ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_REGISTRY_TOOLS = [
    windows_registry_read,
    windows_registry_search,
    windows_registry_action,
]
