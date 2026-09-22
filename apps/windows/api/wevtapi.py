# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Event Log Native API Wrapper (wevtapi.dll)
# =============================================================================
# Description:
#   Direct low-level Ctypes wrapper for Windows Event Log API (wevtapi.dll)
#   and Event Log Registry providers. Enumerates all registered OS log channels,
#   retrieves precise record counts, channel descriptions, and reads native event
#   records without calling external PowerShell processes.
#
# Examples:
#   >>> from apps.windows.api.wevtapi import WevtAPI
#   >>> api = WevtAPI()
#   >>> channels = api.enumerate_channels()
#
# File: wevtapi.py
# Project: AI-Breadboard
# Package: apps.windows.api
# Class: WevtAPI
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Низкоуровневый интерфейс к wevtapi.dll для работы с журналами событий Windows."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import struct
import sys
import winreg
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from logger import logger

EVT_QUERY_CHANNEL_PATH = 0x1
EVT_QUERY_FILE_PATH = 0x2
EVT_QUERY_REVERSE_DIRECTION = 0x200
EVT_RENDER_EVENT_XML = 1

# Известные понятные описания основных каналов
CHANNEL_DESCRIPTIONS: Dict[str, str] = {
    "System": "Системный журнал Windows: события ядра ОС, системных служб, драйверов устройств, сбоев питания и сетевого стека.",
    "Application": "Журнал приложений: события, предупреждения, сбои и ошибки пользовательских и серверных программ (Crash, Faults).",
    "Security": "Журнал безопасности: аудит входов в систему (Logon/Logoff), права доступа, повышение привилегий UAC и политики безопасности.",
    "Setup": "Журнал установки: логи процесса установки операционной системы, обновлений Windows и накопительных пакетов KB.",
    "Microsoft-Windows-WindowsUpdateClient/Operational": "Клиент обновления Windows Update: загрузка, верификация и установка патчей, исправления безопасности и драйверов.",
    "Microsoft-Windows-Kernel-PnP/Configuration": "Конфигурация оборудования Plug and Play: подключение новых устройств, установка драйверов, коды ошибок 10/43.",
    "Microsoft-Windows-Kernel-Power/Operational": "Питание ядра Windows: переходы в сон/гибернацию, сбои питания (Event 41), изменение состояний батареи и ACPI.",
    "Microsoft-Windows-TaskScheduler/Operational": "Планировщик заданий: запуск, завершение, сбои и выполнение фоновых регламентных задач Windows.",
    "Microsoft-Windows-Windows Defender/Operational": "Антивирус Microsoft Defender: обнаружение угроз, сканирование в реальном времени, обновление антивирусных сигнатур.",
    "Microsoft-Windows-Hyper-V-Compute-Operational": "Платформа виртуализации Hyper-V: жизненный цикл виртуальных машин, контейнеров WSL2 и виртуальных адаптеров.",
    "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall": "Брандмауэр Windows: блокировки входящего/исходящего трафика, сетевые правила фильтрации и аномалии сокетов.",
    "Microsoft-Windows-Diagnostics-Performance/Operational": "Диагностика производительности: анализ времени загрузки Windows, выключения и зависания системных компонентов.",
    "Microsoft-Windows-Bits-Client/Operational": "Фоновая интеллектуальная служба передачи (BITS): загрузка файлов и обновлений по сети с контролем канала.",
    "Microsoft-Windows-DNS-Client/Operational": "DNS-клиент Windows: резолвинг доменных имен, таймауты DNS серверов и сетевые кэширования.",
    "Microsoft-Windows-CodeIntegrity/Operational": "Контроль целостности кода: проверка цифровых подписей драйверов и исполняемых системных файлов.",
    "Microsoft-Windows-PowerShell/Operational": "Исполнение скриптов PowerShell: запуск командлетов, сценариев автоматизации и модулей администрирования.",
    "Microsoft-Windows-Sysmon/Operational": "Microsoft System Monitor (Sysmon): глубокая телеметрия создания процессов (Event 1), сети (Event 3), файловых операций (11/23/26) и хэшей исполняемых файлов.",
}


@dataclass
class ChannelMetadata:
    """Метаданные о канале журнала Windows."""
    channel_name: str
    display_name: str
    description: str = ""
    is_enabled: bool = True
    record_count: int = 0
    category: str = "Windows Event Log"


class WevtAPI:
    """Ctypes-обертка для wevtapi.dll и реестра Windows Event Log."""

    def __init__(self) -> None:
        """Инициализация библиотеки wevtapi.dll."""
        self._available = False
        self.wevtapi: Optional[ctypes.WinDLL] = None
        if sys.platform == "win32":
            try:
                self.wevtapi = ctypes.windll.LoadLibrary("wevtapi.dll")
                self._setup_signatures()
                self._available = True
            except Exception as ex:
                logger.debug(f"[WevtAPI] Не удалось загрузить wevtapi.dll: {ex}")

    def _setup_signatures(self) -> None:
        """Настройка типов аргументов и возвращаемых значений функций."""
        if not self.wevtapi:
            return

        # EvtOpenChannelEnum
        self.wevtapi.EvtOpenChannelEnum.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.wevtapi.EvtOpenChannelEnum.restype = wintypes.HANDLE

        # EvtNextChannelPath
        self.wevtapi.EvtNextChannelPath.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.wevtapi.EvtNextChannelPath.restype = wintypes.BOOL

        # EvtClose
        self.wevtapi.EvtClose.argtypes = [wintypes.HANDLE]
        self.wevtapi.EvtClose.restype = wintypes.BOOL

        # EvtOpenLog
        self.wevtapi.EvtOpenLog.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
        self.wevtapi.EvtOpenLog.restype = wintypes.HANDLE

        # EvtGetLogInfo
        self.wevtapi.EvtGetLogInfo.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.wevtapi.EvtGetLogInfo.restype = wintypes.BOOL

        # EvtQuery
        self.wevtapi.EvtQuery.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
        ]
        self.wevtapi.EvtQuery.restype = wintypes.HANDLE

        # EvtNext
        self.wevtapi.EvtNext.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.wevtapi.EvtNext.restype = wintypes.BOOL

        # EvtRender
        self.wevtapi.EvtRender.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.wevtapi.EvtRender.restype = wintypes.BOOL

    def is_available(self) -> bool:
        """Проверить доступность wevtapi.dll в текущей системе."""
        return self._available

    def get_channel_record_count(self, channel_name: str) -> int:
        """Мгновенно получить точное количество записей в канале через EvtGetLogInfo."""
        if not self._available or not self.wevtapi:
            return 0
        h_log = self.wevtapi.EvtOpenLog(None, channel_name, 1)  # 1 = EvtOpenChannelPath
        if not h_log:
            return 0
        try:
            buf = (ctypes.c_byte * 128)()
            used = wintypes.DWORD(0)
            # PropID 5: EvtLogNumberOfLogRecords
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
        
        # Интеллектуальный авто-вывод на основе имени провайдера
        if "Defender" in channel_name:
            return "Журнал защитных механизмов, антивирусного сканирования и предотвращения вторжений Microsoft Defender."
        if "Kernel-Power" in channel_name:
            return "Журнал управления электропитанием, состояний ACPI, спящего режима и аварийных отключений питания."
        if "Kernel-PnP" in channel_name:
            return "Журнал конфигурации оборудования, обнаружения и инициализации устройств Plug and Play."
        if "WindowsUpdate" in channel_name:
            return "Журнал службы обновлений Windows, загрузки пакетов KB и применения хотфиксов."
        if "TaskScheduler" in channel_name:
            return "Журнал планировщика задач Windows, запуска автоматических фоновых процессов и триггеров."
        if "Hyper-V" in channel_name:
            return "Журнал подсистемы виртуализации Hyper-V, WSL2 контейнеров и гостевых служб."
        if "PowerShell" in channel_name:
            return "Журнал среды PowerShell, выполнения скриптов автоматизации и команд администрирования."
        if "Firewall" in channel_name:
            return "Журнал сетевого брандмауэра Windows, правил сетевого экрана и событий фильтрации трафика."
        if "Storage" in channel_name or "Disk" in channel_name:
            return "Журнал дисковой подсистемы, контроллеров накопителей, томов NTFS/ReFS и файловой системы."
        if "Network" in channel_name or "Wlan" in channel_name or "NDIS" in channel_name:
            return "Журнал сетевых интерфейсов, Wi-Fi соединений, сетевых адаптеров и стека TCP/IP."
        if "Audio" in channel_name or "Sound" in channel_name:
            return "Журнал аудиоподсистемы, службы Windows Audio и конечных звуковых устройств."
        if "Print" in channel_name or "Spooler" in channel_name:
            return "Журнал диспетчера очереди печати и драйверов принтеров."
        if "Bluetooth" in channel_name or "BTH" in channel_name:
            return "Журнал стека Bluetooth, сопряжения беспроводных устройств и протоколов передачи данных."
        if "USB" in channel_name:
            return "Журнал контроллеров USB, хабов и подключенных внешних периферийных устройств."
        
        return f"Специализированный системный журнал Windows для компонента '{channel_name}'."

    def enumerate_channels(self) -> List[ChannelMetadata]:
        """Получить исчерпывающий список всех каналов Windows Event Log с количеством записей."""
        channels: List[ChannelMetadata] = []
        seen: set[str] = set()

        classic = [
            ("System", "System (Системный)"),
            ("Application", "Application (Приложения)"),
            ("Security", "Security (Безопасность)"),
            ("Setup", "Setup (Установка)"),
            ("Microsoft-Windows-WindowsUpdateClient/Operational", "Windows Update Client"),
            ("Microsoft-Windows-Kernel-PnP/Configuration", "Kernel PnP Configuration"),
            ("Microsoft-Windows-Kernel-Power/Operational", "Kernel Power"),
            ("Microsoft-Windows-TaskScheduler/Operational", "Task Scheduler"),
            ("Microsoft-Windows-Windows Defender/Operational", "Windows Defender"),
            ("Microsoft-Windows-Hyper-V-Compute-Operational", "Hyper-V Compute"),
            ("Microsoft-Windows-PowerShell/Operational", "Windows PowerShell"),
        ]
        for cname, dname in classic:
            rec_cnt = self.get_channel_record_count(cname)
            channels.append(
                ChannelMetadata(
                    channel_name=cname,
                    display_name=dname,
                    description=self.get_channel_description(cname),
                    record_count=rec_cnt,
                    is_enabled=True,
                )
            )
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
                            channels.append(
                                ChannelMetadata(
                                    channel_name=chan_str,
                                    display_name=chan_str,
                                    description=self.get_channel_description(chan_str),
                                    record_count=rec_cnt,
                                    is_enabled=True,
                                )
                            )
                            seen.add(chan_str.lower())
                    self.wevtapi.EvtClose(h_enum)
            except Exception as ex:
                logger.debug(f"[WevtAPI] Ошибка при перечислении через EvtOpenChannelEnum: {ex}")

        try:
            reg_channels = self._enumerate_registry_channels()
            for r_chan in reg_channels:
                if r_chan.lower() not in seen:
                    rec_cnt = self.get_channel_record_count(r_chan)
                    channels.append(
                        ChannelMetadata(
                            channel_name=r_chan,
                            display_name=r_chan,
                            description=self.get_channel_description(r_chan),
                            record_count=rec_cnt,
                            is_enabled=True,
                        )
                    )
                    seen.add(r_chan.lower())
        except Exception as ex:
            logger.debug(f"[WevtAPI] Ошибка чтения каналов из реестра: {ex}")

        return channels

    def _enumerate_registry_channels(self) -> List[str]:
        """Считать имена зарегистрированных каналов из реестра Windows."""
        res: List[str] = []
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\WINEVT\Channels"
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

    def read_events(
        self,
        channel: str = "System",
        limit: int = 100,
        level: str = "",
        search: str = "",
        event_id: int = 0,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Быстрое чтение событий из указанного канала через EvtQuery / EvtRender."""
        if not self._available or not self.wevtapi:
            return []

        limit = max(1, min(limit, 2000))
        xpath_parts: List[str] = []

        if level:
            lvl_lower = level.lower()
            if "crit" in lvl_lower:
                xpath_parts.append("Level=1")
            elif "err" in lvl_lower:
                xpath_parts.append("Level=2")
            elif "warn" in lvl_lower:
                xpath_parts.append("Level=3")
            elif "inf" in lvl_lower:
                xpath_parts.append("Level=4")
            elif "verb" in lvl_lower:
                xpath_parts.append("Level=5")

        if event_id > 0:
            xpath_parts.append(f"EventID={event_id}")

        if xpath_parts:
            clause = " and ".join(xpath_parts)
            query_xpath = f"*[System[{clause}]]"
        else:
            query_xpath = "*"

        events: List[Dict[str, Any]] = []
        try:
            h_query = self.wevtapi.EvtQuery(
                None,
                channel,
                query_xpath,
                EVT_QUERY_CHANNEL_PATH | EVT_QUERY_REVERSE_DIRECTION,
            )
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
                                    msg = str(ev_dict.get("message", "")).lower()
                                    prov = str(ev_dict.get("provider", "")).lower()
                                    eid = str(ev_dict.get("event_id", ""))
                                    if s_lower not in msg and s_lower not in prov and s_lower not in eid:
                                        self.wevtapi.EvtClose(h_ev)
                                        continue
                                events.append(ev_dict)
                            self.wevtapi.EvtClose(h_ev)
            finally:
                self.wevtapi.EvtClose(h_query)
        except Exception as ex:
            logger.debug(f"[WevtAPI] Ошибка при чтении событий ({channel}): {ex}")

        return events

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
        if not self.wevtapi.EvtRender(
            None,
            h_event,
            EVT_RENDER_EVENT_XML,
            used.value,
            ctypes.byref(buf),
            ctypes.byref(used),
            ctypes.byref(prop_count),
        ):
            return None

        xml_str = buf.value
        if not xml_str:
            return None

        return self._parse_event_xml(xml_str, channel)

    def _parse_event_xml(self, xml_str: str, channel: str) -> Dict[str, Any]:
        """Разобрать XML представление Windows события в нормализованную структуру."""
        res: Dict[str, Any] = {
            "timestamp": "",
            "level": "Information",
            "event_id": 0,
            "provider": "",
            "computer": "",
            "process_id": 0,
            "thread_id": 0,
            "channel": channel,
            "message": "",
            "raw_data": xml_str,
        }

        try:
            clean_xml = ET.fromstring(xml_str)
            system_elem = clean_xml.find("{http://schemas.microsoft.com/win/2004/08/events/event}System")
            if system_elem is None:
                system_elem = clean_xml.find("System")

            if system_elem is not None:
                for child in system_elem:
                    tag = child.tag.split("}")[-1]
                    if tag == "TimeCreated":
                        raw_time = child.attrib.get("SystemTime", "")
                        if raw_time:
                            res["timestamp"] = raw_time.replace("T", " ").split(".")[0]
                    elif tag == "EventID":
                        try:
                            res["event_id"] = int(child.text or "0")
                        except ValueError:
                            res["event_id"] = 0
                    elif tag == "Level":
                        lvl_map = {
                            "1": "Critical",
                            "2": "Error",
                            "3": "Warning",
                            "4": "Information",
                            "5": "Verbose",
                        }
                        res["level"] = lvl_map.get(str(child.text or "").strip(), "Information")
                    elif tag == "Provider":
                        res["provider"] = child.attrib.get("Name", "")
                    elif tag == "Computer":
                        res["computer"] = child.text or ""
                    elif tag == "Execution":
                        try:
                            res["process_id"] = int(child.attrib.get("ProcessID", 0))
                            res["thread_id"] = int(child.attrib.get("ThreadID", 0))
                        except ValueError:
                            pass
                    elif tag == "Channel":
                        if child.text:
                            res["channel"] = child.text

            data_dict: Dict[str, str] = {}
            for d in clean_xml.iter():
                tag = d.tag.split("}")[-1]
                if tag in ("Data", "string", "Value") and d.text:
                    t = d.text.strip()
                    name_attr = d.attrib.get("Name")
                    if name_attr:
                        data_dict[name_attr] = t
                        data_texts.append(f"{name_attr}: {t}")
                    elif t:
                        data_texts.append(t)

            res["event_data"] = data_dict

            if data_texts:
                res["message"] = " | ".join(data_texts[:12])
            else:
                res["message"] = f"Event {res['event_id']} from {res['provider']}"
        except Exception:
            res["message"] = f"Event recorded in {channel}"

        return res

    def query_process_events(
        self,
        limit: int = 100,
        filter_process: Optional[str] = None,
        filter_user: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
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

        # 1. Попытка чтения из Sysmon (Event 1: Process Create)
        sysmon_events = self.read_events(
            channel="Microsoft-Windows-Sysmon/Operational",
            limit=limit,
            event_id=1,
        )

        for ev in sysmon_events:
            ed = ev.get("event_data", {})
            exe_path = ed.get("Image", "")
            cmd_line = ed.get("CommandLine", "")
            user = ed.get("User", "")
            pid = int(ed.get("ProcessId", 0) or 0)
            ppid = int(ed.get("ParentProcessId", 0) or 0)
            parent_exe = ed.get("ParentImage", "")
            parent_cmd = ed.get("ParentCommandLine", "")
            hashes = ed.get("Hashes", "")
            guid = ed.get("ProcessGuid", "")
            parent_guid = ed.get("ParentProcessGuid", "")

            # Фильтрация
            if filter_process and filter_process.lower() not in exe_path.lower() and filter_process.lower() not in cmd_line.lower():
                continue
            if filter_user and filter_user.lower() not in user.lower():
                continue

            results.append({
                "source": "Sysmon (Event 1)",
                "timestamp": ev.get("timestamp"),
                "event_id": 1,
                "process_id": pid,
                "process_name": exe_path.replace("\\", "/").split("/")[-1] if exe_path else "",
                "executable_path": exe_path,
                "command_line": cmd_line,
                "user": user,
                "parent_process_id": ppid,
                "parent_process_name": parent_exe.replace("\\", "/").split("/")[-1] if parent_exe else "",
                "parent_executable_path": parent_exe,
                "parent_command_line": parent_cmd,
                "process_guid": guid,
                "parent_process_guid": parent_guid,
                "hashes": hashes,
                "raw_event": ev,
            })

        # 2. Если Sysmon вернул мало/пусто, запрашиваем Security Log (Event 4688)
        if len(results) < limit:
            remaining = limit - len(results)
            sec_events = self.read_events(
                channel="Security",
                limit=remaining,
                event_id=4688,
            )

            for ev in sec_events:
                ed = ev.get("event_data", {})
                exe_path = ed.get("NewProcessName", "")
                cmd_line = ed.get("CommandLine", "")
                user = ed.get("SubjectUserName", "")
                
                # PID в Security Log часто передается в hex виде (0x1a4)
                raw_pid = ed.get("NewProcessId", "0")
                try:
                    pid = int(raw_pid, 16) if str(raw_pid).startswith("0x") else int(raw_pid or 0)
                except ValueError:
                    pid = 0

                raw_ppid = ed.get("ProcessId", "0")
                try:
                    ppid = int(raw_ppid, 16) if str(raw_ppid).startswith("0x") else int(raw_ppid or 0)
                except ValueError:
                    ppid = 0

                parent_exe = ed.get("ParentProcessName", "")

                if filter_process and filter_process.lower() not in exe_path.lower() and filter_process.lower() not in cmd_line.lower():
                    continue
                if filter_user and filter_user.lower() not in user.lower():
                    continue

                results.append({
                    "source": "Security Audit (Event 4688)",
                    "timestamp": ev.get("timestamp"),
                    "event_id": 4688,
                    "process_id": pid,
                    "process_name": exe_path.replace("\\", "/").split("/")[-1] if exe_path else "",
                    "executable_path": exe_path,
                    "command_line": cmd_line,
                    "user": user,
                    "parent_process_id": ppid,
                    "parent_process_name": parent_exe.replace("\\", "/").split("/")[-1] if parent_exe else "",
                    "parent_executable_path": parent_exe,
                    "parent_command_line": "",
                    "process_guid": "",
                    "parent_process_guid": "",
                    "hashes": "",
                    "raw_event": ev,
                })

        return results


__all__ = ["WevtAPI", "ChannelMetadata", "CHANNEL_DESCRIPTIONS"]

