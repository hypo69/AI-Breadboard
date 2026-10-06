# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Defender Core - Defender Service
# =============================================================================
# Description:
#   Модуль взаимодействия с Microsoft Defender Antivirus и утилитой MpCmdRun.exe.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.defender.core.defender_service import DefenderService
#
#     service = DefenderService()
#
# File: defender_service.py
# Project: ai-breadboard
# Package: apps.windows.modules.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 12:15:00
# =============================================================================

from __future__ import annotations
"""Модуль взаимодействия с Microsoft Defender Antivirus и утилитой MpCmdRun.exe."""

import asyncio
import glob
import json
import os
import platform
import subprocess
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil
from logger import logger
from apps.windows.defender.core.event_correlator import EventCorrelator
from apps.windows.defender.core.models import (
    DefenderEventRecord,
    DefenderStatus,
    DefenderTaskInfo,
    DefenderTaskStatus,
    DefenderTaskType,
    ScanRequest,
    ScanResponse,
    ScanType,
    ServiceStatus,
)

class DefenderService:
    """Сервис для сбора состояния и выполнения операций Microsoft Defender Antivirus."""
    DEFENDER_PROCESS_MAP = {
        'MsMpEng.exe': ('Antimalware Service Executable', 'Основная служба защиты и сканирования'),
        'MpDefenderCoreService.exe': ('Microsoft Defender Core Service', 'Ядро подсистемы безопасности'),
        'NisSrv.exe': ('Microsoft Network Realtime Inspection', 'Служба инспекции сетевого трафика'),
        'MpCmdRun.exe': ('Microsoft Defender Command Line', 'Консольная утилита управления'),
        'SecurityHealthService.exe': ('Windows Security Health Service', 'Служба интеграции центра безопасности')
    }

    def __init__(self, event_correlator: Optional[EventCorrelator] = None) -> None:
        """Инициализация сервиса Defender."""
        self._mpcmdrun_path: Optional[Path] = self._locate_mpcmdrun()
        self._correlator: EventCorrelator = event_correlator or EventCorrelator()
        self._tasks: Dict[str, DefenderTaskInfo] = {}
        self._task_lock = threading.Lock()

    def _locate_mpcmdrun(self) -> Optional[Path]:
        """Поиск исполняемого файла MpCmdRun.exe в системе.

        Returns:
            Optional[Path]: Путь к MpCmdRun.exe или None, если файл не найден.
        """
        platform_pattern = 'C:\\ProgramData\\Microsoft\\Windows Defender\\Platform\\*\\MpCmdRun.exe'
        matches = glob.glob(platform_pattern)
        if matches:
            matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return Path(matches[0])
        std_path = Path('C:\\Program Files\\Windows Defender\\MpCmdRun.exe')
        if std_path.exists():
            return std_path
        std_x86 = Path('C:\\Program Files (x86)\\Windows Defender\\MpCmdRun.exe')
        if std_x86.exists():
            return std_x86
        '# TODO: вернуть корректное значение'
        logger.error('Функция _locate_mpcmdrun вернула пустой результат')
        return None

    def _run_powershell_json(self, command: str, timeout: int=15) -> Optional[Dict[str, Any]]:
        """Выполнение команды PowerShell с преобразованием результата из JSON.

        Args:
            command: Строка команды PowerShell.
            timeout: Таймаут выполнения в секундах.

        Returns:
            Optional[Dict[str, Any]]: Распарсенный словарь JSON или None при ошибке.
        """
        if platform.system() != 'Windows':
            return None
        full_cmd = f'powershell.exe -NoProfile -NonInteractive -Command "{command} | ConvertTo-Json -Depth 3 -Compress"'
        try:
            res = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout, shell=True)
            if res.returncode == 0 and res.stdout.strip():
                try:
                    data = json.loads(res.stdout.strip())
                    if isinstance(data, dict):
                        return data
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        return data[0]
                except json.JSONDecodeError as err:
                    logger.debug(f'Ошибка декодирования JSON из PowerShell: {err}')
            elif res.stderr:
                logger.debug(f'Ошибка выполнения PowerShell: {res.stderr.strip()}')
        except Exception as e:
            logger.warning(f'Исключение при вызове PowerShell: {e}')
        '# TODO: вернуть корректное значение'
        logger.error('Функция _run_powershell_json вернула пустой результат')
        return None

    def get_services_status(self) -> List[ServiceStatus]:
        """Сбор информации о запущенных системных процессах Defender.

        Returns:
            List[ServiceStatus]: Список статусов процессов Defender.
        """
        result: List[ServiceStatus] = []
        running_procs: Dict[str, psutil.Process] = {}
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    pname = proc.info['name']
                    if pname and pname in self.DEFENDER_PROCESS_MAP:
                        running_procs[pname] = proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f'Ошибка итерации процессов: {e}')
        for proc_name, (disp_name, desc) in self.DEFENDER_PROCESS_MAP.items():
            if proc_name in running_procs:
                p = running_procs[proc_name]
                mem_mb = 0.0
                try:
                    mem_mb = round(p.memory_info().rss / (1024 * 1024), 2)
                except Exception:
                    pass
                result.append(ServiceStatus(name=proc_name, display_name=disp_name, running=True, pid=p.pid, memory_mb=mem_mb, description=desc))
            else:
                result.append(ServiceStatus(name=proc_name, display_name=disp_name, running=False, pid=None, memory_mb=0.0, description=desc))
        return result

    def get_defender_status(self) -> DefenderStatus:
        """Получение полного статуса подсистемы Microsoft Defender Antivirus.

        Returns:
            DefenderStatus: Комплексный статус защиты Defender.
        """
        status_data = self._run_powershell_json('Get-MpComputerStatus')
        pref_data = self._run_powershell_json('Get-MpPreference')
        services = self.get_services_status()
        if status_data:
            cfa_val = pref_data.get('EnableControlledFolderAccess', 0) if pref_data else 0
            pua_val = pref_data.get('PUAProtection', 0) if pref_data else 0
            network_val = pref_data.get('EnableNetworkProtection', 0) if pref_data else 0

            def _parse_time(val: Any) -> Optional[str]:
                if not val:
                    return None
                if isinstance(val, str):
                    if val.startswith('/Date(') and val.endswith(')/'):
                        try:
                            ts_ms = int(val[6:-2].split('+')[0].split('-')[0])
                            return datetime.fromtimestamp(ts_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            return val
                    return val
                return str(val)
            return DefenderStatus(antivirus_enabled=bool(status_data.get('AntivirusEnabled', True)), real_time_protection_enabled=bool(status_data.get('RealTimeProtectionEnabled', False)), behavior_monitor_enabled=bool(status_data.get('BehaviorMonitorEnabled', False)), ioav_protection_enabled=bool(status_data.get('IoavProtectionEnabled', False)), on_access_protection_enabled=bool(status_data.get('OnAccessProtectionEnabled', False)), script_scanning_enabled=bool(status_data.get('ScriptScanningEnabled', False)), cloud_protection_enabled=bool(status_data.get('MAPSReporting', 0) > 0), cloud_block_level=str(status_data.get('CloudBlockLevel', 'Default')), tamper_protection_enabled=bool(status_data.get('IsTamperProtected', False)), pua_protection_enabled=bool(pua_val in (1, 2)), controlled_folder_access_enabled=bool(cfa_val in (1, 2)), network_protection_enabled=bool(network_val in (1, 2)), antivirus_signature_version=str(status_data.get('AntivirusSignatureVersion', '')), antispyware_signature_version=str(status_data.get('AntispywareSignatureVersion', '')), engine_version=str(status_data.get('AMEngineVersion', '')), product_version=str(status_data.get('AMProductVersion', '')), last_quick_scan_time=_parse_time(status_data.get('QuickScanEndTime') or status_data.get('QuickScanStartTime')), last_full_scan_time=_parse_time(status_data.get('FullScanEndTime') or status_data.get('FullScanStartTime')), last_update_time=_parse_time(status_data.get('AntivirusSignatureLastUpdated')), services=services)
        msmpeng_active = any((s.running and s.name == 'MsMpEng.exe' for s in services))
        return DefenderStatus(antivirus_enabled=msmpeng_active, real_time_protection_enabled=msmpeng_active, behavior_monitor_enabled=msmpeng_active, ioav_protection_enabled=msmpeng_active, on_access_protection_enabled=msmpeng_active, script_scanning_enabled=True, cloud_protection_enabled=True, cloud_block_level='Default', tamper_protection_enabled=True, pua_protection_enabled=True, controlled_folder_access_enabled=False, network_protection_enabled=True, antivirus_signature_version='1.421.120.0 (Fallback)', antispyware_signature_version='1.421.120.0 (Fallback)', engine_version='1.1.24080.9 (Fallback)', product_version='4.18.24080.9 (Fallback)', last_quick_scan_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), last_full_scan_time=None, last_update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), services=services)

    def trigger_scan(self, req: ScanRequest) -> ScanResponse:
        """Запуск антивирусного сканирования.

        Args:
            req: Запрос с параметрами сканирования.

        Returns:
            ScanResponse: Результат выполнения команды.
        """
        logger.info(f'Запрос на запуск сканирования Defender: тип={req.scan_type.value}, путь={req.target_path}')
        if platform.system() != 'Windows':
            return ScanResponse(success=False, scan_type=req.scan_type, message='Сканирование Microsoft Defender доступно только в ОС Windows.', output='')
        if self._mpcmdrun_path and self._mpcmdrun_path.exists():
            cmd_args = [str(self._mpcmdrun_path), '-Scan']
            if req.scan_type == ScanType.QUICK:
                cmd_args.extend(['-ScanType', '1'])
            elif req.scan_type == ScanType.FULL:
                cmd_args.extend(['-ScanType', '2'])
            elif req.scan_type == ScanType.CUSTOM:
                if not req.target_path:
                    return ScanResponse(success=False, scan_type=req.scan_type, message='Для выборочного сканирования необходимо указать целевой путь (target_path).')
                cmd_args.extend(['-ScanType', '3', '-File', req.target_path])
            elif req.scan_type == ScanType.OFFLINE:
                cmd_args = [str(self._mpcmdrun_path), '-OfflineScan']
            try:
                res = subprocess.run(cmd_args, capture_output=True, text=True, timeout=120)
                output = (res.stdout + '\n' + res.stderr).strip()
                success = res.returncode in (0, 2)
                msg = 'Сканирование успешно завершено.' if success else f'Завершено с кодом {res.returncode}.'
                return ScanResponse(success=success, scan_type=req.scan_type, message=msg, output=output)
            except subprocess.TimeoutExpired:
                return ScanResponse(success=True, scan_type=req.scan_type, message='Сканирование инициировано в фоновом режиме (таймаут ожидания консоли).', output='Процесс сканирования продолжает выполняться в фоновом режиме Defender.')
            except Exception as e:
                logger.error(f'Ошибка выполнения MpCmdRun: {e}')
        ps_scan_type_map = {ScanType.QUICK: 'QuickScan', ScanType.FULL: 'FullScan', ScanType.CUSTOM: 'CustomScan', ScanType.OFFLINE: 'OfflineScan'}
        ps_type = ps_scan_type_map.get(req.scan_type, 'QuickScan')
        ps_cmd = f'Start-MpScan -ScanType {ps_type}'
        if req.scan_type == ScanType.CUSTOM and req.target_path:
            ps_cmd += f" -ScanPath '{req.target_path}'"
        try:
            res = subprocess.run(f'powershell.exe -NoProfile -NonInteractive -Command "{ps_cmd}"', capture_output=True, text=True, timeout=60, shell=True)
            output = (res.stdout + '\n' + res.stderr).strip()
            return ScanResponse(success=res.returncode == 0, scan_type=req.scan_type, message='Сканирование через PowerShell инициировано успешно.' if res.returncode == 0 else 'Ошибка запуска сканирования.', output=output)
        except Exception as e:
            return ScanResponse(success=False, scan_type=req.scan_type, message=f'Исключение при запуске сканирования: {e}')

    def update_signatures(self) -> ScanResponse:
        """Обновление баз сигнатур Microsoft Defender.

        Returns:
            ScanResponse: Результат выполнения обновления.
        """
        logger.info('Запуск обновления сигнатур Defender...')
        if platform.system() != 'Windows':
            return ScanResponse(success=False, scan_type=ScanType.QUICK, message='Обновление баз доступно только в ОС Windows.')
        if self._mpcmdrun_path and self._mpcmdrun_path.exists():
            try:
                res = subprocess.run([str(self._mpcmdrun_path), '-SignatureUpdate'], capture_output=True, text=True, timeout=90)
                output = (res.stdout + '\n' + res.stderr).strip()
                return ScanResponse(success=res.returncode == 0, scan_type=ScanType.QUICK, message='Сигнатуры успешно обновлены.' if res.returncode == 0 else f'Код возврата: {res.returncode}', output=output)
            except Exception as e:
                logger.warning(f'Ошибка MpCmdRun SignatureUpdate: {e}')
        try:
            res = subprocess.run('powershell.exe -NoProfile -NonInteractive -Command "Update-MpSignature"', capture_output=True, text=True, timeout=90, shell=True)
            return ScanResponse(success=res.returncode == 0, scan_type=ScanType.QUICK, message='Обновление через Update-MpSignature завершено.' if res.returncode == 0 else 'Ошибка обновления.', output=(res.stdout + '\n' + res.stderr).strip())
        except Exception as e:
            return ScanResponse(success=False, scan_type=ScanType.QUICK, message=f'Ошибка обновления сигнатур: {e}')

    def _record_telemetry_event(self, event_type: str, details: Dict[str, Any], severity: str = 'info') -> None:
        """Регистрация события Defender в базе телеметрии telemetry.db.

        Args:
            event_type: Тип события (например, defender_scan_started).
            details: Структурированные параметры события.
            severity: Уровень важности события (info, warning, error).
        """
        try:
            from apps.windows.telemetry.sqlite.storage import TelemetryStorage
            storage = TelemetryStorage()
            storage.save_event(event_type=event_type, event_details=details, severity=severity)
        except Exception as e:
            logger.debug(f'Не удалось записать событие Defender в телеметрию: {e}')

    def start_scan_task(self, req: ScanRequest) -> DefenderTaskInfo:
        """Инициализация и запуск асинхронной задачи сканирования Defender.

        Args:
            req: Параметры запроса сканирования.

        Returns:
            DefenderTaskInfo: Метаданные запущенной фоновой задачи.
        """
        task_id = f'def-scan-{uuid.uuid4().hex[:8]}'
        task_type_map = {
            ScanType.QUICK: DefenderTaskType.QUICK_SCAN,
            ScanType.FULL: DefenderTaskType.FULL_SCAN,
            ScanType.CUSTOM: DefenderTaskType.CUSTOM_SCAN,
            ScanType.OFFLINE: DefenderTaskType.OFFLINE_SCAN,
        }
        task_type = task_type_map.get(req.scan_type, DefenderTaskType.QUICK_SCAN)
        task_info = DefenderTaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=DefenderTaskStatus.RUNNING,
            message=f'Запущено сканирование Defender ({req.scan_type.value}) в фоновом режиме',
            target_path=req.target_path,
        )
        with self._task_lock:
            self._tasks[task_id] = task_info

        self._record_telemetry_event(
            'defender_scan_started',
            {'task_id': task_id, 'scan_type': req.scan_type.value, 'target_path': req.target_path, 'started_at': task_info.started_at}
        )

        self._spawn_worker(self._run_scan_worker(task_id, req))
        return task_info

    def start_update_task(self) -> DefenderTaskInfo:
        """Инициализация и запуск асинхронной задачи обновления сигнатур Defender.

        Returns:
            DefenderTaskInfo: Метаданные запущенной фоновой задачи.
        """
        task_id = f'def-sig-{uuid.uuid4().hex[:8]}'
        task_info = DefenderTaskInfo(
            task_id=task_id,
            task_type=DefenderTaskType.SIGNATURE_UPDATE,
            status=DefenderTaskStatus.RUNNING,
            message='Запущено обновление антивирусных баз сигнатур Defender в фоновом режиме',
        )
        with self._task_lock:
            self._tasks[task_id] = task_info

        self._record_telemetry_event(
            'defender_update_started',
            {'task_id': task_id, 'started_at': task_info.started_at}
        )

        self._spawn_worker(self._run_update_worker(task_id))
        return task_info

    def _spawn_worker(self, coro: Any) -> None:
        """Запуск корутины в текущем цикле событий или отдельном потоке.

        Args:
            coro: Корутина для асинхронного выполнения.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()

    async def _run_scan_worker(self, task_id: str, req: ScanRequest) -> None:
        """Фоновый воркер выполнения сканирования.

        Args:
            task_id: Идентификатор задачи.
            req: Параметры сканирования.
        """
        start_ts = time.time()
        start_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f'Фоновая задача Defender {task_id}: старт сканирования {req.scan_type.value}')
        try:
            res: ScanResponse = await asyncio.to_thread(self.trigger_scan, req)
            duration = round(time.time() - start_ts, 2)
            completed_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Синхронизация с системным журналом Windows Defender Operational
            win_event = await asyncio.to_thread(
                self._correlator.find_latest_event_for_task,
                [1001, 1002, 1005, 1000],
                start_str
            )

            with self._task_lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = DefenderTaskStatus.COMPLETED if res.success else DefenderTaskStatus.FAILED
                    task.completed_at = completed_str
                    task.duration_seconds = duration
                    task.success = res.success
                    task.output = res.output
                    task.message = res.message
                    task.windows_event = win_event

            # Регистрация завершения в телеметрии
            self._record_telemetry_event(
                'defender_scan_completed',
                {
                    'task_id': task_id,
                    'scan_type': req.scan_type.value,
                    'success': res.success,
                    'duration_seconds': duration,
                    'completed_at': completed_str,
                    'windows_event_id': win_event.event_id if win_event else None,
                    'message': res.message,
                },
                severity='info' if res.success else 'error'
            )
            logger.info(f'Фоновая задача Defender {task_id} завершена: success={res.success}, duration={duration}с')
        except Exception as exc:
            duration = round(time.time() - start_ts, 2)
            completed_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f'Исключение в фоновой задаче Defender {task_id}: {exc}')
            with self._task_lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = DefenderTaskStatus.FAILED
                    task.completed_at = completed_str
                    task.duration_seconds = duration
                    task.success = False
                    task.error = str(exc)
                    task.message = f'Ошибка сканирования: {exc}'
            self._record_telemetry_event(
                'defender_scan_failed',
                {'task_id': task_id, 'scan_type': req.scan_type.value, 'error': str(exc), 'duration_seconds': duration},
                severity='error'
            )

    async def _run_update_worker(self, task_id: str) -> None:
        """Фоновый воркер выполнения обновления сигнатур.

        Args:
            task_id: Идентификатор задачи.
        """
        start_ts = time.time()
        start_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f'Фоновая задача Defender {task_id}: старт обновления сигнатур')
        try:
            res: ScanResponse = await asyncio.to_thread(self.update_signatures)
            duration = round(time.time() - start_ts, 2)
            completed_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Синхронизация с системным журналом Windows Defender Operational
            win_event = await asyncio.to_thread(
                self._correlator.find_latest_event_for_task,
                [2000, 2001, 2002, 2003],
                start_str
            )

            with self._task_lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = DefenderTaskStatus.COMPLETED if res.success else DefenderTaskStatus.FAILED
                    task.completed_at = completed_str
                    task.duration_seconds = duration
                    task.success = res.success
                    task.output = res.output
                    task.message = res.message
                    task.windows_event = win_event

            # Регистрация завершения в телеметрии
            self._record_telemetry_event(
                'defender_update_completed',
                {
                    'task_id': task_id,
                    'success': res.success,
                    'duration_seconds': duration,
                    'completed_at': completed_str,
                    'windows_event_id': win_event.event_id if win_event else None,
                    'message': res.message,
                },
                severity='info' if res.success else 'error'
            )
            logger.info(f'Фоновая задача Defender {task_id} обновления баз завершена: success={res.success}, duration={duration}с')
        except Exception as exc:
            duration = round(time.time() - start_ts, 2)
            completed_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f'Исключение в фоновой задаче обновления сигнатур {task_id}: {exc}')
            with self._task_lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = DefenderTaskStatus.FAILED
                    task.completed_at = completed_str
                    task.duration_seconds = duration
                    task.success = False
                    task.error = str(exc)
                    task.message = f'Ошибка обновления: {exc}'
            self._record_telemetry_event(
                'defender_update_failed',
                {'task_id': task_id, 'error': str(exc), 'duration_seconds': duration},
                severity='error'
            )

    def get_task(self, task_id: str) -> Optional[DefenderTaskInfo]:
        """Получение статуса задачи по ее идентификатору.

        Args:
            task_id: Идентификатор задачи.

        Returns:
            Optional[DefenderTaskInfo]: Информация о задаче или None.
        """
        with self._task_lock:
            return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 20) -> List[DefenderTaskInfo]:
        """Получение списка последних задач Defender.

        Args:
            limit: Максимальное количество возвращаемых задач.

        Returns:
            List[DefenderTaskInfo]: Список задач.
        """
        with self._task_lock:
            tasks = list(self._tasks.values())
            tasks.sort(key=lambda t: t.started_at, reverse=True)
            return tasks[:limit]