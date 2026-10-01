# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Reboot Analyzer
# =============================================================================
# Description:
#   Модуль глубокого анализа и корреляции причин перезагрузок Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.reboot_analyzer import WindowsRebootAnalyzer
#
#     service = WindowsRebootAnalyzer()
#
# File: reboot_analyzer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль глубокого анализа и корреляции причин перезагрузок Windows."""

import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from logger import logger
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI
from apps.windows.telemetry.win32_ffi.error_decoder import decode_bugcheck_code, format_system_error
from apps.windows.telemetry.models import (
    RebootAnalysisReport,
    RebootCorrelatedEvent,
    RebootSession,
    ShutdownType,
)
from apps.windows.telemetry.sqlite import TelemetryStorage

# Целевые Event ID для корреляции жизненного цикла загрузки и выключения
TARGET_EVENT_IDS = {
    1074: ('User32', 'Плановый перезапуск или выключение инициировано процессом/пользователем'),
    41: ('Kernel-Power', 'Система перезагрузилась без корректного предварительного выключения'),
    6008: ('EventLog', 'Предыдущее завершение работы системы было неожиданным'),
    1001: ('WER-SystemErrorReporting', 'Критический системный сбой ОС (BSOD / BugCheck)'),
    19: ('WindowsUpdateClient', 'Успешная установка обновления Windows Update'),
    20: ('WindowsUpdateClient', 'Ошибка установки обновления Windows Update'),
    21: ('WindowsUpdateClient', 'Завершена установка обновлений, требуется перезапуск'),
    12: ('Kernel-General', 'Запуск ядра операционной системы'),
    13: ('Kernel-General', 'Завершение работы операционной системы'),
    6005: ('EventLog', 'Запуск службы журнала событий Windows (система загружена)'),
    6006: ('EventLog', 'Остановка службы журнала событий Windows (штатное выключение)'),
    7045: ('Service Control Manager', 'В системе была установлена новая служба'),
    109: ('Kernel-Power', 'Переход ядра в режим гибернации / Fast Startup'),
}


class WindowsRebootAnalyzer:
    """Анализатор жизненного цикла перезагрузок и выключений операционной системы."""

    def __init__(
        self,
        storage: Optional[TelemetryStorage] = None,
        wevtapi: Optional[WevtAPI] = None,
    ) -> None:
        """Инициализация анализатора перезагрузок.

        Args:
            storage: Хранилище телеметрии TelemetryStorage.
            wevtapi: Экземпляр низкоуровневого API WevtAPI.
        """
        self.storage = storage or TelemetryStorage.get_instance()
        self.wevtapi = wevtapi or WevtAPI()

    def get_current_boot_info(self) -> Tuple[datetime, float]:
        """Получить время текущей загрузки ОС и текущий аптайм.

        Returns:
            Tuple[datetime, float]: (время старта, аптайм в секундах).
        """
        try:
            import psutil
            b_epoch = psutil.boot_time()
            boot_dt = datetime.fromtimestamp(b_epoch, tz=timezone.utc)
            uptime_sec = max(0.0, time.time() - b_epoch)
            return boot_dt, uptime_sec
        except Exception:
            # Fallback
            boot_dt = datetime.now(timezone.utc)
            return boot_dt, 0.0

    def collect_reboot_history(
        self,
        limit: int = 20,
        hours: int = 720,
        persist_to_storage: bool = True,
    ) -> RebootAnalysisReport:
        """Сбор и глубокая корреляция истории перезагрузок за указанный период.

        Args:
            limit: Максимальное количество анализируемых сессий перезагрузки.
            hours: Глубина выборки событий в часах (по умолчанию 30 дней = 720 ч).
            persist_to_storage: Сохранять ли выявленные новые сессии в БД SQLite.

        Returns:
            RebootAnalysisReport: Полный аналитический отчет с сессиями и оценкой стабильности.
        """
        cur_boot_dt, cur_uptime = self.get_current_boot_info()
        cur_boot_str = cur_boot_dt.strftime('%Y-%m-%d %H:%M:%S')
        hostname = socket.gethostname()

        # 1. Извлечение событий из EventLog
        raw_events = self._query_system_events(hours=hours)

        # 2. Корреляция событий в хронологические сессии
        sessions = self._correlate_events_into_sessions(raw_events, limit=limit)

        # 3. Сохранение в постоянное хранилище при необходимости
        if persist_to_storage and self.storage:
            for session in sessions:
                try:
                    self.storage.save_reboot_session(session)
                except Exception as ex:
                    logger.debug(f'Ошибка сохранения сессии перезагрузки {session.boot_id}: {ex}')

        # 4. Подсчет статистики стабильности
        planned_cnt = sum(1 for s in sessions if s.shutdown_type in (
            ShutdownType.PLANNED, ShutdownType.UPDATE_RESTART, ShutdownType.USER_INITIATED, ShutdownType.HYBRID_SHUTDOWN
        ))
        unexpected_cnt = sum(1 for s in sessions if s.shutdown_type in (
            ShutdownType.UNEXPECTED, ShutdownType.DIRTY_POWER_LOSS, ShutdownType.HARDWARE_POWER_BUTTON
        ))
        bsod_cnt = sum(1 for s in sessions if s.shutdown_type == ShutdownType.CRASH_BSOD)
        update_cnt = sum(1 for s in sessions if s.shutdown_type == ShutdownType.UPDATE_RESTART)
        total_cnt = len(sessions)

        if total_cnt > 0:
            stability_score = round(max(0.0, 100.0 - (unexpected_cnt * 25.0 + bsod_cnt * 35.0) / total_cnt), 1)
        else:
            stability_score = 100.0

        # Формирование текстового резюме
        summary_parts = [
            f'Проанализировано {total_cnt} перезапусков Windows.',
            f'Плановых: {planned_cnt}, Обновлений: {update_cnt}, Аварийных/внезапных: {unexpected_cnt}, BSOD: {bsod_cnt}.',
            f'Индекс стабильности завершений работы: {stability_score}%/100%.',
        ]
        if bsod_cnt > 0:
            summary_parts.append(f'ВНИМАНИЕ: Зафиксировано {bsod_cnt} критических сбоев синего экрана (BSOD).')
        elif unexpected_cnt > 0:
            summary_parts.append(f'ПРЕДУПРЕЖДЕНИЕ: Зафиксировано {unexpected_cnt} внезапных обесточиваний или зависаний.')
        else:
            summary_parts.append('Все недавние перезагрузки системы завершены в штатном запланированном режиме.')

        return RebootAnalysisReport(
            hostname=hostname,
            current_boot_time=cur_boot_str,
            current_uptime_seconds=round(cur_uptime, 1),
            current_uptime_human=self._format_duration(cur_uptime),
            total_reboots_analyzed=total_cnt,
            planned_count=planned_cnt,
            unexpected_count=unexpected_cnt,
            bsod_count=bsod_cnt,
            update_reboot_count=update_cnt,
            stability_score=stability_score,
            sessions=sessions,
            summary_ru=' '.join(summary_parts),
        )

    def analyze_current_boot(self) -> Optional[RebootSession]:
        """Быстрый анализ причины завершения предыдущей сессии перед текущим запуском.

        Returns:
            Optional[RebootSession]: Сессия текущего запуска с расследованием предшествующего выключения.
        """
        report = self.collect_reboot_history(limit=1, hours=72, persist_to_storage=True)
        if report.sessions:
            return report.sessions[0]
        return None

    def _query_system_events(self, hours: int = 720) -> List[Dict[str, Any]]:
        """Запрос событий из журналов Windows через WevtAPI или PowerShell fallback."""
        events: List[Dict[str, Any]] = []

        # 1. Попытка нативного сбора через WevtAPI
        if self.wevtapi and self.wevtapi.is_available():
            try:
                for eid in TARGET_EVENT_IDS.keys():
                    # Читаем System
                    sys_evs = self.wevtapi.read_events(channel='System', limit=100, event_id=eid, hours=hours)
                    events.extend(sys_evs)
                    # Читаем Application
                    if eid in (1001, 1074):
                        app_evs = self.wevtapi.read_events(channel='Application', limit=50, event_id=eid, hours=hours)
                        events.extend(app_evs)
                    # Читаем WindowsUpdateClient
                    if eid in (19, 20, 21):
                        wu_evs = self.wevtapi.read_events(
                            channel='Microsoft-Windows-WindowsUpdateClient/Operational',
                            limit=50,
                            event_id=eid,
                            hours=hours,
                        )
                        events.extend(wu_evs)
            except Exception as ex:
                logger.debug(f'Ошибка нативного чтения WevtAPI для перезагрузок: {ex}')

        # 2. Если событий мало или WevtAPI недоступен, выполняем надежный PowerShell сбор
        if len(events) < 2:
            ps_events = self._query_events_powershell(hours=hours)
            events.extend(ps_events)

        # 3. Дедупликация и сортировка от самых новых к старым
        unique_events: List[Dict[str, Any]] = []
        seen_keys = set()
        for ev in events:
            t = ev.get('timestamp', '')
            eid = ev.get('event_id', 0)
            prov = ev.get('provider', '')
            key = f'{t}_{eid}_{prov}'
            if key not in seen_keys:
                seen_keys.add(key)
                unique_events.append(ev)

        # Сортировка по времени (по убыванию)
        def _parse_ts(e: Dict[str, Any]) -> str:
            return e.get('timestamp', '')

        unique_events.sort(key=_parse_ts, reverse=True)
        return unique_events

    def _query_events_powershell(self, hours: int = 720) -> List[Dict[str, Any]]:
        """Fallback сбор событий через PowerShell Get-WinEvent."""
        if os.name != 'nt':
            return []

        ids_str = ','.join(str(k) for k in TARGET_EVENT_IDS.keys())
        ps_script = f"""
        $ErrorActionPreference = 'SilentlyContinue'
        $startTime = (Get-Date).AddHours(-{hours})
        $filter = @{{
            LogName = 'System', 'Application'
            Id = @({ids_str})
            StartTime = $startTime
        }}
        $events = Get-WinEvent -FilterHashtable $filter -MaxEvents 300
        $result = @()
        foreach ($e in $events) {{
            $result += [PSCustomObject]@{{
                timestamp = $e.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                event_id = $e.Id
                provider = $e.ProviderName
                level = $e.LevelDisplayName
                message = $e.Message
                event_data = @{{}}
            }}
        }}
        $result | ConvertTo-Json -Depth 3 -Compress
        """
        try:
            res = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=12,
            )
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
        except Exception as ex:
            logger.debug(f'Ошибка выполнения PowerShell для событий перезагрузки: {ex}')
        return []

    def _correlate_events_into_sessions(
        self,
        events: List[Dict[str, Any]],
        limit: int = 20,
    ) -> List[RebootSession]:
        """Связывает сырые события в структурированные сессии перезагрузок."""
        # Находим маркеры запуска ОС (Event 12, Event 6005, или Event 41 как признак нового старта)
        boot_events: List[Dict[str, Any]] = []
        for ev in events:
            eid = int(ev.get('event_id', 0))
            if eid in (12, 6005, 41):
                boot_events.append(ev)

        # Если маркеров старта нет, но есть события выключения (1074, 6006, 13), группируем вокруг них
        if not boot_events:
            for ev in events:
                eid = int(ev.get('event_id', 0))
                if eid in (1074, 6006, 13, 6008):
                    boot_events.append(ev)

        # Кластеризация событий по сессиям
        sessions: List[RebootSession] = []
        session_idx = 1

        # Отслеживаем временные границы сессий
        processed_boots = set()

        for boot_ev in boot_events:
            boot_time_str = boot_ev.get('timestamp', '')
            if not boot_time_str:
                continue

            # Нормализация времени для дедупликации близких меток старта (в пределах 2 минут)
            boot_dt = self._parse_iso_time(boot_time_str)
            if not boot_dt:
                continue

            is_duplicate = False
            for seen_dt in processed_boots:
                if abs((boot_dt - seen_dt).total_seconds()) < 120:
                    is_duplicate = True
                    break
            if is_duplicate:
                continue

            processed_boots.add(boot_dt)

            # Находим события в окне [-15 мин; +3 мин] вокруг момента старта / выключения
            window_start = boot_dt - timedelta(minutes=15)
            window_end = boot_dt + timedelta(minutes=3)

            session_events = [
                ev for ev in events
                if self._is_time_in_window(ev.get('timestamp', ''), window_start, window_end)
            ]

            session = self._analyze_session_window(boot_dt, session_events, session_idx)
            sessions.append(session)
            session_idx += 1

            if len(sessions) >= limit:
                break

        # Рассчитываем uptime между последовательными сессиями
        for i in range(len(sessions)):
            curr = sessions[i]
            if i + 1 < len(sessions):
                prev = sessions[i + 1]
                curr.previous_boot_time = prev.boot_time
                prev_dt = self._parse_iso_time(prev.boot_time)
                curr_dt = self._parse_iso_time(curr.boot_time)
                if prev_dt and curr_dt and curr_dt > prev_dt:
                    diff_sec = (curr_dt - prev_dt).total_seconds()
                    curr.uptime_seconds = round(diff_sec, 1)
                    curr.uptime_human = self._format_duration(diff_sec)

        return sessions

    def _analyze_session_window(
        self,
        boot_dt: datetime,
        window_events: List[Dict[str, Any]],
        session_idx: int,
    ) -> RebootSession:
        """Анализирует события в окне сессии и строит вывод о причине перезагрузки."""
        boot_id = f"reboot-{boot_dt.strftime('%Y%m%d-%H%M%S')}"
        boot_time_str = boot_dt.strftime('%Y-%m-%d %H:%M:%S')

        # Извлечение специфических событий
        ev_1074 = self._find_event(window_events, 1074)
        ev_41 = self._find_event(window_events, 41)
        ev_6008 = self._find_event(window_events, 6008)
        ev_1001 = self._find_event(window_events, 1001)
        ev_19 = self._find_event(window_events, 19)
        ev_7045 = self._find_event(window_events, 7045)
        ev_109 = self._find_event(window_events, 109)

        evidence: List[str] = []
        events_chain: List[RebootCorrelatedEvent] = []

        for ev in window_events:
            eid = int(ev.get('event_id', 0))
            prov = ev.get('provider', '')
            desc = TARGET_EVENT_IDS.get(eid, (prov, 'Системное событие'))[1]
            events_chain.append(
                RebootCorrelatedEvent(
                    event_id=eid,
                    provider=prov or 'System',
                    timestamp=ev.get('timestamp', ''),
                    level=ev.get('level') or 'Information',
                    description=desc,
                    details=ev.get('event_data') or {},
                )
            )

        # 1. Извлечение полей из Event 1074 (User32)
        initiating_proc = None
        initiating_user = None
        shutdown_action = None
        reason_text = None
        reason_code = None

        if ev_1074:
            msg = ev_1074.get('message', '')
            data = ev_1074.get('event_data', {})
            initiating_proc = data.get('param1') or self._extract_regex(msg, r'process\s+([^\s]+)\s+has', r'процесс\s+([^\s]+)\s+инициировал')
            initiating_user = data.get('param7') or data.get('param2') or self._extract_regex(msg, r'on behalf of user\s+([^\s]+)', r'от имени пользователя\s+([^\s]+)')
            shutdown_action = data.get('param5') or self._extract_regex(msg, r'Shutdown Type:\s*([^\r\n]+)', r'Тип выключения:\s*([^\r\n]+)')
            reason_text = data.get('param3') or self._extract_regex(msg, r'following reason:\s*([^\r\n]+)', r'следующей причине:\s*([^\r\n]+)')
            reason_code = data.get('param4') or self._extract_regex(msg, r'Reason Code:\s*([0-9a-fx]+)', r'Код причины:\s*([0-9a-fx]+)')
            evidence.append(f'Event 1074 (User32): Инициатор={initiating_proc or "N/A"}, Пользователь={initiating_user or "N/A"}, Действие={shutdown_action or "restart"}')
            if reason_code:
                decoded_reason = format_system_error(reason_code)
                if decoded_reason:
                    evidence.append(f'Код причины {reason_code}: {decoded_reason}')

        # 2. Извлечение полей из Event 41 (Kernel-Power)
        bugcheck_code = None
        bugcheck_params: List[str] = []
        power_button_ts = None

        if ev_41:
            data = ev_41.get('event_data', {})
            bc_raw = data.get('BugcheckCode', '0')
            try:
                bc_int = int(bc_raw)
                if bc_int != 0:
                    bugcheck_code = f'0x{bc_int:08X}'
            except ValueError:
                pass
            p_btn = data.get('PowerButtonTimestamp', '0')
            try:
                p_btn_int = int(p_btn)
                if p_btn_int > 0:
                    power_button_ts = p_btn_int
            except ValueError:
                pass
            for i in range(1, 5):
                p_val = data.get(f'BugcheckParameter{i}')
                if p_val:
                    bugcheck_params.append(str(p_val))
            evidence.append(f'Event 41 (Kernel-Power): BugCheck={bugcheck_code or "none"}, PowerButtonTS={power_button_ts or "none"}')

        # 3. Извлечение полей из Event 6008 (EventLog)
        if ev_6008:
            evidence.append('Event 6008 (EventLog): Неожиданное завершение предыдущей сессии')

        # 4. Извлечение полей из Event 1001 (BSOD / WER)
        if ev_1001:
            msg = ev_1001.get('message', '')
            bc_match = self._extract_regex(msg, r'0x[0-9a-fA-F]{8}')
            if bc_match and not bugcheck_code:
                bugcheck_code = bc_match
            evidence.append(f'Event 1001 (WER/BugCheck): Зафиксирован аварийный дамп {bugcheck_code or ""}')

        # 5. Извлечение полей из Event 19 (WindowsUpdateClient)
        kb_number = None
        if ev_19:
            msg = ev_19.get('message', '')
            kb_number = self._extract_regex(msg, r'KB\d+')
            evidence.append(f'Event 19 (WindowsUpdateClient): Установка обновления {kb_number or "KB"}')

        # 6. Извлечение полей из Event 7045 (SCM)
        service_name = None
        if ev_7045:
            msg = ev_7045.get('message', '')
            service_name = self._extract_regex(msg, r'Service Name:\s*([^\r\n]+)', r'Имя службы:\s*([^\r\n]+)')
            evidence.append(f'Event 7045 (SCM): Установка службы {service_name or "Unknown"}')

        # -------------------------------------------------------------
        # Дерево принятия решений (Decision Gate) для классификации
        # -------------------------------------------------------------
        shutdown_type = ShutdownType.UNKNOWN
        likely_class = 'unknown'
        conclusion = ''

        # Сценарий А: BSOD / Синий экран
        if ev_1001 or (bugcheck_code and bugcheck_code != '0x00000000'):
            shutdown_type = ShutdownType.CRASH_BSOD
            likely_class = 'bsod_crash'
            bc_info = decode_bugcheck_code(bugcheck_code) if bugcheck_code else {}
            sym = bc_info.get('symbol')
            desc = bc_info.get('description_ru')
            if sym and sym != 'UNKNOWN_BUGCHECK':
                conclusion = f'Критический сбой операционной системы (BSOD): {sym} ({bugcheck_code}) — {desc}'
            elif desc and desc != 'Критический сбой ядра Windows.':
                conclusion = f'Критический сбой операционной системы (BSOD): {bugcheck_code} — {desc}'
            else:
                conclusion = f'Критический сбой операционной системы (BSOD). Код ошибки: {bugcheck_code or "Неизвестен"}.'

        # Сценарий Б: Принудительное выключение физической кнопкой питания
        elif power_button_ts and power_button_ts > 0:
            shutdown_type = ShutdownType.HARDWARE_POWER_BUTTON
            likely_class = 'hardware_power_button'
            conclusion = 'Принудительное выключение долгим нажатием аппаратной кнопки питания.'

        # Сценарий В: Внезапное отключение электропитания / зависание (Event 41 / 6008 без 1074)
        elif (ev_41 or ev_6008) and not ev_1074:
            shutdown_type = ShutdownType.DIRTY_POWER_LOSS
            likely_class = 'dirty_power_loss'
            conclusion = 'Внезапная потеря электропитания или мгновенный аппаратный сброс без сохранения состояния.'

        # Сценарий Г: Плановый рестарт после обновления Windows Update
        elif ev_1074 and (
            ev_19
            or (initiating_proc and any(k in initiating_proc.lower() for k in ('svchost', 'trustedinstaller', 'tiworker', 'wuauclt')))
            or (reason_text and any(k in reason_text.lower() for k in ('update', 'обновлен', 'security', 'безопасн')))
            or (reason_code and '80020010' in reason_code.lower())
        ):
            shutdown_type = ShutdownType.UPDATE_RESTART
            likely_class = 'update_related_restart'
            kb_str = f' ({kb_number})' if kb_number else ''
            conclusion = f'Плановый перезапуск службы обновления Windows Update{kb_str} от имени {initiating_user or "SYSTEM"}.'

        # Сценарий Д: Перезапуск после установки программы / службы
        elif ev_1074 and (ev_7045 or (reason_text and any(k in reason_text.lower() for k in ('install', 'установк', 'установ')))):
            shutdown_type = ShutdownType.PLANNED
            likely_class = 'software_installation_restart'
            svc_str = f' (служба: {service_name})' if service_name else ''
            conclusion = f'Плановый перезапуск после инсталляции программного обеспечения{svc_str}.'

        # Сценарий Е: Пользовательское штатное выключение / перезапуск
        elif ev_1074:
            shutdown_type = ShutdownType.USER_INITIATED if (initiating_proc and 'explorer' in initiating_proc.lower()) else ShutdownType.PLANNED
            likely_class = 'planned_clean_reboot'
            act = shutdown_action or 'перезапуск'
            conclusion = f'Штатный {act} инициирован процессом {initiating_proc or "Система"} (пользователь: {initiating_user or "Пользователь"}).'

        # Сценарий Ж: Быстрый запуск / Fast Startup (Kernel-Power 109)
        elif ev_109:
            shutdown_type = ShutdownType.HYBRID_SHUTDOWN
            likely_class = 'hybrid_fast_startup'
            conclusion = 'Штатное завершение работы в режиме гибридного сна (Fast Startup / Hiberboot).'

        # Fallback по умолчанию: Корректный перезапуск
        else:
            shutdown_type = ShutdownType.PLANNED
            likely_class = 'clean_restart'
            conclusion = 'Штатный запуск операционной системы без зафиксированных системных ошибок.'

        return RebootSession(
            boot_id=boot_id,
            boot_time=boot_time_str,
            shutdown_type=shutdown_type,
            likely_class=likely_class,
            conclusion=conclusion,
            initiating_process=initiating_proc,
            initiating_user=initiating_user,
            shutdown_action=shutdown_action,
            reason_text=reason_text,
            reason_code=reason_code,
            bugcheck_code=bugcheck_code,
            bugcheck_params=bugcheck_params,
            power_button_timestamp=power_button_ts,
            windows_update_kb=kb_number,
            service_installed=service_name,
            evidence=evidence,
            events_chain=events_chain,
        )

    def _find_event(self, events: List[Dict[str, Any]], target_id: int) -> Optional[Dict[str, Any]]:
        """Находит первое событие с заданным ID среди списка."""
        for e in events:
            if int(e.get('event_id', 0)) == target_id:
                return e
        return None

    def _extract_regex(self, text: str, *patterns: str) -> Optional[str]:
        """Извлекает подстроку по первому совпавшему регулярному выражению."""
        if not text:
            return None
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0).strip()
        return None

    def _parse_iso_time(self, ts_str: str) -> Optional[datetime]:
        """Парсинг строки времени в datetime UTC."""
        if not ts_str:
            return None
        clean_ts = ts_str.replace('Z', '').split('.')[0]
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d.%m.%Y %H:%M:%S'):
            try:
                dt = datetime.strptime(clean_ts, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    def _is_time_in_window(self, ts_str: str, start: datetime, end: datetime) -> bool:
        """Проверяет, попадает ли временная метка в заданный интервал."""
        dt = self._parse_iso_time(ts_str)
        if not dt:
            return False
        return start <= dt <= end

    def _format_duration(self, seconds: Optional[float]) -> str:
        """Форматирует секунды в читаемый вид (напр. '7h 25m')."""
        if seconds is None or seconds < 0:
            return 'N/A'
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f'{days}д {hours}ч {mins}м'
        if hours > 0:
            return f'{hours}ч {mins}м'
        return f'{mins}м {secs}с'
