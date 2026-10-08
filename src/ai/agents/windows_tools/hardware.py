# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Hardware Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой аппаратного мониторинга и диагностики
#   (apps.windows.modules.hardware).
#   Сгруппированы по 3 логическим блокам:
#     1. Телеметрия и мониторинг оборудования в реальном времени (windows_hardware_monitor)
#     2. Аппаратная инвентаризация и S.M.A.R.T. накопителей (windows_hardware_inventory)
#     3. Контролируемые стресс-тесты SafeOps и ИИ-бенчмарки (windows_hardware_benchmark)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.hardware import windows_hardware_monitor
#     res = await windows_hardware_monitor(action="summary")
#
# File: hardware.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:48:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Hardware Diagnostics для ИИ-агентов."""

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
    """Вспомогательное преобразование объектов моделей и dataclass в сериализуемый словарь."""
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
# Блок 1: Телеметрия и мониторинг оборудования в реальном времени
# =============================================================================

@tool
async def windows_hardware_monitor(
    action: str,
    component: str = "all",
) -> str:
    """Телеметрия и мониторинг аппаратных компонентов системы в реальном времени (CPU, RAM, GPU, Storage, Sensors, Network, Battery).

    Args:
        action: Операция мониторинга:
            - 'snapshot': полный моментальный снимок всех компонентов оборудования
            - 'summary': краткая сводка здоровья системы и активных превышений порогов
            - 'component': выборка метрик конкретного компонента (параметр component)
        component: Целевой компонент для 'component': 'cpu', 'memory', 'gpu', 'storage', 'sensors', 'network', 'battery'.

    Returns:
        JSON с метриками телеметрии или сводкой состояния оборудования.
    """
    try:
        from apps.windows.modules.hardware.hardware_monitor import HardwareMonitor

        mon = HardwareMonitor()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()
        comp = component.strip().lower()

        if act == "snapshot":
            res = await loop.run_in_executor(None, mon.get_snapshot)
            return json.dumps({"status": "ok", "action": act, "snapshot": _to_serializable(res)}, ensure_ascii=False)
        elif act == "summary":
            res = await loop.run_in_executor(None, mon.get_summary)
            return json.dumps({"status": "ok", "action": act, "summary": _to_serializable(res)}, ensure_ascii=False)
        elif act == "component":
            if comp == "cpu":
                res = await loop.run_in_executor(None, mon.get_cpu_metrics)
            elif comp in ("memory", "ram"):
                res = await loop.run_in_executor(None, mon.get_memory_metrics)
            elif comp == "gpu":
                res = await loop.run_in_executor(None, mon.get_gpu_metrics)
            elif comp == "storage":
                res = await loop.run_in_executor(None, mon.get_storage_metrics)
            elif comp == "sensors":
                res = await loop.run_in_executor(None, mon.get_sensor_metrics)
            elif comp in ("net", "network"):
                res = await loop.run_in_executor(None, mon.get_network_metrics)
            elif comp == "battery":
                res = await loop.run_in_executor(None, mon.get_battery_metrics)
            else:
                return json.dumps({"status": "error", "message": f"Неизвестный компонент: '{component}'"}, ensure_ascii=False)

            return json.dumps({"status": "ok", "action": act, "component": comp, "metrics": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.hardware] Ошибка выполнения hardware_monitor ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Аппаратная инвентаризация и S.M.A.R.T. накопителей
# =============================================================================

@tool
async def windows_hardware_inventory(
    action: str = "summary",
) -> str:
    """Аппаратное досье и инвентаризация оборудования компьютера, а также S.M.A.R.T. статус дисков.

    Args:
        action: Тип инвентаризации:
            - 'summary': аппаратное досье компьютера (модели CPU/GPU, планки RAM, материнская плата, BIOS)
            - 'smart': состояние здоровья и S.M.A.R.T. параметры дисковых накопителей

    Returns:
        JSON с аппаратными характеристиками оборудования или показаниями S.M.A.R.T.
    """
    try:
        from apps.windows.modules.hardware.hardware_monitor import HardwareMonitor

        mon = HardwareMonitor()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "summary":
            try:
                from apps.windows.modules.hardware.discovery import HardwareDiscovery
                disc = HardwareDiscovery()
                res = await loop.run_in_executor(None, disc.get_full_inventory)
            except Exception:
                res = await loop.run_in_executor(None, mon.get_snapshot)

            return json.dumps({"status": "ok", "action": act, "inventory": _to_serializable(res)}, ensure_ascii=False)
        elif act == "smart":
            storage = await loop.run_in_executor(None, mon.get_storage_metrics)
            smart_data = storage.smart_drives if hasattr(storage, "smart_drives") else []
            return json.dumps({"status": "ok", "action": act, "smart_drives": _to_serializable(smart_data)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.hardware] Ошибка инвентаризации hardware_inventory ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Контролируемые стресс-тесты SafeOps и ИИ-бенчмарки
# =============================================================================

@tool
async def windows_hardware_benchmark(
    action: str,
    target: str = "cpu",
    duration_seconds: int = 10,
    max_safe_temp_c: float = 90.0,
    provider: str = "gemini",
    model_name: str = "gemini-3.1-flash",
    prompt: str = "Тестовый запрос для замера скорости инференса.",
) -> str:
    """Проведение контролируемых стресс-тестов оборудования SafeOps и ИИ-бенчмаркинга.

    Args:
        action: Операция бенчмаркинга:
            - 'stress': стресс-тест CPU или GPU по протоколу SafeOps с автоотключением по температуре max_safe_temp_c
            - 'ai_inference': замер скорости инференса ИИ-модели (TTFT, токены в секунду, время генерации)
            - 'ai_history': история проведенных замеров инференса ИИ
        target: Цель стресс-теста для 'stress': 'cpu' или 'gpu'.
        duration_seconds: Длительность стресс-теста в секундах (по умолчанию 10).
        max_safe_temp_c: Порог аварийной остановки стресс-теста по температуре в °C (по умолчанию 90.0).
        provider: Провайдер ИИ-модели для 'ai_inference' (например, 'gemini', 'ollama', 'openai').
        model_name: Имя модели ИИ (например, 'gemini-3.1-flash').
        prompt: Текст запроса для замера скорости инференса.

    Returns:
        JSON с результатами стресс-теста или метриками скорости ИИ-инференса.
    """
    try:
        from apps.windows.modules.hardware.stress_benchmark import StressBenchmarkEngine

        engine = StressBenchmarkEngine(max_safe_temp_c=max_safe_temp_c)
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "stress":
            t_target = target.strip().lower()
            if t_target == "gpu":
                res = await loop.run_in_executor(None, engine.run_gpu_stress, duration_seconds)
            else:
                res = await loop.run_in_executor(None, engine.run_cpu_stress, duration_seconds)
            return json.dumps({"status": "ok", "action": act, "target": t_target, "result": _to_serializable(res)}, ensure_ascii=False)
        elif act == "ai_inference":
            res = await loop.run_in_executor(
                None, engine.run_ai_inference_benchmark, provider, model_name, prompt
            )
            return json.dumps({"status": "ok", "action": act, "ai_benchmark": _to_serializable(res)}, ensure_ascii=False)
        elif act == "ai_history":
            res = await loop.run_in_executor(None, engine.get_ai_benchmark_history)
            return json.dumps({"status": "ok", "action": act, "history": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.hardware] Ошибка выполнения бенчмарка hardware_benchmark ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_HARDWARE_TOOLS = [
    windows_hardware_monitor,
    windows_hardware_inventory,
    windows_hardware_benchmark,
]
