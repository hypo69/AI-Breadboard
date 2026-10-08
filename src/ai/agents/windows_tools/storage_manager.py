# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Storage Manager Tools Module
# =============================================================================
# Description:
#   Инструменты инспекции, аудита дисковых накопителей, томов и выполнения
#   безопасных административных операций над хранилищем Windows SafeOps (apps.windows.modules.storage_manager).
#   Включают:
#     1. Инспекция и аудит дисков и томов (windows_storage_audit)
#     2. Административные действия над хранилищем SafeOps (windows_storage_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.storage_manager import windows_storage_audit
#     res = await windows_storage_audit(action="summary")
#
# File: storage_manager.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:27:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления дисковым хранилищем Windows для ИИ-агентов."""

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
# Блок 1: Инспекция и аудит дискового хранилища
# =============================================================================

@tool
async def windows_storage_audit(
    action: str = "summary",
    limit: int = 50,
) -> str:
    """Глубокая инспекция и аудит дисковых накопителей и логических томов Windows.

    Args:
        action: Режим инспекции:
            - 'summary': сводная статистика общего объёма, свободного места, количества физических дисков и томов
            - 'volumes': список логических томов (буквы дисков, файловые системы NTFS/ReFS/FAT32, процент занятости)
            - 'disks': физические накопители (NVMe, SSD, HDD, размер, статус здоровья, системный/загрузочный диск)
            - 'report': полный структурированный отчёт о блочной инфраструктуре хранения
        limit: Ограничение выдачи списков элементов (по умолчанию 50).

    Returns:
        JSON с результатами инспекции дискового хранилища.
    """
    try:
        from apps.windows.modules.storage_manager.core.manager import StorageManager

        sm = StorageManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            report = await loop.run_in_executor(None, sm.generate_report)
            disks_count = len(report.disks)
            vols_count = len(report.volumes)
            total_cap = sum(getattr(v, "total_gb", 0.0) for v in report.volumes) if report.volumes else 0.0
            free_cap = sum(getattr(v, "free_gb", 0.0) for v in report.volumes) if report.volumes else 0.0
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_disks": disks_count,
                "total_volumes": vols_count,
                "total_capacity_gb": round(total_cap, 2),
                "free_capacity_gb": round(free_cap, 2),
            }, ensure_ascii=False)

        elif act == "volumes":
            vols = await loop.run_in_executor(None, sm.get_volumes)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_volumes": len(vols),
                "volumes": _to_serializable(vols[:limit]),
            }, ensure_ascii=False)

        elif act == "disks":
            disks = await loop.run_in_executor(None, sm.get_disks)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_disks": len(disks),
                "disks": _to_serializable(disks[:limit]),
            }, ensure_ascii=False)

        elif act == "report":
            report = await loop.run_in_executor(None, sm.generate_report)
            return json.dumps({
                "status": "ok",
                "action": act,
                "report": _to_serializable(report),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.storage_manager] Ошибка аудита хранилища ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Административные операции над хранилищем (SafeOps)
# =============================================================================

@tool
async def windows_storage_action(
    action: str,
    target: str,
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Выполнение административных операций над дисковым хранилищем (анализ, проверка ФС, оптимизация) SafeOps.

    Args:
        action: Тип действия (например: 'check_filesystem', 'analyze_space', 'trim_ssd', 'defrag').
        target: Целевой диск или том (например: 'C:', '\\\\.\\PhysicalDrive0').
        dry_run: Режим симуляции (по умолчанию True для предотвращения нежелательных операций).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом выполнения или симуляции операции над хранилищем.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": action,
                "target": target,
                "dry_run": True,
                "message": f"Симуляция операции '{action}' для цели '{target}' прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        from apps.windows.modules.storage_manager.core.manager import StorageManager
        sm = StorageManager()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, sm.execute_operation, action, target)
        return json.dumps({
            "status": "ok",
            "action": action,
            "target": target,
            "result": _to_serializable(res),
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.storage_manager] Ошибка операции '{action}' над '{target}': {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "target": target, "error": str(e)}, ensure_ascii=False)


WINDOWS_STORAGE_MANAGER_TOOLS = [
    windows_storage_audit,
    windows_storage_action,
]
