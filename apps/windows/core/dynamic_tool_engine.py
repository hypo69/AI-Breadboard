# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Dynamic Tool & Skill Synthesis Engine
# =============================================================================
# Description:
#   Динамический движок синтеза инструментов и навыков на базе API Windows
#   (apps/windows/core/modules и apps/windows/api). Преобразует произвольный
#   вопрос пользователя в целевой зонд (collector/PowerShell/WinAPI),
#   выполняет безопасный опрос хоста, формирует структурированный ответ
#   и автоматически сохраняет переиспользуемый навык в каталог .skills/.
#
# Examples:
#   >>> engine = DynamicWindowsToolEngine()
#   >>> res = await engine.process_query("Какие мыши были подключены к компьютеру?")
#
# File: dynamic_tool_engine.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Динамический генератор и исполнитель системных инструментов Windows."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.logger import logger
from header import __root__

from apps.windows.core.modules import (
    CleanCollector,
    DriverCollector,
    EventLogCollector,
    IntegrityCollector,
    NetworkCollector,
    PerformanceCollector,
    ProcessCollector,
    SecurityCollector,
    ServicesCollector,
    SoftwareCollector,
    StorageCollector,
    TasksCollector,
    UpdateCollector,
)


KNOWN_VENDORS = {
    "VID_046D": "Logitech",
    "VID_045E": "Microsoft",
    "VID_1532": "Razer",
    "VID_1038": "SteelSeries",
    "VID_1B1C": "Corsair",
    "VID_093A": "PixArt / Genius",
    "VID_258A": "SinoWealth / Redragon",
    "VID_04F2": "Chicony",
    "VID_514C": "A4Tech / Bloody / Gaming Mouse",
    "VID_0461": "Primax Electronics (Dell/HP OEM)",
    "VID_17EF": "Lenovo",
    "VID_03F0": "HP Inc.",
    "VID_0781": "SanDisk",
    "VID_0951": "Kingston",
    "VID_8087": "Intel",
    "VID_0D8C": "C-Media USB Audio",
    "VID_152D": "JMicron (USB Storage / UAS)",
    "VID_174C": "ASMedia (USB-SATA / ASMT)",
    "VID_413C": "Dell",
    "VID_0BDA": "Realtek",
    "VID_058F": "Alcor Micro",
    "VID_13FE": "Phison Electronics",
    "VID_05E3": "Genesys Logic Hub",
    "VID_0424": "Microchip / SMSC Hub",
}


CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}


def to_ascii_slug(text: str) -> str:
    """Преобразование произвольной строки (включая кириллицу) в валидный ASCII kebab-case slug.

    Args:
        text: Исходная строка запроса или имени.

    Returns:
        str: Безопасный ASCII slug в kebab-case.
    """
    text = (text or "").lower()
    res: List[str] = []
    for ch in text:
        if ch in CYRILLIC_TO_LATIN:
            res.append(CYRILLIC_TO_LATIN[ch])
        elif ch.isalnum() and ord(ch) < 128:
            res.append(ch)
        elif ch in (' ', '-', '_', '.'):
            res.append('-')
    slug = re.sub(r'-+', '-', ''.join(res)).strip('-')
    return slug or "windows-probe"


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Извлечение и парсинг первого валидного JSON-объекта из текстового ответа LLM.

    Args:
        text: Ответ языковой модели.

    Returns:
        Optional[Dict[str, Any]]: Распарсенный словарь или None при ошибке.
    """
    if not text:
        return None
    cleaned = text.strip()
    # 1. Попытка прямого парсинга
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Поиск блока в кодовых блоках ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # 3. Поиск первого сбалансированного {...}
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def lookup_vendor(instance_id: str) -> str:
    """Определение производителя оборудования по строке InstanceId."""
    upper = (instance_id or "").upper()
    for vid, name in KNOWN_VENDORS.items():
        if vid in upper:
            return name
    if "VEN_SANDISK" in upper:
        return "SanDisk"
    if "VEN_ASMT" in upper:
        return "ASMedia"
    return "Стандартное Windows/PnP устройство"


@dataclass
class DynamicToolPlan:
    """План выполнения динамического инструмента."""
    intent: str
    tool_name: str
    tool_title: str
    description_ru: str
    probe_type: str  # "collector" | "powershell" | "winapi"
    collector_name: Optional[str] = None
    probe_script: Optional[str] = None
    instructions: str = ""
    summary_hint: str = ""


class DynamicWindowsToolEngine:
    """Динамический генератор и исполнитель инструментов на базе подсистемы apps/windows."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        """Инициализация движка."""
        self.chat_model = chat_model
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.collectors = {
            "driver": DriverCollector(),
            "storage": StorageCollector(),
            "network": NetworkCollector(),
            "process": ProcessCollector(),
            "services": ServicesCollector(),
            "tasks": TasksCollector(),
            "security": SecurityCollector(),
            "eventlog": EventLogCollector(),
            "performance": PerformanceCollector(),
            "software": SoftwareCollector(),
            "clean": CleanCollector(),
            "update": UpdateCollector(),
            "integrity": IntegrityCollector(),
        }

    async def _get_model(self) -> Any:
        """Получение активной языковой модели."""
        if self.chat_model:
            return self.chat_model
        try:
            from src.api.router_chat import get_chat_model
            from src.config import ai_cfg
            model_key = getattr(ai_cfg, "gemini_model_id", "gemini-3.1-flash-lite")
            if getattr(ai_cfg, "use_gemini_cli", False) and not model_key.startswith(
                ("gemini_cli:", "gemini-cli-", "foundry:", "ollama:", "openai:", "hf:", "onnx:", "agy-")
            ):
                cli_id = getattr(ai_cfg, "gemini_cli_model_id", "gemini-3.1-flash-lite")
                model_key = f"gemini_cli:{cli_id}"
            return get_chat_model(model_key)
        except Exception as e:
            logger.debug(f"[DynamicWindowsToolEngine] Не удалось получить модель: {e}")
            return None

    async def plan_tool(self, query: str, conversation_id: Optional[str] = None) -> DynamicToolPlan:
        """Планирование стратегии зондирования на основе запроса пользователя и контекста сессии."""
        model = await self._get_model()
        if model:
            system_prompt = (
                "Ты — системный архитектор Windows и генератор динамических инструментов для платформы AI Breadboard.\n"
                "Твоя задача — проанализировать запрос пользователя (с учетом контекста предыдущих сообщений и корректировок) и сгенерировать точный план зондирования хоста Windows.\n\n"
                "Доступные коллекторы из apps/windows/core/modules:\n"
                "- driver: Опрос устройств PnP, ошибок драйверов, DriverStore пакетов.\n"
                "- storage: Опрос физических дисков, томов, свободного места, SMART.\n"
                "- network: Опрос сетевых интерфейсов, активных TCP/UDP сокетов, открытых портов.\n"
                "- process: Снимок процессов, потребление RAM/CPU, дерево процессов.\n"
                "- services: База служб Windows, статусы, типы автозапуска, осиротевшие службы.\n"
                "- tasks: Задачи планировщика Windows Task Scheduler, триггеры, состояние.\n"
                "- security: Windows Defender, UAC, Firewall, автозагрузка (Run/RunOnce).\n"
                "- eventlog: Журналы System, Application, Security WevtAPI.\n"
                "- performance: Анализ узких мест производительности, нагрузка, автозагрузка.\n"
                "- software: Установленные приложения из реестра и MSI.\n"
                "- update: Состояние обновлений Windows, установленные KB, ожидание перезагрузки.\n\n"
                "Если задача требует точной выборки PnP/WMI (например, принтеры, мыши, USB устройства, видеокарты, мониторы, специфические порты), "
                "сформируй безопасную read-only команду PowerShell с выводом в JSON.\n\n"
                "Ответ СТРОГО должен быть валидным JSON со структурой:\n"
                "{\n"
                '  "intent": "Краткая цель",\n'
                '  "tool_name": "kebab-case-slug (например, printers-inspector, mouse-history-inspector, usb-device-auditor)",\n'
                '  "tool_title": "Человекочитаемое название инструмента",\n'
                '  "description_ru": "Подробное описание назначения инструмента на русском языке",\n'
                '  "probe_type": "powershell" или "collector",\n'
                '  "collector_name": "имя коллектора или null",\n'
                '  "probe_script": "PowerShell скрипт с | ConvertTo-Json (если probe_type=powershell)",\n'
                '  "instructions": "1. Шаг 1\\n2. Шаг 2"\n'
                "}"
            )
            try:
                user_msg = f"Запрос пользователя: {query}"
                if conversation_id and conversation_id in self.sessions and self.sessions[conversation_id]:
                    history_snippet = "\n".join(
                        f"{m['role']}: {m['content'][:300]}" for m in self.sessions[conversation_id][-4:]
                    )
                    user_msg = f"Контекст предыдущего диалога сессии:\n{history_snippet}\n\nТекущий запрос / корректировка пользователя: {query}"
                resp_str = ""
                if hasattr(model, "ask"):
                    resp_str = await model.ask(user_msg, system_instruction=system_prompt)
                elif hasattr(model, "chat"):
                    resp_str = await model.chat(user_msg)
                elif hasattr(model, "generate_response"):
                    resp_str = await model.generate_response(user_msg)

                if resp_str:
                    data = extract_json_block(resp_str)
                    if data:
                        raw_tool_name = str(data.get("tool_name", "custom-windows-probe"))
                        safe_tool_name = to_ascii_slug(raw_tool_name)
                        return DynamicToolPlan(
                            intent=data.get("intent", query),
                            tool_name=safe_tool_name,
                            tool_title=data.get("tool_title", "Пользовательский инструмент Windows"),
                            description_ru=data.get("description_ru", f"Инспекция системы по запросу: {query}"),
                            probe_type=data.get("probe_type", "powershell"),
                            collector_name=data.get("collector_name"),
                            probe_script=data.get("probe_script"),
                            instructions=data.get("instructions", "Выполнить системный опрос и проанализировать результат."),
                        )
            except Exception as e:
                logger.warning(f"[DynamicWindowsToolEngine] Ошибка LLM планирования инструмента ({e}), переход к эвристике.")

        # Эвристический fallback планирования
        return self._heuristic_plan(query)

    def _heuristic_plan(self, query: str) -> DynamicToolPlan:
        """Эвристический генератор плана зондирования."""
        q = query.lower()

        # Принтеры / Очереди печати
        if any(w in q for w in ("принтер", "printer", "печат", "print", "мфу", "плоттер")):
            return DynamicToolPlan(
                intent="Аудит и список установленных принтеров и очередей печати",
                tool_name="printers-inspector",
                tool_title="Аудит и список принтеров (Printers Inspector)",
                description_ru="Автоматизированная инспекция активных принтеров, очередей печати и драйверов в Windows.",
                probe_type="powershell",
                probe_script="Get-CimInstance Win32_Printer | Select-Object Name, DriverName, PortName, @{Name='Status';Expression={if($_.PrinterState -eq 0 -or -not $_.PrinterState){'OK'}else{'Warning'}}}, Default, Shared, DeviceID | ConvertTo-Json",
                instructions="1. Выполнить опрос Win32_Printer через PowerShell.\n2. Получить имя принтера, статус, порт и драйвер.\n3. Сформировать список устройств печати.",
            )

        # Мыши / Манипуляторы
        if any(w in q for w in ("мыш", "mouse", "манипулятор", "мышка", "мышей", "курсор")):
            return DynamicToolPlan(
                intent="Аудит активных и ранее подключенных мышей",
                tool_name="mouse-history-inspector",
                tool_title="Аудит и история подключенных мышей (Mouse History Inspector)",
                description_ru="Автоматизированная инспекция активных и ранее подключенных мышей и манипуляторов через PnP и реестр Windows.",
                probe_type="powershell",
                probe_script="Get-PnpDevice -Class Mouse -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                instructions="1. Выполнить `Get-PnpDevice -Class Mouse`.\n2. Извлечь свойства FriendlyName, InstanceId и Status.\n3. Сопоставить VID с каталогом производителей.",
            )

        # Все USB устройства
        if any(w in q for w in ("usb", "флешк", "внешн")):
            return DynamicToolPlan(
                intent="Аудит всех активных и зарегистрированных USB устройств",
                tool_name="usb-device-auditor",
                tool_title="Аудит USB устройств (USB Device Auditor)",
                description_ru="Проверка полного списка активных и зарегистрированных USB контроллеров, накопителей и периферии в Windows.",
                probe_type="powershell",
                probe_script="Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object { $_.InstanceId -like 'USB*' -or $_.Class -eq 'USB' -or $_.Class -eq 'USBDevice' } | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                instructions="1. Выполнить опрос PnP с фильтром по InstanceId 'USB*' и классу USB.\n2. Разделить на активные и исторические.\n3. Определить вендоров по VID.",
            )

        # Мониторы / Дисплеи / Видеокарты
        if any(w in q for w in ("монитор", "дисплей", "экран", "видеокарт", "gpu", "display", "monitor")):
            return DynamicToolPlan(
                intent="Аудит мониторов, дисплеев и видеоадаптеров",
                tool_name="display-monitor-inspector",
                tool_title="Аудит мониторов и видеокарт (Display & GPU Inspector)",
                description_ru="Инспекция подключенных мониторов, экранов и видеоадаптеров в Windows.",
                probe_type="powershell",
                probe_script="Get-PnpDevice -Class 'Display','Monitor' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                instructions="1. Выполнить Get-PnpDevice по классам Display и Monitor.\n2. Извлечь активные и подключенные дисплеи.",
            )

        # Аудио / Звук / Микрофоны
        if any(w in q for w in ("звук", "аудио", "микрофон", "динамик", "колонки", "наушник", "sound", "audio", "mic")):
            return DynamicToolPlan(
                intent="Аудит звуковых устройств и аудиоинтерфейсов",
                tool_name="audio-devices-inspector",
                tool_title="Аудит аудиоустройств (Audio Devices Inspector)",
                description_ru="Инспекция звуковых карт, микрофонов, колонок и аудиовыходов в Windows.",
                probe_type="powershell",
                probe_script="Get-PnpDevice -Class 'AudioEndpoint','Media' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                instructions="1. Выполнить Get-PnpDevice для аудиоустройств.\n2. Собрать статус и названия источников звука.",
            )

        # Bluetooth устройства
        if any(w in q for w in ("bluetooth", "блютуз", "bt")):
            return DynamicToolPlan(
                intent="Аудит Bluetooth адаптеров и подключенных устройств",
                tool_name="bluetooth-device-inspector",
                tool_title="Аудит Bluetooth устройств (Bluetooth Inspector)",
                description_ru="Инспекция Bluetooth адаптеров и связанных беспроводных устройств.",
                probe_type="powershell",
                probe_script="Get-PnpDevice -Class 'Bluetooth' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                instructions="1. Выполнить Get-PnpDevice для Bluetooth устройств.\n2. Проверить статус сопряжения и активности.",
            )

        # Камеры и веб-камеры
        if any(w in q for w in ("камер", "веб-камер", "вебкамер", "camera", "webcam")):
            return DynamicToolPlan(
                intent="Аудит камер и устройств захвата видео",
                tool_name="camera-devices-inspector",
                tool_title="Аудит камер и веб-камер (Camera Inspector)",
                description_ru="Инспекция встроенных и внешних веб-камер и видеосенсоров.",
                probe_type="powershell",
                probe_script="Get-PnpDevice -Class 'Camera','Image' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                instructions="1. Выполнить Get-PnpDevice для классов Camera и Image.\n2. Проверить статус подключения.",
            )

        # Журналы событий / Логи
        if any(w in q for w in ("лог", "журнал", "eventlog", "event", "ошибк")):
            return DynamicToolPlan(
                intent="Анализ системных журналов и событий ошибок Windows",
                tool_name="eventlog-inspector",
                tool_title="Анализ журналов событий (Event Log Inspector)",
                description_ru="Сбор и анализ критических событий и ошибок из журналов System и Application.",
                probe_type="collector",
                collector_name="eventlog",
                instructions="1. Запустить EventLogCollector.\n2. Проанализировать последние критические ошибки и предупреждения.",
            )

        # Процессы / Диспетчер задач
        if any(w in q for w in ("процесс", "process", "taskmgr", "поток")):
            return DynamicToolPlan(
                intent="Снимок активных процессов Windows",
                tool_name="process-inspector",
                tool_title="Инспектор процессов (Process Inspector)",
                description_ru="Снимок запущенных процессов, потребления ресурсов CPU и памяти.",
                probe_type="collector",
                collector_name="process",
                instructions="1. Запустить ProcessCollector.\n2. Собрать топ процессов по ресурсам.",
            )

        # Давно не запускавшиеся / неиспользуемые программы
        if any(w in q for w in ("давно не", "не запускавш", "неиспользуем", "редко запускаем", "не запускались", "заброшенн", "dormant", "unused", "rarely used")):
            return DynamicToolPlan(
                intent="Аудит и поиск давно не запускавшихся и неиспользуемых программ",
                tool_name="dormant-software-auditor",
                tool_title="Аудит давно не запускавшихся программ (Dormant Software Auditor)",
                description_ru="Двухэтапный аудит ПО Windows: 1) Сбор перечня установленных программ из реестра (HKLM/HKCU). 2) Анализ истории запусков через артефакты UserAssist (ROT13) и Prefetch для выявления программ, не запускавшихся длительное время.",
                probe_type="collector",
                collector_name="software",
                instructions="1. Выполнить инвентаризацию установленных приложений через SoftwareCollector/SoftwareAuditEngine (HKLM, HKCU, Wow6432Node).\n2. Собрать артефакты запусков из веток реестра UserAssist (ROT13) и каталога Prefetch.\n3. Сопоставить список программ с историей запусков и выявить приложения, не запускавшиеся более 60-90 дней или не запускавшиеся вовсе.\n4. Предоставить рекомендации и команды деинсталляции.",
            )

        # Установленные программы
        if any(w in q for w in ("программ", "приложени", "софт", "software", "установлен")):
            return DynamicToolPlan(
                intent="Инвентаризация установленных программ",
                tool_name="software-inventory-inspector",
                tool_title="Инвентаризация установленного ПО (Software Inspector)",
                description_ru="Сбор списка установленных программ из реестра и пакетов Windows с анализом активности.",
                probe_type="collector",
                collector_name="software",
                instructions="1. Запустить SoftwareCollector / SoftwareAuditEngine.\n2. Сформировать перечень установленных приложений и историю запусков.",
            )

        # Обновления Windows
        if any(w in q for w in ("обновлен", "update", "kb", "патч")):
            return DynamicToolPlan(
                intent="Анализ состояния обновлений Windows",
                tool_name="windows-updates-inspector",
                tool_title="Инспектор обновлений Windows (Update Inspector)",
                description_ru="Проверка установленных KB-патчей и статуса ожидания перезагрузки.",
                probe_type="collector",
                collector_name="update",
                instructions="1. Запустить UpdateCollector.\n2. Проверить историю и статус обновлений.",
            )

        # Сеть / Порты
        if any(w in q for w in ("порт", "port", "сеть", "network", "соединени", "сокет", "ip", "dns", "адаптер")):
            return DynamicToolPlan(
                intent="Аудит сетевых интерфейсов и портов",
                tool_name="network-ports-auditor",
                tool_title="Аудит сетевых интерфейсов и портов (Network Ports Auditor)",
                description_ru="Проверка активных сетевых адаптеров, прослушиваемых портов TCP/UDP и соединений.",
                probe_type="collector",
                collector_name="network",
                instructions="1. Запустить NetworkCollector из apps/windows/core/modules.\n2. Собрать список открытых портов и адаптеров.",
            )

        # Службы Windows
        if any(w in q for w in ("служб", "service", "сервис")):
            return DynamicToolPlan(
                intent="Аудит служб Windows",
                tool_name="services-status-inspector",
                tool_title="Инспектор служб Windows (Services Inspector)",
                description_ru="Анализ состояния служб, типов автозапуска и поиск проблемных сервисов.",
                probe_type="collector",
                collector_name="services",
                instructions="1. Запустить ServicesCollector.\n2. Проверить остановленные службы с автозапуском.",
            )

        # Общие папки / Расшаривание / SMB
        if any(w in q for w in ("расшар", "общ папка", "общую папку", "общие папки", "сетевая папка", "сетевую папку", "smb", "share", "share folder")):
            return DynamicToolPlan(
                intent="Аудит и управление общими папками Windows (SMB Shares)",
                tool_name="folder-sharing-manager",
                tool_title="Управление общими папками (Folder Sharing Manager)",
                description_ru="Инспекция активных сетевых ресурсов SMB и предоставление общего доступа к папкам.",
                probe_type="powershell",
                probe_script="Get-SmbShare | Select-Object Name, Path, Description, ScopeName | ConvertTo-Json",
                instructions="1. Выполнить Get-SmbShare для инспекции активных сетевых ресурсов.\n2. Предоставить инструкции по GUI и PowerShell для New-SmbShare.",
            )

        # Диски / Память / Хранилище
        if any(w in q for w in ("диск", "disk", "smart", "мест", "хранилищ", "накопител")):
            return DynamicToolPlan(
                intent="Аудит дисков и накопителей",
                tool_name="storage-health-inspector",
                tool_title="Аудит дисков и накопителей (Storage Health Inspector)",
                description_ru="Проверка состояния физических дисков, томов, свободного места и SMART.",
                probe_type="collector",
                collector_name="storage",
                instructions="1. Запустить StorageCollector.\n2. Проверить свободное место и состояние SMART.",
            )

        # Автозагрузка / Производительность
        if any(w in q for w in ("автозагрузк", "startup", "тормоз", "нагрузк", "cpu", "ram", "памят")):
            return DynamicToolPlan(
                intent="Анализ производительности и автозагрузки",
                tool_name="performance-startup-auditor",
                tool_title="Аудит производительности и автозагрузки",
                description_ru="Поиск узких мест CPU/RAM и проверка записей автозагрузки Windows.",
                probe_type="collector",
                collector_name="performance",
                instructions="1. Запустить PerformanceCollector.\n2. Проверить программы автозапуска и нагрузку.",
            )

        # Драйверы и PnP ошибки
        if any(w in q for w in ("драйвер", "driver", "pnp", "диспетчер устройств")):
            return DynamicToolPlan(
                intent="Аудит пакетов драйверов и ошибок PnP",
                tool_name="driver-packages-auditor",
                tool_title="Аудит драйверов и PnP устройств",
                description_ru="Сбор пакетов драйверов DriverStore и выявление сбойных PnP устройств.",
                probe_type="collector",
                collector_name="driver",
                instructions="1. Запустить DriverCollector.\n2. Проверить пакеты драйверов и ошибки оборудования.",
            )

        # Дефолтный зонд общего назначения (безопасный опрос PnP)
        slug = to_ascii_slug(q[:25])
        return DynamicToolPlan(
            intent=query,
            tool_name=f"probe-{slug}",
            tool_title=f"Зонд: {query[:35]}",
            description_ru=f"Диагностический зонд оборудования и конфигурации для запроса: {query}",
            probe_type="powershell",
            probe_script="Get-PnpDevice -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
            instructions=f"1. Выполнить опрос PnP устройств системы для запроса: {query}",
        )

    async def execute_probe(self, plan: DynamicToolPlan) -> Tuple[Any, Optional[str]]:
        """Исполнение зонда на хосте Windows."""
        command_used = plan.probe_script

        if plan.probe_type == "collector" and plan.collector_name:
            collector = self.collectors.get(plan.collector_name)
            if collector:
                try:
                    res = await asyncio.to_thread(collector.collect)
                    return res.to_dict() if hasattr(res, "to_dict") else res, f"apps.windows.core.modules.{plan.collector_name}_collector.collect()"
                except Exception as e:
                    logger.warning(f"Ошибка выполнения коллектора {plan.collector_name}: {e}")

        if plan.probe_script and platform.system() == "Windows":
            try:
                proc = await asyncio.to_thread(
                    subprocess.run,
                    ["powershell", "-NoProfile", "-Command", plan.probe_script],
                    capture_output=True,
                    text=True,
                    timeout=12,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    try:
                        parsed = json.loads(proc.stdout.strip())
                        return parsed, plan.probe_script
                    except json.JSONDecodeError:
                        return proc.stdout.strip(), plan.probe_script
            except Exception as e:
                logger.warning(f"Ошибка выполнения PowerShell зонда '{plan.probe_script}': {e}")

        return {"status": "ok", "message": "Опрос выполнен через базовый WinAPI интерфейс"}, command_used

    async def synthesize_response_stream(
        self,
        query: str,
        plan: DynamicToolPlan,
        probe_data: Any,
        command_used: Optional[str],
        conversation_id: Optional[str] = None,
    ):
        """Потоковый синтез отчета по частям (чанками) с сохранением в историю сессии."""
        # Нормализация одиночного объекта словаря в список
        if isinstance(probe_data, dict) and any(
            k in probe_data for k in ("InstanceId", "FriendlyName", "Name", "DeviceID", "DriverName")
        ):
            probe_data = [probe_data]

        # Специализированное форматирование списков устройств (принтеры, мыши, USB, мониторы и др.)
        if (
            isinstance(probe_data, list)
            and len(probe_data) > 0
            and isinstance(probe_data[0], dict)
            and any(
                k in probe_data[0]
                for k in ("InstanceId", "FriendlyName", "Name", "DeviceID", "DriverName")
            )
        ):
            full_reply = await self.synthesize_response(
                query, plan, probe_data, command_used, conversation_id=conversation_id
            )
            # Для готовых форматированных таблиц устройств отдаем небольшими смысловыми фрагментами
            lines = full_reply.split("\n")
            for line in lines:
                yield line + "\n"
                await asyncio.sleep(0.015)
            return

        # Вызов LLM в режиме стриминга
        model = await self._get_model()
        full_text_acc = []

        if model:
            try:
                context_extra = ""
                if conversation_id and conversation_id in self.sessions and self.sessions[conversation_id]:
                    history_snip = "\n".join(
                        f"{m['role']}: {m['content'][:250]}" for m in self.sessions[conversation_id][-4:]
                    )
                    context_extra = f"\nКонтекст предыдущего диалога:\n{history_snip}\n"

                prompt = (
                    f"Пользователь задал вопрос о системе Windows: «{query}».{context_extra}\n"
                    f"Инструмент: {plan.tool_title}\n"
                    f"Собранные фактические данные с хоста:\n"
                    f"```json\n{json.dumps(probe_data, ensure_ascii=False, indent=2)[:3000]}\n```\n\n"
                    f"Сформируй понятный, профессиональный, красивый Markdown-ответ на русском языке с эмодзи и списками. "
                    f"Не придумывай факты, опирайся строго на собранные данные.\n\n"
                    f"ВАЖНО: Если ты предлагаешь пользователю выполнить какое-либо действие, исправление, оптимизацию или настройку в Windows "
                    f"(например: включение аудита через auditpol, остановка/отключение/запуск службы, очистка диска, завершение процесса, изменение реестра и т.д.), "
                    f"обязательно добавь в самый конец ответа блок действия в формате:\n"
                    f"```action\n"
                    f'{{\n  "action_id": "уникальный_id_на_латинице",\n  "action_type": "custom_command",\n  "title": "Краткое название действия на русском",\n  "description": "Что именно произойдет в системе",\n  "target": "объект_или_команда",\n  "risk": "caution",\n  "execution_command": "точная_команда_powershell_или_cmd"\n}}\n'
                    f"```"
                )

                # Проверяем методы потоковой генерации у модели (chat_stream / generate_content_stream / ask)
                if hasattr(model, "chat_stream"):
                    async for chunk in model.chat_stream(prompt):
                        if chunk:
                            full_text_acc.append(chunk)
                            yield chunk
                elif hasattr(model, "generate_content_stream"):
                    async for chunk in model.generate_content_stream(prompt):
                        if chunk:
                            full_text_acc.append(chunk)
                            yield chunk
                elif hasattr(model, "ask"):
                    res = await model.ask(prompt)
                    if res:
                        full_text_acc.append(res)
                        yield res
            except Exception as e:
                logger.debug(f"LLM streaming synthesis fallback: {e}")

        if not full_text_acc:
            fallback = (
                f"### 🔍 {plan.tool_title}\n"
                f"Запрос: *«{query}»*\n\n"
                f"**Результаты системного опроса:**\n"
                f"```json\n{json.dumps(probe_data, ensure_ascii=False, indent=2)[:1500]}\n```\n"
                + (f"\nКоманда проверки: `{command_used}`" if command_used else "")
            )
            yield fallback
            full_reply_str = fallback
        else:
            full_reply_str = "".join(full_text_acc)

        # Сохраняем ход диалога в сессию
        if conversation_id:
            self.sessions.setdefault(conversation_id, []).append({"role": "user", "content": query})
            self.sessions[conversation_id].append({"role": "model", "content": full_reply_str})

    def get_execution_metadata(self, plan: DynamicToolPlan, probe_data: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Формирует список задействованных агентов и источников знаний."""
        agents: List[Dict[str, Any]] = [
            {
                "name": "DynamicWindowsToolEngine",
                "role": "Оркестратор системных зондов и синтеза ответов",
                "type": "orchestrator",
                "icon": "🧠",
            },
        ]
        if plan.collector_name == "software" or "software" in plan.tool_name or "dormant" in plan.tool_name:
            agents.append({
                "name": "SoftwareAuditEngine",
                "role": "Агент инвентаризации ПО и анализа артефактов запусков",
                "type": "collector",
                "icon": "📦",
            })
            agents.append({
                "name": "UserAssist & Prefetch Parser",
                "role": "Парсер артефактов активности и истории исполнения (ROT13 / WevtAPI)",
                "type": "agent",
                "icon": "⏱️",
            })
        elif plan.collector_name:
            agents.append({
                "name": f"{plan.collector_name.capitalize()}Collector",
                "role": f"Системный коллектор подсистемы apps/windows ({plan.collector_name})",
                "type": "collector",
                "icon": "🔍",
            })
        elif plan.probe_type == "powershell":
            agents.append({
                "name": "PowerShell System Probe",
                "role": "Агент прямого WinAPI / WMI / PnP зондирования хоста",
                "type": "probe",
                "icon": "⚡",
            })

        # LLM agent
        model_name = "Google Gemini 3.7 Flash"
        try:
            from src.config import ai_cfg
            raw_m = getattr(ai_cfg, "gemini_model_id", "Gemini 3.7 Flash")
            if "gemini" in raw_m.lower():
                model_name = "Google Gemini 3.7 Flash"
            else:
                model_name = raw_m
        except Exception:
            pass

        agents.append({
            "name": model_name,
            "role": "Анализ системных фактов и синтез ответа",
            "type": "llm",
            "icon": "🤖",
        })

        knowledge: List[Dict[str, Any]] = []
        if plan.collector_name == "software" or "software" in plan.tool_name or "dormant" in plan.tool_name:
            knowledge.append({
                "title": "Windows UserAssist Specification (ROT13)",
                "description": "Спецификация и декодер артефактов запусков программ из реестра Windows Explorer",
                "type": "artifact",
                "badge": "Реестр HKCU",
            })
            knowledge.append({
                "title": "Windows Prefetch Execution Database",
                "description": "База данных временных меток и хэшей запуска бинарных файлов (C:\\Windows\\Prefetch)",
                "type": "artifact",
                "badge": "Prefetch",
            })
            knowledge.append({
                "title": "Windows Registry Uninstall Keys",
                "description": "База установленного ПО: HKLM/HKCU/Wow6432Node Uninstall",
                "type": "registry",
                "badge": "Uninstall DB",
            })
        elif "mouse" in plan.tool_name or "usb" in plan.tool_name or "pnp" in (plan.probe_script or "").lower():
            knowledge.append({
                "title": "Windows PnP & VID/PID Hardware Registry",
                "description": "Спецификация идентификаторов производителей оборудования (VID/PID)",
                "type": "hardware_db",
                "badge": "PnP Vendor DB",
            })
            knowledge.append({
                "title": "Win32 PnP Device Specifications",
                "description": "Спецификация классов устройств и состояний Get-PnpDevice",
                "type": "winapi",
                "badge": "WinAPI",
            })
        elif "printer" in plan.tool_name:
            knowledge.append({
                "title": "Win32_Printer CIM / WMI Model",
                "description": "Спецификация управления очередями и драйверами печати",
                "type": "wmi",
                "badge": "CIM / WMI",
            })

        knowledge.append({
            "title": f"Навык: {plan.tool_name}",
            "description": f"Каталог .skills/ ({plan.description_ru})",
            "type": "skill",
            "badge": ".skills",
        })
        knowledge.append({
            "title": "Инженерный регламент AI Breadboard & SafeOps",
            "description": "Стандарты безопасности выполнения системных команд и Fail-Fast проверок",
            "type": "standards",
            "badge": "GEMINI.md",
        })

        return agents, knowledge

    async def synthesize_response(
        self,
        query: str,
        plan: DynamicToolPlan,
        probe_data: Any,
        command_used: Optional[str],
        conversation_id: Optional[str] = None,
    ) -> str:
        """Синтез структурированного отчета на русском языке (синхронно / целиком)."""
        reply_result = ""

        # Специализированное форматирование для аудита программного обеспечения (SoftwareCollector)
        if plan.collector_name == "software" or "software" in plan.tool_name or "dormant" in plan.tool_name or (isinstance(probe_data, dict) and probe_data.get("domain_name") == "software"):
            metrics = probe_data.get("metrics", {}) if isinstance(probe_data, dict) else {}
            findings = probe_data.get("findings", []) if isinstance(probe_data, dict) else []
            total_apps = metrics.get("total_apps_count", len(findings))
            active_apps_cnt = metrics.get("active_apps_count", 0)
            unused_apps_cnt = metrics.get("unused_apps_count", metrics.get("dormant_apps_count", 0))
            ms_cnt = metrics.get("microsoft_apps_count", 0)
            third_cnt = metrics.get("third_party_apps_count", 0)

            dormant_findings = [f for f in findings if f.get("category") == "dormant_software"]
            unknown_pub_findings = [f for f in findings if f.get("category") == "unknown_publisher"]

            lines = [
                f"### 🔍 {plan.tool_title}",
                f"Я провел двухэтапный анализ программного обеспечения хоста: вначале собрал полный список установленных приложений, а затем сопоставил их с историей активности в реестре UserAssist (ROT13) и системном каталоге Prefetch.\n",
                "#### 📋 Этап 1: Инвентаризация установленного ПО",
                f"- **Всего приложений в реестре:** {total_apps}",
                f"- **Стороннее ПО:** {third_cnt}",
                f"- **Системные компоненты Microsoft:** {ms_cnt}\n",
                "#### ⏱️ Этап 2: Аудит истории запусков и активности (UserAssist / Prefetch)",
                f"- **Активных программ (запускались недавно):** {active_apps_cnt}",
                f"- **Давно не запускавшихся или заброшенных программ:** {len(dormant_findings) or unused_apps_cnt}\n",
            ]

            if dormant_findings:
                lines.append("#### ⚠️ Выявленные неиспользуемые и давно не запускавшиеся программы:")
                for idx, f in enumerate(dormant_findings[:15], 1):
                    evidence = f.get("evidence", {})
                    name = evidence.get("display_name") or evidence.get("name") or f.get("title", "")
                    publisher = evidence.get("publisher") or "Издатель не указан"
                    exec_info = evidence.get("execution_info") or {}
                    last_run = exec_info.get("last_run_time") if isinstance(exec_info, dict) else getattr(exec_info, "last_run_time", None)
                    run_count = exec_info.get("run_count", 0) if isinstance(exec_info, dict) else getattr(exec_info, "run_count", 0)
                    install_date = evidence.get("install_date") or "Неизвестна"
                    uninstall_str = evidence.get("uninstall_string") or ""
                    purpose = evidence.get("purpose_description") or ""

                    status_str = f"Последний запуск: `{last_run}`" if last_run else "Ни разу не запускалась (нет записей запусков)"
                    lines.append(f"{idx}. **{name}** ({publisher})")
                    lines.append(f"   - **Активность:** {status_str} (всего запусков: {run_count})")
                    if install_date and install_date != "Неизвестна":
                        lines.append(f"   - **Дата установки:** {install_date}")
                    if purpose:
                        lines.append(f"   - **Назначение:** {purpose}")
                    if uninstall_str:
                        lines.append(f"   - **Путь к деинсталлятору:** `{uninstall_str}`")
                    lines.append("")

                if len(dormant_findings) > 15:
                    lines.append(f"*...и ещё {len(dormant_findings) - 15} неиспользуемых программ.*")
            elif unknown_pub_findings:
                lines.append("#### ℹ️ Программы без указания издателя:")
                for idx, f in enumerate(unknown_pub_findings[:10], 1):
                    lines.append(f"{idx}. **{f.get('title')}**: {f.get('description')}")
            else:
                lines.append("✅ Все установленные программы регулярно используются или являются активными системными сервисами.")

            lines.append("\n💡 **Рекомендация SafeOps:** Удалите неиспользуемые программы через «Установку и удаление программ» для освобождения дискового пространства и оптимизации системы.")
            if command_used:
                lines.append(f"\nКоманда проверки: `{command_used}`")

            reply_result = "\n".join(lines)

        # Нормализация одиночного объекта словаря в список
        elif isinstance(probe_data, dict) and any(
            k in probe_data for k in ("InstanceId", "FriendlyName", "Name", "DeviceID", "DriverName")
        ):
            probe_data = [probe_data]

        # Специализированное форматирование списков устройств (принтеры, мыши, USB, мониторы и др.)
        if not reply_result and (
            isinstance(probe_data, list)
            and len(probe_data) > 0
            and isinstance(probe_data[0], dict)
            and any(
                k in probe_data[0]
                for k in ("InstanceId", "FriendlyName", "Name", "DeviceID", "DriverName")
            )
        ):
            items = probe_data
            active = []
            history = []
            for item in items:
                inst = str(item.get("InstanceId") or item.get("DeviceID") or "")
                name = str(item.get("FriendlyName") or item.get("Name") or item.get("name") or "Устройство")
                cls = str(item.get("Class") or item.get("Type") or ("Принтер" if "DriverName" in item else "Device"))
                driver = item.get("DriverName")
                port = item.get("PortName")
                is_default = bool(item.get("Default"))

                vendor = lookup_vendor(inst) if inst else (driver or "Windows")
                st = str(item.get("Status") or "OK")
                is_ok = st.upper() in ("OK", "0", "TRUE", "NORMAL")
                entry = {
                    "name": name,
                    "class": cls,
                    "vendor": vendor,
                    "driver": driver,
                    "port": port,
                    "is_default": is_default,
                    "instance_id": inst,
                    "status": "Подключено / Готово (OK)" if is_ok else "Не активно / Ошибка",
                    "is_connected": is_ok,
                }
                if is_ok:
                    active.append(entry)
                else:
                    history.append(entry)

            lines = [
                f"### 🔍 {plan.tool_title}",
                f"В системе обнаружено записей: **{len(items)}** (активно / готово к работе: **{len(active)}**, другие: **{len(history)}**).\n",
            ]
            if active:
                lines.append("**Текущие активные устройства:**")
                for a in active:
                    cls_label = f" [{a['class']}]" if a["class"] not in ("Device", "PrintQueue", "Printer", "Принтер") else ""
                    default_label = " 🌟 *(По умолчанию)*" if a.get("is_default") else ""
                    details = []
                    if a.get("driver"):
                        details.append(f"Драйвер: `{a['driver']}`")
                    if a.get("port"):
                        details.append(f"Порт: `{a['port']}`")
                    detail_str = f" ({', '.join(details)})" if details else f" — Производитель: *{a['vendor']}*"
                    lines.append(f"- 🟢 **{a['name']}**{default_label}{cls_label}{detail_str}")
                lines.append("")

            if history:
                lines.append("**Дополнительные устройства / история реестра PnP:**")
                for h in history[:12]:
                    cls_label = f" [{h['class']}]" if h["class"] not in ("Device", "Принтер") else ""
                    lines.append(f"- ⚪ **{h['name']}**{cls_label} — *{h['vendor']}* (`{h['instance_id'][:45]}...`)")
                if len(history) > 12:
                    lines.append(f"- *...и ещё {len(history) - 12} записей в реестре PnP.*")
                lines.append("")

            if command_used:
                lines.append(f"Команда инспекции: `{command_used}`")

            reply_result = "\n".join(lines)
        elif not reply_result:
            # Вызов LLM для генерации ответа по собранным фактам
            model = await self._get_model()
            if model:
                try:
                    context_extra = ""
                    if conversation_id and conversation_id in self.sessions and self.sessions[conversation_id]:
                        history_snip = "\n".join(
                            f"{m['role']}: {m['content'][:250]}" for m in self.sessions[conversation_id][-4:]
                        )
                        context_extra = f"\nКонтекст предыдущего диалога:\n{history_snip}\n"

                    prompt = (
                        f"Пользователь задал вопрос о системе Windows: «{query}».{context_extra}\n"
                        f"Инструмент: {plan.tool_title}\n"
                        f"Собранные фактические данные с хоста:\n"
                        f"```json\n{json.dumps(probe_data, ensure_ascii=False, indent=2)[:3000]}\n```\n\n"
                        f"Сформируй понятный, профессиональный, красивый Markdown-ответ на русском языке с эмодзи и списками. "
                        f"Не придумывай факты, опирайся строго на собранные данные.\n\n"
                        f"ВАЖНО: Если ты предлагаешь пользователю выполнить какое-либо действие, исправление, оптимизацию или настройку в Windows "
                        f"(например: включение аудита через auditpol, остановка/отключение/запуск службы, очистка диска, завершение процесса, изменение реестра и т.д.), "
                        f"обязательно добавь в самый конец ответа блок действия в формате:\n"
                        f"```action\n"
                        f'{{\n  "action_id": "уникальный_id_на_латинице",\n  "action_type": "custom_command",\n  "title": "Краткое название действия на русском",\n  "description": "Что именно произойдет в системе",\n  "target": "объект_или_команда",\n  "risk": "caution",\n  "execution_command": "точная_команда_powershell_или_cmd"\n}}\n'
                        f"```"
                    )
                    if hasattr(model, "ask"):
                        res = await model.ask(prompt)
                        if res:
                            reply_result = res
                except Exception as e:
                    logger.debug(f"LLM synthesis fallback: {e}")

            if not reply_result:
                # Простой fallback формат
                reply_result = (
                    f"### 🔍 {plan.tool_title}\n"
                    f"Запрос: *«{query}»*\n\n"
                    f"**Результаты системного опроса:**\n"
                    f"```json\n{json.dumps(probe_data, ensure_ascii=False, indent=2)[:1500]}\n```\n"
                    + (f"\nКоманда проверки: `{command_used}`" if command_used else "")
                )

        # Сохраняем ход диалога в сессию
        if conversation_id:
            self.sessions.setdefault(conversation_id, []).append({"role": "user", "content": query})
            self.sessions[conversation_id].append({"role": "model", "content": reply_result})

        return reply_result

    def save_skill(self, plan: DynamicToolPlan, command_used: Optional[str]) -> Dict[str, Any]:
        """Автоматическое сохранение сгенерированного навыка в .skills/ и .agents/skills/."""
        safe_name = to_ascii_slug(plan.tool_name)
        target_dirs = [
            __root__ / ".skills" / safe_name,
            __root__ / ".agents" / "skills" / safe_name,
        ]

        already_existed = any((t_dir / "SKILL.md").exists() for t_dir in target_dirs)

        skill_md_content = f"""---
name: {safe_name}
description: Automated assistant skill for: {plan.description_ru}
---

# {plan.tool_title}

## 🎯 Назначение (Purpose)
{plan.description_ru}

## 🚀 Триггеры и применение (When to Use & Triggers)
Используется при запросах пользователя о системном оборудовании, истории подключений и экспресс-диагностике в интерфейсе Test Computer (/tc) и консоли.

## ⚙️ Протокол выполнения (Execution Protocol)
{plan.instructions}
"""

        created_path = ""
        for t_dir in target_dirs:
            try:
                t_dir.mkdir(parents=True, exist_ok=True)
                skill_file = t_dir / "SKILL.md"
                skill_file.write_text(skill_md_content, encoding="utf-8")
                if command_used and not command_used.startswith("apps.windows"):
                    scripts_dir = t_dir / "scripts"
                    scripts_dir.mkdir(parents=True, exist_ok=True)
                    (scripts_dir / "probe.ps1").write_text(command_used, encoding="utf-8")
                if not created_path:
                    created_path = str(skill_file.relative_to(__root__))
            except Exception as e:
                logger.warning(f"Не удалось записать навык в {t_dir}: {e}")

        if not created_path:
            created_path = f".skills/{safe_name}/SKILL.md"

        if already_existed:
            logger.info(f"✨ Навык уже существует (обновлен): {created_path}")
        else:
            logger.info(f"✨ Сформирован и сохранён новый динамический навык: {created_path}")

        return {
            "name": safe_name,
            "title": plan.tool_title,
            "path": created_path,
            "description_ru": plan.description_ru,
            "is_new": not already_existed,
        }

    def extract_remediation_actions(self, probe_data: Any, reply: str = "") -> List[Dict[str, Any]]:
        """Извлекает список доступных SafeOps-исправлений из данных коллектора и текста ответа."""
        actions: List[Dict[str, Any]] = []
        seen_ids = set()

        # 1. Извлечение из структурированных findings коллектора
        if isinstance(probe_data, dict):
            findings = probe_data.get("findings", [])
            if isinstance(findings, list):
                for f in findings:
                    if isinstance(f, dict):
                        f_actions = f.get("actions", [])
                        if isinstance(f_actions, list):
                            for a in f_actions:
                                if isinstance(a, dict):
                                    aid = a.get("action_id") or a.get("target") or a.get("execution_command")
                                    if aid and aid not in seen_ids:
                                        seen_ids.add(aid)
                                        actions.append({
                                            "action_id": str(a.get("action_id") or f"action_{len(actions)+1}"),
                                            "action_type": str(a.get("action_type") or "custom_command"),
                                            "title": str(a.get("title") or a.get("action_id") or "Выполнить исправление"),
                                            "description": str(a.get("description") or ""),
                                            "target": str(a.get("target") or ""),
                                            "risk": str(a.get("risk") or "caution"),
                                            "execution_command": str(a.get("execution_command") or ""),
                                        })

        # 2. Извлечение структурированных блоков ```action ... ``` или ```json:action ... ```
        if reply:
            clean_reply = reply
            action_blocks = re.findall(r"```(?:action|json:action|json)?\s*(\{[\s\S]*?\})\s*```", reply, re.IGNORECASE)
            for block in action_blocks:
                try:
                    act_obj = extract_json_block(block)
                    if not act_obj:
                        try:
                            act_obj = json.loads(block)
                        except Exception:
                            pass
                    if isinstance(act_obj, dict) and any(k in act_obj for k in ("action_id", "execution_command", "target", "title")):
                        aid = act_obj.get("action_id") or f"action_{len(actions)+1}"
                        if aid not in seen_ids:
                            seen_ids.add(aid)
                            actions.append({
                                "action_id": str(aid),
                                "action_type": str(act_obj.get("action_type") or "custom_command"),
                                "title": str(act_obj.get("title") or aid),
                                "description": str(act_obj.get("description") or ""),
                                "target": str(act_obj.get("target") or ""),
                                "risk": str(act_obj.get("risk") or "caution"),
                                "execution_command": str(act_obj.get("execution_command") or ""),
                            })
                except Exception:
                    pass

            clean_reply = re.sub(r"```(?:action|json:action|json)?\s*\{[\s\S]*?\}\s*```", "", clean_reply, flags=re.IGNORECASE)

            # 3. Извлечение тегов [ACTION: {...}]
            tag_blocks = re.findall(r"\[ACTION:\s*(\{[\s\S]*?\})\s*\]", clean_reply, re.IGNORECASE)
            for block in tag_blocks:
                try:
                    act_obj = json.loads(block)
                    if isinstance(act_obj, dict):
                        aid = act_obj.get("action_id") or f"action_{len(actions)+1}"
                        if aid not in seen_ids:
                            seen_ids.add(aid)
                            actions.append({
                                "action_id": str(aid),
                                "action_type": str(act_obj.get("action_type") or "custom_command"),
                                "title": str(act_obj.get("title") or aid),
                                "description": str(act_obj.get("description") or ""),
                                "target": str(act_obj.get("target") or ""),
                                "risk": str(act_obj.get("risk") or "caution"),
                                "execution_command": str(act_obj.get("execution_command") or ""),
                            })
                except Exception:
                    pass

            clean_reply = re.sub(r"\[ACTION:\s*\{[\s\S]*?\}\s*\]", "", clean_reply, flags=re.IGNORECASE)

            # 4. Извлечение команд auditpol
            audit_cmds = re.findall(r"(auditpol(?:\.exe)?\s+/set\s+[^\r\n`]+)", clean_reply, re.IGNORECASE)
            for full_cmd in audit_cmds:
                aid = "apply_audit_policy"
                if aid not in seen_ids:
                    seen_ids.add(aid)
                    actions.append({
                        "action_id": aid,
                        "action_type": "custom_command",
                        "title": "Включить политику аудита Windows",
                        "description": f"Настройка аудита через команду: {full_cmd.strip()}",
                        "target": "Audit Policy",
                        "risk": "caution",
                        "execution_command": full_cmd.strip(),
                    })

            # Если в тексте упоминается предложение включить аудит процессов, но явного блока не было
            reply_lower = clean_reply.lower()
            if ("аудит" in reply_lower or "audit" in reply_lower) and any(w in reply_lower for w in ("включ", "активир", "настро", "требуется", "подтвердите")) and any(w in reply_lower for w in ("процесс", "process", "создани")):
                aid = "enable_process_creation_audit"
                if aid not in seen_ids and "apply_audit_policy" not in seen_ids:
                    seen_ids.add(aid)
                    actions.append({
                        "action_id": aid,
                        "action_type": "custom_command",
                        "title": "Включить расширенный аудит создания процессов",
                        "description": "Включение аудита создания процессов через auditpol (Process Creation)",
                        "target": "Process Creation Audit",
                        "risk": "caution",
                        "execution_command": 'auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable',
                    })

            # 5. Извлечение команд Set-Service / Stop-Service / Start-Service
            svc_matches = re.findall(r"(Set-Service\s+-Name\s+['\"]?([a-zA-Z0-9_-]+)['\"]?\s+-StartupType\s+Disabled)", clean_reply, re.IGNORECASE)
            for full_cmd, svc_name in svc_matches:
                aid = f"disable_service_{svc_name.lower()}"
                if aid not in seen_ids:
                    seen_ids.add(aid)
                    actions.append({
                        "action_id": aid,
                        "action_type": "disable_service",
                        "title": f"Отключить службу '{svc_name}'",
                        "description": f"Отключение службы через PowerShell: {full_cmd}",
                        "target": svc_name,
                        "risk": "caution",
                        "execution_command": full_cmd,
                    })

            stop_matches = re.findall(r"(Stop-Service\s+-Name\s+['\"]?([a-zA-Z0-9_-]+)['\"]?(?:\s+-Force)?)", clean_reply, re.IGNORECASE)
            for full_cmd, svc_name in stop_matches:
                aid = f"stop_service_{svc_name.lower()}"
                if aid not in seen_ids:
                    seen_ids.add(aid)
                    actions.append({
                        "action_id": aid,
                        "action_type": "stop_service",
                        "title": f"Остановить службу '{svc_name}'",
                        "description": f"Остановка службы через PowerShell: {full_cmd}",
                        "target": svc_name,
                        "risk": "caution",
                        "execution_command": full_cmd,
                    })

        return actions

    async def process_query(
        self, query: str, auto_create_skill: bool = False, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Полный конвейер: планирование инструмента -> сбор фактов -> синтез ответа -> сохранение навыка."""
        logger.info(f"[DynamicWindowsToolEngine] Обработка запроса (сессия={conversation_id}): '{query}'")

        # 1. Планирование с учетом контекста
        plan = await self.plan_tool(query, conversation_id=conversation_id)
        logger.info(f"[DynamicWindowsToolEngine] Сгенерирован план инструмента: {plan.tool_name} ({plan.probe_type})")

        # 2. Исполнение зонда на хосте
        probe_data, command_used = await self.execute_probe(plan)

        # 3. Синтез ответа с учетом истории
        reply = await self.synthesize_response(query, plan, probe_data, command_used, conversation_id=conversation_id)

        # 4. Сохранение навыка при необходимости
        created_skill = None
        if auto_create_skill:
            created_skill = self.save_skill(plan, command_used)

        remediation_actions = self.extract_remediation_actions(probe_data, reply)
        agents_used, knowledge_used = self.get_execution_metadata(plan, probe_data)

        return {
            "reply": reply,
            "command_executed": command_used,
            "created_skill": created_skill,
            "tool_plan": {
                "tool_name": plan.tool_name,
                "tool_title": plan.tool_title,
                "description_ru": plan.description_ru,
                "probe_type": plan.probe_type,
                "collector_name": plan.collector_name,
                "probe_script": plan.probe_script,
                "instructions": plan.instructions,
            },
            "remediation_actions": remediation_actions,
            "raw_data": probe_data,
            "agents_used": agents_used,
            "knowledge_used": knowledge_used,
            "status": "ok",
        }

    async def process_query_stream(
        self, query: str, auto_create_skill: bool = False, conversation_id: Optional[str] = None
    ):
        """Потоковый генератор этапов зондирования и фрагментов ответа в реальном времени с поддержкой контекста."""
        logger.info(f"[DynamicWindowsToolEngine] Потоковая обработка запроса (сессия={conversation_id}): '{query}'")

        # 0. Инициализация конвейера
        yield {
            "type": "stage",
            "stage": "init",
            "title": "Инициализация подсистем",
            "message": "🔌 Подключение к локальной подсистеме Windows API и сервисам хоста...",
            "details": "Подготовка системных интерфейсов WMI/PnP, коллекторов и контекста сессии",
        }

        # 1. Этап планирования
        yield {
            "type": "stage",
            "stage": "planning",
            "title": "Семантический анализ",
            "message": "🧠 Анализ семантики запроса и поиск подходящего инструмента...",
            "details": f"Сопоставление с 11 системными коллекторами и каталогом .skills для: «{query[:45]}»",
        }
        plan = await self.plan_tool(query, conversation_id=conversation_id)

        plan_detail = f"Инструмент: {plan.tool_title} | Тип: {plan.probe_type}"
        if plan.collector_name:
            plan_detail += f" ({plan.collector_name})"
        if plan.probe_script:
            plan_detail += f" | Скрипт: {plan.probe_script[:70]}..."

        yield {
            "type": "stage",
            "stage": "planned",
            "title": "План зондирования",
            "message": f"📋 Сформирован план: {plan.tool_title} ({plan.probe_type})",
            "tool_name": plan.tool_name,
            "tool_title": plan.tool_title,
            "probe_type": plan.probe_type,
            "collector_name": plan.collector_name,
            "description_ru": plan.description_ru,
            "probe_script": plan.probe_script,
            "details": plan_detail,
        }

        # 2. Этап выполнения зонда
        exec_target = f"Коллектор: {plan.collector_name}" if plan.collector_name else (f"PowerShell: {plan.probe_script[:80]}..." if plan.probe_script else "WinAPI прямой опрос")
        yield {
            "type": "stage",
            "stage": "executing",
            "title": "Исполнение зонда",
            "message": f"⚡ Запуск зонда на хосте Windows ({plan.probe_type}: {plan.collector_name or plan.tool_name})...",
            "probe_script": plan.probe_script,
            "details": exec_target,
        }
        probe_data, command_used = await self.execute_probe(plan)

        # 2.1 Этап постобработки данных
        records_count = len(probe_data) if isinstance(probe_data, list) else (len(probe_data.keys()) if isinstance(probe_data, dict) else 1)
        sample_keys = []
        if isinstance(probe_data, list) and probe_data and isinstance(probe_data[0], dict):
            sample_keys = list(probe_data[0].keys())[:4]
        elif isinstance(probe_data, dict):
            sample_keys = list(probe_data.keys())[:4]
        keys_str = f" [поля: {', '.join(sample_keys)}]" if sample_keys else ""

        yield {
            "type": "stage",
            "stage": "collected",
            "title": "Сбор метрик",
            "message": f"📡 Получены системные метрики ({records_count} записей). Подготовка данных...",
            "command_used": command_used,
            "records_count": records_count,
            "details": f"Собрано {records_count} записей метрик{keys_str} | Источник: {command_used or 'Host API'}",
        }

        # 3. Этап синтеза ответа со стримингом чанков
        model_name = "LLM"
        try:
            from src.config import ai_cfg
            raw_m = getattr(ai_cfg, "gemini_model_id", "Gemini 3.7 Flash")
            model_name = "Gemini 3.7 Flash" if "gemini" in raw_m.lower() else raw_m
        except Exception:
            pass

        yield {
            "type": "stage",
            "stage": "synthesizing",
            "title": "Синтез отчета",
            "message": f"✍️ Синтез структурированного отчета через {model_name}...",
            "model": model_name,
            "command_used": command_used,
            "details": f"Генерация профессионального отчета на русском языке через {model_name}",
        }

        full_reply_chunks = []
        async for chunk in self.synthesize_response_stream(
            query, plan, probe_data, command_used, conversation_id=conversation_id
        ):
            if chunk:
                full_reply_chunks.append(chunk)
                yield {
                    "type": "chunk",
                    "content": chunk,
                }

        final_reply = "".join(full_reply_chunks)

        # 4. Сохранение навыка при необходимости
        created_skill = None
        if auto_create_skill:
            created_skill = self.save_skill(plan, command_used)

        remediation_actions = self.extract_remediation_actions(probe_data, final_reply)
        agents_used, knowledge_used = self.get_execution_metadata(plan, probe_data)

        yield {
            "type": "done",
            "reply": final_reply,
            "command_executed": command_used,
            "created_skill": created_skill,
            "tool_plan": {
                "tool_name": plan.tool_name,
                "tool_title": plan.tool_title,
                "description_ru": plan.description_ru,
                "probe_type": plan.probe_type,
                "collector_name": plan.collector_name,
                "probe_script": plan.probe_script,
                "instructions": plan.instructions,
            },
            "remediation_actions": remediation_actions,
            "raw_data": probe_data,
            "agents_used": agents_used,
            "knowledge_used": knowledge_used,
            "status": "ok",
        }


