# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Autonomous Function-Calling Agent Loop
# =============================================================================
# Description:
#   Автономный агентский цикл (ReAct / Function Calling) для подсистемы Windows:
#   - Формирует системную инструкцию с описанием доступных инструментов
#   - Передает вызовы инструментов (tools) в модель
#   - Обрабатывает структурированные вызовы (tool_calls) или JSON-планы
#   - Исполняет запрошенные инструменты (включая create_custom_tool на лету)
#   - Предоставляет результаты обратно модели для финального синтеза фактов
#   - Генерирует SSE-события стриминга этапов в реальном времени
#
# Examples:
#   >>> from apps.windows.core.agent_loop import WindowsAgentLoop
#   >>> agent = WindowsAgentLoop(registry, model_resolver)
#   >>> async for evt in agent.run_stream("Какие мыши подключены?"):
#   ...     print(evt)
#
# File: agent_loop.py
# Project: AI-Breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Автономный агентский цикл с поддержкой нативного Function Calling и саморасширения."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

from src.logger import logger
from apps.windows.core.tools.base import BaseTool, ToolExecutionResult
from apps.windows.core.tools.dynamic_factory import DynamicSynthesizedTool, DynamicToolFactory
from apps.windows.core.tools.registry import ToolRegistry


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Извлечение JSON объекта из текста или блока разметки ```json ... ```."""
    if not text:
        return None
    text_clean = text.strip()
    try:
        data = json.loads(text_clean)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


class WindowsAgentLoop:
    """Интеллектуальный агентский цикл взаимодействия с инструментами Windows."""

    def __init__(
        self,
        registry: ToolRegistry,
        factory: DynamicToolFactory,
        model_getter: Callable[[], Any],
        model_info_resolver: Callable[[], Tuple[str, str, str]],
    ) -> None:
        """Инициализация агентского цикла.

        Args:
            registry: Реестр зарегистрированных инструментов.
            factory: Фабрика создания динамических инструментов.
            model_getter: Асинхронный коллбэк получения экземпляра языковой модели.
            model_info_resolver: Функция получения информации о модели (provider, model_id, display_name).
        """
        self.registry = registry
        self.factory = factory
        self._get_model = model_getter
        self._resolve_model_info = model_info_resolver

    def build_system_instruction(self) -> str:
        """Формирует системную инструкцию с описанием инструментов и правил SafeOps."""
        tools_list = self.registry.list_tools()
        tools_desc = []
        for t in tools_list:
            tools_desc.append(f"- **{t.name}** ({t.title}): {t.description}")

        tools_str = "\n".join(tools_desc)

        return (
            "Ты — интеллектуальный системный агент платформы AI Breadboard для ОС Windows.\n"
            "Твоя задача — исследовать систему, собирать достоверные факты и формировать профессиональные отчеты.\n\n"
            "### 🛠️ ДОСТУПНЫЕ ИНСТРУМЕНТЫ:\n"
            f"{tools_str}\n\n"
            "### ⚙️ ПРАВИЛА ВЫПОЛНЕНИЯ:\n"
            "1. Если для решения задачи подходит встроенный инструмент (например, windows_collector), используй его.\n"
            "2. Если требуется специализированный или отсутствующий опрос (например, история мышей, принтеры, USB, мониторы, сетевые папки SMB, специфические ключи реестра), "
            "ИСПОЛЬЗУЙ инструмент `create_custom_tool` — сформируй точный, безопасный read-only скрипт PowerShell с конвертацией вывода в JSON (`| ConvertTo-Json`).\n"
            "3. При формировании ответа опирайся СТРОГО на собранные данные.\n"
            "4. Если предлагаешь пользователю действие/исправление (отключение службы, очистка диска, включение аудита auditpol), добавь блок действия:\n"
            "```action\n"
            '{\n  "action_id": "уникальный_id",\n  "action_type": "custom_command",\n  "title": "Название действия",\n  "description": "Что произойдет",\n  "target": "объект",\n  "risk": "caution",\n  "execution_command": "powershell_или_cmd_команда"\n}\n'
            "```\n\n"
            "Для вызова инструмента верни JSON:\n"
            '```tool_call\n{"tool_name": "имя_инструмента", "arguments": { ... }}\n```\n'
            "Если сбор данных завершен, сформируй красивый финальный ответ в Markdown на русском языке."
        )

    async def plan_and_select_tool(
        self,
        query: str,
        session_history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Определяет, какой инструмент требуется вызвать для запроса пользователя."""
        model = await self._get_model()
        if not model:
            return self._heuristic_fallback(query)

        system_instruction = self.build_system_instruction()

        history_context = ""
        if session_history:
            history_snip = "\n".join(f"{m['role']}: {m['content'][:250]}" for m in session_history[-4:])
            history_context = f"Контекст предыдущего диалога:\n{history_snip}\n\n"

        prompt = (
            f"{history_context}Запрос пользователя: «{query}»\n\n"
            "Выбери наиболее подходящий инструмент из доступных или создай новый через `create_custom_tool`.\n"
            "Ответь СТРОГО в формате JSON:\n"
            "```json\n"
            "{\n"
            '  "tool_name": "имя_инструмента",\n'
            '  "arguments": { ... }\n'
            "}\n"
            "```"
        )

        try:
            resp_str = ""
            if hasattr(model, "ask"):
                resp_str = await model.ask(prompt, system_instruction=system_instruction)
            elif hasattr(model, "chat"):
                resp_str = await model.chat(prompt)

            if resp_str:
                data = extract_json_block(resp_str)
                if data and "tool_name" in data:
                    t_name = str(data["tool_name"]).strip()
                    args = data.get("arguments", {})
                    if not isinstance(args, dict):
                        args = {}
                    return t_name, args
        except Exception as e:
            logger.warning(f"[WindowsAgentLoop] Ошибка выбора инструмента через LLM: {e}")

        # Эвристический fallback при сбое связи с моделью
        return self._heuristic_fallback(query)

    def _heuristic_fallback(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Безопасный эвристический fallback при недоступности LLM."""
        q = query.lower()

        # 1. Доменные коллекторы
        if any(w in q for w in ("служб", "service", "сервис")):
            return "windows_collector", {"collector_name": "services"}
        if any(w in q for w in ("диск", "disk", "smart", "мест", "хранилищ")):
            return "windows_collector", {"collector_name": "storage"}
        if any(w in q for w in ("порт", "port", "сеть", "network", "ip", "сокет")):
            return "windows_collector", {"collector_name": "network"}
        if any(w in q for w in ("dormant", "давно не запускавш", "неиспользуем")):
            return "create_custom_tool", {
                "tool_name": "dormant-software-auditor",
                "tool_title": "Аудитор неиспользуемого ПО (UserAssist / Prefetch)",
                "description_ru": "Двухэтапный аудит установленного и неиспользуемого ПО",
                "probe_script": "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, Publisher, InstallDate | ConvertTo-Json",
                "instructions": "Собрать список установленного ПО и сопоставить с UserAssist/Prefetch.",
            }
        if any(w in q for w in ("программ", "software", "приложен", "установл")):
            return "windows_collector", {"collector_name": "software"}
        if any(w in q for w in ("лог", "журнал", "event", "ошибк")):
            return "windows_collector", {"collector_name": "eventlog"}

        # 2. Специализированные динамические инструменты PnP / WinAPI
        if any(w in q for w in ("мыш", "мышей", "mouse", "манипулятор")):
            return "create_custom_tool", {
                "tool_name": "mouse-history-inspector",
                "tool_title": "Инспектор истории подключения мышей",
                "description_ru": "Аудит истории подключения мышей и манипуляторов HID/USB",
                "probe_script": "Get-PnpDevice -Class 'Mouse' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                "instructions": "Собрать историю и состояние мышей и координатных устройств в реестре PnP.",
            }

        if any(w in q for w in ("usb", "юсб", "флешк", "флэшк")):
            return "create_custom_tool", {
                "tool_name": "usb-device-auditor",
                "tool_title": "Аудитор USB-устройств",
                "description_ru": "Аудит подключенных и ранее использованных USB-устройств",
                "probe_script": "Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object { $_.InstanceId -like '*USB*' } | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                "instructions": "Собрать список устройств с шиной USB.",
            }

        if any(w in q for w in ("принтер", "печать", "printer", "print")):
            return "create_custom_tool", {
                "tool_name": "printers-inspector",
                "tool_title": "Инспектор принтеров и очередей печати",
                "description_ru": "Опрос локальных и сетевых принтеров и драйверов печати",
                "probe_script": "Get-Printer -ErrorAction SilentlyContinue | Select-Object Name, Type, DriverName, PortName, Shared, Default | ConvertTo-Json",
                "instructions": "Собрать список всех настроенных принтеров Windows.",
            }

        if any(w in q for w in ("монитор", "экран", "дисплей", "видеокарт", "display", "monitor", "gpu")):
            return "create_custom_tool", {
                "tool_name": "display-monitor-inspector",
                "tool_title": "Инспектор мониторов и видеоадаптеров",
                "description_ru": "Опрос видеокарт и подключенных мониторов",
                "probe_script": "Get-PnpDevice -Class 'Display', 'Monitor' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                "instructions": "Собрать данные о дисплеях и видеоадаптерах.",
            }

        if any(w in q for w in ("звук", "аудио", "микрофон", "динамик", "audio", "sound")):
            return "create_custom_tool", {
                "tool_name": "audio-devices-inspector",
                "tool_title": "Инспектор звуковых устройств",
                "description_ru": "Опрос звуковых адаптеров, динамиков и микрофонов",
                "probe_script": "Get-PnpDevice -Class 'AudioEndpoint', 'MEDIA' -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
                "instructions": "Собрать аудиоустройства хоста.",
            }

        if any(w in q for w in ("драйвер", "driver", "pnp", "устройств", "device")):
            return "windows_collector", {"collector_name": "driver"}

        # По умолчанию создаем динамический PnP зонд
        return "create_custom_tool", {
            "tool_name": f"probe-{to_ascii_slug(query[:20])}",
            "tool_title": f"Зонд: {query[:30]}",
            "description_ru": f"Инспекция устройств и конфигурации для запроса: {query}",
            "probe_script": "Get-PnpDevice -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
            "instructions": f"Опрос оборудования хоста для запроса: {query}",
        }

    def build_synthesis_prompt(
        self,
        query: str,
        tool_name: str,
        tool_title: str,
        data: Any,
        session_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Формирует итоговый промпт для синтеза ответа."""
        history_context = ""
        if session_history:
            history_snip = "\n".join(f"{m['role']}: {m['content'][:250]}" for m in session_history[-4:])
            history_context = f"\nКонтекст предыдущего диалога:\n{history_snip}\n"

        data_json = json.dumps(data, ensure_ascii=False, indent=2)[:3500] if data is not None else "{}"

        return (
            f"Пользователь задал вопрос о системе Windows: «{query}».{history_context}\n"
            f"Инструмент: {tool_title} (`{tool_name}`)\n"
            f"Фактические результаты с хоста Windows:\n"
            f"```json\n{data_json}\n```\n\n"
            "Сформируй понятный, профессиональный, красивый Markdown-ответ на русском языке с эмодзи, таблицами или списками. "
            "Опирайся СТРОГО на собранные факты, не выдумывай несуществующих параметров.\n\n"
            "ВАЖНО: Если ты предлагаешь пользователю оптимизацию, исправление или настройку (например, включение аудита auditpol, остановка/отключение службы, очистка диска, завершение процесса), "
            "обязательно добавь в самый конец ответа структурированный блок действия:\n"
            "```action\n"
            '{\n  "action_id": "уникальный_id_на_латинице",\n  "action_type": "custom_command",\n  "title": "Краткое название действия на русском",\n  "description": "Что именно произойдет в системе",\n  "target": "объект_или_команда",\n  "risk": "caution",\n  "execution_command": "точная_команда_powershell_или_cmd"\n}\n'
            "```"
        )

