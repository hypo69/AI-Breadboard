# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Startup Tools Module
# =============================================================================
# Description:
#   Инструменты глубокого аудита и управления элементами автозагрузки Windows
#   (реестр Run/RunOnce, папки автозапуска, задачи планировщика) (apps.windows.sdk.modules.startup).
#   Включают:
#     1. Сканирование и аудит рисков элементов автозагрузки (windows_startup_audit)
#     2. Переключение состояния (включение/отключение) автозапуска SafeOps (windows_startup_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.startup import windows_startup_audit
#     res = await windows_startup_audit(action="summary")
#
# File: startup.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:54:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления автозагрузкой Windows для ИИ-агентов."""

import asyncio
import json
import subprocess
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from logger import logger


def _audit_wmi_persistence() -> Dict[str, Any]:
    """Проверка элементов WMI Persistence (__EventFilter, __EventConsumer, __FilterToConsumerBinding)."""
    consumers: List[Dict[str, Any]] = []
    filters: List[Dict[str, Any]] = []
    bindings: List[Dict[str, Any]] = []
    try:
        ps_cmd = (
            "Get-CimInstance -Namespace root\\subscription -ClassName __EventConsumer | Select-Object Name, Caption | ConvertTo-Json; "
            "Get-CimInstance -Namespace root\\subscription -ClassName __EventFilter | Select-Object Name, Query | ConvertTo-Json; "
            "Get-CimInstance -Namespace root\\subscription -ClassName __FilterToConsumerBinding | Select-Object Consumer, Filter | ConvertTo-Json"
        )
        proc = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, text=True, timeout=8)
        if proc.returncode == 0 and proc.stdout.strip():
            lines = proc.stdout.strip().split("\n")
            for line in lines:
                if line.startswith("{") or line.startswith("["):
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict):
                            consumers.append(data)
                        elif isinstance(data, list):
                            consumers.extend(data)
                    except Exception:
                        pass
    except Exception as e:
        logger.debug(f"[startup] WMI persistence audit error: {e}")

    return {
        "status": "ok",
        "action": "wmi_persistence",
        "total_consumers": len(consumers),
        "wmi_event_consumers": consumers,
        "wmi_event_filters": filters,
        "wmi_bindings": bindings,
    }


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
# Блок 1: Аудит автозагрузки Windows
# =============================================================================

@tool
async def windows_startup_audit(
    action: str = "summary",
    limit: int = 50,
) -> str:
    """Глубокий аудит автозагрузки Windows (реестр HKLM/HKCU Run, папки автозапуска, задачи планировщика, WMI Persistence).

    Args:
        action: Режим аудита:
            - 'summary': сводная статистика (всего элементов, включенных/отключенных, подозрительных, битых ссылок)
            - 'report': полный структурированный отчёт о всех элементах автозапуска
            - 'high_risk': фильтрация элементов с повышенным или критическим уровнем риска (SUSPICIOUS/CRITICAL)
            - 'broken': списки элементов автозагрузки, ссылающихся на несуществующие файлы
            - 'wmi_persistence': аудит закрепления в системе через подписки WMI EventConsumer / EventFilter
        limit: Ограничение выдачи списка элементов (по умолчанию 50).

    Returns:
        JSON с результатом аудита точек автозагрузки.
    """
    try:
        from apps.windows.sdk.modules.startup.core.auditor import StartupAuditor

        auditor = StartupAuditor()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "wmi_persistence":
            wmi_res = await loop.run_in_executor(None, _audit_wmi_persistence)
            return json.dumps(wmi_res, ensure_ascii=False)

        report = await loop.run_in_executor(None, auditor.run_audit)

        if act == "summary":
            return json.dumps({
                "status": "ok",
                "action": act,
                "summary": _to_serializable(report.summary),
                "system_recommendations": getattr(report, "recommendations", []),
            }, ensure_ascii=False)

        elif act == "report":
            return json.dumps({
                "status": "ok",
                "action": act,
                "total": len(report.entries),
                "entries": _to_serializable(report.entries[:limit]),
            }, ensure_ascii=False)

        elif act == "high_risk":
            alerts = getattr(report, "security_alerts", [])
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_alerts": len(alerts),
                "high_risk_entries": _to_serializable(alerts[:limit]),
            }, ensure_ascii=False)

        elif act == "broken":
            broken = getattr(report, "broken_items", [])
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_broken": len(broken),
                "broken_entries": _to_serializable(broken[:limit]),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.startup] Ошибка аудита автозагрузки ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление состоянием элементов автозапуска (SafeOps)
# =============================================================================

@tool
async def windows_startup_action(
    entry_id_or_name: str,
    enable: bool = True,
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Включение или отключение элемента автозагрузки Windows по протоколу SafeOps/dry_run.

    Args:
        entry_id_or_name: Идентификатор или имя элемента автозагрузки.
        enable: True для включения, False для отключения.
        dry_run: Режим симуляции (по умолчанию True для безопасности).
        operator: Оператор изменений (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом переключения элемента автозапуска.
    """
    try:
        from apps.windows.sdk.modules.startup.core.auditor import StartupAuditor
        from apps.windows.sdk.modules.startup.core.manager import StartupManager

        if dry_run:
            return json.dumps({
                "status": "ok",
                "entry_id_or_name": entry_id_or_name,
                "dry_run": True,
                "message": f"Симуляция переключения элемента автозагрузки '{entry_id_or_name}' в состояние enable={enable} прошла успешно.",
            }, ensure_ascii=False)

        auditor = StartupAuditor()
        sm = StartupManager()
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(None, auditor.run_audit)

        target_entry = None
        for e in report.entries:
            if e.id == entry_id_or_name or e.name.lower() == entry_id_or_name.lower():
                target_entry = e
                break

        if not target_entry:
            return json.dumps({
                "status": "error",
                "message": f"Элемент автозагрузки '{entry_id_or_name}' не найден."
            }, ensure_ascii=False)

        res = await loop.run_in_executor(None, sm.toggle_item, target_entry, enable)
        return json.dumps({"status": "ok", "entry_id": target_entry.id, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.startup] Ошибка управления элементом автозагрузки '{entry_id_or_name}': {e}", exc_info=True)
        return json.dumps({"status": "error", "entry_id_or_name": entry_id_or_name, "error": str(e)}, ensure_ascii=False)


WINDOWS_STARTUP_TOOLS = [
    windows_startup_audit,
    windows_startup_action,
]
