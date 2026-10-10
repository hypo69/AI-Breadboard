# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows System Checkpoints Tools Module
# =============================================================================
# Description:
#   Инструменты управления единым координатором контрольных точек восстановления
#   Windows (DISM WIM-образы, WinRE и Restore Points VSS) (apps.windows.sdk.modules.system_checkpoints).
#   Включают:
#     1. Инспекция готовности и дрейфа контрольных точек (windows_checkpoints_audit)
#     2. Создание и управление контрольными точками SafeOps (windows_checkpoints_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.system_checkpoints import windows_checkpoints_audit
#     res = await windows_checkpoints_audit(action="health")
#
# File: system_checkpoints.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:31:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов контрольных точек восстановления Windows для ИИ-агентов."""

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
# Блок 1: Инспекция готовности контрольных точек и восстановления
# =============================================================================

@tool
async def windows_checkpoints_audit(
    action: str = "health",
    limit: int = 50,
) -> str:
    """Аудит готовности системы контрольных точек и трех механизмов восстановления Windows (WIM, WinRE, VSS).

    Args:
        action: Режим аудита:
            - 'health': сводный индекс готовности восстановления (0-100), статусы WinRE, System Restore и WIM-образов
            - 'freshness': оценка актуальности последнего контрольного образа и временного дрейфа системы
            - 'catalog': реестр всех сохранённых контрольных точек системы
        limit: Ограничение выдачи списка элементов в каталоге (по умолчанию 50).

    Returns:
        JSON с результатами аудита контрольных точек восстановления.
    """
    try:
        try:
            from apps.windows.sdk.modules.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator
        except ImportError:
            from apps.windows.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator

        coord = CheckpointCoordinator()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "health":
            health = await loop.run_in_executor(None, coord.get_comprehensive_health)
            return json.dumps({
                "status": "ok",
                "action": act,
                "health": _to_serializable(health),
            }, ensure_ascii=False)

        elif act == "freshness":
            freshness = await loop.run_in_executor(None, coord.get_freshness_report)
            return json.dumps({
                "status": "ok",
                "action": act,
                "freshness": _to_serializable(freshness),
            }, ensure_ascii=False)

        elif act == "catalog":
            catalog = await loop.run_in_executor(None, coord.load_catalog)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_checkpoints": len(catalog),
                "catalog": _to_serializable(catalog[:limit]),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.system_checkpoints] Ошибка аудита контрольных точек ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Создание и управление контрольными точками SafeOps
# =============================================================================

@tool
async def windows_checkpoints_action(
    action: str = "create",
    title: str = "",
    checkpoint_type: str = "PERIODIC",
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Создание и выполнение операций над контрольными точками восстановления SafeOps.

    Args:
        action: Тип операции (например: 'create', 'verify', 'delete').
        title: Понятное название контрольной точки (например: 'Перед обновлением драйверов GPU').
        checkpoint_type: Категория контрольной точки ('BASELINE', 'POST_CONFIG', 'PRE_UPDATE', 'PRE_EXPERIMENT', 'PERIODIC', 'CUSTOM').
        dry_run: Режим симуляции (по умолчанию True для предотвращения внезапных тяжелых бэкапов).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом создания или симуляции контрольной точки.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": action,
                "title": title or "Симуляция контрольной точки",
                "checkpoint_type": checkpoint_type,
                "dry_run": True,
                "message": f"Симуляция создания контрольной точки '{title}' (тип: {checkpoint_type}) прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        try:
            from apps.windows.sdk.modules.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator
            from apps.windows.sdk.modules.system_checkpoints.models import CheckpointCreateRequest, CheckpointType
        except ImportError:
            from apps.windows.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator
            from apps.windows.system_checkpoints.models import CheckpointCreateRequest, CheckpointType

        coord = CheckpointCoordinator()
        loop = asyncio.get_running_loop()

        ctype = CheckpointType.PERIODIC
        try:
            ctype = CheckpointType(checkpoint_type.upper())
        except ValueError:
            pass

        req = CheckpointCreateRequest(
            title=title or "Автоматическая контрольная точка",
            checkpoint_type=ctype,
            description=f"Создано оператором {operator}",
        )
        res = await loop.run_in_executor(None, coord.create_checkpoint, req)
        return json.dumps({
            "status": "ok",
            "action": action,
            "result": _to_serializable(res),
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.system_checkpoints] Ошибка выполнения операции над контрольной точкой: {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_SYSTEM_CHECKPOINTS_TOOLS = [
    windows_checkpoints_audit,
    windows_checkpoints_action,
]
