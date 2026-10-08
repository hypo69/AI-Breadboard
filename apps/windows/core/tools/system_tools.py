# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core Tools - System Tools
# =============================================================================
# Description:
#   Встроенные умные системные инструменты для подсистемы Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.tools.system_tools import WindowsCollectorTool
#
#     service = WindowsCollectorTool()
#
# File: system_tools.py
# Project: ai-breadboard
# Package: apps.windows.core.tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 19:35:00
# =============================================================================

from __future__ import annotations
"""Встроенные умные системные инструменты для подсистемы Windows."""

import asyncio
import json
import platform
import subprocess
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.core.models import RiskLevel
from apps.windows.core.tools.base import BaseTool, ToolExecutionResult
from apps.windows.core.tools.registry import ToolRegistry


class WindowsCollectorTool(BaseTool):
    """Инструмент запуска специализированных доменных коллекторов Windows."""
    name = 'windows_collector'
    title = 'Коллектор аудита Windows'
    description = "Запускает встроенный коллектор аудита Windows. Доступные домены: 'driver' (PnP устройства и драйверы), 'storage' (диски, тома, SMART), 'network' (сетевые адаптеры, открытые порты, сокеты), 'process' (активные процессы, CPU/RAM), 'services' (службы Windows и типы автозапуска), 'tasks' (планировщик Task Scheduler), 'security' (Defender, UAC, автозагрузка Run), 'eventlog' (журналы ошибок System/App), 'performance' (нагрузка и узкие места), 'software' (установленное ПО, UserAssist, Prefetch), 'update' (обновления Windows и установленные KB), 'clean' (временные файлы и кэш), 'integrity' (целостность файлов), 'file_activity' (активность файлов), 'postinstall' (артефакты после установки)."
    parameters_schema = {'type': 'object', 'properties': {'collector_name': {'type': 'string', 'enum': ['driver', 'storage', 'network', 'process', 'services', 'tasks', 'security', 'eventlog', 'performance', 'software', 'update', 'clean', 'integrity', 'file_activity', 'postinstall'], 'description': 'Имя доменного коллектора для запуска'}}, 'required': ['collector_name']}
    risk_level = RiskLevel.SAFE

    def __init__(self) -> None:
        """Инициализация коллекторов."""
        from pathlib import Path
        from apps.windows.core.audits import CleanCollector, DriverCollector, EventLogCollector, FileActivityCollector, IntegrityCollector, NetworkCollector, PerformanceCollector, PostInstallCollector, ProcessCollector, SecurityCollector, ServicesCollector, SoftwareCollector, StorageCollector, TasksCollector, UpdateCollector
        self.collectors: Dict[str, Any] = {
            'driver': DriverCollector(),
            'storage': StorageCollector(),
            'network': NetworkCollector(),
            'process': ProcessCollector(),
            'services': ServicesCollector(),
            'tasks': TasksCollector(),
            'security': SecurityCollector(),
            'eventlog': EventLogCollector(),
            'performance': PerformanceCollector(),
            'software': SoftwareCollector(),
            'clean': CleanCollector(),
            'update': UpdateCollector(),
            'integrity': IntegrityCollector(),
            'file_activity': FileActivityCollector(monitored_paths=[str(Path.cwd() / 'data')]),
            'postinstall': PostInstallCollector(),
        }

    async def execute(self, collector_name: str, **kwargs: Any) -> ToolExecutionResult:
        """Выполнение коллектора на хосте."""
        collector = self.collectors.get(collector_name)
        if not collector:
            return ToolExecutionResult(tool_name=self.name, status='error', data=None, message=f"Неизвестный коллектор: '{collector_name}'")
        try:
            res = await asyncio.to_thread(collector.collect)
            data_dict = res.to_dict() if hasattr(res, 'to_dict') else res
            return ToolExecutionResult(tool_name=self.name, status='ok', data=data_dict, message=f"Коллектор '{collector_name}' успешно собрал телеметрию.", command_executed=f'apps.windows.core.modules.{collector_name}_collector.collect()', metadata={'collector_name': collector_name})
        except Exception as e:
            logger.error(f'[WindowsCollectorTool] Ошибка коллектора {collector_name}: {e}', exc_info=True)
            return ToolExecutionResult(tool_name=self.name, status='error', data=None, message=f'Сбой выполнения коллектора {collector_name}: {e}')

class SafePowerShellProbeTool(BaseTool):
    """Инструмент безопасного выполнения PowerShell зондов с выводом в JSON."""
    name = 'safe_powershell_probe'
    title = 'PowerShell зонд'
    description = 'Выполняет безопасный PowerShell-скрипт чтения конфигурации (read-only WMI/CIM/Get-* запросы) с конвертацией вывода в JSON. Запрещены деструктивные команды модификации.'
    parameters_schema = {'type': 'object', 'properties': {'script': {'type': 'string', 'description': 'PowerShell скрипт (например: Get-PnpDevice | Select-Object Status, FriendlyName | ConvertTo-Json)'}, 'timeout_sec': {'type': 'integer', 'default': 12, 'description': 'Таймаут выполнения в секундах'}}, 'required': ['script']}
    risk_level = RiskLevel.SAFE
    FORBIDDEN_KEYWORDS = ('remove-item', 'rmdir', 'del ', 'format-volume', 'stop-process', 'restart-computer', 'stop-computer', 'set-executionpolicy', 'new-service', 'remove-service')

    async def execute(self, script: str, timeout_sec: int=12, **kwargs: Any) -> ToolExecutionResult:
        """Исполнение безопасного скрипта PowerShell."""
        script_lower = script.lower()
        if any((bad_word in script_lower for bad_word in self.FORBIDDEN_KEYWORDS)):
            return ToolExecutionResult(tool_name=self.name, status='error', data=None, message='Команда отклонена политикой безопасности SafeOps (обнаружены деструктивные инструкции).', command_executed=script, risk_level=RiskLevel.CRITICAL)
        if platform.system() != 'Windows':
            return ToolExecutionResult(tool_name=self.name, status='ok', data={'mock': True, 'message': 'Платформа не является Windows, зонд симулирован.'}, command_executed=script)
        try:
            proc = await asyncio.to_thread(subprocess.run, ['powershell', '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True, text=True, timeout=timeout_sec)
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            if proc.returncode != 0 and (not stdout):
                return ToolExecutionResult(tool_name=self.name, status='error', data={'stderr': stderr}, message=f"PowerShell вернул ошибку: {stderr or 'код ' + str(proc.returncode)}", command_executed=script)
            try:
                parsed_data = json.loads(stdout) if stdout else []
            except json.JSONDecodeError:
                parsed_data = stdout
            return ToolExecutionResult(tool_name=self.name, status='ok', data=parsed_data, message='PowerShell зонд выполнен успешно.', command_executed=script)
        except subprocess.TimeoutExpired:
            return ToolExecutionResult(tool_name=self.name, status='error', data=None, message=f'Превышен таймаут выполнения PowerShell ({timeout_sec} сек).', command_executed=script)
        except Exception as e:
            return ToolExecutionResult(tool_name=self.name, status='error', data=None, message=f'Сбой запуска PowerShell: {e}', command_executed=script)

def register_system_tools(registry: ToolRegistry) -> None:
    """Регистрирует базовые умные инструменты в переданном реестре."""
    registry.register(WindowsCollectorTool())
    registry.register(SafePowerShellProbeTool())