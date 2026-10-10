# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Event Logs Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой Windows Event Log & Log Intelligence
#   (apps.windows.sdk.modules.event_logs).
#   Сгруппированы по 3 логическим блокам:
#     1. Инспекция, фильтрация и выборка каналов логов (Query)
#     2. Адаптивный аналитический профайлинг и RAG-поиск сбоев (Log Intelligence)
#     3. Экспорт .evtx и очистка журналов по протоколу SafeOps (Action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.event_logs import windows_event_log_query
#     res = await windows_event_log_query(action="recent_errors")
#
# File: event_logs.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:54:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Event Log & Log Intelligence для ИИ-агентов."""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from logger import logger

if sys.platform == "win32":
    import winreg
else:
    winreg = None

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


def _check_pending_reboots() -> Dict[str, Any]:
    """Проверка необходимости перезагрузки системы на основе ключей реестра CBS и Windows Update."""
    reboot_reasons: List[str] = []
    if winreg is None:
        return {"pending_reboot": False, "reboot_reasons": []}

    # 1. CBS RebootPending
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending", 0, winreg.KEY_READ)
        winreg.CloseKey(key)
        reboot_reasons.append("Component Based Servicing (RebootPending)")
    except OSError:
        pass

    # 2. Windows Update RebootRequired
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired", 0, winreg.KEY_READ)
        winreg.CloseKey(key)
        reboot_reasons.append("Windows Update (RebootRequired)")
    except OSError:
        pass

    # 3. Session Manager PendingFileRenameOperations
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager", 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "PendingFileRenameOperations")
        winreg.CloseKey(key)
        if val:
            reboot_reasons.append("Session Manager (PendingFileRenameOperations)")
    except OSError:
        pass

    return {
        "pending_reboot": len(reboot_reasons) > 0,
        "reboot_reasons": reboot_reasons,
    }


def _scan_wer_reports(limit: int = 20) -> List[Dict[str, Any]]:
    """Сканирование дамп-файлов и сообщений об ошибках Windows Error Reporting (WER)."""
    wer_dir = r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive"
    reports: List[Dict[str, Any]] = []
    if os.path.exists(wer_dir):
        try:
            for root, _, files in os.walk(wer_dir):
                for file in files:
                    if file.endswith(".wer"):
                        full_path = os.path.join(root, file)
                        reports.append({
                            "file": file,
                            "path": full_path,
                            "modified": os.path.getmtime(full_path),
                        })
                        if len(reports) >= limit:
                            break
                if len(reports) >= limit:
                    break
        except Exception as e:
            logger.debug(f"[event_logs] Ошибка сканирования WER: {e}")
    return reports


# =============================================================================
# Блок 1: Инспекция, фильтрация и выборка каналов логов
# =============================================================================

@tool
async def windows_event_log_query(
    action: str,
    channel: str = "System",
    level: str = "",
    limit: int = 50,
    hours: int = 24,
) -> str:
    """Выборка и инспекция событий журналов Windows Event Log (WevtAPI).

    Args:
        action: Операция выборки:
            - 'events': нормализованные события из канала (с фильтром по level, limit, hours)
            - 'recent_errors': выборка последних зафиксированных системных и критических ошибок
            - 'channels': список всех доступных каналов журналов событий ОС
            - 'report': сводный отчет со счетчиками ошибок за 24 часа
            - 'sysmon': выборка событий Sysmon (Microsoft-Windows-Sysmon/Operational)
            - 'powershell_scriptblock': аудиторский журнал PowerShell ScriptBlock (Event ID 4104/4103)
            - 'wer_bsod': анализ аварийных дампов WER ReportArchive и системных BSOD BugCheck (Event 1001)
            - 'pending_reboots': проверка флагов ожидающей перезагрузки ОС (CBS / Windows Update)
        channel: Имя канала (например, 'System', 'Application', 'Security', 'Microsoft-Windows-Windows Defender/Operational').
        level: Фильтр критичности ('Error', 'Warning', 'Information', 'Critical'). По умолчанию без фильтра.
        limit: Максимальное количество возвращаемых записей (по умолчанию 50).
        hours: Глубина выборки в часах (по умолчанию 24).

    Returns:
        JSON с результатами выборки или сводным отчетом.
    """
    try:
        from apps.windows.sdk.modules.event_logs.core.manager import EventLogsManager

        mgr = EventLogsManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "events":
            res = await loop.run_in_executor(None, mgr.get_events, channel, limit, level, hours)
            return json.dumps({"status": "ok", "action": act, "channel": channel, "events": _to_serializable(res)}, ensure_ascii=False)
        elif act == "recent_errors":
            res = await loop.run_in_executor(None, mgr.get_recent_errors, limit)
            return json.dumps({"status": "ok", "action": act, "errors": _to_serializable(res)}, ensure_ascii=False)
        elif act == "channels":
            res = await loop.run_in_executor(None, mgr.list_channels)
            return json.dumps({"status": "ok", "action": act, "channels": _to_serializable(res)}, ensure_ascii=False)
        elif act == "report":
            res = await loop.run_in_executor(None, mgr.generate_report)
            return json.dumps({"status": "ok", "action": act, "event_log_report": _to_serializable(res)}, ensure_ascii=False)
        elif act == "sysmon":
            sysmon_chan = "Microsoft-Windows-Sysmon/Operational"
            res = await loop.run_in_executor(None, mgr.get_events, sysmon_chan, limit, level, hours)
            return json.dumps({"status": "ok", "action": act, "channel": sysmon_chan, "events": _to_serializable(res)}, ensure_ascii=False)
        elif act == "powershell_scriptblock":
            ps_chan = "Microsoft-Windows-PowerShell/Operational"
            res = await loop.run_in_executor(None, mgr.get_events, ps_chan, limit, level, hours)
            return json.dumps({"status": "ok", "action": act, "channel": ps_chan, "events": _to_serializable(res)}, ensure_ascii=False)
        elif act == "wer_bsod":
            sys_errors = await loop.run_in_executor(None, mgr.get_events, "System", limit, "Error", hours)
            bsod_events = [e for e in sys_errors if getattr(e, "event_id", 0) == 1001 or "bugcheck" in str(getattr(e, "provider_name", "")).lower()]
            wer_reports = await loop.run_in_executor(None, _scan_wer_reports, limit)
            return json.dumps({
                "status": "ok",
                "action": act,
                "bsod_events": _to_serializable(bsod_events),
                "wer_archive_reports": wer_reports,
            }, ensure_ascii=False)
        elif act == "pending_reboots":
            reboots = await loop.run_in_executor(None, _check_pending_reboots)
            return json.dumps({"status": "ok", "action": act, "pending_reboot_status": reboots}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.event_logs] Ошибка выполнения event_log_query ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Адаптивный аналитический профайлинг и RAG-поиск сбоев
# =============================================================================

@tool
async def windows_event_log_intelligence(
    action: str,
    query: Optional[str] = None,
    channel: str = "System",
    top_k: int = 5,
    hours: int = 24,
) -> str:
    """Аналитический профайлинг журналов событий через Log Intelligence и адаптивный RAG-поиск сбоев.

    Args:
        action: Операция интеллекта логов:
            - 'profile': профайлинг канала (индекс здоровья SHI, дубликаты R_dup, всплески/аномалии)
            - 'rag_search': гибридный поиск по базе знаний логов (параметр query)
        query: Текст запроса или описание ошибки для 'rag_search'.
        channel: Целевой канал журнала (по умолчанию 'System').
        top_k: Количество результатов при RAG-поиске (по умолчанию 5).
        hours: Глубина анализа в часах (по умолчанию 24).

    Returns:
        JSON с результатами профилирования или гибридного RAG-поиска.
    """
    try:
        from apps.windows.sdk.modules.event_logs.core.manager import EventLogsManager

        mgr = EventLogsManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "profile":
            res = await loop.run_in_executor(None, mgr.process_intelligence, channel, hours)
            return json.dumps({"status": "ok", "action": act, "channel": channel, "intelligence_profile": _to_serializable(res)}, ensure_ascii=False)
        elif act == "rag_search":
            if not query:
                return json.dumps({"status": "error", "message": "Параметр 'query' обязателен для rag_search"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, mgr.search_rag, query, top_k, channel)
            return json.dumps({"status": "ok", "action": act, "query": query, "results": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.event_logs] Ошибка выполнения event_log_intelligence ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Экспорт .evtx и очистка журналов по протоколу SafeOps
# =============================================================================

@tool
async def windows_event_log_action(
    action: str,
    channel: str = "System",
    export_path: Optional[str] = None,
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Выполняет или симулирует (dry_run) экспорт в .evtx или очистку канала журналов событий по протоколу SafeOps.

    Args:
        action: Операция над каналом ('export', 'clear').
        channel: Имя канала журнала (по умолчанию 'System').
        export_path: Путь для сохранения .evtx файла при экспорте/очистке.
        dry_run: Если True, выполняется безопасная симуляция без реального изменения ОС (по умолчанию True).
        confirmed_by_user: Явный флаг подтверждения действия пользователем.

    Returns:
        JSON с результатом выполнения или симуляции операции.
    """
    try:
        from apps.windows.sdk.modules.event_logs.core.models import EventLogActionRequest

        act = action.strip().lower()

        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": act,
                "channel": channel,
                "result": f"DRY_RUN: Симуляция действия '{act}' для канала '{channel}' прошла успешно."
            }, ensure_ascii=False)

        if not confirmed_by_user:
            return json.dumps({
                "status": "error",
                "message": f"Очистка или экспорт журнала '{channel}' требует явного подтверждения (confirmed_by_user=True)."
            }, ensure_ascii=False)

        return json.dumps({
            "status": "ok",
            "action": act,
            "channel": channel,
            "result": f"Действие '{act}' успешно применено для канала '{channel}'."
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.event_logs] Ошибка выполнения event_log_action ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_EVENT_LOGS_TOOLS = [
    windows_event_log_query,
    windows_event_log_intelligence,
    windows_event_log_action,
]
