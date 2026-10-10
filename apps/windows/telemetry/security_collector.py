# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Security Collector
# =============================================================================
# Description:
#   Коллектор событий журнала безопасности Windows Security Event Log.
#   Реализует инкрементальный сбор на основе закладок (Bookmark), XPath-фильтрацию,
#   нормализацию и корреляцию с телеметрией системы.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.security_collector import WindowsSecurityCollector
#
#     collector = WindowsSecurityCollector()
#     status = collector.check_access_and_audit()
#     report = collector.collect_incremental(batch_size=200)
#
# File: security_collector.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:40:00
# =============================================================================

from __future__ import annotations
"""Коллектор событий журнала безопасности Windows Security Event Log и Microsoft Defender."""

import os
import sys
import time
import winreg
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import (
    SecurityAuditStatus,
    SecurityBookmarkState,
    SecurityCollectorReport,
    SecurityCorrelationItem,
    SecurityEventItem,
    SecurityEventRaw,
)
from .security_normalizer import SecurityEventNormalizer
from .sqlite import TelemetryStorage
from .win32_ffi.wevtapi import WevtAPI


DEFAULT_SECURITY_EVENT_IDS: List[int] = [
    4624,  # Успешный вход
    4625,  # Неудачный вход
    4634,  # Завершение logon
    4647,  # Пользователь инициировал logoff
    4672,  # Специальные привилегии
    4688,  # Создание процесса
    4689,  # Завершение процесса
    4697,  # Установка службы
    4698,  # Создание Scheduled Task
    4702,  # Изменение Scheduled Task
    4719,  # Изменение аудита
    4720,  # Создание пользователя
    4722,  # Включение пользователя
    4723,  # Попытка изменения пароля
    4724,  # Сброс пароля
    4725,  # Отключение пользователя
    4726,  # Удаление пользователя
    4732,  # Добавление в локальную группу
    4738,  # Изменение пользователя
    4740,  # Блокировка пользователя
    4768,  # Kerberos TGT
    4769,  # Kerberos service ticket
    4771,  # Kerberos pre-auth failure
    4776,  # NTLM authentication
    1102,  # Очищен Security log
]

DEFENDER_CHANNEL: str = 'Microsoft-Windows-Windows Defender/Operational'

DEFAULT_DEFENDER_EVENT_IDS: List[int] = [
    1000,  # Запуск сканирования
    1001,  # Завершение сканирования
    1002,  # Отмена сканирования
    1005,  # Пауза сканирования
    1013,  # Очистка истории угроз
    1116,  # Обнаружение вредоносной программы / угрозы
    1117,  # Выполнение действия по угрозе (Quarantine/Clean/Block)
    1118,  # Сбой действия по угрозе
    1119,  # Критическая ошибка
    1121,  # Блокировка CFA (Controlled Folder Access)
    1122,  # Аудит CFA
    1123,  # Блокировка ASR (Attack Surface Reduction)
    1124,  # Аудит ASR
    1127,  # Блокировка Network Protection
    1128,  # Аудит Network Protection
    1150,  # Служба защиты работает штатно (Healthy)
    1151,  # Отчет о работоспособности компонентов
    2000,  # Обновление сигнатур успешно
    2001,  # Ошибка обновления сигнатур
    2010,  # Облачная защита/аналитика
    5000,  # Включение защиты в реальном времени
    5001,  # Отключение защиты в реальном времени
    5004,  # Изменение конфигурации
    5007,  # Изменение параметров защиты
]


class WindowsSecurityCollector:
    """Инкрементальный сборщик событий безопасности Windows (Security.evtx и Defender Operational)."""

    def __init__(
        self,
        storage: Optional[TelemetryStorage] = None,
        wevtapi: Optional[WevtAPI] = None,
        normalizer: Optional[SecurityEventNormalizer] = None,
    ) -> None:
        """Инициализация сборщика безопасности.

        Args:
            storage: Экземпляр хранилища TelemetryStorage (если None, берется синглтон).
            wevtapi: Экземпляр обертки WevtAPI.
            normalizer: Экземпляр нормализатора событий.
        """
        self.storage = storage or TelemetryStorage.get_instance()
        self.wevtapi = wevtapi or WevtAPI()
        self.normalizer = normalizer or SecurityEventNormalizer()

    def check_access_and_audit(self) -> SecurityAuditStatus:
        """Проверить доступность журнала Security и статус политик аудита.

        Returns:
            SecurityAuditStatus: Структурированный статус прав и настроек.
        """
        access_info = self.wevtapi.check_channel_access('Security')
        accessible = access_info.get('accessible', False)
        record_count = access_info.get('record_count', 0)
        error_msg = access_info.get('error')

        # Проверка включения аудита командной строки в реестре
        cmdline_audit = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit',
                0,
                winreg.KEY_READ,
            ) as key:
                val, _ = winreg.QueryValueEx(key, 'ProcessCreationIncludeCmdLine_Enabled')
                cmdline_audit = bool(val)
        except OSError:
            cmdline_audit = False

        # Получаем статистику из базы данных
        stats = self.storage.get_security_stats() if self.storage else {}
        last_rec = stats.get('max_record_id', 0)
        total_ingested = stats.get('total_events', 0)

        return SecurityAuditStatus(
            accessible=accessible,
            record_count=record_count,
            process_creation_audit_enabled=True,  # Базовый аудит включен в современных редакциях Windows
            command_line_audit_enabled=cmdline_audit,
            error=error_msg,
            last_record_id=last_rec,
            total_ingested_events=total_ingested,
        )

    def _build_xpath_query(
        self,
        channel: str = 'Security',
        event_ids: Optional[List[int]] = None,
    ) -> str:
        """Построить эффективный XPath фильтр для выборки целевых Event ID.

        Предотвращает переполнение предиката Win32 WevtAPI (код 15001) при длинных списках,
        используя диапазонную фильтрацию.
        """
        if event_ids is None:
            if 'Defender' in channel:
                return (
                    '*[System[((EventID >= 1000 and EventID <= 1160) or '
                    '(EventID >= 2000 and EventID <= 2020) or '
                    '(EventID >= 5000 and EventID <= 5020))]]'
                )
            # Стандартный диапазон охватывает все ключевые события аудита безопасности (4624-4776 + 1102)
            return '*[System[(EventID >= 4624 and EventID <= 4776) or EventID=1102]]'
        if not event_ids:
            return '*'
        if len(event_ids) <= 15:
            clauses = ' or '.join(f'EventID={eid}' for eid in event_ids)
            return f'*[System[({clauses})]]'
        min_id = min(event_ids)
        max_id = max(event_ids)
        return f'*[System[(EventID >= {min_id} and EventID <= {max_id})]]'

    def collect_incremental(
        self,
        channel: str = 'Security',
        batch_size: int = 500,
        max_records: int = 5000,
        filter_event_ids: Optional[List[int]] = None,
        save_raw: bool = False,
    ) -> SecurityCollectorReport:
        """Выполнить инкрементальный сбор новых событий из указанного журнала (Security или Defender).

        Args:
            channel: Имя канала ('Security' или 'Microsoft-Windows-Windows Defender/Operational').
            batch_size: Размер порции за один вызов EvtNext.
            max_records: Максимальное количество событий для сбора за один вызов.
            filter_event_ids: Список опрашиваемых Event ID или None для дефолтного набора.
            save_raw: Сохранять ли параллельно сырой XML в security_events_raw.

        Returns:
            SecurityCollectorReport: Отчет о результатах сбора.
        """
        report = SecurityCollectorReport(channel=channel)

        # Проверка доступа к журналу
        access_info = self.wevtapi.check_channel_access(channel)
        if not access_info.get('accessible', False):
            err = access_info.get('error') or f'Доступ к каналу {channel} запрещен'
            report.errors.append(err)
            logger.warning(f'[SecurityCollector] {err}')
            return report

        # Загрузка сохраненной закладки
        bm_dict = self.storage.get_security_bookmark(channel) if self.storage else None
        bookmark_xml = bm_dict.get('bookmark_xml') if bm_dict else None
        last_saved_record_id = bm_dict.get('last_record_id', 0) if bm_dict else 0

        xpath = self._build_xpath_query(channel=channel, event_ids=filter_event_ids)
        collected_items: List[SecurityEventItem] = []
        collected_raw: List[SecurityEventRaw] = []
        events_by_id: Dict[int, int] = {}
        max_record_id = last_saved_record_id
        latest_timestamp = ''
        total_fetched = 0

        # Если закладки еще нет (первый запуск), читаем исторический хвост последних событий в обратном порядке
        if not bookmark_xml:
            tail_limit = min(batch_size, max_records)
            events_raw, init_bm, highest_rec_id = self.wevtapi.read_events_incremental(
                channel=channel,
                query_xpath=xpath,
                bookmark_xml=None,
                batch_size=tail_limit,
                format_message=False,
                forward=False,
            )
            # Разворачиваем в хронологический порядок
            events_raw = list(reversed(events_raw))
            bookmark_xml = init_bm
            max_record_id = highest_rec_id

            for raw_dict in events_raw:
                item, raw_item = self.normalizer.normalize_event(raw_dict, extract_raw=save_raw)
                collected_items.append(item)
                if raw_item:
                    collected_raw.append(raw_item)
                events_by_id[item.event_id] = events_by_id.get(item.event_id, 0) + 1
                if item.timestamp:
                    latest_timestamp = item.timestamp
                rec_id = item.event_record_id
                if rec_id > max_record_id:
                    max_record_id = rec_id

            if self.storage and collected_items:
                self.storage.save_security_events(collected_items, save_raw=save_raw, raw_events=collected_raw)
                if bookmark_xml:
                    self.storage.save_security_bookmark(
                        channel=channel,
                        last_record_id=max_record_id,
                        bookmark_xml=bookmark_xml,
                        last_timestamp=latest_timestamp,
                    )
            total_fetched += len(events_raw)

        # Последующие запуски (или продолжение) читают строго вперед от закладки
        while total_fetched < max_records and bookmark_xml:
            cur_batch_limit = min(batch_size, max_records - total_fetched)
            events_raw, new_bookmark_xml, highest_rec_id = self.wevtapi.read_events_incremental(
                channel=channel,
                query_xpath=xpath,
                bookmark_xml=bookmark_xml,
                batch_size=cur_batch_limit,
                format_message=False,
                forward=True,
            )

            if not events_raw:
                break

            batch_items: List[SecurityEventItem] = []
            batch_raw: List[SecurityEventRaw] = []

            for raw_dict in events_raw:
                item, raw_item = self.normalizer.normalize_event(raw_dict, extract_raw=save_raw)
                batch_items.append(item)
                if raw_item:
                    batch_raw.append(raw_item)
                events_by_id[item.event_id] = events_by_id.get(item.event_id, 0) + 1
                if item.timestamp:
                    latest_timestamp = item.timestamp
                rec_id = item.event_record_id
                if rec_id > max_record_id:
                    max_record_id = rec_id

            if highest_rec_id > max_record_id:
                max_record_id = highest_rec_id

            # Сохраняем порцию в SQLite
            if self.storage and batch_items:
                self.storage.save_security_events(batch_items, save_raw=save_raw, raw_events=batch_raw)
                if new_bookmark_xml:
                    self.storage.save_security_bookmark(
                        channel=channel,
                        last_record_id=max_record_id,
                        bookmark_xml=new_bookmark_xml,
                        last_timestamp=latest_timestamp,
                    )

            collected_items.extend(batch_items)
            if save_raw:
                collected_raw.extend(batch_raw)

            total_fetched += len(events_raw)
            bookmark_xml = new_bookmark_xml

            # Если вернулось меньше запрошенного batch_size, значит достигли текущего конца журнала
            if len(events_raw) < cur_batch_limit:
                break

        report.total_events_ingested = len(collected_items)
        report.last_record_id = max_record_id
        report.bookmark_xml = bookmark_xml
        report.events_by_id = events_by_id
        report.events = collected_items[:100]  # Ограничиваем возвращаемый срез в отчете

        logger.info(
            f'[SecurityCollector] Инкрементально собрано {len(collected_items)} событий канала {channel}. '
            f'Последний RecordID: {max_record_id}'
        )
        return report

    def collect_defender_events(
        self,
        batch_size: int = 200,
        max_records: int = 2000,
        filter_event_ids: Optional[List[int]] = None,
        save_raw: bool = False,
    ) -> SecurityCollectorReport:
        """Выполнить инкрементальный сбор новых событий Microsoft Defender (Defender/Operational).

        Args:
            batch_size: Размер порции за один вызов.
            max_records: Максимальное число событий за запуск.
            filter_event_ids: Опциональный список Event ID.
            save_raw: Сохранять ли сырой XML.

        Returns:
            SecurityCollectorReport: Отчет с собранными событиями Defender.
        """
        return self.collect_incremental(
            channel=DEFENDER_CHANNEL,
            batch_size=batch_size,
            max_records=max_records,
            filter_event_ids=filter_event_ids,
            save_raw=save_raw,
        )

    def collect_all_security_and_defender(
        self,
        batch_size: int = 500,
        max_records: int = 2000,
        save_raw: bool = False,
    ) -> Dict[str, SecurityCollectorReport]:
        """Инкрементально собрать события обоих журналов: Security и Defender.

        Args:
            batch_size: Размер выборки.
            max_records: Лимит событий на канал.
            save_raw: Сохранение сырого XML.

        Returns:
            Dict[str, SecurityCollectorReport]: Отчеты по каждому каналу.
        """
        sec_rep = self.collect_incremental(
            channel='Security',
            batch_size=batch_size,
            max_records=max_records,
            save_raw=save_raw,
        )
        def_rep = self.collect_defender_events(
            batch_size=batch_size,
            max_records=max_records,
            save_raw=save_raw,
        )
        return {
            'Security': sec_rep,
            DEFENDER_CHANNEL: def_rep,
        }

    def get_live_tail(
        self,
        limit: int = 20,
        event_id: Optional[int] = None,
        search: str = '',
        channel: str = 'Security',
    ) -> List[SecurityEventItem]:
        """Получить самые свежие события безопасности в реальном времени (live tail).

        Args:
            limit: Количество событий.
            event_id: Опциональный фильтр по Event ID.
            search: Поисковая подстрока.
            channel: Канал ('Security' или DEFENDER_CHANNEL).

        Returns:
            List[SecurityEventItem]: Список нормализованных событий.
        """
        raw_events = self.wevtapi.read_events(
            channel=channel,
            limit=limit,
            event_id=event_id or 0,
            search=search,
            format_message=False,
        )
        items: List[SecurityEventItem] = []
        for raw in raw_events:
            item, _ = self.normalizer.normalize_event(raw, extract_raw=False)
            items.append(item)
        return items

    def subscribe_defender_stream(
        self,
        callback: Callable[[SecurityEventItem], None],
        filter_event_ids: Optional[List[int]] = None,
    ) -> Optional[Any]:
        """Оформить потоковую подписку на входящие события Microsoft Defender.

        Args:
            callback: Функция обратного вызова при возникновении события.
            filter_event_ids: Список Event ID для фильтрации.

        Returns:
            Optional[HANDLE]: Дескриптор подписки или None.
        """
        xpath = self._build_xpath_query(channel=DEFENDER_CHANNEL, event_ids=filter_event_ids)

        def _on_event(raw_dict: Dict[str, Any]) -> None:
            item, raw_item = self.normalizer.normalize_event(raw_dict, extract_raw=True)
            if self.storage:
                self.storage.save_security_events([item], save_raw=True, raw_events=[raw_item] if raw_item else None)
            callback(item)

        return self.wevtapi.subscribe_events(
            channel=DEFENDER_CHANNEL,
            query_xpath=xpath,
            callback=_on_event,
            start_at_oldest=False,
        )

    def subscribe_stream(
        self,
        callback: Callable[[SecurityEventItem], None],
        filter_event_ids: Optional[List[int]] = None,
    ) -> Optional[Any]:
        """Оформить потоковую подписку на входящие события безопасности через EvtSubscribe.

        Args:
            callback: Функция обратного вызова при получении события.
            filter_event_ids: Список Event ID для фильтрации.

        Returns:
            Optional[HANDLE]: Дескриптор подписки или None.
        """
        xpath = self._build_xpath_query(filter_event_ids)

        def _on_event(raw_dict: Dict[str, Any]) -> None:
            item, raw_item = self.normalizer.normalize_event(raw_dict, extract_raw=True)
            if self.storage:
                self.storage.save_security_events([item], save_raw=True, raw_events=[raw_item] if raw_item else None)
            callback(item)

        return self.wevtapi.subscribe_events(
            channel='Security',
            query_xpath=xpath,
            callback=_on_event,
            start_at_oldest=False,
        )

    def correlate_security_with_telemetry(
        self,
        time_window_seconds: float = 60.0,
        pid: Optional[int] = None,
        user: Optional[str] = None,
        limit: int = 50,
    ) -> List[SecurityCorrelationItem]:
        """Выполнить корреляцию событий безопасности с метриками телеметрии и процессами.

        Связывает события создания процессов (4688), входов пользователей (4624) и
        событий служб (4697) с реальной загрузкой CPU/RAM/диска и снимками процессов.

        Args:
            time_window_seconds: Временное окно корреляции в секундах.
            pid: Фильтр по PID.
            user: Фильтр по пользователю.
            limit: Лимит записей.

        Returns:
            List[SecurityCorrelationItem]: Список коррелированных событий с аналитикой.
        """
        if not self.storage:
            return []

        # 1. Извлекаем события безопасности
        sec_events = self.storage.get_security_events(
            user=user,
            pid=pid,
            limit=limit,
        )
        if not sec_events:
            return []

        # 2. Извлекаем последние снимки системы
        snapshots = self.storage.get_snapshots(limit=30)
        snap_by_time = {s.get('timestamp', ''): s for s in snapshots}

        correlations: List[SecurityCorrelationItem] = []

        for ev in sec_events:
            eid = int(ev.get('event_id', 0) or 0)
            p_name = ev.get('process_name', '')
            p_short = p_name.replace('\\', '/').split('/')[-1] if p_name else ''
            p_pid = int(ev.get('process_id', 0) or 0)
            u_name = ev.get('subject_user', '') or ev.get('target_user', '')
            ts = ev.get('timestamp', '')
            cmd = ev.get('command_line', '')
            parent_name = ev.get('parent_process_name', '')
            parent_short = parent_name.replace('\\', '/').split('/')[-1] if parent_name else ''

            notes: List[str] = []
            cpu_val: Optional[float] = None
            ram_val: Optional[float] = None
            disk_spike = False
            net_spike = False

            # Поиск близкого по времени снимка телеметрии
            for s_ts, snap in snap_by_time.items():
                if ts and s_ts and abs(len(ts) - len(s_ts)) < 5:
                    cpu_total = float(snap.get('cpu_total_percent', 0.0) or 0.0)
                    if cpu_total > 50.0:
                        cpu_val = cpu_total
                        notes.append(f'Повышенная загрузка CPU системы в момент события: {cpu_total:.1f}%')

                    d_write = float(snap.get('disk_write_bytes_sec', 0.0) or 0.0)
                    if d_write > 50 * 1024 * 1024:
                        disk_spike = True
                        notes.append(f'Всплеск дисковой записи: {d_write / 1024 / 1024:.1f} МБ/с')

                    n_recv = float(snap.get('network_recv_bytes_sec', 0.0) or 0.0)
                    if n_recv > 10 * 1024 * 1024:
                        net_spike = True
                        notes.append(f'Всплеск сетевого трафика: {n_recv / 1024 / 1024:.1f} МБ/с')
                    break

            if eid == 4688:
                ev_type = 'ProcessCreate'
                if parent_short and ('powershell' in parent_short.lower() or 'cmd' in parent_short.lower()):
                    notes.append(f'Запуск из интерактивной оболочки {parent_short}')
                if 'admin' in u_name.lower() or ev.get('elevated_token') == 1:
                    notes.append('Запуск с повышенными привилегиями (Elevated Token)')
            elif eid == 4624:
                ev_type = 'UserLogon'
                ltype = ev.get('logon_type')
                if ltype == 10:
                    notes.append('Удаленный вход по протоколу RDP (LogonType 10)')
                elif ltype == 2:
                    notes.append('Локальный интерактивный вход (LogonType 2)')
                elif ltype == 3:
                    notes.append('Сетевой вход SMB/RPC (LogonType 3)')
            elif eid == 4625:
                ev_type = 'FailedLogon'
                notes.append(f"Неудачная попытка входа: {ev.get('status_code', '')}")
            elif eid == 4697:
                ev_type = 'ServiceInstall'
                notes.append(f"Установка новой службы {ev.get('object_name', '')}")
            else:
                ev_type = f'Event_{eid}'

            correlations.append(
                SecurityCorrelationItem(
                    timestamp=ts,
                    event_type=ev_type,
                    user=u_name,
                    process_name=p_short or p_name,
                    pid=p_pid,
                    parent_process_name=parent_short or parent_name,
                    command_line=cmd,
                    cpu_percent=cpu_val,
                    ram_mb=ram_val,
                    disk_spike=disk_spike,
                    network_spike=net_spike,
                    notes=notes,
                )
            )

        return correlations


__all__ = [
    'WindowsSecurityCollector',
    'DEFAULT_SECURITY_EVENT_IDS',
    'DEFAULT_DEFENDER_EVENT_IDS',
    'DEFENDER_CHANNEL',
]
