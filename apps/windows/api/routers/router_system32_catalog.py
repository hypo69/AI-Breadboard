# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api - Router System32 Catalog
# =============================================================================
# Description:
#   FastAPI REST API роутер для расширенного каталога возможностей системных инструментов
#   Windows 10/11 (%SystemRoot%\System32), Control Planes, Telemetry Tiers и AI-интерпретатора команд.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_system32_catalog import init_router
#
#     router = init_router()
#
# File: router_system32_catalog.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 15:20:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST API роутер для расширенного каталога системных инструментов Windows (%SystemRoot%\\System32)."""

import asyncio
import platform
import subprocess
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from logger import logger
from apps.windows.sdk.core.system32_catalog import System32Catalog
from apps.windows.sdk.core.system32_models import (
    AccessType,
    ControlPlaneType,
    System32CatalogSummary,
    System32QueryFilter,
    System32Tool,
    SystemToolCategory,
    TelemetryTier,
    ToolDangerLevel,
    ToolPrivilegeLevel,
)
from apps.windows.sdk.core.etw_pipeline import EtwPipelineStatus, EtwTelemetryPipeline


router = APIRouter(prefix='/api/v1/system32', tags=['Windows System32 Capability Catalog'])


def init_router() -> APIRouter:
    """Инициализирует и возвращает APIRouter для каталога System32.

    Returns:
        APIRouter: Экземпляр FastAPI роутера.
    """
    return router


class NaturalLanguageCommandRequest(BaseModel):
    """Запрос на подбор и выполнение команды по естественному языку."""
    prompt: str = Field(..., description="Команда пользователя свободным текстом (например: 'проверь статус trim', 'покажи порты netstat')")
    execute: bool = Field(True, description="Выполнять ли команду или вернуть только разбор")
    confirmed_by_user: bool = Field(False, description="Подтверждение запуска для потенциально опасных операций")


class NaturalLanguageCommandResponse(BaseModel):
    """Результат подбора и выполнения команды."""
    matched_executable: str
    category: str
    category_code: str
    telemetry_tier: str
    danger_level: str
    required_privileges: str
    command_line: str
    explanation: str
    powershell_equivalent: Optional[str] = None
    win32_api_equivalent: Optional[str] = None
    status: str
    executed: bool
    execution_output: str
    execution_time_ms: float


def _decode_bytes(raw: bytes) -> str:
    """Безопасное декодирование вывода консоли Windows."""
    for enc in ('utf-8', 'cp866', 'cp1251', 'latin-1'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def _match_intent_to_command(prompt: str, catalog: System32Catalog) -> tuple[System32Tool, str, str]:
    """Интеллектуальный подбор инструмента и точной команды по пользовательскому тексту."""
    p_lower = prompt.lower().strip()

    # 1. Специфические ключевые намерения
    if any(k in p_lower for k in ('trim', 'трим', 'ssd')):
        tool = catalog.get_tool('fsutil.exe') or catalog.get_all_tools()[0]
        return tool, 'fsutil.exe behavior query DisableDeleteNotify', 'Запрос глобального статуса TRIM для твердотельных накопителей SSD.'

    if any(k in p_lower for k in ('dns', 'днс', 'flushdns', 'кэш dns', 'сбрось dns', 'очисти dns')):
        tool = catalog.get_tool('ipconfig.exe') or catalog.get_all_tools()[0]
        return tool, 'ipconfig.exe /flushdns', 'Очистка локального кэша сопоставителя DNS.'

    if any(k in p_lower for k in ('порт', 'порты', 'соединен', 'netstat', 'tcp', 'udp', 'listening', 'сокет')):
        tool = catalog.get_tool('netstat.exe') or catalog.get_all_tools()[0]
        return tool, 'netstat.exe -ano', 'Отображение всех активных сетевых TCP/UDP соединений и прослушиваемых портов с PID процессов.'

    if any(k in p_lower for k in ('usn', 'журнал нтфс', 'журнал usn', 'файловый журнал')):
        tool = catalog.get_tool('fsutil.exe') or catalog.get_all_tools()[0]
        return tool, 'fsutil.exe usn queryjournal C:', 'Запрос метаданных и диапазона номеров USN Journal тома C:.'

    if any(k in p_lower for k in ('etw', 'трассировк', 'logman', 'сборщик', 'сессии')):
        tool = catalog.get_tool('logman.exe') or catalog.get_all_tools()[0]
        return tool, 'logman.exe query -ets', 'Запрос списка активных сессий трассировки Event Tracing for Windows в реальном времени.'

    if any(k in p_lower for k in ('счетчик', 'производительност', 'typeperf', 'загрузка cpu')):
        tool = catalog.get_tool('typeperf.exe') or catalog.get_all_tools()[0]
        return tool, 'typeperf.exe "\\Processor(_Total)\\% Processor Time" -si 2 -sc 3', 'Снятие серии мгновенных значений загрузки процессора.'

    if any(k in p_lower for k in ('сниффер', 'пакет', 'pktmon', 'трафик')):
        tool = catalog.get_tool('pktmon.exe') or catalog.get_all_tools()[0]
        return tool, 'pktmon.exe counters', 'Опрос системных счетчиков перехвата пакетов Packet Monitor.'

    if any(k in p_lower for k in ('кто я', 'whoami', 'токен', 'права польз', 'sid польз')):
        tool = catalog.get_tool('whoami.exe') or catalog.get_all_tools()[0]
        return tool, 'whoami.exe /all', 'Полный аудит контекста безопасности текущего пользователя (SID, группы, привилегии, UAC).'

    if any(k in p_lower for k in ('аудит', 'auditpol', 'политик')):
        tool = catalog.get_tool('auditpol.exe') or catalog.get_all_tools()[0]
        return tool, 'auditpol.exe /get /category:*', 'Выгрузка всех категорий политик аудита безопасности Windows Security Log.'

    if any(k in p_lower for k in ('процесс', 'памят', 'tasklist', 'запущенные')):
        tool = catalog.get_tool('tasklist.exe') or catalog.get_all_tools()[0]
        return tool, 'tasklist.exe /FO CSV /V', 'Список выполняющихся процессов с подробными атрибутами и памятью.'

    if any(k in p_lower for k in ('служеб', 'служб', 'сервис', 'демон', 'sc query')):
        tool = catalog.get_tool('sc.exe') or catalog.get_all_tools()[0]
        return tool, 'sc.exe query type= service state= all', 'Запрос списка всех системных служб Windows Service Control Manager.'

    if any(k in p_lower for k in ('bitlocker', 'шифрован', 'битлокер')):
        tool = catalog.get_tool('manage-bde.exe') or catalog.get_all_tools()[0]
        return tool, 'manage-bde.exe -status', 'Проверка состояния полнодискового шифрования BitLocker на всех томах.'

    if any(k in p_lower for k in ('диск', 'раздел', 'том', 'диски', 'mountvol')):
        tool = catalog.get_tool('mountvol.exe') or catalog.get_all_tools()[0]
        return tool, 'mountvol.exe', 'Список всех смонтированных томов и соответствующих им GUID.'

    if any(k in p_lower for k in ('часовой пояс', 'время', 'таймзон', 'tzutil')):
        tool = catalog.get_tool('tzutil.exe') or catalog.get_all_tools()[0]
        return tool, 'tzutil.exe /g', 'Получение идентификатора текущего часового пояса системы.'

    if any(k in p_lower for k in ('брандмауэр', 'firewall', 'фаервол')):
        tool = catalog.get_tool('netsh.exe') or catalog.get_all_tools()[0]
        return tool, 'netsh.exe advfirewall show allprofiles', 'Отображение состояния всех профилей Брандмауэра Защитника Windows.'

    if any(k in p_lower for k in ('вайфай', 'wifi', 'wi-fi', 'wlan')):
        tool = catalog.get_tool('netsh.exe') or catalog.get_all_tools()[0]
        return tool, 'netsh.exe wlan show interfaces', 'Инспекция активных беспроводных Wi-Fi адаптеров и статуса подключения.'

    if any(k in p_lower for k in ('система', 'информация', 'systeminfo', 'сборка', 'биос', 'bios')):
        tool = catalog.get_tool('systeminfo.exe') or catalog.get_all_tools()[0]
        return tool, 'systeminfo.exe /FO CSV', 'Полная сводка о конфигурации системы, процессоре, памяти и хотфиксах.'

    # 2. Поиск по общему каталогу
    search_matches = catalog.filter_tools(System32QueryFilter(search_query=prompt))
    if search_matches:
        tool = search_matches[0]
        cmd = tool.command_templates[0] if tool.command_templates else tool.executable
        return tool, cmd, tool.purpose

    # Fallback на tasklist
    default_tool = catalog.get_tool('tasklist.exe') or catalog.get_all_tools()[0]
    return default_tool, 'tasklist.exe /FO CSV', 'Список запущенных процессов (по умолчанию).'


@router.post('/interpret-and-run', response_model=NaturalLanguageCommandResponse)
async def interpret_and_run_command(req: NaturalLanguageCommandRequest) -> NaturalLanguageCommandResponse:
    """Анализ свободного текста пользователя, подбор утилиты System32 и безопасное исполнение."""
    catalog = System32Catalog.get_instance()
    t_start = time.perf_counter()

    tool, cmd_line, explanation = _match_intent_to_command(req.prompt, catalog)

    is_dangerous = tool.danger_level in (ToolDangerLevel.HIGH, ToolDangerLevel.CRITICAL) or tool.telemetry_tier == TelemetryTier.DESTRUCTIVE
    is_admin = tool.required_privileges in (ToolPrivilegeLevel.ADMINISTRATOR, ToolPrivilegeLevel.SYSTEM)

    # Если требуется подтверждение
    if req.execute and is_dangerous and not req.confirmed_by_user:
        return NaturalLanguageCommandResponse(
            matched_executable=tool.executable,
            category=tool.category.value,
            category_code=tool.category_code,
            telemetry_tier=tool.telemetry_tier.value,
            danger_level=tool.danger_level.value,
            required_privileges=tool.required_privileges.value,
            command_line=cmd_line,
            explanation=f"⚠️ {explanation} Операция имеет уровень риска {tool.danger_level.value} и требует подтверждения пользователя.",
            powershell_equivalent=tool.powershell_equivalent,
            win32_api_equivalent=tool.native_api_equivalent,
            status='requires_confirmation',
            executed=False,
            execution_output='[SafeOps Guard] Запуск отложен. Требуется явное подтверждение пользователя (confirmed_by_user=True).',
            execution_time_ms=round((time.perf_counter() - t_start) * 1000, 2)
        )

    # Режим симуляции (dry_run)
    if not req.execute:
        return NaturalLanguageCommandResponse(
            matched_executable=tool.executable,
            category=tool.category.value,
            category_code=tool.category_code,
            telemetry_tier=tool.telemetry_tier.value,
            danger_level=tool.danger_level.value,
            required_privileges=tool.required_privileges.value,
            command_line=cmd_line,
            explanation=explanation,
            powershell_equivalent=tool.powershell_equivalent,
            win32_api_equivalent=tool.native_api_equivalent,
            status='dry_run',
            executed=False,
            execution_output=f'[Dry-Run] Команда подобрана: {cmd_line}',
            execution_time_ms=round((time.perf_counter() - t_start) * 1000, 2)
        )

    # Реальное выполнение команды на Windows
    is_win = platform.system().lower() == 'windows'
    out_text = ''
    status_str = 'success'

    if is_win:
        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd_line,
                    shell=True,
                    capture_output=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            )
            stdout_str = _decode_bytes(res.stdout or b'')
            stderr_str = _decode_bytes(res.stderr or b'')

            if res.returncode != 0 and stderr_str:
                out_text = f"Status: Error (Exit Code: {res.returncode})\n{stderr_str}\n{stdout_str}"
                status_str = 'warn'
            else:
                out_text = stdout_str if stdout_str else (stderr_str or 'Команда выполнена успешно (вывод пуст).')
        except subprocess.TimeoutExpired:
            out_text = f'Таймаут выполнения команды ({cmd_line}) превысил 15 секунд.'
            status_str = 'timeout'
        except Exception as ex:
            out_text = f'Сбой выполнения команды ({cmd_line}): {ex}'
            status_str = 'error'
    else:
        out_text = f'[Simulated Host] Команда {cmd_line} сымитирована на платформе {platform.system()}.'

    t_dur = round((time.perf_counter() - t_start) * 1000, 2)
    return NaturalLanguageCommandResponse(
        matched_executable=tool.executable,
        category=tool.category.value,
        category_code=tool.category_code,
        telemetry_tier=tool.telemetry_tier.value,
        danger_level=tool.danger_level.value,
        required_privileges=tool.required_privileges.value,
        command_line=cmd_line,
        explanation=explanation,
        powershell_equivalent=tool.powershell_equivalent,
        win32_api_equivalent=tool.native_api_equivalent,
        status=status_str,
        executed=True,
        execution_output=out_text,
        execution_time_ms=t_dur
    )


@router.get('/catalog')
async def get_system32_catalog(
    category: Optional[SystemToolCategory] = Query(None, description='Фильтр по системной категории'),
    access_type: Optional[AccessType] = Query(None, description='Тип доступа (READ, WRITE, READ_WRITE)'),
    required_privileges: Optional[ToolPrivilegeLevel] = Query(None, description='Требуемые системные привилегии'),
    danger_level: Optional[ToolDangerLevel] = Query(None, description='Уровень риска'),
    telemetry_tier: Optional[TelemetryTier] = Query(None, description='Уровень AITelemetry Tier'),
    primary_control_plane: Optional[ControlPlaneType] = Query(None, description='Слой Control Plane'),
    can_run_unattended: Optional[bool] = Query(None, description='Фоновое выполнение'),
    can_monitor: Optional[bool] = Query(None, description='Пригодность для мониторинга'),
    can_modify_system: Optional[bool] = Query(None, description='Модификация состояния системы'),
    etw_pipeline_enabled: Optional[bool] = Query(None, description='Интеграция в ETW конвейер'),
    usn_journal_enabled: Optional[bool] = Query(None, description='Работает с NTFS USN Journal'),
    is_cmd_builtin: Optional[bool] = Query(None, description='Встроенные команды CMD'),
    query: Optional[str] = Query(None, description='Поисковая строка')
) -> Dict[str, Any]:
    """Возвращает каталог инструментов System32 с многопараметрической фильтрацией и поиском."""
    catalog = System32Catalog.get_instance()
    q_filter = System32QueryFilter(
        category=category,
        access_type=access_type,
        required_privileges=required_privileges,
        danger_level=danger_level,
        telemetry_tier=telemetry_tier,
        primary_control_plane=primary_control_plane,
        can_run_unattended=can_run_unattended,
        can_monitor=can_monitor,
        can_modify_system=can_modify_system,
        etw_pipeline_enabled=etw_pipeline_enabled,
        usn_journal_enabled=usn_journal_enabled,
        is_cmd_builtin=is_cmd_builtin,
        search_query=query,
    )
    tools = catalog.filter_tools(q_filter)
    return {
        'total': len(tools),
        'tools': [t.to_dict() for t in tools]
    }


@router.get('/categories')
async def get_system32_categories() -> Dict[str, Any]:
    """Возвращает список всех зарегистрированных категорий со счетчиками инструментов."""
    catalog = System32Catalog.get_instance()
    res = []
    for cat in SystemToolCategory:
        tools = catalog.get_tools_by_category(cat)
        if tools:
            res.append({
                'category_id': cat.value,
                'name': cat.name,
                'category_code': tools[0].category_code if tools else cat.value,
                'tools_count': len(tools),
                'executables': [t.executable for t in tools]
            })
    return {'categories': res, 'total_categories': len(res)}


@router.get('/tiers')
async def get_system32_tiers() -> Dict[str, Any]:
    """Группировка каталога по градации AITelemetry Tiers (OBSERVE, DIAGNOSE, CONTROL, ADMIN, DESTRUCTIVE, RECOVERY)."""
    catalog = System32Catalog.get_instance()
    return catalog.get_tiers_tree()


@router.get('/control-planes')
async def get_system32_control_planes() -> Dict[str, Any]:
    """Группировка каталога по слоям Windows Control Plane (CLI, PS, WMI/CIM, COM, Win32, ETW, Event Log, Registry, GUI/MMC)."""
    catalog = System32Catalog.get_instance()
    return catalog.get_control_planes_tree()


@router.get('/tree')
async def get_system32_tree() -> Dict[str, Any]:
    """Иерархическое дерево возможностей («Категория -> Инструменты -> Свойства/Команды»)."""
    catalog = System32Catalog.get_instance()
    return catalog.get_hierarchy_tree()


@router.get('/tool/{executable}')
async def get_tool_details(executable: str) -> Dict[str, Any]:
    """Возвращает полную карточку инструмента с эквивалентами Control Plane, подкомандами и шаблонами."""
    catalog = System32Catalog.get_instance()
    tool = catalog.get_tool(executable)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Инструмент '{executable}' не найден в каталоге.")

    avail = catalog.check_availability(executable)
    data = tool.to_dict()
    data['host_availability'] = avail
    return data


@router.get('/subcommands/{executable}')
async def get_tool_subcommands(executable: str) -> Dict[str, Any]:
    """Возвращает детальное дерево подкоманд и операций утилиты (diskpart, fsutil, netsh, vssadmin, pktmon и др.)."""
    catalog = System32Catalog.get_instance()
    tool = catalog.get_tool(executable)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Инструмент '{executable}' не найден в каталоге.")

    return {
        'executable': tool.executable,
        'category': tool.category.value,
        'subcommands_info': tool.subcommands_info,
        'subcommands_tree': tool.subcommands_tree,
        'command_templates': tool.command_templates,
    }


@router.get('/usn-journal')
async def get_usn_journal_tools() -> Dict[str, Any]:
    """Инструменты и операции для работы с NTFS USN Journal (fsutil usn queryjournal/createjournal/readjournal)."""
    catalog = System32Catalog.get_instance()
    tools = catalog.get_usn_tools()
    return {
        'total': len(tools),
        'tools': [t.to_dict() for t in tools],
        'description': 'NTFS USN Journal позволяет строить наблюдение за изменениями файловой системы без постоянного полного сканирования диска.'
    }


@router.get('/inventory')
async def get_system32_inventory() -> Dict[str, Any]:
    """Сверка каталога с реальным наличием файлов в %SystemRoot%\\System32 текущей системы."""
    catalog = System32Catalog.get_instance()
    return catalog.get_system_inventory()


@router.get('/etw-pipeline', response_model=EtwPipelineStatus)
async def get_etw_pipeline_status() -> EtwPipelineStatus:
    """Статус конвейера телеметрии ETW / Performance Counters и список активных сессий."""
    pipeline = EtwTelemetryPipeline.get_instance()
    return await pipeline.get_pipeline_status()


@router.get('/summary', response_model=System32CatalogSummary)
async def get_system32_summary() -> System32CatalogSummary:
    """Сводная статистика каталога инструментов System32."""
    catalog = System32Catalog.get_instance()
    return catalog.get_summary()


__all__ = [
    'router',
    'init_router',
    'NaturalLanguageCommandRequest',
    'NaturalLanguageCommandResponse',
]
