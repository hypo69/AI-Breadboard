# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Network Terminal Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой сетевой диагностики и сканирования LAN
#   (apps.windows.sdk.modules.network).
#   Сгруппированы по 3 логическим блокам:
#     1. Обнаружение и сканирование устройств в локальной сети (windows_network_scan_lan)
#     2. Мониторинг сетевого трафика адаптеров и процессов (windows_network_usage_stats)
#     3. Измерение скорости, задержки и качества соединения Speedtest (windows_network_speedtest)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.network import windows_network_scan_lan
#     res = await windows_network_scan_lan(action="devices")
#
# File: network.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:52:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Network Terminal для ИИ-агентов."""

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
# Блок 1: Обнаружение и сканирование устройств в локальной сети
# =============================================================================

@tool
async def windows_network_scan_lan(
    action: str = "devices",
    subnet_cidr: Optional[str] = None,
    full_scan: bool = False,
    include_ssdp: bool = True,
) -> str:
    """Обнаружение хостов, смарт-устройств и сканирование локальной сети (LAN Device Discovery).

    Args:
        action: Операция сканирования LAN:
            - 'devices': получение списка известных и активных устройств в локальной сети
            - 'scan': запуск активного ARP-свипа и SSDP поиска устройств
            - 'subnets': список активных локальных IPv4 подсетей и шлюзов по умолчанию
        subnet_cidr: Маска подсети в формате CIDR (например, '192.168.1.0/24'). Если None — используется локальная сеть.
        full_scan: Флаг активного зондирования всех IP в диапазоне подсети через SendARP (по умолчанию False).
        include_ssdp: Поиск смарт-устройств (Smart TV, роутеры, медиасерверы) через SSDP/UPnP (по умолчанию True).

    Returns:
        JSON со списком обнаруженных устройств (IP, MAC, Hostname, Vendor, State) или подсетей.
    """
    try:
        from apps.windows.sdk.modules.network.lan_scanner import WindowsLanScanner

        scanner = WindowsLanScanner()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act in ("devices", "scan"):
            is_full = full_scan or (act == "scan")
            res = await loop.run_in_executor(
                None, scanner.discover_devices, is_full, subnet_cidr, include_ssdp
            )
            return json.dumps({"status": "ok", "action": act, "total": len(res), "devices": _to_serializable(res)}, ensure_ascii=False)
        elif act == "subnets":
            subnets = await loop.run_in_executor(None, scanner.get_local_subnets)
            gateways = await loop.run_in_executor(None, scanner.get_default_gateways)
            return json.dumps({"status": "ok", "action": act, "subnets": subnets, "default_gateways": gateways}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.network] Ошибка сканирования сети network_scan_lan ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Мониторинг сетевого трафика адаптеров и процессов
# =============================================================================

@tool
async def windows_network_usage_stats(
    action: str = "adapters",
) -> str:
    """Статистика использования сетевого трафика адаптеров и сетевая активность процессов Windows.

    Args:
        action: Вид статистики:
            - 'adapters': накопительная статистика сетевых адаптеров (ReceivedBytes, SentBytes, ошибки)
            - 'process_usage': потребление сетевого трафика процессами системы

    Returns:
        JSON со статистикой сетевых адаптеров или трафиком процессов.
    """
    try:
        from apps.windows.sdk.modules.network.network_usage import WindowsNetworkUsageCollector

        collector = WindowsNetworkUsageCollector()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "adapters":
            res = await loop.run_in_executor(None, collector.get_adapter_statistics)
            return json.dumps({"status": "ok", "action": act, "adapters": _to_serializable(res)}, ensure_ascii=False)
        elif act == "process_usage":
            res = await loop.run_in_executor(None, collector.get_app_network_usage)
            return json.dumps({"status": "ok", "action": act, "processes": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.network] Ошибка получения статистики network_usage_stats ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Измерение скорости и качества соединения (Speedtest)
# =============================================================================

@tool
async def windows_network_speedtest(
    duration_seconds: int = 5,
) -> str:
    """Измерение входящей/исходящей скорости (Download/Upload Mbps), задержки latency и оценки Bufferbloat через CDN Fast.com.

    Args:
        duration_seconds: Длительность фазы замера в секундах (по умолчанию 5).

    Returns:
        JSON с результатами замера скорости (Mbps, latency_ms, bufferbloat_grade, rating).
    """
    try:
        from apps.windows.sdk.modules.network.speedtest import NetworkSpeedTester

        tester = NetworkSpeedTester(duration_s=float(duration_seconds))
        res = await tester.run_full_speedtest()
        return json.dumps({"status": "ok", "speedtest": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.network] Ошибка замера скорости network_speedtest: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


WINDOWS_NETWORK_TOOLS = [
    windows_network_scan_lan,
    windows_network_usage_stats,
    windows_network_speedtest,
]
