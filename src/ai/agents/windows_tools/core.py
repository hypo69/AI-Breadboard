# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Core Tools Module
# =============================================================================
# Description:
#   Базовые инструменты взаимодействия с подсистемой Windows OS (аудит, процессы, службы, PowerShell).
#
# File: core.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 20:25:00
# =============================================================================

from __future__ import annotations
"""Базовые инструменты взаимодействия с подсистемой Windows OS."""

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
async def windows_collector_audit(collector_name: str) -> str:
    """Запускает доменный коллектор аудита Windows для сбора глубокой телеметрии.

    Args:
        collector_name: Домен телеметрии. Доступные значения:
            - 'driver': PnP устройства, драйверы и ошибки оборудования
            - 'storage': физические диски, тома, SMART, свободное место
            - 'network': сетевые адаптеры, активные IP-адреса, открытые порты, сокеты
            - 'process': активные процессы, потребление CPU и памяти
            - 'services': системные службы Windows и типы автозапуска
            - 'tasks': задания планировщика Windows Task Scheduler
            - 'security': статус Windows Defender, UAC, автозагрузка Run
            - 'eventlog': критические события и ошибки из журналов System и Application
            - 'performance': общая нагрузка на систему и выявление узких мест
            - 'software': установленное ПО, UserAssist, Prefetch
            - 'update': установленные обновления KB и статус Windows Update
            - 'clean': объем временных файлов, кэша и возможности очистки
            - 'integrity': целостность системных файлов и компонентов (SFC/DISM)
    """
    try:
        from apps.windows.core.tools.system_tools import WindowsCollectorTool
        collector_tool = WindowsCollectorTool()
        result = await collector_tool.execute(collector_name=collector_name)
        payload = {
            'status': result.status,
            'collector': collector_name,
            'message': result.message,
            'data': result.data,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка выполнения коллектора '{collector_name}': {e}", exc_info=True)
        return json.dumps({'status': 'error', 'collector': collector_name, 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_execute_atomic_op(
    operation_id: str,
    params: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
) -> str:
    """Выполняет проверенную атомарную операцию Windows из каталога возможностей.

    Args:
        operation_id: Идентификатор атомарной операции (например,
            'diskpart.disk.list', 'diskpart.partition.list', 'sc.service.query',
            'netsh.advfirewall.show_all', 'netsh.interface.show_ip',
            'wevtutil.log.query', 'dism.image.checkhealth', 'sfc.scan.now',
            'bcdedit.enum.all', 'reg.query', 'icacls.grant', 'schtasks.query').
        params: Словарь параметров операции (например, {'disk_id': 0} или {'service_name': 'wuauserv'}).
        dry_run: Если True, возвращает предварительный просмотр формируемой команды без ее реального выполнения.
    """
    try:
        from apps.windows.core.atomic_capabilities import get_atomic_registry
        from apps.windows.core.atomic_models import AtomicOperationExecutionRequest

        registry = get_atomic_registry()
        req = AtomicOperationExecutionRequest(
            operation_id=operation_id,
            parameters=params or {},
            dry_run=dry_run,
        )
        res = await registry.execute_operation(req)
        payload = {
            'status': res.status,
            'operation_id': res.operation_id,
            'utility': res.utility,
            'risk_level': res.risk_level,
            'required_privilege': res.required_privilege,
            'is_dry_run': res.is_dry_run,
            'command_executed': res.command_executed,
            'message': res.message,
            'data': res.data,
            'execution_time_ms': res.execution_time_ms,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка выполнения атомарной операции '{operation_id}': {e}", exc_info=True)
        return json.dumps({'status': 'error', 'operation_id': operation_id, 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_manage_service(service_name: str, action: str = 'status') -> str:
    """Управляет состоянием службы Windows (получение статуса, запуск, остановка, перезапуск).

    Args:
        service_name: Имя системной службы (например, 'wuauserv', 'WinDefend', 'Spooler', 'EventLog').
        action: Действие со службой: 'status' (проверить статус), 'start' (запустить), 'stop' (остановить), 'restart' (перезапустить).
    """
    try:
        from apps.windows.modules.services_manager.core.manager import ServicesManager
        from apps.windows.modules.services_manager.core.models import ServiceActionRequest

        manager = ServicesManager()
        normalized_action = action.strip().lower()

        if normalized_action in ('status', 'info', 'query'):
            services = await asyncio.to_thread(manager.list_services)
            target = next((s for s in services if s.name.lower() == service_name.lower()), None)
            if target:
                return json.dumps({
                    'status': 'ok',
                    'service': {
                        'name': target.name,
                        'display_name': target.display_name,
                        'status': target.status,
                        'start_type': target.start_type,
                        'pid': target.pid,
                        'binary_path': target.binary_path,
                        'account': target.account,
                    }
                }, ensure_ascii=False)
            return json.dumps({'status': 'not_found', 'message': f"Служба '{service_name}' не найдена."}, ensure_ascii=False)

        req = ServiceActionRequest(
            name=service_name,
            action=normalized_action,
            confirmed_by_user=True,
            dry_run=False,
        )
        res = await manager.execute_service_action(req)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка управления службой '{service_name}': {e}", exc_info=True)
        return json.dumps({'status': 'error', 'service': service_name, 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_manage_process(action: str = 'list', pid: Optional[int] = None, name: Optional[str] = None) -> str:
    """Управляет процессами операционной системы (просмотр списка, поиск, завершение процесса).

    Args:
        action: Действие с процессом: 'list' (список активных процессов), 'inspect' (детальная информация по PID), 'terminate' (завершить процесс).
        pid: Идентификатор процесса (Process ID).
        name: Опциональный фильтр по имени процесса при поиске.
    """
    try:
        import psutil
        normalized_action = action.strip().lower()

        if normalized_action == 'list':
            processes: List[Dict[str, Any]] = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = p.info
                    if name and name.lower() not in (info.get('name') or '').lower():
                        continue
                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            processes.sort(key=lambda x: x.get('memory_percent') or 0.0, reverse=True)
            return json.dumps({'status': 'ok', 'total': len(processes), 'processes': processes[:30]}, ensure_ascii=False)

        if normalized_action == 'inspect':
            if not pid:
                return json.dumps({'status': 'error', 'message': 'Требуется указать pid для действия inspect.'}, ensure_ascii=False)
            proc = psutil.Process(pid)
            data = proc.as_dict(attrs=['pid', 'name', 'exe', 'cmdline', 'num_threads', 'cpu_percent', 'memory_info', 'create_time', 'status'])
            return json.dumps({'status': 'ok', 'process': data}, ensure_ascii=False)

        if normalized_action == 'terminate':
            if not pid:
                return json.dumps({'status': 'error', 'message': 'Требуется указать pid для завершения процесса.'}, ensure_ascii=False)
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc.terminate()
            return json.dumps({'status': 'ok', 'message': f"Процесс '{proc_name}' (PID {pid}) успешно завершен."}, ensure_ascii=False)

        return json.dumps({'status': 'error', 'message': f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка управления процессами ({action}): {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_manage_restore_point(action: str = 'list', description: str = 'AI-Breadboard Checkpoint', sequence_number: Optional[int] = None) -> str:
    """Управляет точками восстановления Windows (System Restore).

    Args:
        action: Действие: 'list' (список существующих точек), 'status' (проверка защиты диска C:), 'create' (создать новую точку), 'delete' (удалить точку по sequence_number).
        description: Описание создаваемой точки восстановления.
        sequence_number: Номер точки восстановления для удаления или отката.
    """
    try:
        from apps.windows.core.system_restore import WindowsSystemRestoreManager
        manager = WindowsSystemRestoreManager()
        normalized_action = action.strip().lower()

        if normalized_action == 'status':
            status = await asyncio.to_thread(manager.check_protection_status)
            return json.dumps(status, ensure_ascii=False)

        if normalized_action == 'list':
            points = await asyncio.to_thread(manager.list_restore_points)
            return json.dumps({'status': 'ok', 'restore_points': points}, ensure_ascii=False)

        if normalized_action == 'create':
            res = await asyncio.to_thread(manager.create_restore_point, description=description)
            return json.dumps(res, ensure_ascii=False)

        if normalized_action == 'delete':
            if sequence_number is None:
                return json.dumps({'status': 'error', 'message': 'Требуется sequence_number для удаления точки.'}, ensure_ascii=False)
            res = await asyncio.to_thread(manager.delete_restore_point, sequence_number=sequence_number)
            return json.dumps(res, ensure_ascii=False)

        return json.dumps({'status': 'error', 'message': f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка управления точками восстановления ({action}): {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_manage_sys_param(action: str = 'list', param_id: Optional[str] = None, value: Any = None, create_restore_point: bool = True) -> str:
    """Безопасно управляет параметрами операционной системы по протоколу SafeOps.

    Args:
        action: Действие: 'list' (список параметров), 'preview' (симуляция изменения / dry-run), 'apply' (применить изменение), 'history' (журнал изменений).
        param_id: Идентификатор системного параметра.
        value: Новое устанавливаемое значение параметра.
        create_restore_point: Создавать ли автоматическую контрольную точку восстановления перед модификацией.
    """
    try:
        from apps.windows.core.system_param_manager import SafeSystemParamManager
        manager = SafeSystemParamManager()
        normalized_action = action.strip().lower()

        if normalized_action == 'list':
            catalog = await asyncio.to_thread(manager.list_parameters)
            return json.dumps({'status': 'ok', 'parameters': catalog}, ensure_ascii=False)

        if normalized_action == 'preview':
            if not param_id:
                return json.dumps({'status': 'error', 'message': 'Требуется param_id для preview.'}, ensure_ascii=False)
            res = await asyncio.to_thread(manager.preview_change, param_id, value)
            return json.dumps(res, ensure_ascii=False)

        if normalized_action == 'apply':
            if not param_id:
                return json.dumps({'status': 'error', 'message': 'Требуется param_id для apply.'}, ensure_ascii=False)
            res = await asyncio.to_thread(manager.apply_change, param_id, value, create_restore_point=create_restore_point)
            return json.dumps(res, ensure_ascii=False)

        if normalized_action == 'history':
            history = await asyncio.to_thread(manager.get_history)
            return json.dumps({'status': 'ok', 'history': history}, ensure_ascii=False)

        return json.dumps({'status': 'error', 'message': f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка управления параметрами системы ({action}): {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_safe_probe(script: str, timeout_sec: int = 15) -> str:
    """Безопасно выполняет PowerShell/CIM/WMI диагностический зонд с конвертацией вывода в JSON.

    Args:
        script: PowerShell-скрипт чтения параметров.
        timeout_sec: Таймаут выполнения в секундах.
    """
    try:
        from apps.windows.core.tools.system_tools import SafePowerShellProbeTool
        probe = SafePowerShellProbeTool()
        result = await probe.execute(script=script, timeout_sec=timeout_sec)
        payload = {
            'status': result.status,
            'message': result.message,
            'data': result.data,
            'command': result.command_executed,
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка выполнения PowerShell зонда: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_execute_powershell(
    script: str,
    timeout_sec: int = 30,
    as_json: bool = False,
    dry_run: bool = False,
) -> str:
    """Выполняет команду или скрипт PowerShell для расширенного управления Windows.

    Args:
        script: Текст скрипта или команды PowerShell.
        timeout_sec: Максимальное время выполнения в секундах.
        as_json: Парсить ли результат как JSON.
        dry_run: Симуляция выполнения.
    """
    import platform
    import subprocess
    import time

    if dry_run:
        return json.dumps({
            'status': 'DRY_RUN_SIMULATED',
            'is_dry_run': True,
            'script': script,
            'message': 'Симуляция PowerShell команды выполнена.',
        }, ensure_ascii=False)

    critical_blacklist = ('format-volume -force', 'format c:', 'diskpart /s clean', 'rmdir -recurse c:\\windows')
    script_lower = script.lower()
    if any(b in script_lower for b in critical_blacklist):
        return json.dumps({
            'status': 'error',
            'risk_level': 'CRITICAL',
            'message': 'Команда заблокирована SafeOps политикой безопасности.',
            'script': script,
        }, ensure_ascii=False)

    if platform.system() != 'Windows':
        return json.dumps({
            'status': 'ok',
            'mock': True,
            'script': script,
            'stdout': 'Симуляция: платформа не является Windows.',
            'stderr': '',
            'returncode': 0,
        }, ensure_ascii=False)

    start_t = time.perf_counter()
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', script],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        returncode = proc.returncode

        parsed_data = None
        if as_json and stdout:
            try:
                parsed_data = json.loads(stdout)
            except json.JSONDecodeError:
                parsed_data = None

        payload = {
            'status': 'ok' if returncode == 0 else 'error',
            'returncode': returncode,
            'stdout': stdout,
            'stderr': stderr,
            'data': parsed_data if parsed_data is not None else stdout,
            'execution_time_ms': duration_ms,
            'script': script,
        }
        return json.dumps(payload, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
        logger.error(f"[windows_tools.core] Превышен таймаут выполнения PowerShell ({timeout_sec}с)")
        return json.dumps({
            'status': 'error',
            'message': f'Превышен таймаут выполнения PowerShell ({timeout_sec}с)',
            'execution_time_ms': duration_ms,
            'script': script,
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка выполнения PowerShell: {e}", exc_info=True)
        return json.dumps({'status': 'error', 'error': str(e), 'script': script}, ensure_ascii=False)


@tool
async def windows_manage_optional_feature(
    action: str,
    feature_name: Optional[str] = None,
    include_all: bool = True,
) -> str:
    """Управление опциональными компонентами Windows (Windows Optional Features / DISM).

    Использует функции подсистемы apps.windows.features для аудита, включения и отключения компонентов ОС.

    Args:
        action: Действие для выполнения:
            - 'list': получение списка всех доступных optional features с их состоянием (Enabled/Disabled)
            - 'enable': включение указанного компонента feature_name
            - 'disable': отключение указанного компонента feature_name
        feature_name: Имя компонента (обязательно для 'enable' и 'disable', например 'Microsoft-Hyper-V', 'VirtualMachinePlatform', 'TelnetClient').
        include_all: Если True (по умолчанию), при включении компонента также устанавливаются его зависимости (-All).
    """
    try:
        from apps.windows.features.manager import (
            get_windows_features,
            enable_windows_feature,
            disable_windows_feature,
        )

        act = action.strip().lower()
        if act in ('list', 'get'):
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, get_windows_features)
            return json.dumps({'status': 'ok', 'action': 'list', 'features': data}, ensure_ascii=False)
        elif act in ('enable', 'install'):
            if not feature_name:
                return json.dumps({'status': 'error', 'message': "Имя компонента 'feature_name' обязательно для действия 'enable'"}, ensure_ascii=False)
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, enable_windows_feature, feature_name, include_all)
            return json.dumps({'status': 'ok', 'action': 'enable', 'feature': data}, ensure_ascii=False)
        elif act in ('disable', 'remove'):
            if not feature_name:
                return json.dumps({'status': 'error', 'message': "Имя компонента 'feature_name' обязательно для действия 'disable'"}, ensure_ascii=False)
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, disable_windows_feature, feature_name)
            return json.dumps({'status': 'ok', 'action': 'disable', 'feature': data}, ensure_ascii=False)
        else:
            return json.dumps({'status': 'error', 'message': f"Неизвестное действие: '{action}'. Допустимые: 'list', 'enable', 'disable'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка работы с optional features ('{action}', '{feature_name}'): {e}", exc_info=True)
        return json.dumps({'status': 'error', 'action': action, 'error': str(e)}, ensure_ascii=False)


@tool
async def windows_manage_accounts_identity(
    action: str,
    target: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """Управление учетными записями, группами, сессиями, правами LSA, токенами и аудитом Windows Identity.

    Использует центральный сервис подсистемы apps.windows.modules.accounts_identity.

    Args:
        action: Выполняемая операция:
            - 'whoami': получить токен и контекст безопасности текущего пользователя
            - 'list_users': получить список всех локальных пользователей системы
            - 'get_user': подробная информация о пользователе по имени или SID (target)
            - 'list_groups': список локальных групп
            - 'get_group': детали о группе (target)
            - 'who_is_admin': список всех аккаунтов с правами администратора
            - 'who_can_rdp': список пользователей с правом входа через RDP
            - 'who_can_logon_as_service': список пользователей с правом запуска служб (SeServiceLogonRight)
            - 'list_sessions': список активных сессий входа в систему
            - 'list_profiles': список профилей пользователей на диске
            - 'find_orphaned': поиск осиротевших SID и неиспользуемых профилей
            - 'get_domain_info': данные о домене и Entra ID
            - 'get_audit_events': история событий безопасности и аудита входа
            - 'create_user': создание пользователя (target - имя, params: {'password': '...', 'full_name': '...'})
            - 'delete_user': удаление пользователя (target - имя)
            - 'add_to_group': добавление пользователя в группу (target - имя группы, params: {'username': '...'})
            - 'remove_from_group': удаление из группы (target - имя группы, params: {'username': '...'})
            - 'resolve': разрешение SID или имени в объект безопасности (target)
            - 'explain_pid': анализ безопасности токена процесса PID (target - PID)
        target: Опциональный целевой идентификатор (имя пользователя, имя группы, SID или PID процесса).
        params: Опциональный словарь дополнительных параметров (пароль, имя, лимит).
    """
    try:
        from apps.windows.modules.accounts_identity.service import get_accounts_identity_service

        service = get_accounts_identity_service()
        act = action.strip().lower()
        p = params or {}

        def _to_serializable(obj: Any) -> Any:
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            if hasattr(obj, "dict"):
                return obj.dict()
            if hasattr(obj, "__dict__"):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            if isinstance(obj, list):
                return [_to_serializable(item) for item in obj]
            return str(obj)

        loop = asyncio.get_running_loop()

        if act == "whoami":
            res = await loop.run_in_executor(None, service.get_current_identity)
            return json.dumps({"status": "ok", "action": act, "identity": _to_serializable(res)}, ensure_ascii=False)
        elif act == "list_users":
            res = await loop.run_in_executor(None, service.list_users)
            return json.dumps({"status": "ok", "action": act, "users": _to_serializable(res)}, ensure_ascii=False)
        elif act == "get_user":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя или SID) обязателен"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, service.get_user, target)
            return json.dumps({"status": "ok", "action": act, "user": _to_serializable(res)}, ensure_ascii=False)
        elif act == "list_groups":
            res = await loop.run_in_executor(None, service.list_groups)
            return json.dumps({"status": "ok", "action": act, "groups": _to_serializable(res)}, ensure_ascii=False)
        elif act == "get_group":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя группы) обязателен"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, service.get_group, target)
            return json.dumps({"status": "ok", "action": act, "group": _to_serializable(res)}, ensure_ascii=False)
        elif act == "who_is_admin":
            res = await loop.run_in_executor(None, service.who_is_admin)
            return json.dumps({"status": "ok", "action": act, "admins": _to_serializable(res)}, ensure_ascii=False)
        elif act == "who_can_rdp":
            res = await loop.run_in_executor(None, service.who_can_rdp)
            return json.dumps({"status": "ok", "action": act, "rdp_users": res}, ensure_ascii=False)
        elif act == "who_can_logon_as_service":
            res = await loop.run_in_executor(None, service.who_can_logon_as_service)
            return json.dumps({"status": "ok", "action": act, "service_logon_users": res}, ensure_ascii=False)
        elif act == "list_sessions":
            res = await loop.run_in_executor(None, service.list_sessions)
            return json.dumps({"status": "ok", "action": act, "sessions": _to_serializable(res)}, ensure_ascii=False)
        elif act == "list_profiles":
            res = await loop.run_in_executor(None, service.list_profiles)
            return json.dumps({"status": "ok", "action": act, "profiles": _to_serializable(res)}, ensure_ascii=False)
        elif act == "find_orphaned":
            sids = await loop.run_in_executor(None, service.find_orphaned_sids)
            profiles = await loop.run_in_executor(None, service.find_orphaned_profiles)
            return json.dumps({"status": "ok", "action": act, "orphaned_sids": sids, "orphaned_profiles": profiles}, ensure_ascii=False)
        elif act == "get_domain_info":
            res = await loop.run_in_executor(None, service.get_domain_info)
            return json.dumps({"status": "ok", "action": act, "domain_info": _to_serializable(res)}, ensure_ascii=False)
        elif act == "get_audit_events":
            limit = int(p.get("limit", 30))
            event_id = int(p["event_id"]) if "event_id" in p else None
            res = await loop.run_in_executor(None, service.get_audit_events, limit, event_id)
            return json.dumps({"status": "ok", "action": act, "events": _to_serializable(res)}, ensure_ascii=False)
        elif act == "create_user":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя нового пользователя) обязателен"}, ensure_ascii=False)
            pwd = p.get("password")
            full_name = p.get("full_name", "")
            desc = p.get("description", "")
            success = await loop.run_in_executor(None, service.create_user, target, pwd, full_name, desc)
            return json.dumps({"status": "ok" if success else "error", "action": act, "user_created": success, "username": target}, ensure_ascii=False)
        elif act == "delete_user":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя пользователя) обязателен"}, ensure_ascii=False)
            success = await loop.run_in_executor(None, service.delete_user, target)
            return json.dumps({"status": "ok" if success else "error", "action": act, "user_deleted": success, "username": target}, ensure_ascii=False)
        elif act == "add_to_group":
            username = p.get("username")
            if not target or not username:
                return json.dumps({"status": "error", "message": "Требуются target (группа) и params['username']"}, ensure_ascii=False)
            success = await loop.run_in_executor(None, service.add_user_to_group, target, username)
            return json.dumps({"status": "ok" if success else "error", "action": act, "added": success, "group": target, "username": username}, ensure_ascii=False)
        elif act == "remove_from_group":
            username = p.get("username")
            if not target or not username:
                return json.dumps({"status": "error", "message": "Требуются target (группа) и params['username']"}, ensure_ascii=False)
            success = await loop.run_in_executor(None, service.remove_user_from_group, target, username)
            return json.dumps({"status": "ok" if success else "error", "action": act, "removed": success, "group": target, "username": username}, ensure_ascii=False)
        elif act == "resolve":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (имя или SID) обязателен"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, service.resolve, target)
            return json.dumps({"status": "ok", "action": act, "principal": res}, ensure_ascii=False)
        elif act == "explain_pid":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр 'target' (PID) обязателен"}, ensure_ascii=False)
            pid_val = int(target)
            res = await loop.run_in_executor(None, service.explain_pid, pid_val)
            return json.dumps({"status": "ok", "action": act, "pid_analysis": res}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.core] Ошибка управления Accounts & Identity ('{action}', '{target}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_CORE_TOOLS = [
    windows_collector_audit,
    windows_execute_atomic_op,
    windows_manage_service,
    windows_manage_process,
    windows_manage_restore_point,
    windows_manage_sys_param,
    windows_safe_probe,
    windows_execute_powershell,
    windows_manage_optional_feature,
    windows_manage_accounts_identity,
]

__all__ = [
    'windows_collector_audit',
    'windows_execute_atomic_op',
    'windows_manage_service',
    'windows_manage_process',
    'windows_manage_restore_point',
    'windows_manage_sys_param',
    'windows_safe_probe',
    'windows_execute_powershell',
    'windows_manage_optional_feature',
    'windows_manage_accounts_identity',
    'WINDOWS_CORE_TOOLS',
]


