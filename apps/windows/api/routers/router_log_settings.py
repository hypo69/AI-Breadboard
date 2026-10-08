# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Log Settings
# =============================================================================
# Description:
#   FastAPI роутер для вкладки настройки и просмотра параметров журналов событий Windows
#   (Security, System, Application, Sysmon и др.), аудита командных строк и управления закладками.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_log_settings import init_router
#
#     router = init_router()
#
# File: router_log_settings.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:30:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер для вкладки настройки и просмотра параметров журналов событий Windows."""

import asyncio
import datetime
import os
from pathlib import Path
import re
import subprocess
import winreg
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI, CHANNEL_DESCRIPTIONS
from apps.windows.telemetry.security_collector import WindowsSecurityCollector
from apps.windows.telemetry.sqlite import TelemetryStorage

router = APIRouter(prefix='/api/v1/log-settings', tags=['Windows Log Settings & Parameters'])
_wevtapi = WevtAPI()
_security_collector = WindowsSecurityCollector()
_storage = TelemetryStorage()

# Ключевые каналы для быстрого мониторинга
PRIORITY_CHANNELS = [
    'Security',
    'System',
    'Application',
    'Setup',
    'Microsoft-Windows-Sysmon/Operational',
    'Microsoft-Windows-TaskScheduler/Operational',
    'Microsoft-Windows-Windows Defender/Operational',
    'Microsoft-Windows-PowerShell/Operational',
    'Microsoft-Windows-Kernel-Power/Operational',
    'Microsoft-Windows-Kernel-PnP/Configuration',
    'Microsoft-Windows-WindowsUpdateClient/Operational',
    'Microsoft-Windows-Windows Firewall With Advanced Security/Firewall',
    'Microsoft-Windows-Diagnostics-Performance/Operational',
    'Microsoft-Windows-Bits-Client/Operational',
    'Microsoft-Windows-DNS-Client/Operational',
    'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational',
]


class LogChannelDetail(BaseModel):
    """Модель подробных параметров канала журнала Windows."""
    channel_name: str = Field(..., description="Имя канала журнала")
    display_name: str = Field(..., description="Отображаемое имя")
    description: str = Field('', description="Описание назначения журнала")
    is_enabled: bool = Field(True, description="Включен ли журнал")
    channel_type: str = Field('Admin', description="Тип канала (Admin, Operational, Analytic, Debug)")
    log_file_path: str = Field('', description="Путь к файлу .evtx на диске")
    file_size_bytes: int = Field(0, description="Текущий размер файла на диске в байтах")
    file_size_mb: float = Field(0.0, description="Текущий размер файла в МБ")
    max_size_bytes: int = Field(0, description="Максимальный разрешенный размер в байтах")
    max_size_mb: float = Field(0.0, description="Максимальный разрешенный размер в МБ")
    usage_pct: float = Field(0.0, description="Процент заполнения журнала")
    record_count: int = Field(0, description="Текущее количество записей в журнале")
    oldest_record_id: int = Field(0, description="Старейший Record ID")
    newest_record_id: int = Field(0, description="Новейший Record ID")
    is_full: bool = Field(False, description="Признак переполнения журнала")
    retention: bool = Field(False, description="Политика удержания (не перезаписывать)")
    auto_backup: bool = Field(False, description="Автоматическая архивация при заполнении")
    creation_time: str = Field('', description="Время создания файла журнала")
    last_access_time: str = Field('', description="Время последнего доступа")
    last_write_time: str = Field('', description="Время последней записи")
    is_accessible: bool = Field(True, description="Доступен ли журнал для чтения")


class LogChannelConfigRequest(BaseModel):
    """Запрос на изменение параметров канала журнала."""
    channel_name: str = Field(..., description="Имя канала")
    max_size_mb: Optional[int] = Field(None, ge=1, le=65536, description="Новый максимальный размер в МБ")
    is_enabled: Optional[bool] = Field(None, description="Включение/отключение канала")
    auto_backup: Optional[bool] = Field(None, description="Авто-бэкап при переполнении")
    retention: Optional[bool] = Field(None, description="Удержание записей")


class LogChannelClearRequest(BaseModel):
    """Запрос на очистку журнала."""
    channel_name: str = Field(..., description="Имя канала")
    backup_path: Optional[str] = Field(None, description="Путь для сохранения архива перед очисткой")


class AuditPolicyStatus(BaseModel):
    """Статус политик аудита и сборщика телеметрии."""
    cmdline_audit_enabled: bool = Field(False, description="Включен ли аудит CommandLine в процессах (Event 4688)")
    security_channel_accessible: bool = Field(False, description="Доступен ли канал Security для чтения")
    last_bookmark_record_id: Optional[int] = Field(None, description="Последний RecordID в закладке telemetry.db")
    last_bookmark_timestamp: Optional[str] = Field(None, description="Время фиксации закладки")
    db_security_events_count: int = Field(0, description="Число сохраненных событий Security в telemetry.db")


class SetCmdlineAuditRequest(BaseModel):
    """Запрос на переключение аудита командной строки."""
    enabled: bool = Field(..., description="Включить (True) или выключить (False) аудит CommandLine")


class BookmarkResetRequest(BaseModel):
    """Запрос на сброс закладки сборщика."""
    channel: str = Field('Security', description="Имя канала")
    record_id: Optional[int] = Field(None, description="Целевой Record ID (None = сбросить на текущий конец журнала)")


def _query_wevtutil_channel_info(channel_name: str) -> Dict[str, Any]:
    """Считывает параметры канала через утилиту wevtutil gl и wevtutil gli."""
    info: Dict[str, Any] = {
        'channel_name': channel_name,
        'enabled': True,
        'type': 'Operational',
        'log_file_path': '',
        'retention': False,
        'auto_backup': False,
        'max_size_bytes': 20971520,
        'file_size_bytes': 0,
        'record_count': 0,
        'oldest_record_id': 0,
        'newest_record_id': 0,
        'creation_time': '',
        'last_access_time': '',
        'last_write_time': '',
        'is_accessible': True,
    }

    try:
        # 1. Получение статической конфигурации
        res_gl = subprocess.run(
            ['wevtutil', 'gl', channel_name],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res_gl.returncode == 0:
            for line in res_gl.stdout.splitlines():
                line = line.strip()
                if line.startswith('enabled:'):
                    info['enabled'] = line.split(':', 1)[1].strip().lower() == 'true'
                elif line.startswith('type:'):
                    info['type'] = line.split(':', 1)[1].strip()
                elif line.startswith('logFileName:'):
                    raw_path = line.split(':', 1)[1].strip()
                    info['log_file_path'] = os.path.expandvars(raw_path)
                elif line.startswith('retention:'):
                    info['retention'] = line.split(':', 1)[1].strip().lower() == 'true'
                elif line.startswith('autoBackup:'):
                    info['auto_backup'] = line.split(':', 1)[1].strip().lower() == 'true'
                elif line.startswith('maxSize:'):
                    try:
                        info['max_size_bytes'] = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
        else:
            info['is_accessible'] = False

        # 2. Получение динамического состояния
        res_gli = subprocess.run(
            ['wevtutil', 'gli', channel_name],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res_gli.returncode == 0:
            for line in res_gli.stdout.splitlines():
                line = line.strip()
                if line.startswith('fileSize:'):
                    try:
                        info['file_size_bytes'] = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('numberOfLogRecords:'):
                    try:
                        info['record_count'] = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('oldestRecordNumber:'):
                    try:
                        info['oldest_record_id'] = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('creationTime:'):
                    info['creation_time'] = line.split(':', 1)[1].strip()
                elif line.startswith('lastAccessTime:'):
                    info['last_access_time'] = line.split(':', 1)[1].strip()
                elif line.startswith('lastWriteTime:'):
                    info['last_write_time'] = line.split(':', 1)[1].strip()

            if info['record_count'] > 0 and info['oldest_record_id'] > 0:
                info['newest_record_id'] = info['oldest_record_id'] + info['record_count'] - 1
            else:
                info['newest_record_id'] = info['oldest_record_id']
    except Exception as exc:
        logger.debug(f"[LogSettings] Ошибка опроса wevtutil для {channel_name}: {exc}")
        info['is_accessible'] = False

    return info


@router.get('/channels')
async def get_channels_list() -> Dict[str, Any]:
    """Возвращает список всех приоритетных и системных каналов с их подробными параметрами."""
    def _collect():
        channels_res: List[Dict[str, Any]] = []
        for cname in PRIORITY_CHANNELS:
            raw = _query_wevtutil_channel_info(cname)
            max_bytes = raw.get('max_size_bytes', 20971520) or 20971520
            file_bytes = raw.get('file_size_bytes', 0)
            usage_pct = min(100.0, round((file_bytes / max_bytes) * 100, 1)) if max_bytes > 0 else 0.0

            channels_res.append({
                'channel_name': cname,
                'display_name': cname,
                'description': _wevtapi.get_channel_description(cname),
                'is_enabled': raw.get('enabled', True),
                'channel_type': raw.get('type', 'Admin'),
                'log_file_path': raw.get('log_file_path', ''),
                'file_size_bytes': file_bytes,
                'file_size_mb': round(file_bytes / (1024 * 1024), 2),
                'max_size_bytes': max_bytes,
                'max_size_mb': round(max_bytes / (1024 * 1024), 2),
                'usage_pct': usage_pct,
                'record_count': raw.get('record_count', 0),
                'oldest_record_id': raw.get('oldest_record_id', 0),
                'newest_record_id': raw.get('newest_record_id', 0),
                'is_full': usage_pct >= 99.0,
                'retention': raw.get('retention', False),
                'auto_backup': raw.get('auto_backup', False),
                'creation_time': raw.get('creation_time', ''),
                'last_access_time': raw.get('last_access_time', ''),
                'last_write_time': raw.get('last_write_time', ''),
                'is_accessible': raw.get('is_accessible', True),
            })
        return {'channels': channels_res, 'total': len(channels_res)}

    return await asyncio.to_thread(_collect)


@router.get('/channel/{channel_name:path}')
async def get_channel_detail(channel_name: str) -> Dict[str, Any]:
    """Получение детальных параметров конкретного канала журнала."""
    def _fetch():
        raw = _query_wevtutil_channel_info(channel_name)
        max_bytes = raw.get('max_size_bytes', 20971520) or 20971520
        file_bytes = raw.get('file_size_bytes', 0)
        usage_pct = min(100.0, round((file_bytes / max_bytes) * 100, 1)) if max_bytes > 0 else 0.0

        return {
            'channel_name': channel_name,
            'display_name': channel_name,
            'description': _wevtapi.get_channel_description(channel_name),
            'is_enabled': raw.get('enabled', True),
            'channel_type': raw.get('type', 'Admin'),
            'log_file_path': raw.get('log_file_path', ''),
            'file_size_bytes': file_bytes,
            'file_size_mb': round(file_bytes / (1024 * 1024), 2),
            'max_size_bytes': max_bytes,
            'max_size_mb': round(max_bytes / (1024 * 1024), 2),
            'usage_pct': usage_pct,
            'record_count': raw.get('record_count', 0),
            'oldest_record_id': raw.get('oldest_record_id', 0),
            'newest_record_id': raw.get('newest_record_id', 0),
            'is_full': usage_pct >= 99.0,
            'retention': raw.get('retention', False),
            'auto_backup': raw.get('auto_backup', False),
            'creation_time': raw.get('creation_time', ''),
            'last_access_time': raw.get('last_access_time', ''),
            'last_write_time': raw.get('last_write_time', ''),
            'is_accessible': raw.get('is_accessible', True),
        }

    return await asyncio.to_thread(_fetch)


@router.post('/channel/config')
async def set_channel_config(req: LogChannelConfigRequest) -> Dict[str, Any]:
    """Изменение параметров конфигурации канала журнала (размер, включение, политики)."""
    def _apply():
        args = ['wevtutil', 'sl', req.channel_name]
        applied: Dict[str, Any] = {}

        if req.max_size_mb is not None:
            max_bytes = req.max_size_mb * 1024 * 1024
            args.append(f'/ms:{max_bytes}')
            applied['max_size_mb'] = req.max_size_mb

        if req.is_enabled is not None:
            args.append(f"/e:{'true' if req.is_enabled else 'false'}")
            applied['is_enabled'] = req.is_enabled

        if req.auto_backup is not None:
            args.append(f"/ab:{'true' if req.auto_backup else 'false'}")
            applied['auto_backup'] = req.auto_backup

        if req.retention is not None:
            args.append(f"/rt:{'true' if req.retention else 'false'}")
            applied['retention'] = req.retention

        res = subprocess.run(args, capture_output=True, text=True, check=False, timeout=10)
        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip() or f"Код ошибки {res.returncode}"
            logger.warning(f"[LogSettings] Ошибка изменения параметров {req.channel_name}: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось применить параметры к журналу '{req.channel_name}': {err_msg}. Возможно, требуются права Администратора.",
            )

        updated_info = _query_wevtutil_channel_info(req.channel_name)
        return {
            'success': True,
            'channel_name': req.channel_name,
            'applied': applied,
            'current_config': updated_info,
            'message': f"Параметры журнала '{req.channel_name}' успешно обновлены.",
        }

    return await asyncio.to_thread(_apply)


@router.post('/channel/clear')
async def clear_channel_log(req: LogChannelClearRequest) -> Dict[str, Any]:
    """Очистка журнала событий с возможностью предварительного резервного копирования."""
    def _do_clear():
        args = ['wevtutil', 'cl', req.channel_name]
        if req.backup_path:
            p = Path(req.backup_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            args.append(f'/bu:{req.backup_path}')

        res = subprocess.run(args, capture_output=True, text=True, check=False, timeout=15)
        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка очистки журнала '{req.channel_name}': {err_msg}",
            )

        return {
            'success': True,
            'channel_name': req.channel_name,
            'backup_saved': bool(req.backup_path),
            'backup_path': req.backup_path,
            'message': f"Журнал '{req.channel_name}' успешно очищен.",
        }

    return await asyncio.to_thread(_do_clear)


@router.get('/audit-status')
async def get_audit_status() -> Dict[str, Any]:
    """Проверка статуса политик аудита безопасности и состояния закладки телеметрии."""
    def _check():
        audit_res = _security_collector.check_access_and_audit()
        bm = _storage.get_security_bookmark('Security')
        stats = _storage.get_security_stats()

        last_bm_id = bm.get('last_record_id') if isinstance(bm, dict) else (getattr(bm, 'last_record_id', None) if bm else None)
        last_bm_time = bm.get('updated_at') if isinstance(bm, dict) else (getattr(bm, 'updated_at', None) if bm else None)

        return {
            'cmdline_audit_enabled': audit_res.command_line_audit_enabled,
            'security_channel_accessible': audit_res.accessible,
            'last_bookmark_record_id': last_bm_id,
            'last_bookmark_timestamp': last_bm_time,
            'db_security_events_count': stats.get('total_events', 0),
            'events_by_id': stats.get('events_by_id', {}),
            'earliest_event': stats.get('earliest_event', ''),
            'latest_event': stats.get('latest_event', ''),
        }

    return await asyncio.to_thread(_check)


@router.post('/audit-status/cmdline')
async def set_cmdline_audit(req: SetCmdlineAuditRequest) -> Dict[str, Any]:
    """Включение или отключение аудита командной строки процессов в реестре Windows."""
    def _set_reg():
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit"
        val = 1 if req.enabled else 0
        try:
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY) as key:
                winreg.SetValueEx(key, "ProcessCreationIncludeCmdLine_Enabled", 0, winreg.REG_DWORD, val)
            logger.info(f"[LogSettings] Аудит CommandLine установлен в {val}")
            return {
                'success': True,
                'cmdline_audit_enabled': req.enabled,
                'message': f"Аудит командных строк процессов (Event 4688) {'включен' if req.enabled else 'выключен'}.",
            }
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Отказано в доступе к реестру HKLM. Требуются права Администратора.",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка записи в реестр: {exc}",
            )

    return await asyncio.to_thread(_set_reg)


@router.post('/collector/collect')
async def run_collector_collection(limit: int = Query(500, ge=10, le=5000)) -> Dict[str, Any]:
    """Запуск инкрементального сбора журнала безопасности в telemetry.db."""
    def _collect():
        report = _security_collector.collect_incremental(batch_size=limit)
        return {
            'success': True,
            'channel': report.channel,
            'total_events_ingested': report.total_events_ingested,
            'last_record_id': report.last_record_id,
            'events_by_id': report.events_by_id,
            'errors': report.errors,
            'message': f"Собрано {report.total_events_ingested} новых событий. Последний Record ID: {report.last_record_id}",
        }

    return await asyncio.to_thread(_collect)


@router.post('/collector/reset-bookmark')
async def reset_collector_bookmark(req: BookmarkResetRequest) -> Dict[str, Any]:
    """Сброс закладки сборщика на указанный Record ID или на текущий конец журнала."""
    def _reset():
        target_id = req.record_id
        if target_id is None:
            raw_info = _query_wevtutil_channel_info(req.channel)
            target_id = raw_info.get('newest_record_id', 0)

        fake_xml = f"<BookmarkList>\n  <Bookmark Channel='{req.channel}' RecordId='{target_id}' IsCurrent='true'/>\n</BookmarkList>"
        _storage.save_security_bookmark(req.channel, target_id, fake_xml)
        logger.info(f"[LogSettings] Закладка для {req.channel} сброшена на Record ID {target_id}")

        return {
            'success': True,
            'channel': req.channel,
            'reset_record_id': target_id,
            'message': f"Закладка журнала '{req.channel}' успешно установлена на Record ID {target_id}.",
        }

    return await asyncio.to_thread(_reset)


@router.get('/events')
async def get_channel_events(
    channel: str = Query('Security', description="Имя канала или 'telemetry_db'"),
    event_id: int = Query(0, description="Фильтр по Event ID (0 = все)"),
    level: str = Query('', description="Фильтр по уровню (Information, Warning, Error, Critical)"),
    search: str = Query('', description="Поисковая строка по тексту сообщения или полям"),
    user: str = Query('', description="Фильтр по имени пользователя"),
    process: str = Query('', description="Фильтр по имени процесса"),
    limit: int = Query(50, ge=1, le=500, description="Максимальное число записей"),
) -> Dict[str, Any]:
    """Чтение и фильтрация событий из выбранного журнала или из базы telemetry.db."""
    def _fetch_events():
        if channel == 'telemetry_db' or channel.lower() == 'security_db':
            items = _storage.get_security_events(
                limit=limit,
                event_id=event_id if event_id > 0 else None,
                user=user or None,
                process_name=process or None,
            )
            if search:
                s_low = search.lower()
                items = [
                    it for it in items
                    if s_low in str(it.get('message', '')).lower()
                    or s_low in str(it.get('process_name', '')).lower()
                    or s_low in str(it.get('subject_user', '')).lower()
                    or s_low in str(it.get('command_line', '')).lower()
                ]
            return {
                'source': 'telemetry.db',
                'channel': 'Security',
                'events': items,
                'total': len(items),
            }

        # Чтение напрямую через WevtAPI
        raw_events = _wevtapi.read_events(
            channel=channel,
            limit=limit * 2 if (user or process or search) else limit,
            level=level,
            search=search,
            event_id=event_id if event_id > 0 else 0,
            hours=72,
        )

        filtered: List[Dict[str, Any]] = []
        for ev in raw_events:
            msg = ev.get('message', '')
            raw_data = str(ev.get('raw_data', ''))

            if user:
                u_low = user.lower()
                if u_low not in msg.lower() and u_low not in raw_data.lower():
                    continue
            if process:
                p_low = process.lower()
                if p_low not in msg.lower() and p_low not in raw_data.lower() and p_low not in str(ev.get('provider', '')).lower():
                    continue

            filtered.append(ev)
            if len(filtered) >= limit:
                break

        return {
            'source': 'wevtapi',
            'channel': channel,
            'events': filtered,
            'total': len(filtered),
        }

    return await asyncio.to_thread(_fetch_events)


# -----------------------------------------------------------------------------
# Иерархический каталог провайдеров и 7 доменов телеметрии
# -----------------------------------------------------------------------------
from apps.windows.telemetry.event_catalog import WindowsEventCatalogEngine

_catalog_engine = WindowsEventCatalogEngine()


@router.get('/catalog')
async def get_event_catalog(
    domain: Optional[str] = Query(None, description="Фильтр по домену телеметрии"),
    volume: Optional[str] = Query(None, description="Фильтр по объему (Low, Medium, High, Extreme)"),
    search: Optional[str] = Query(None, description="Поиск по имени провайдера или описанию"),
) -> Dict[str, Any]:
    """Возвращает структурированный каталог провайдеров и каналов Windows Event Log."""
    def _fetch_catalog():
        entries = _catalog_engine.get_full_catalog()
        filtered = []
        for e in entries:
            dom_val = e.domain.value if hasattr(e.domain, 'value') else str(e.domain)
            if domain and domain.lower() not in dom_val.lower():
                continue
            if volume and volume.lower() != e.volume_rating.lower():
                continue
            if search:
                s_low = search.lower()
                if (s_low not in e.provider.lower() and
                    s_low not in e.channel.lower() and
                    s_low not in e.description.lower()):
                    continue

            filtered.append({
                'id': e.id,
                'provider': e.provider,
                'channel': e.channel,
                'domain': dom_val,
                'domain_title': e.domain_title,
                'key_events': e.key_events,
                'levels': e.levels,
                'realtime_supported': e.realtime_supported,
                'historical_supported': e.historical_supported,
                'privilege_required': e.privilege_required,
                'volume_rating': e.volume_rating,
                'useful_fields': e.useful_fields,
                'recommended_collector': e.recommended_collector,
                'storage_class': e.storage_class,
                'correlation_targets': e.correlation_targets,
                'description': e.description,
                'is_present_on_host': e.is_present_on_host,
                'record_count': e.record_count,
                'size_mb': e.size_mb,
            })
        return {'catalog': filtered, 'total': len(filtered)}

    return await asyncio.to_thread(_fetch_catalog)


@router.get('/domains')
async def get_telemetry_domains_summary() -> Dict[str, Any]:
    """Сводка и метрики готовности по 7 доменам телеметрии Windows Event Logs."""
    return await asyncio.to_thread(_catalog_engine.get_domains_summary)


@router.get('/provenance/process')
async def get_process_provenance_graph(
    process_name: Optional[str] = Query(None, description="Имя целевого процесса"),
    pid: Optional[int] = Query(None, description="Идентификатор PID"),
    hours: int = Query(24, ge=1, le=168, description="Глубина выборки в часах"),
) -> Dict[str, Any]:
    """Построение графа происхождения процессов (Process Provenance Graph: User -> Parent -> Process -> Service/Task)."""
    return await asyncio.to_thread(
        _catalog_engine.reconstruct_process_provenance,
        process_name=process_name,
        pid=pid,
        hours=hours,
    )


@router.get('/lifecycle/power')
async def get_power_lifecycle(
    hours: int = Query(72, ge=1, le=720, description="Глубина выборки в часах"),
) -> Dict[str, Any]:
    """Реконструкция хронологии жизненного цикла ОС: Boot -> Login -> Sleep -> Wake -> Shutdown/Crash."""
    events = await asyncio.to_thread(_catalog_engine.reconstruct_power_lifecycle, hours=hours)
    return {'timeline': events, 'total': len(events)}


@router.get('/hardware/pnp')
async def get_hardware_pnp_chain(
    hours: int = Query(72, ge=1, le=720, description="Глубина выборки в часах"),
) -> Dict[str, Any]:
    """Реконструкция цепочки событий оборудования и драйверов Plug and Play."""
    events = await asyncio.to_thread(_catalog_engine.reconstruct_hardware_pnp_chain, hours=hours)
    return {'chain': events, 'total': len(events)}


@router.get('/sysmon/status')
async def get_sysmon_status() -> Dict[str, Any]:
    """Проверка доступности и статуса расширенной подсистемы Sysmon."""
    return await asyncio.to_thread(_catalog_engine.check_sysmon_status)


def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router


__all__ = ['router', 'init_router']
