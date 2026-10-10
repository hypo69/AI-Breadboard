# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Native FFI Tools Module
# =============================================================================
# Description:
#   Нативные инструменты прямого взаимодействия с Win32 C API (apps.windows.sdk.native).
#
# File: native.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:30:00
# =============================================================================

from __future__ import annotations
"""Нативные инструменты прямого взаимодействия с Win32 C API (apps.windows.sdk.native)."""

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


@tool
async def windows_native_event_log_query(
    channel: str = 'System',
    limit: int = 50,
    level: str = '',
    search: str = '',
    event_id: int = 0,
) -> str:
    """Высокоскоростной нативный запрос журналов событий Windows через wevtapi.dll (без внешней утилиты wevtutil).

    Args:
        channel: Имя канала журнала (например, 'System', 'Application', 'Security', 'Microsoft-Windows-Sysmon/Operational').
        limit: Максимальное количество записей (от 1 до 500).
        level: Фильтр уровня ('Critical', 'Error', 'Warning', 'Information').
        search: Подстрока для текстового поиска в сообщении или провайдере.
        event_id: Конкретный идентификатор события (EventID) или 0 для всех.
    """
    try:
        from apps.windows.sdk.native import WindowsEventLogAPI
        wevt = WindowsEventLogAPI()
        if not wevt.is_available():
            return json.dumps({'status': 'error', 'message': 'wevtapi.dll недоступна в текущей среде.'}, ensure_ascii=False)
        
        events = await asyncio.to_thread(
            wevt.read_events,
            channel=channel,
            limit=limit,
            level=level,
            search=search,
            event_id=event_id,
        )
        return json.dumps({'status': 'ok', 'channel': channel, 'total': len(events), 'events': events}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка нативного запроса журналов '{channel}': {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_native_network_sockets(include_arp: bool = True) -> str:
    """Получает активные TCP/UDP сокеты и ARP-таблицу через нативный IP Helper API (iphlpapi.dll) с привязкой к PID.

    Args:
        include_arp: Включать ли таблицу ARP-соседей локальной сети.
    """
    try:
        from apps.windows.sdk.native import IPHelperAPI
        iphlp = IPHelperAPI()
        
        tcp = await asyncio.to_thread(iphlp.get_tcp_connections)
        udp = await asyncio.to_thread(iphlp.get_udp_sockets)
        arp = await asyncio.to_thread(iphlp.get_ip_net_table) if include_arp else []
        adapters = await asyncio.to_thread(iphlp.get_adapter_statistics)
        
        payload = {
            'status': 'ok',
            'tcp_count': len(tcp),
            'udp_count': len(udp),
            'arp_count': len(arp),
            'tcp_connections': [t.to_dict() for t in tcp[:100]],
            'udp_sockets': [u.to_dict() for u in udp[:100]],
            'arp_table': arp,
            'adapters': adapters,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка получения нативных сетевых сокетов: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_native_pnp_devices(only_problems: bool = False) -> str:
    """Инвентаризация PnP-устройств и выявление аппаратных сбоев (коды 10/43/28) через SetupAPI и CfgMgr32.

    Args:
        only_problems: Возвращать только устройства с аппаратными проблемами и ошибками.
    """
    try:
        from apps.windows.sdk.native import SetupAPI
        setup = SetupAPI()
        
        devices = await asyncio.to_thread(setup.get_problem_devices if only_problems else setup.get_all_devices, only_present=True)
        payload = {
            'status': 'ok',
            'only_problems': only_problems,
            'total': len(devices),
            'devices': [d.to_dict() for d in devices],
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка получения PnP устройств: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_native_services_enum(max_services: int = 200, only_running: bool = False) -> str:
    """Пакетное перечисление системных служб Windows через Service Control Manager (advapi32.dll).

    Args:
        max_services: Максимальное количество служб в выдаче.
        only_running: Фильтровать только запущенные службы.
    """
    try:
        from apps.windows.sdk.native import ServiceManagerFFI
        scm = ServiceManagerFFI()
        
        services = await asyncio.to_thread(scm.enum_services)
        if only_running:
            services = [s for s in services if s.state == 'RUNNING']
        
        results = []
        for s in services[:max_services]:
            cfg = scm.get_service_config(s.name) or {}
            d = s.to_dict()
            d.update(cfg)
            results.append(d)
            
        payload = {
            'status': 'ok',
            'total': len(results),
            'services': results,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка нативного перечисления служб: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_native_tasks_enum(max_tasks: int = 100) -> str:
    """Аудит запланированных задач Windows через Task Scheduler 2.0 COM API (Schedule.Service).

    Args:
        max_tasks: Лимит возвращаемых задач.
    """
    try:
        from apps.windows.sdk.native import TaskSchedulerFFI
        ts = TaskSchedulerFFI()
        if not ts.is_available:
            return json.dumps({'status': 'error', 'message': 'COM-интерфейс Task Scheduler недоступен.'}, ensure_ascii=False)
            
        tasks = await asyncio.to_thread(ts.get_all_tasks, max_tasks=max_tasks)
        payload = {
            'status': 'ok',
            'total': len(tasks),
            'tasks': tasks,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка аудита задач планировщика: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_native_error_decode(code: str) -> str:
    """Декодирует системные коды ошибок Win32, HRESULT, NTSTATUS и Stop-коды BSOD (BugCheck).

    Args:
        code: Код ошибки в числовом или шестнадцатеричном виде (например, '5', '0x80070005', '0xC0000005', '0xD1').
    """
    try:
        from apps.windows.sdk.native import WindowsErrorDecoder
        decoder = WindowsErrorDecoder()
        
        uint_code, hex_code = decoder.parse_error_code(code)
        sys_desc = decoder.format_system_error(uint_code)
        bugcheck = decoder.decode_bugcheck_code(uint_code)
        
        payload = {
            'status': 'ok',
            'code_input': code,
            'code_uint32': uint_code,
            'code_hex': hex_code,
            'system_description': sys_desc,
            'bugcheck_info': bugcheck if bugcheck.get('symbol') != 'UNKNOWN_BUGCHECK' or uint_code > 0xFF else None,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка декодирования кода '{code}': {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_native_performance_counters() -> str:
    """Собирает ключевые счетчики производительности Windows в реальном времени через PDH API (pdh.dll)."""
    try:
        from apps.windows.sdk.native import PDHManager
        pdh = PDHManager()
        if not pdh.is_available:
            return json.dumps({'status': 'error', 'message': 'pdh.dll недоступна в текущей среде.'}, ensure_ascii=False)
            
        if not pdh.open_query():
            return json.dumps({'status': 'error', 'message': 'Не удалось инициализировать PDH запрос.'}, ensure_ascii=False)
            
        pdh.add_counter('cpu_total', '\\Processor(_Total)\\% Processor Time')
        pdh.add_counter('mem_committed', '\\Memory\\Committed Bytes')
        
        success = pdh.collect()
        if not success:
            pdh.close()
            return json.dumps({'status': 'error', 'message': 'Не удалось собрать данные PDH счетчиков.'}, ensure_ascii=False)
            
        cpu_val = pdh.get_value('cpu_total')
        mem_val = pdh.get_value('mem_committed')
        pdh.close()
        
        payload = {
            'status': 'ok',
            'cpu_processor_time_percent': cpu_val,
            'memory_committed_bytes': mem_val,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.native] Ошибка сбора PDH счетчиков: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


WINDOWS_NATIVE_FFI_TOOLS = [
    windows_native_event_log_query,
    windows_native_network_sockets,
    windows_native_pnp_devices,
    windows_native_services_enum,
    windows_native_tasks_enum,
    windows_native_error_decode,
    windows_native_performance_counters,
]

__all__ = [
    'windows_native_event_log_query',
    'windows_native_network_sockets',
    'windows_native_pnp_devices',
    'windows_native_services_enum',
    'windows_native_tasks_enum',
    'windows_native_error_decode',
    'windows_native_performance_counters',
    'WINDOWS_NATIVE_FFI_TOOLS',
]
