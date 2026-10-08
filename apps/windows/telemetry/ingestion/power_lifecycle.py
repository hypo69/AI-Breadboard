# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Power Lifecycle
# =============================================================================
# Description:
#   Движок сбора, разбора и корреляции событий жизненного цикла питания Windows
#   (Boot, Clean Shutdown, Planned Restart, Unexpected Power Loss, BSOD, Sleep/Wake)
#   и автоматической реконструкции сессий питания (Power Sessions).
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.power_lifecycle import PowerLifecycleEngine
#
#     engine = PowerLifecycleEngine()
#     summary = engine.scan_and_reconstruct(hours=720)
#     sessions = engine.get_sessions(limit=20)
#
# File: power_lifecycle.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:51:00
# =============================================================================

from __future__ import annotations
"""Движок анализа событий питания и реконструкции сессий жизненного цикла Windows."""

import json
import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI
from apps.windows.telemetry.win32_ffi.error_decoder import decode_bugcheck_code, format_system_error
from apps.windows.telemetry.models import (
    PowerEventRecord,
    PowerSessionRecord,
    PowerLifecycleSummary,
)
from apps.windows.telemetry.sqlite import TelemetryStorage


# Целевые Event ID для жизненного цикла питания и выключений
POWER_LIFECYCLE_EVENT_IDS = {
    1074: ('User32', 'Плановое выключение / перезагрузка инициирована пользователем или процессом'),
    13: ('Microsoft-Windows-Kernel-General', 'Операционная система начала завершение работы'),
    6006: ('EventLog', 'Служба Event Log корректно остановлена (штатное чистое выключение)'),
    6008: ('EventLog', 'Предыдущее завершение работы системы было неожиданным (Unexpected Shutdown)'),
    41: ('Microsoft-Windows-Kernel-Power', 'КРИТИЧЕСКИЙ СБОЙ: Перезагрузка без предварительного чистого выключения'),
    12: ('Microsoft-Windows-Kernel-General', 'Операционная система запущена (Boot)'),
    6005: ('EventLog', 'Служба Event Log запущена (ОС готова к работе)'),
    6009: ('EventLog', 'Windows записала информацию о версии ядра при загрузке'),
    1001: ('WER-SystemErrorReporting', 'Аварийный сбой ядра / BSOD (BugCheck)'),
    19: ('Microsoft-Windows-WindowsUpdateClient', 'Успешно установлено обновление Windows Update'),
    42: ('Microsoft-Windows-Kernel-Power', 'Переход системы в спящий режим (Sleep)'),
    107: ('Microsoft-Windows-Kernel-Power', 'Пробуждение системы из спящего режима (Resume/Wake)'),
}


def format_uptime_human(seconds: float) -> str:
    """Форматирует секунды аптайма в человекочитаемую строку на русском языке.

    Args:
        seconds: Длительность в секундах.

    Returns:
        str: Строка вида '3д 14ч 35м 31с' или '14ч 35м 31с'.
    """
    total_sec = max(0, int(seconds))
    days = total_sec // 86400
    hours = (total_sec % 86400) // 3600
    minutes = (total_sec % 3600) // 60
    sec = total_sec % 60

    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0 or days > 0:
        parts.append(f"{hours}ч")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}м")
    parts.append(f"{sec}с")

    return ' '.join(parts)


class PowerLifecycleEngine:
    """Движок глубокого анализа и реконструкции жизненного цикла питания ОС."""

    def __init__(
        self,
        storage: Optional[TelemetryStorage] = None,
        wevtapi: Optional[WevtAPI] = None,
    ) -> None:
        """Инициализация движка жизненного цикла питания.

        Args:
            storage: Экземпляр TelemetryStorage SQLite хранилища.
            wevtapi: Низкоуровневая Ctypes-обертка WevtAPI.
        """
        self.storage = storage or TelemetryStorage.get_instance()
        self.wevtapi = wevtapi or WevtAPI()

    def get_current_system_boot(self) -> Tuple[datetime, float]:
        """Определяет точное время последней загрузки и текущий аптайм.

        Returns:
            Tuple[datetime, float]: (boot_time UTC, uptime в секундах).
        """
        try:
            import psutil
            b_epoch = psutil.boot_time()
            boot_dt = datetime.fromtimestamp(b_epoch, tz=timezone.utc)
            uptime_sec = max(0.0, time.time() - b_epoch)
            return boot_dt, uptime_sec
        except Exception:
            boot_dt = datetime.now(timezone.utc)
            return boot_dt, 0.0

    def parse_event_1074(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        """Глубокий разбор события User32 1074 (инициатор, процесс, тип, причина).

        Args:
            ev: Словарь события из WevtAPI.

        Returns:
            Dict[str, Any]: Извлеченные нормализованные параметры.
        """
        msg = ev.get('message', '') or ev.get('formatted_message', '')
        data = ev.get('event_data', {}) or {}

        # 1. Попытка извлечения из XML Data (param1 ... param7)
        process = data.get('param1') or data.get('Process') or ''
        computer = data.get('param2') or data.get('Computer') or ev.get('computer', '')
        reason = data.get('param3') or data.get('Reason') or ''
        reason_code = data.get('param4') or data.get('ReasonCode') or ''
        shutdown_type = data.get('param5') or data.get('ShutdownType') or ''
        comment = data.get('param6') or data.get('Comment') or ''
        user = data.get('param7') or data.get('User') or ''

        # 2. Если параметры пустые, применяем регулярные выражения к сообщению
        if not process and msg:
            # Process regex
            m_proc = re.search(r'(?:process|процесс|процессом)\s+([^\s]+)', msg, re.IGNORECASE)
            if m_proc:
                process = m_proc.group(1).rstrip('.,;:')

            # User regex
            m_user = re.search(r'(?:user|пользователя|пользователь|имени)\s+([^\s]+)', msg, re.IGNORECASE)
            if m_user:
                user = m_user.group(1).rstrip('.,;:')

            # Reason Code regex
            m_code = re.search(r'(?:Reason Code|код причины|кодом причины)[:\s]+(0x[0-9a-fA-F]+)', msg, re.IGNORECASE)
            if m_code:
                reason_code = m_code.group(1)

            # Shutdown Type regex
            m_type = re.search(r'(?:Shutdown Type|тип выключения|тип завершения)[:\s]+([a-zA-Zа-яА-Я0-9_-]+)', msg, re.IGNORECASE)
            if m_type:
                shutdown_type = m_type.group(1)

            # Reason text regex
            m_reason = re.search(r'(?:reason|причине|причина)[:\s]+(.*?)(?:Reason Code|код причины|$)', msg, re.IGNORECASE)
            if m_reason:
                reason = m_reason.group(1).strip()

            # Comment regex
            m_comment = re.search(r'(?:comment|комментарий)[:\s]+(.*)$', msg, re.IGNORECASE)
            if m_comment:
                comment = m_comment.group(1).strip()

        # Нормализация типа выключения
        norm_type = 'Shutdown'
        st_lower = str(shutdown_type).lower()
        if 'restart' in st_lower or 'перезагр' in st_lower:
            norm_type = 'Restart'
        elif 'power off' in st_lower or 'выключ' in st_lower or 'poweroff' in st_lower:
            norm_type = 'PowerOff'
        elif 'hybrid' in st_lower or 'fast' in st_lower:
            norm_type = 'HybridShutdown'

        domain = ''
        if '\\' in user:
            domain, user_name = user.split('\\', 1)
        else:
            user_name = user

        # Корреляция цепочки инициатора
        initiator_chain: List[str] = []
        proc_lower = process.lower()
        if 'wmiprvse' in proc_lower:
            initiator_chain = [
                f"Пользователь/Скрипт ({user or 'WMI Client'})",
                "WMI Remote/Local Call",
                "wmiprvse.exe",
                "Windows ExitWindowsEx API",
            ]
        elif 'shutdown.exe' in proc_lower:
            initiator_chain = [
                f"Пользователь ({user or 'Console'})",
                "Командная строка / Task Scheduler",
                "shutdown.exe",
                "InitiateSystemShutdownEx API",
            ]
        elif 'explorer.exe' in proc_lower:
            initiator_chain = [
                f"Пользователь ({user or 'Interactive'})",
                "Меню Пуск / Win+X / Alt+F4",
                "explorer.exe",
                "Shell Shutdown API",
            ]
        elif 'svchost.exe' in proc_lower:
            initiator_chain = [
                "Служба обновления Windows / System Service",
                "svchost.exe",
                "Automatic Maintenance Restart",
            ]
        elif process:
            initiator_chain = [
                f"Пользователь ({user or 'User'})",
                f"Процесс ({process})",
                "Shutdown API",
            ]

        return {
            'process': process,
            'computer': computer,
            'reason': reason or 'Плановое завершение работы',
            'reason_code': reason_code,
            'shutdown_type': norm_type,
            'comment': comment,
            'user': user,
            'user_name': user_name,
            'domain': domain,
            'initiator_chain': initiator_chain,
        }

    def read_raw_power_events(self, hours: int = 720, limit: int = 500) -> List[Dict[str, Any]]:
        """Извлекает сырые события питания из журнала System Windows.

        Args:
            hours: Глубина выборки в часах.
            limit: Максимальное количество событий каждого типа.

        Returns:
            List[Dict[str, Any]]: Список событий, упорядоченных хронологически.
        """
        target_ids = list(POWER_LIFECYCLE_EVENT_IDS.keys())
        raw_events = self.wevtapi.read_events(
            channel='System',
            limit=limit,
            hours=hours,
            event_id=target_ids,
            format_message=True,
        )

        normalized: List[Dict[str, Any]] = []
        for ev in raw_events:
            eid = ev.get('event_id', 0)
            if eid not in POWER_LIFECYCLE_EVENT_IDS:
                continue

            provider_info = POWER_LIFECYCLE_EVENT_IDS.get(eid, ('System', ''))
            provider = ev.get('provider') or provider_info[0]
            ts = ev.get('timestamp') or ''
            raw_xml = ev.get('raw_data') or ''
            msg = ev.get('message') or ev.get('formatted_message') or provider_info[1]

            event_type = 'event'
            shutdown_type = None
            user = None
            domain = None
            process = None
            pid = ev.get('process_id')
            reason = None
            reason_code = None
            comment = None
            unexpected = False
            bugcheck_code = None
            bugcheck_params = None
            details: Dict[str, Any] = {'message': msg}

            if eid == 1074:
                parsed_1074 = self.parse_event_1074(ev)
                event_type = 'shutdown_planned'
                shutdown_type = parsed_1074['shutdown_type']
                user = parsed_1074['user']
                domain = parsed_1074['domain']
                process = parsed_1074['process']
                reason = parsed_1074['reason']
                reason_code = parsed_1074['reason_code']
                comment = parsed_1074['comment']
                details['initiator_chain'] = parsed_1074['initiator_chain']
                details['computer'] = parsed_1074['computer']

            elif eid == 13:
                event_type = 'shutdown_clean'
                shutdown_type = 'Shutdown'
                reason = 'Операционная система завершает работу ядра'

            elif eid == 6006:
                event_type = 'shutdown_clean'
                shutdown_type = 'Shutdown'
                reason = 'Служба Event Log корректно остановлена'

            elif eid in (41, 6008):
                event_type = 'shutdown_unexpected'
                unexpected = True
                shutdown_type = 'Unexpected'
                reason = 'Внезапное завершение работы (потеря питания / зависание / сбой)'
                if eid == 41:
                    ev_data = ev.get('event_data', {})
                    bc = ev_data.get('BugcheckCode')
                    if bc and str(bc) != '0':
                        try:
                            bc_int = int(bc)
                            bugcheck_code = hex(bc_int)
                            decoded = decode_bugcheck_code(bc_int)
                            details['bugcheck_info'] = decoded
                            details['bugcheck_symbol'] = decoded.get('symbol', '')
                        except Exception:
                            bugcheck_code = str(bc)
                    details['power_button_timestamp'] = ev_data.get('PowerButtonTimestamp', '0')

            elif eid in (12, 6005, 6009):
                event_type = 'boot'
                reason = 'Запуск операционной системы и системных служб'

            elif eid == 1001:
                event_type = 'bsod'
                reason = 'Критический сбой операционной системы (BugCheck / BSOD)'
                ev_data = ev.get('event_data', {})
                bugcheck_code = ev_data.get('param1') or ev_data.get('BugcheckCode')
                details['bugcheck_params'] = [ev_data.get(f'param{i}') for i in range(1, 6)]

            elif eid == 19:
                event_type = 'update_install'
                reason = 'Успешно установлено обновление Windows Update'

            elif eid == 42:
                event_type = 'sleep'
                reason = 'Переход системы в спящий режим'

            elif eid == 107:
                event_type = 'wake'
                reason = 'Выход системы из спящего режима'

            record = {
                'event_id': eid,
                'provider': provider,
                'channel': ev.get('channel', 'System'),
                'timestamp': ts,
                'created_at': self._parse_iso_to_epoch(ts),
                'event_type': event_type,
                'shutdown_type': shutdown_type,
                'user': user,
                'domain': domain,
                'process': process,
                'process_id': pid,
                'reason': reason,
                'reason_code': reason_code,
                'comment': comment,
                'unexpected': unexpected,
                'bugcheck_code': bugcheck_code,
                'bugcheck_params_json': json.dumps(bugcheck_params, ensure_ascii=False) if bugcheck_params else None,
                'details_json': json.dumps(details, ensure_ascii=False),
                'raw_xml': raw_xml,
            }
            normalized.append(record)

        # Сортировка от старых к новым для корректной реконструкции
        normalized.sort(key=lambda x: x['created_at'])
        return normalized

    def _parse_iso_to_epoch(self, ts_str: str) -> float:
        """Преобразует строку даты/времени в unix epoch timestamp."""
        if not ts_str:
            return time.time()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%fZ'):
            try:
                dt = datetime.strptime(ts_str.split('.')[0].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                return dt.replace(tzinfo=timezone.utc).timestamp()
            except Exception:
                pass
        return time.time()

    def reconstruct_power_sessions(self, events: List[Dict[str, Any]]) -> List[PowerSessionRecord]:
        """Реконструирует цепочки Boot -> Power Session -> Shutdown/Crash.

        Args:
            events: Хронологически отсортированный список нормализованных событий.

        Returns:
            List[PowerSessionRecord]: Список собранных сессий питания.
        """
        sessions: List[PowerSessionRecord] = []
        current_session: Optional[Dict[str, Any]] = None

        for ev in events:
            eid = ev.get('event_id', 0)
            e_type = ev.get('event_type', '')
            ts = ev.get('timestamp', '')
            epoch = ev.get('created_at', 0.0)

            # Событие запуска ОС (Boot)
            if eid in (12, 6005, 6009) or e_type == 'boot':
                # Если уже была открыта сессия без штатного завершения, закрываем её как Unexpected
                if current_session:
                    s_id = current_session['session_id']
                    uptime_sec = max(0.0, epoch - current_session['boot_timestamp'])
                    current_session['shutdown_time'] = ts
                    current_session['shutdown_timestamp'] = epoch
                    current_session['uptime_seconds'] = uptime_sec
                    current_session['uptime_human'] = format_uptime_human(uptime_sec)
                    if not current_session.get('shutdown_type') or current_session.get('shutdown_type') == 'Active':
                        current_session['shutdown_type'] = 'Unexpected'
                        current_session['unexpected_shutdown'] = True
                        current_session['clean_shutdown'] = False
                        current_session['reason'] = current_session['reason'] or 'Внезапный перезапуск без выключения (Kernel-Power 41 / 6008)'
                    sessions.append(PowerSessionRecord(**current_session))

                # Открываем новую сессию
                session_id = f"PS-{ts.replace(':', '').replace('-', '').replace(' ', '-')}"
                current_session = {
                    'session_id': session_id,
                    'boot_time': ts,
                    'boot_timestamp': epoch,
                    'shutdown_time': None,
                    'shutdown_timestamp': None,
                    'uptime_seconds': 0.0,
                    'uptime_human': '',
                    'shutdown_type': 'Active',
                    'initiator': None,
                    'process': None,
                    'reason': None,
                    'reason_code': None,
                    'comment': None,
                    'clean_shutdown': True,
                    'unexpected_shutdown': False,
                    'bugcheck': None,
                    'boot_event_id': eid,
                    'shutdown_event_id': None,
                    'initiator_chain': [],
                    'events': [ev],
                    'created_at': epoch,
                }

            elif current_session:
                current_session['events'].append(ev)

                # Завершение сессии (1074, 13, 6006)
                if eid == 1074:
                    current_session['shutdown_event_id'] = 1074
                    current_session['shutdown_type'] = ev.get('shutdown_type') or 'Restart'
                    current_session['initiator'] = ev.get('user')
                    current_session['process'] = ev.get('process')
                    current_session['reason'] = ev.get('reason')
                    current_session['reason_code'] = ev.get('reason_code')
                    current_session['comment'] = ev.get('comment')
                    current_session['clean_shutdown'] = True
                    details = json.loads(ev.get('details_json') or '{}') if isinstance(ev.get('details_json'), str) else (ev.get('details_json') or {})
                    if details.get('initiator_chain'):
                        current_session['initiator_chain'] = details['initiator_chain']

                elif eid in (13, 6006):
                    if not current_session.get('shutdown_event_id'):
                        current_session['shutdown_event_id'] = eid
                    if current_session.get('shutdown_type') == 'Active':
                        current_session['shutdown_type'] = 'Shutdown'
                    current_session['clean_shutdown'] = True

                elif eid in (41, 6008):
                    current_session['unexpected_shutdown'] = True
                    current_session['clean_shutdown'] = False
                    current_session['shutdown_type'] = 'Unexpected'
                    current_session['shutdown_event_id'] = eid
                    if ev.get('bugcheck_code'):
                        current_session['bugcheck'] = ev.get('bugcheck_code')
                    current_session['reason'] = ev.get('reason') or 'Внезапное выключение питания (Kernel-Power 41)'

                elif eid == 1001:
                    current_session['unexpected_shutdown'] = True
                    current_session['clean_shutdown'] = False
                    current_session['shutdown_type'] = 'BSOD'
                    current_session['bugcheck'] = ev.get('bugcheck_code') or 'CRITICAL_PROCESS_DIED'

        # Финализация последней активной сессии
        if current_session:
            cur_dt, cur_uptime = self.get_current_system_boot()
            now_epoch = time.time()
            if not current_session.get('shutdown_time'):
                current_session['shutdown_type'] = 'Active'
                current_session['uptime_seconds'] = max(0.0, now_epoch - current_session['boot_timestamp'])
                current_session['uptime_human'] = format_uptime_human(current_session['uptime_seconds'])
            sessions.append(PowerSessionRecord(**current_session))

        # Сортировка сессий от самых свежих к старым
        sessions.sort(key=lambda s: s.boot_timestamp, reverse=True)
        return sessions

    def scan_and_reconstruct(self, hours: int = 720, force: bool = False) -> PowerLifecycleSummary:
        """Выполняет сканирование журналов событий, парсинг и сохранение сессий в SQLite.

        Args:
            hours: Глубина выборки в часах (по умолчанию 720ч = 30 дней).
            force: Принудительно выполнить пересчет.

        Returns:
            PowerLifecycleSummary: Сводный отчет жизненного цикла питания.
        """
        logger.info(f'[PowerLifecycle] Сканирование событий питания Windows за последние {hours}ч...')
        raw_events = self.read_raw_power_events(hours=hours)

        if raw_events:
            self.storage.save_power_events(raw_events)
            sessions = self.reconstruct_power_sessions(raw_events)
            self.storage.save_power_sessions(sessions)
            logger.info(f'[PowerLifecycle] Реконструировано {len(sessions)} сессий питания из {len(raw_events)} событий.')
        else:
            sessions = []

        return self.get_summary()

    def get_summary(self) -> PowerLifecycleSummary:
        """Получает сводную статистику и последние сессии питания из БД SQLite.

        Returns:
            PowerLifecycleSummary: Сводный объект метрик.
        """
        db_summary = self.storage.get_power_summary()
        db_sessions_raw = self.storage.get_power_sessions(limit=30)
        sessions_records = [PowerSessionRecord(**s) for s in db_sessions_raw]

        cur_dt, cur_uptime = self.get_current_system_boot()
        cur_boot_str = cur_dt.strftime('%Y-%m-%d %H:%M:%S')
        cur_uptime_human = format_uptime_human(cur_uptime)

        return PowerLifecycleSummary(
            current_boot_time=db_summary.get('current_boot_time') or cur_boot_str,
            current_uptime_seconds=cur_uptime,
            current_uptime_human=cur_uptime_human,
            total_sessions_count=db_summary.get('total_sessions_count', 0),
            clean_shutdowns_count=db_summary.get('clean_shutdowns_count', 0),
            unexpected_shutdowns_count=db_summary.get('unexpected_shutdowns_count', 0),
            bsod_count=db_summary.get('bsod_count', 0),
            last_shutdown_type=db_summary.get('last_shutdown_type'),
            last_initiator=db_summary.get('last_initiator'),
            last_reason=db_summary.get('last_reason'),
            sessions=sessions_records,
        )

    def get_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        shutdown_type: Optional[str] = None,
        unexpected_only: bool = False,
    ) -> List[PowerSessionRecord]:
        """Возвращает список сессий питания с фильтрацией."""
        items = self.storage.get_power_sessions(
            limit=limit,
            offset=offset,
            shutdown_type=shutdown_type,
            unexpected_only=unexpected_only,
        )
        return [PowerSessionRecord(**it) for it in items]

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_id: Optional[Union[int, List[int]]] = None,
    ) -> List[PowerEventRecord]:
        """Возвращает список событий питания из БД."""
        items = self.storage.get_power_events(limit=limit, offset=offset, event_id=event_id)
        return [PowerEventRecord(**it) for it in items]


__all__ = [
    'PowerLifecycleEngine',
    'POWER_LIFECYCLE_EVENT_IDS',
    'format_uptime_human',
]
