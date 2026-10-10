# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Defender Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой Microsoft Defender & AI Security
#   (apps.windows.sdk.modules.defender).
#   Сгруппированы по 3 логическим блокам:
#     1. Мониторинг защиты, сканирование и обновление сигнатур (Status & Scan)
#     2. Аудит ASR правил, эвристика исключений и история угроз (Audit Security)
#     3. Итоговая диагностика защищенности Security Score (AI Diagnostics)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.defender import windows_defender_status_scan
#     res = await windows_defender_status_scan(action="status")
#
# File: defender.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:17:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Microsoft Defender & AI Security для ИИ-агентов."""

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
# Блок 1: Статус защиты, запуск сканирования и обновление сигнатур
# =============================================================================

@tool
async def windows_defender_status_scan(
    action: str,
    scan_type: str = "quick",
    target_path: Optional[str] = None,
) -> str:
    """Управление Microsoft Defender: проверка статуса защиты в реальном времени, запуск сканирования и обновление баз.

    Args:
        action: Операция:
            - 'status': статус Real-Time Protection, AMSI, антивирусного движка и служб
            - 'scan': запуск антивирусного сканирования (scan_type: 'quick', 'full', 'custom')
            - 'update_signatures': принудительное обновление антивирусных баз сигнатур
        scan_type: Тип сканирования для action='scan' ('quick', 'full', 'custom'). По умолчанию 'quick'.
        target_path: Целевой путь к папке/файлу для выборочного сканирования (scan_type='custom').

    Returns:
        JSON со статусом защиты, результатами сканирования или обновления.
    """
    try:
        from apps.windows.sdk.modules.defender.core.defender_service import DefenderService

        srv = DefenderService()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "status":
            res = await loop.run_in_executor(None, srv.get_defender_status)
            return json.dumps({"status": "ok", "action": act, "defender_status": _to_serializable(res)}, ensure_ascii=False)
        elif act == "scan":
            res = await loop.run_in_executor(None, srv.run_scan, scan_type, target_path)
            return json.dumps({"status": "ok", "action": act, "scan_result": _to_serializable(res)}, ensure_ascii=False)
        elif act == "update_signatures":
            res = await loop.run_in_executor(None, srv.update_signatures)
            return json.dumps({"status": "ok" if getattr(res, 'success', True) else "error", "action": act, "update_result": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.defender] Ошибка выполнения defender_status_scan ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Аудит правил ASR, исключений и история угроз
# =============================================================================

@tool
async def windows_defender_audit_security(
    mode: str = "all",
) -> str:
    """Аудит правил Attack Surface Reduction (ASR), эвристический анализ исключений и история угроз.

    Args:
        mode: Режим аудита:
            - 'all': полный аудит (ASR правила, эвристика исключений, журнал обнаруженных угроз)
            - 'asr': аудит статуса 14+ правил Attack Surface Reduction
            - 'exclusions': аудит исключений с выявление рисков (C:\\, %TEMP%, системные скрипты)
            - 'threats': история найденного вредоносного ПО и статус изоляции в карантине

    Returns:
        JSON с результатами аудита подсистем безопасности Defender.
    """
    try:
        from apps.windows.sdk.modules.defender.core.asr_manager import ASRManager
        from apps.windows.sdk.modules.defender.core.exclusions_auditor import ExclusionsAuditor
        from apps.windows.sdk.modules.defender.core.threat_manager import ThreatManager

        loop = asyncio.get_running_loop()
        m = mode.strip().lower()

        result: Dict[str, Any] = {"status": "ok", "mode": m}

        if m in ("all", "asr"):
            asr_mgr = ASRManager()
            result["asr_rules"] = _to_serializable(await loop.run_in_executor(None, asr_mgr.get_asr_rules))
        if m in ("all", "exclusions"):
            ex_auditor = ExclusionsAuditor()
            result["exclusions_audit"] = _to_serializable(await loop.run_in_executor(None, ex_auditor.audit_exclusions))
        if m in ("all", "threats"):
            threat_mgr = ThreatManager()
            result["recent_threats"] = _to_serializable(await loop.run_in_executor(None, threat_mgr.get_threats_history))

        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.defender] Ошибка аудита безопасности (mode='{mode}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "mode": mode, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Итоговая AI-диагностика защищенности (Security Score)
# =============================================================================

@tool
async def windows_defender_ai_diagnostics() -> str:
    """Формирует итоговый аналитический отчёт защищенности системы (Security Score 0-100%).

    Returns:
        JSON со сводным индексом защищенности, приоритизированными уязвимостями и списком рекомендаций.
    """
    try:
        from apps.windows.sdk.modules.defender.core.ai_diagnostician import AIDiagnostician

        diag = AIDiagnostician()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, diag.generate_diagnostic_report)
        return json.dumps({"status": "ok", "security_report": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.defender] Ошибка выполнения AI-диагностики Defender: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


WINDOWS_DEFENDER_TOOLS = [
    windows_defender_status_scan,
    windows_defender_audit_security,
    windows_defender_ai_diagnostics,
]
