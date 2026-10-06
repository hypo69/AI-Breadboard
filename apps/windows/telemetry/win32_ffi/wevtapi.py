# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Win32_Ffi - Wevtapi
# =============================================================================
# Description:
#   Низкоуровневый интерфейс к wevtapi.dll для работы с журналами событий Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.win32_ffi.wevtapi import ChannelMetadata
#
#     service = ChannelMetadata()
#
# File: wevtapi.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.win32_ffi
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 06:52:00
# =============================================================================

from __future__ import annotations
"""Низкоуровневый интерфейс к wevtapi.dll для работы с журналами событий Windows."""

import ctypes
import ctypes.wintypes as wintypes
import struct
import sys
import winreg
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from logger import logger
EVT_QUERY_CHANNEL_PATH = 1
EVT_QUERY_FILE_PATH = 2
EVT_QUERY_REVERSE_DIRECTION = 512
EVT_RENDER_EVENT_XML = 1
CHANNEL_DESCRIPTIONS: Dict[str, str] = {'System': 'Системный журнал Windows: события ядра ОС, системных служб, драйверов устройств, сбоев питания и сетевого стека.', 'Application': 'Журнал приложений: события, предупреждения, сбои и ошибки пользовательских и серверных программ (Crash, Faults).', 'Security': 'Журнал безопасности: аудит входов в систему (Logon/Logoff), права доступа, повышение привилегий UAC и политики безопасности.', 'Setup': 'Журнал установки: логи процесса установки операционной системы, обновлений Windows и накопительных пакетов KB.', 'Microsoft-Windows-WindowsUpdateClient/Operational': 'Клиент обновления Windows Update: загрузка, верификация и установка патчей, исправления безопасности и драйверов.', 'Microsoft-Windows-Kernel-PnP/Configuration': 'Конфигурация оборудования Plug and Play: подключение новых устройств, установка драйверов, коды ошибок 10/43.', 'Microsoft-Windows-Kernel-Power/Operational': 'Питание ядра Windows: переходы в сон/гибернацию, сбои питания (Event 41), изменение состояний батареи и ACPI.', 'Microsoft-Windows-TaskScheduler/Operational': 'Планировщик заданий: запуск, завершение, сбои и выполнение фоновых регламентных задач Windows.', 'Microsoft-Windows-Windows Defender/Operational': 'Антивирус Microsoft Defender: обнаружение угроз, сканирование в реальном времени, обновление антивирусных сигнатур.', 'Microsoft-Windows-Hyper-V-Compute-Operational': 'Платформа виртуализации Hyper-V: жизненный цикл виртуальных машин, контейнеров WSL2 и виртуальных адаптеров.', 'Microsoft-Windows-Windows Firewall With Advanced Security/Firewall': 'Брандмауэр Windows: блокировки входящего/исходящего трафика, сетевые правила фильтрации и аномалии сокетов.', 'Microsoft-Windows-Diagnostics-Performance/Operational': 'Диагностика производительности: анализ времени загрузки Windows, выключения и зависания системных компонентов.', 'Microsoft-Windows-Bits-Client/Operational': 'Фоновая интеллектуальная служба передачи (BITS): загрузка файлов и обновлений по сети с контролем канала.', 'Microsoft-Windows-DNS-Client/Operational': 'DNS-клиент Windows: резолвинг доменных имен, таймауты DNS серверов и сетевые кэширования.', 'Microsoft-Windows-CodeIntegrity/Operational': 'Контроль целостности кода: проверка цифровых подписей драйверов и исполняемых системных файлов.', 'Microsoft-Windows-PowerShell/Operational': 'Исполнение скриптов PowerShell: запуск командлетов, сценариев автоматизации и модулей администрирования.', 'Microsoft-Windows-Sysmon/Operational': 'Microsoft System Monitor (Sysmon): глубокая телеметрия создания процессов (Event 1), сети (Event 3), файловых операций (11/23/26) и хэшей исполняемых файлов.'}

@dataclass
class ChannelMetadata:
    """Метаданные о канале журнала Windows."""
    channel_name: str
    display_name: str
    description: str = ''
    is_enabled: bool = True
    record_count: int = 0
    category: str = 'Windows Event Log'

class WevtAPI:
    """Ctypes-обертка для wevtapi.dll и реестра Windows Event Log."""

    def __init__(self) -> None:
        """Инициализация библиотеки wevtapi.dll."""
        self._available = False
        self.wevtapi: Optional[ctypes.WinDLL] = None
        self._publisher_cache: Dict[str, Optional[wintypes.HANDLE]] = {}
        if sys.platform == 'win32':
            try:
                self.wevtapi = ctypes.windll.LoadLibrary('wevtapi.dll')
                self._setup_signatures()
                self._available = True
            except Exception as ex:
                logger.debug(f'[WevtAPI] Не удалось загрузить wevtapi.dll: {ex}')

    def _setup_signatures(self) -> None:
        """Настройка типов аргументов и возвращаемых значений функций."""
        if not self.wevtapi:
            return
        self.wevtapi.EvtOpenChannelEnum.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.wevtapi.EvtOpenChannelEnum.restype = wintypes.HANDLE
        self.wevtapi.EvtNextChannelPath.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.wevtapi.EvtNextChannelPath.restype = wintypes.BOOL
        self.wevtapi.EvtClose.argtypes = [wintypes.HANDLE]
        self.wevtapi.EvtClose.restype = wintypes.BOOL
        self.wevtapi.EvtOpenLog.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
        self.wevtapi.EvtOpenLog.restype = wintypes.HANDLE
        self.wevtapi.EvtGetLogInfo.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
        self.wevtapi.EvtGetLogInfo.restype = wintypes.BOOL
        self.wevtapi.EvtQuery.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
        self.wevtapi.EvtQuery.restype = wintypes.HANDLE
        self.wevtapi.EvtNext.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self.wevtapi.EvtNext.restype = wintypes.BOOL
        self.wevtapi.EvtRender.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD)]
        self.wevtapi.EvtRender.restype = wintypes.BOOL
        self.wevtapi.EvtOpenPublisherMetadata.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.wevtapi.EvtOpenPublisherMetadata.restype = wintypes.HANDLE
        self.wevtapi.EvtFormatMessage.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.wevtapi.EvtFormatMessage.restype = wintypes.BOOL

    def is_available(self) -> bool:
        """Проверить доступность wevtapi.dll в текущей системе."""
        return self._available

    def get_channel_record_count(self, channel_name: str) -> int:
        """Мгновенно получить точное количество записей в канале через EvtGetLogInfo."""
        if not self._available or not self.wevtapi:
            return 0
        h_log = self.wevtapi.EvtOpenLog(None, channel_name, 1)
        if not h_log:
            return 0
        try:
            buf = (ctypes.c_byte * 128)()
            used = wintypes.DWORD(0)
            if self.wevtapi.EvtGetLogInfo(h_log, 5, 128, ctypes.byref(buf), ctypes.byref(used)):
                return struct.unpack('<Q', bytes(buf)[:8])[0]
        except Exception:
            pass
        finally:
            self.wevtapi.EvtClose(h_log)
        return 0

    def get_channel_description(self, channel_name: str) -> str:
        """Получить человекочитаемое описание назначения канала."""
        if channel_name in CHANNEL_DESCRIPTIONS:
            return CHANNEL_DESCRIPTIONS[channel_name]
        if 'Defender' in channel_name:
            return 'Журнал защитных механизмов, антивирусного сканирования и предотвращения вторжений Microsoft Defender.'
        if 'Kernel-Power' in channel_name:
            return 'Журнал управления электропитанием, состояний ACPI, спящего режима и аварийных отключений питания.'
        if 'Kernel-PnP' in channel_name:
            return 'Журнал конфигурации оборудования, обнаружения и инициализации устройств Plug and Play.'
        if 'WindowsUpdate' in channel_name:
            return 'Журнал службы обновлений Windows, загрузки пакетов KB и применения хотфиксов.'
        if 'TaskScheduler' in channel_name:
            return 'Журнал планировщика задач Windows, запуска автоматических фоновых процессов и триггеров.'
        if 'Hyper-V' in channel_name:
            return 'Журнал подсистемы виртуализации Hyper-V, WSL2 контейнеров и гостевых служб.'
        if 'PowerShell' in channel_name:
            return 'Журнал среды PowerShell, выполнения скриптов автоматизации и команд администрирования.'
        if 'Firewall' in channel_name:
            return 'Журнал сетевого брандмауэра Windows, правил сетевого экрана и событий фильтрации трафика.'
        if 'Storage' in channel_name or 'Disk' in channel_name:
            return 'Журнал дисковой подсистемы, контроллеров накопителей, томов NTFS/ReFS и файловой системы.'
        if 'Network' in channel_name or 'Wlan' in channel_name or 'NDIS' in channel_name:
            return 'Журнал сетевых интерфейсов, Wi-Fi соединений, сетевых адаптеров и стека TCP/IP.'
        if 'Audio' in channel_name or 'Sound' in channel_name:
            return 'Журнал аудиоподсистемы, службы Windows Audio и конечных звуковых устройств.'
        if 'Print' in channel_name or 'Spooler' in channel_name:
            return 'Журнал диспетчера очереди печати и драйверов принтеров.'
        if 'Bluetooth' in channel_name or 'BTH' in channel_name:
            return 'Журнал стека Bluetooth, сопряжения беспроводных устройств и протоколов передачи данных.'
        if 'USB' in channel_name:
            return 'Журнал контроллеров USB, хабов и подключенных внешних периферийных устройств.'
        return f"Специализированный системный журнал Windows для компонента '{channel_name}'."

    def enumerate_channels(self) -> List[ChannelMetadata]:
        """Получить исчерпывающий список всех каналов Windows Event Log с количеством записей."""
        channels: List[ChannelMetadata] = []
        seen: set[str] = set()
        classic = [('System', 'System (Системный)'), ('Application', 'Application (Приложения)'), ('Security', 'Security (Безопасность)'), ('Setup', 'Setup (Установка)'), ('Microsoft-Windows-WindowsUpdateClient/Operational', 'Windows Update Client'), ('Microsoft-Windows-Kernel-PnP/Configuration', 'Kernel PnP Configuration'), ('Microsoft-Windows-Kernel-Power/Operational', 'Kernel Power'), ('Microsoft-Windows-TaskScheduler/Operational', 'Task Scheduler'), ('Microsoft-Windows-Windows Defender/Operational', 'Windows Defender'), ('Microsoft-Windows-Hyper-V-Compute-Operational', 'Hyper-V Compute'), ('Microsoft-Windows-PowerShell/Operational', 'Windows PowerShell')]
        for cname, dname in classic:
            rec_cnt = self.get_channel_record_count(cname)
            channels.append(ChannelMetadata(channel_name=cname, display_name=dname, description=self.get_channel_description(cname), record_count=rec_cnt, is_enabled=True))
            seen.add(cname.lower())
        if self._available and self.wevtapi:
            try:
                h_enum = self.wevtapi.EvtOpenChannelEnum(None, 0)
                if h_enum:
                    buffer_size = 512
                    buf = ctypes.create_unicode_buffer(buffer_size)
                    used = wintypes.DWORD()
                    while True:
                        success = self.wevtapi.EvtNextChannelPath(h_enum, buffer_size, buf, ctypes.byref(used))
                        if not success:
                            err = ctypes.GetLastError()
                            if err == 122:
                                buffer_size = used.value + 10
                                buf = ctypes.create_unicode_buffer(buffer_size)
                                continue
                            break
                        chan_str = buf.value.strip()
                        if chan_str and chan_str.lower() not in seen:
                            rec_cnt = self.get_channel_record_count(chan_str)
                            channels.append(ChannelMetadata(channel_name=chan_str, display_name=chan_str, description=self.get_channel_description(chan_str), record_count=rec_cnt, is_enabled=True))
                            seen.add(chan_str.lower())
                    self.wevtapi.EvtClose(h_enum)
            except Exception as ex:
                logger.debug(f'[WevtAPI] Ошибка при перечислении через EvtOpenChannelEnum: {ex}')
        try:
            reg_channels = self._enumerate_registry_channels()
            for r_chan in reg_channels:
                if r_chan.lower() not in seen:
                    rec_cnt = self.get_channel_record_count(r_chan)
                    channels.append(ChannelMetadata(channel_name=r_chan, display_name=r_chan, description=self.get_channel_description(r_chan), record_count=rec_cnt, is_enabled=True))
                    seen.add(r_chan.lower())
        except Exception as ex:
            logger.debug(f'[WevtAPI] Ошибка чтения каналов из реестра: {ex}')
        return channels

    def _enumerate_registry_channels(self) -> List[str]:
        """Считать имена зарегистрированных каналов из реестра Windows."""
        res: List[str] = []
        key_path = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WINEVT\\Channels'
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                num_subkeys, _, _ = winreg.QueryInfoKey(key)
                for i in range(num_subkeys):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if subkey_name:
                            res.append(subkey_name)
                    except OSError:
                        break
        except Exception:
            pass
        return res

    def read_events(self, channel: str='System', limit: int=100, level: str='', search: str='', event_id: int | list[int] | tuple[int, ...] | set[int] = 0, hours: int=24) -> List[Dict[str, Any]]:
        """Быстрое чтение событий из указанного канала через EvtQuery / EvtRender."""
        if not self._available or not self.wevtapi:
            return []
        limit = max(1, min(limit, 2000))
        xpath_parts: List[str] = []
        if level:
            lvl_lower = level.lower()
            if 'crit' in lvl_lower:
                xpath_parts.append('Level=1')
            elif 'err' in lvl_lower:
                xpath_parts.append('Level=2')
            elif 'warn' in lvl_lower:
                xpath_parts.append('Level=3')
            elif 'inf' in lvl_lower:
                xpath_parts.append('Level=4')
            elif 'verb' in lvl_lower:
                xpath_parts.append('Level=5')
        if isinstance(event_id, (list, tuple, set)):
            valid_eids = [e for e in event_id if isinstance(e, int) and e > 0]
            if valid_eids:
                clauses = ' or '.join(f'EventID={eid}' for eid in valid_eids)
                xpath_parts.append(f'({clauses})')
        elif isinstance(event_id, int) and event_id > 0:
            xpath_parts.append(f'EventID={event_id}')
        if xpath_parts:
            clause = ' and '.join(xpath_parts)
            query_xpath = f'*[System[{clause}]]'
        else:
            query_xpath = '*'
        events: List[Dict[str, Any]] = []
        try:
            h_query = self.wevtapi.EvtQuery(None, channel, query_xpath, EVT_QUERY_CHANNEL_PATH | EVT_QUERY_REVERSE_DIRECTION)
            if not h_query:
                return []
            try:
                event_handles = (wintypes.HANDLE * limit)()
                returned = wintypes.DWORD(0)
                if self.wevtapi.EvtNext(h_query, limit, event_handles, 2000, 0, ctypes.byref(returned)):
                    for i in range(returned.value):
                        h_ev = event_handles[i]
                        if h_ev:
                            ev_dict = self._render_event_xml(h_ev, channel)
                            if ev_dict:
                                if search:
                                    s_lower = search.lower()
                                    msg = str(ev_dict.get('message', '')).lower()
                                    prov = str(ev_dict.get('provider', '')).lower()
                                    eid = str(ev_dict.get('event_id', ''))
                                    if s_lower not in msg and s_lower not in prov and (s_lower not in eid):
                                        self.wevtapi.EvtClose(h_ev)
                                        continue
                                events.append(ev_dict)
                            self.wevtapi.EvtClose(h_ev)
            finally:
                self.wevtapi.EvtClose(h_query)
        except Exception as ex:
            logger.debug(f'[WevtAPI] Ошибка при чтении событий ({channel}): {ex}')
        return events

    def _get_publisher_metadata(self, provider_name: str) -> Optional[wintypes.HANDLE]:
        """Получить кешированный дескриптор метаданных провайдера событий."""
        if not self._available or not self.wevtapi or not provider_name:
            return None
        if provider_name in self._publisher_cache:
            return self._publisher_cache[provider_name]
        try:
            h_pub = self.wevtapi.EvtOpenPublisherMetadata(None, provider_name, None, 0, 0)
            if h_pub:
                self._publisher_cache[provider_name] = h_pub
                return h_pub
            self._publisher_cache[provider_name] = None
        except Exception:
            self._publisher_cache[provider_name] = None
        return None

    def format_event_message(self, h_event: wintypes.HANDLE, provider_name: str, flag: int = 1) -> Optional[str]:
        """Сформировать нативное локализованное системное сообщение события через EvtFormatMessage.

        Args:
            h_event: Дескриптор события Windows.
            provider_name: Имя издателя/провайдера (например, 'Microsoft-Windows-Kernel-Power').
            flag: Флаг форматирования (1 = EvtFormatMessageEvent, 2 = Level, 3 = Task).

        Returns:
            Optional[str]: Отформатированная локализованная строка сообщения или None.
        """
        if not self._available or not self.wevtapi or not h_event or not provider_name:
            return None
        h_pub = self._get_publisher_metadata(provider_name)
        if not h_pub:
            return None
        try:
            used = wintypes.DWORD()
            self.wevtapi.EvtFormatMessage(h_pub, h_event, 0, 0, None, flag, 0, None, ctypes.byref(used))
            err = ctypes.GetLastError()
            if err != 122 or used.value == 0:
                return None
            buf = ctypes.create_unicode_buffer(used.value + 2)
            if self.wevtapi.EvtFormatMessage(h_pub, h_event, 0, 0, None, flag, used.value, buf, ctypes.byref(used)):
                val = buf.value
                if val:
                    return val.strip()
        except Exception:
            pass
        return None

    def close(self) -> None:
        """Освободить все открытые дескрипторы издателей."""
        if self._available and self.wevtapi:
            for h in list(self._publisher_cache.values()):
                if h:
                    try:
                        self.wevtapi.EvtClose(h)
                    except Exception:
                        pass
        self._publisher_cache.clear()

    def __del__(self) -> None:
        """Деструктор для гарантированного освобождения ресурсов."""
        self.close()

    def _render_event_xml(self, h_event: wintypes.HANDLE, channel: str) -> Optional[Dict[str, Any]]:
        """Отрендерить событие в XML строку и разобрать в словарь."""
        if not self.wevtapi:
            return None
        used = wintypes.DWORD()
        prop_count = wintypes.DWORD()
        self.wevtapi.EvtRender(None, h_event, EVT_RENDER_EVENT_XML, 0, None, ctypes.byref(used), ctypes.byref(prop_count))
        err = ctypes.GetLastError()
        if err != 122:
            return None
        buf = ctypes.create_unicode_buffer(used.value // 2 + 2)
        if not self.wevtapi.EvtRender(None, h_event, EVT_RENDER_EVENT_XML, used.value, ctypes.byref(buf), ctypes.byref(used), ctypes.byref(prop_count)):
            return None
        xml_str = buf.value
        if not xml_str:
            return None
        res = self._parse_event_xml(xml_str, channel)
        if res:
            prov = res.get('provider', '')
            if prov:
                formatted = self.format_event_message(h_event, prov, flag=1)
                if formatted:
                    res['formatted_message'] = formatted
                    res['message'] = formatted
        return res

    def _parse_event_xml(self, xml_str: str, channel: str) -> Dict[str, Any]:
        """Разобрать XML представление Windows события в нормализованную структуру."""
        res: Dict[str, Any] = {'timestamp': '', 'level': 'Information', 'event_id': 0, 'provider': '', 'computer': '', 'process_id': 0, 'thread_id': 0, 'channel': channel, 'message': '', 'raw_data': xml_str}
        try:
            clean_xml = ET.fromstring(xml_str)
            system_elem = clean_xml.find('{http://schemas.microsoft.com/win/2004/08/events/event}System')
            if system_elem is None:
                system_elem = clean_xml.find('System')
            if system_elem is not None:
                for child in system_elem:
                    tag = child.tag.split('}')[-1]
                    if tag == 'TimeCreated':
                        raw_time = child.attrib.get('SystemTime', '')
                        if raw_time:
                            res['timestamp'] = raw_time.replace('T', ' ').split('.')[0]
                    elif tag == 'EventID':
                        try:
                            res['event_id'] = int(child.text or '0')
                        except ValueError:
                            res['event_id'] = 0
                    elif tag == 'EventRecordID':
                        try:
                            res['record_id'] = int(child.text or '0')
                        except ValueError:
                            res['record_id'] = 0
                    elif tag == 'Level':
                        lvl_map = {'1': 'Critical', '2': 'Error', '3': 'Warning', '4': 'Information', '5': 'Verbose'}
                        res['level'] = lvl_map.get(str(child.text or '').strip(), 'Information')
                    elif tag == 'Provider':
                        res['provider'] = child.attrib.get('Name', '')
                    elif tag == 'Computer':
                        res['computer'] = child.text or ''
                    elif tag == 'Execution':
                        try:
                            res['process_id'] = int(child.attrib.get('ProcessID', 0))
                            res['thread_id'] = int(child.attrib.get('ThreadID', 0))
                        except ValueError:
                            pass
                    elif tag == 'Channel':
                        if child.text:
                            res['channel'] = child.text
            data_dict: Dict[str, str] = {}
            data_texts: List[str] = []
            for d in clean_xml.iter():
                tag = d.tag.split('}')[-1]
                if tag in ('Data', 'string', 'Value') and d.text:
                    t = d.text.strip()
                    name_attr = d.attrib.get('Name')
                    if name_attr:
                        data_dict[name_attr] = t
                        data_texts.append(f'{name_attr}: {t}')
                    elif t:
                        data_texts.append(t)
            res['event_data'] = data_dict
            if data_texts:
                res['message'] = ' | '.join(data_texts[:12])
            else:
                res['message'] = f"Event {res['event_id']} from {res['provider']}"
        except Exception:
            res['message'] = f'Event recorded in {channel}'
        return res

    def query_process_events(self, limit: int=100, filter_process: Optional[str]=None, filter_user: Optional[str]=None) -> List[Dict[str, Any]]:
        """
        Запросить структурированные события создания процессов из Sysmon (Event 1)
        или Windows Security Log (Event 4688).

        Args:
            limit: Максимальное количество событий.
            filter_process: Фильтр по имени/пути исполняемого файла.
            filter_user: Фильтр по имени учетной записи пользователя.

        Returns:
            Список нормализованных словарей с информацией о запусках процессов.
        """
        results: List[Dict[str, Any]] = []
        sysmon_events = self.read_events(channel='Microsoft-Windows-Sysmon/Operational', limit=limit, event_id=1)
        for ev in sysmon_events:
            ed = ev.get('event_data', {})
            exe_path = ed.get('Image', '')
            cmd_line = ed.get('CommandLine', '')
            user = ed.get('User', '')
            pid = int(ed.get('ProcessId', 0) or 0)
            ppid = int(ed.get('ParentProcessId', 0) or 0)
            parent_exe = ed.get('ParentImage', '')
            parent_cmd = ed.get('ParentCommandLine', '')
            hashes = ed.get('Hashes', '')
            guid = ed.get('ProcessGuid', '')
            parent_guid = ed.get('ParentProcessGuid', '')
            if filter_process and filter_process.lower() not in exe_path.lower() and (filter_process.lower() not in cmd_line.lower()):
                continue
            if filter_user and filter_user.lower() not in user.lower():
                continue
            results.append({'source': 'Sysmon (Event 1)', 'timestamp': ev.get('timestamp'), 'event_id': 1, 'process_id': pid, 'process_name': exe_path.replace('\\', '/').split('/')[-1] if exe_path else '', 'executable_path': exe_path, 'command_line': cmd_line, 'user': user, 'parent_process_id': ppid, 'parent_process_name': parent_exe.replace('\\', '/').split('/')[-1] if parent_exe else '', 'parent_executable_path': parent_exe, 'parent_command_line': parent_cmd, 'process_guid': guid, 'parent_process_guid': parent_guid, 'hashes': hashes, 'raw_event': ev})
        if len(results) < limit:
            remaining = limit - len(results)
            sec_events = self.read_events(channel='Security', limit=remaining, event_id=4688)
            for ev in sec_events:
                ed = ev.get('event_data', {})
                exe_path = ed.get('NewProcessName', '')
                cmd_line = ed.get('CommandLine', '')
                user = ed.get('SubjectUserName', '')
                raw_pid = ed.get('NewProcessId', '0')
                try:
                    pid = int(raw_pid, 16) if str(raw_pid).startswith('0x') else int(raw_pid or 0)
                except ValueError:
                    pid = 0
                raw_ppid = ed.get('ProcessId', '0')
                try:
                    ppid = int(raw_ppid, 16) if str(raw_ppid).startswith('0x') else int(raw_ppid or 0)
                except ValueError:
                    ppid = 0
                parent_exe = ed.get('ParentProcessName', '')
                if filter_process and filter_process.lower() not in exe_path.lower() and (filter_process.lower() not in cmd_line.lower()):
                    continue
                if filter_user and filter_user.lower() not in user.lower():
                    continue
                results.append({'source': 'Security Audit (Event 4688)', 'timestamp': ev.get('timestamp'), 'event_id': 4688, 'process_id': pid, 'process_name': exe_path.replace('\\', '/').split('/')[-1] if exe_path else '', 'executable_path': exe_path, 'command_line': cmd_line, 'user': user, 'parent_process_id': ppid, 'parent_process_name': parent_exe.replace('\\', '/').split('/')[-1] if parent_exe else '', 'parent_executable_path': parent_exe, 'parent_command_line': '', 'process_guid': '', 'parent_process_guid': '', 'hashes': '', 'raw_event': ev})
        return results

    def query_powershell_script_blocks(self, limit: int = 100, filter_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """Запросить блоки скриптов PowerShell (Script Block Logging, Event ID 4104).

        Args:
            limit: Максимальное количество записей.
            filter_text: Подстрока для поиска в теле скрипта или пути.

        Returns:
            List[Dict[str, Any]]: Нормализованные события с блоками кода скриптов.
        """
        results: List[Dict[str, Any]] = []
        ps_events = self.read_events(channel='Microsoft-Windows-PowerShell/Operational', limit=limit, event_id=4104)
        for ev in ps_events:
            ed = ev.get('event_data', {})
            script_text = ed.get('ScriptBlockText', '') or ev.get('message', '')
            script_id = ed.get('ScriptBlockId', '')
            path = ed.get('Path', '')
            user_id = ed.get('UserId', '')
            msg_total = ed.get('MessageTotal', '1')
            msg_number = ed.get('MessageNumber', '1')

            if filter_text and filter_text.lower() not in script_text.lower() and (filter_text.lower() not in path.lower()):
                continue

            results.append({
                'source': 'PowerShell ScriptBlock (Event 4104)',
                'timestamp': ev.get('timestamp'),
                'event_id': 4104,
                'script_block_id': script_id,
                'script_text': script_text,
                'path': path,
                'user_id': user_id,
                'message_number': int(msg_number) if str(msg_number).isdigit() else 1,
                'message_total': int(msg_total) if str(msg_total).isdigit() else 1,
                'raw_event': ev,
            })
        return results

    def query_sysmon_events(
        self,
        limit: int = 100,
        event_ids: Optional[List[int]] = None,
        filter_process: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Запросить события безопасности Sysmon (Event ID 1, 7, 10, 11, 23, 26).

        Args:
            limit: Максимальное количество записей.
            event_ids: Список опрашиваемых идентификаторов событий (по умолчанию: 1, 7, 10, 11, 23, 26).
            filter_process: Фильтр по имени/пути исполняемого файла или модуля.

        Returns:
            List[Dict[str, Any]]: Нормализованные события Sysmon.
        """
        target_ids = event_ids or [1, 7, 10, 11, 23, 26]
        all_events: List[Dict[str, Any]] = []

        for eid in target_ids:
            evs = self.read_events(channel='Microsoft-Windows-Sysmon/Operational', limit=limit, event_id=eid)
            for ev in evs:
                ed = ev.get('event_data', {})
                img = ed.get('Image', '') or ed.get('SourceImage', '')
                if filter_process and filter_process.lower() not in img.lower() and (filter_process.lower() not in str(ed).lower()):
                    continue

                item: Dict[str, Any] = {
                    'source': f'Sysmon (Event {eid})',
                    'timestamp': ev.get('timestamp'),
                    'event_id': eid,
                    'process_id': int(ed.get('ProcessId', 0) or ed.get('SourceProcessId', 0) or 0),
                    'image': img,
                    'process_guid': ed.get('ProcessGuid') or ed.get('SourceProcessGuid', ''),
                    'user': ed.get('User', ''),
                    'raw_event': ev,
                }

                if eid == 1:
                    item.update({
                        'event_type': 'ProcessCreate',
                        'command_line': ed.get('CommandLine', ''),
                        'parent_process_id': int(ed.get('ParentProcessId', 0) or 0),
                        'parent_image': ed.get('ParentImage', ''),
                        'hashes': ed.get('Hashes', ''),
                    })
                elif eid == 7:
                    item.update({
                        'event_type': 'ImageLoaded',
                        'image_loaded': ed.get('ImageLoaded', ''),
                        'signed': ed.get('Signed', ''),
                        'signature': ed.get('Signature', ''),
                        'hashes': ed.get('Hashes', ''),
                    })
                elif eid == 10:
                    item.update({
                        'event_type': 'ProcessAccess',
                        'target_process_id': int(ed.get('TargetProcessId', 0) or 0),
                        'target_image': ed.get('TargetImage', ''),
                        'granted_access': ed.get('GrantedAccess', ''),
                        'call_trace': ed.get('CallTrace', ''),
                    })
                elif eid in (11, 23, 26):
                    item.update({
                        'event_type': 'FileDelete' if eid in (23, 26) else 'FileCreate',
                        'target_filename': ed.get('TargetFilename', ''),
                        'hashes': ed.get('Hashes', ''),
                    })

                all_events.append(item)

        all_events.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)
        return all_events[:limit]


__all__ = ['WevtAPI', 'ChannelMetadata', 'CHANNEL_DESCRIPTIONS']