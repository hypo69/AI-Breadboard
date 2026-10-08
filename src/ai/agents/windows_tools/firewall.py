# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Firewall Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой брандмауэра Windows
#   (apps.windows.modules.firewall_manager).
#   Сгруппированы по 2 логическим блокам:
#     1. Инспекция и аудит профилей и правил сетевого экрана (windows_firewall_audit)
#     2. Безопасные действия с правилами сетевого экрана по SafeOps (windows_firewall_rule_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.firewall import windows_firewall_audit
#     res = await windows_firewall_audit(action="profiles")
#
# File: firewall.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:35:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Firewall Manager для ИИ-агентов."""

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
# Блок 1: Аудит профилей и правил сетевого экрана
# =============================================================================

@tool
async def windows_firewall_audit(
    action: str,
    direction: Optional[str] = None,
) -> str:
    """Аудит профилей и правил сетевого экрана Windows Firewall.

    Args:
        action: Операция аудита брандмауэра:
            - 'profiles': получение статуса профилей Domain, Private, Public
            - 'rules': реестр правил брандмауэра (фильтрация по direction: 'in', 'out' или None)
            - 'report': сводный статистический отчёт безопасности брандмауэра
        direction: Фильтр направления трафика для 'rules' ('in', 'out' или None).

    Returns:
        JSON с результатами аудита профилей, правил или сводного отчёта.
    """
    try:
        from apps.windows.modules.firewall_manager.core.manager import FirewallManager

        mgr = FirewallManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "profiles":
            res = await loop.run_in_executor(None, mgr.get_profiles)
            return json.dumps({"status": "ok", "action": act, "profiles": _to_serializable(res)}, ensure_ascii=False)
        elif act == "rules":
            res = await loop.run_in_executor(None, mgr.list_rules, direction)
            return json.dumps({"status": "ok", "action": act, "direction": direction, "rules": _to_serializable(res)}, ensure_ascii=False)
        elif act == "report":
            res = await loop.run_in_executor(None, mgr.generate_report)
            return json.dumps({"status": "ok", "action": act, "report": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.firewall] Ошибка аудита брандмауэра ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление правилами сетевого экрана по SafeOps
# =============================================================================

@tool
async def windows_firewall_rule_action(
    action: str,
    rule_name: str,
    direction: str = "In",
    rule_action: str = "Allow",
    protocol: str = "TCP",
    port: Optional[str] = None,
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Безопасное выполнение или симуляция действий с правилами сетевого экрана Windows по протоколу SafeOps.

    Args:
        action: Тип операции над правилом ('enable', 'disable', 'add', 'delete', 'allow', 'block').
        rule_name: Уникальное имя правила брандмауэра.
        direction: Направление трафика ('In' или 'Out').
        rule_action: Действие по умолчанию ('Allow' или 'Block').
        protocol: Протокол сетевого соединения ('TCP', 'UDP', 'Any').
        port: Номер локального/удаленного порта (например, '8000', '3389').
        dry_run: Режим безопасной симуляции без внесения изменений в ОС (по умолчанию True).
        confirmed_by_user: Явный флаг подтверждения операции пользователем.

    Returns:
        JSON с результатом выполнения или симуляции операции над правилом.
    """
    try:
        from apps.windows.modules.firewall_manager.core.manager import FirewallManager
        from apps.windows.modules.firewall_manager.core.models import FirewallRuleActionRequest

        mgr = FirewallManager()
        req = FirewallRuleActionRequest(
            rule_name=rule_name,
            action=action,
            direction=direction,
            rule_action=rule_action,
            port=port,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await mgr.execute_rule_action(req)
        return json.dumps({"status": "ok", "action": action, "rule_name": rule_name, "result": res}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.firewall] Ошибка выполнения действия над правилом '{rule_name}' ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "rule_name": rule_name, "error": str(e)}, ensure_ascii=False)


WINDOWS_FIREWALL_TOOLS = [
    windows_firewall_audit,
    windows_firewall_rule_action,
]
