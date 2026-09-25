# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Dynamic Tool & Skill Synthesis Engine
# =============================================================================
# Description:
#   Динамический движок синтеза инструментов и навыков на базе API Windows.
#   Использует модульный ToolRegistry, фабрику динамических инструментов на лету
#   и автономный агентский цикл (WindowsAgentLoop) с поддержкой Function Calling.
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

from header import __root__
from logger import logger
from apps.windows.core.models import RiskLevel
from apps.windows.core.tools.base import BaseTool, ToolExecutionResult
from apps.windows.core.tools.dynamic_factory import (
    CreateCustomToolMetaTool,
    DynamicSynthesizedTool,
    DynamicToolFactory,
    to_ascii_slug,
)
from apps.windows.core.tools.registry import ToolRegistry
from apps.windows.core.tools.system_tools import (
    SafePowerShellProbeTool,
    WindowsCollectorTool,
    register_system_tools,
)
from apps.windows.core.agent_loop import WindowsAgentLoop, extract_json_block


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
    """План выполнения инструмента (обратная совместимость)."""

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
    """Динамический оркестратор инструментов Windows с поддержкой Function Calling."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        """Инициализация движка и реестра инструментов."""
        self.chat_model = chat_model
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

        # 1. Инициализация ToolRegistry и системных инструментов
        self.registry = ToolRegistry()
        register_system_tools(self.registry)

        # 2. Инициализация фабрики динамических инструментов и мета-инструмента
        self.factory = DynamicToolFactory(self.registry)
        self.meta_tool = CreateCustomToolMetaTool(self.factory)
        self.registry.register(self.meta_tool)

        # 3. Инициализация агентского цикла
        self.agent_loop = WindowsAgentLoop(
            registry=self.registry,
            factory=self.factory,
            model_getter=self._get_model,
            model_info_resolver=self._resolve_model_info,
        )

        # Обратная совместимость для коллекторов
        collector_tool = self.registry.get("windows_collector")
        self.collectors = getattr(collector_tool, "collectors", {})

    def _resolve_model_info(self) -> Tuple[str, str, str]:
        """Определяет активного провайдера, ID модели и отображаемое имя из конфигурации.

        Returns:
            Tuple[str, str, str]: (provider, model_id, display_name)
        """
        try:
            from src.config import ai_cfg
            provider = getattr(ai_cfg, "provider", "") or ""

            if provider:
                provider_upper = str(provider).upper()
                # New format: use provider-specific model_id
                if provider_upper == "GEMINI":
                    model_id = getattr(ai_cfg, "gemini_model_id", getattr(ai_cfg, "model", "gemini-2.5-flash"))
                elif provider_upper == "GEMINI_CLI":
                    model_id = getattr(ai_cfg, "gemini_cli_model_id", getattr(ai_cfg, "model", "gemini-3.1-flash-lite"))
                elif provider_upper == "AGY":
                    model_id = getattr(ai_cfg, "agy_model_id", getattr(ai_cfg, "model", "agy-gemini-3.6-flash"))
                elif provider_upper == "OLLAMA":
                    model_id = getattr(ai_cfg, "ollama_model_id", getattr(ai_cfg, "model", "llama3.1"))
                elif provider_upper == "FOUNDRY":
                    model_id = getattr(ai_cfg, "foundry_model_id", getattr(ai_cfg, "model", "qwen2.5-1.5b"))
                else:
                    model_id = getattr(ai_cfg, "model", "default")
                return provider_upper, str(model_id), f"{provider_upper}: {model_id}"

            # Проверка булевых флагов активности провайдеров
            if getattr(ai_cfg, "use_ollama", False):
                model_id = getattr(ai_cfg, "ollama_model_id", getattr(ai_cfg, "model", "llama3.1"))
                return "OLLAMA", str(model_id), f"Ollama: {model_id}"
            if getattr(ai_cfg, "use_foundry", False):
                model_id = getattr(ai_cfg, "foundry_model_id", getattr(ai_cfg, "model", "qwen2.5-1.5b"))
                return "FOUNDRY", str(model_id), f"Foundry: {model_id}"
            if getattr(ai_cfg, "use_gemini_cli", False):
                model_id = getattr(ai_cfg, "gemini_cli_model_id", getattr(ai_cfg, "model", "gemini-3.1-flash-lite"))
                return "GEMINI_CLI", str(model_id), f"Gemini CLI: {model_id}"

            # Fallback to model field or gemini_model_id
            m = getattr(ai_cfg, "model", getattr(ai_cfg, "gemini_model_id", "AI"))
            return "AI", str(m), str(m)
        except Exception:
            return "AI", "default", "AI Model"

    async def _get_model(self) -> Any:
        """Получение активной языковой модели на основе конфигурации."""
        if self.chat_model:
            return self.chat_model
        try:
            from src.api.router_chat import get_chat_model
            provider, model_id, _ = self._resolve_model_info()

            if provider == "GEMINI_CLI" and not model_id.startswith(("gemini_cli:", "gemini-cli-")):
                model_key = f"gemini_cli:{model_id}"
            elif provider == "FOUNDRY" and not model_id.startswith("foundry:"):
                model_key = f"foundry:{model_id}"
            elif provider == "OLLAMA" and not model_id.startswith("ollama:"):
                model_key = f"ollama:{model_id}"
            elif provider == "AGY" and not model_id.startswith("agy-"):
                model_key = f"agy-{model_id}"
            elif provider in ("OPENAI", "DEEPSEEK", "GROQ", "OPENROUTER", "LMSTUDIO") and ":" not in model_id:
                model_key = f"{provider.lower()}:{model_id}"
            else:
                model_key = model_id

            return get_chat_model(model_key)
        except Exception as e:
            logger.debug(f"[DynamicWindowsToolEngine] Не удалось получить модель: {e}")
            return None

    async def plan_tool(self, query: str, conversation_id: Optional[str] = None) -> DynamicToolPlan:
        """Планирование стратегии зондирования на основе запроса пользователя."""
        session_history = self.sessions.get(conversation_id, []) if conversation_id else None
        selection = await self.agent_loop.plan_and_select_tool(query, session_history=session_history)

        if selection:
            t_name, args = selection
            if t_name == "create_custom_tool":
                raw_name = args.get("tool_name", f"probe-{to_ascii_slug(query[:20])}")
                return DynamicToolPlan(
                    intent=args.get("tool_title", query),
                    tool_name=to_ascii_slug(raw_name),
                    tool_title=args.get("tool_title", f"Инструмент: {query[:30]}"),
                    description_ru=args.get("description_ru", f"Диагностический зонд: {query}"),
                    probe_type="powershell",
                    probe_script=args.get("probe_script"),
                    instructions=args.get("instructions", "Выполнить зондирование хоста."),
                )
            elif t_name == "windows_collector":
                col_name = args.get("collector_name", "driver")
                return DynamicToolPlan(
                    intent=f"Аудит через коллектор {col_name}",
                    tool_name=f"{col_name}-collector",
                    tool_title=f"Коллектор Windows: {col_name.capitalize()}",
                    description_ru=f"Сбор системной информации через {col_name} коллектор",
                    probe_type="collector",
                    collector_name=col_name,
                    instructions=f"Запустить {col_name} коллектор подсистемы Windows.",
                )
            else:
                existing_tool = self.registry.get(t_name)
                title = getattr(existing_tool, "title", t_name)
                desc = getattr(existing_tool, "description", t_name)
                return DynamicToolPlan(
                    intent=title,
                    tool_name=t_name,
                    tool_title=title,
                    description_ru=desc,
                    probe_type="powershell" if "probe" in t_name else "winapi",
                    probe_script=args.get("script"),
                    instructions=f"Исполнение инструмента {t_name}",
                )

        # Резервный план
        return DynamicToolPlan(
            intent=query,
            tool_name=f"probe-{to_ascii_slug(query[:20])}",
            tool_title=f"Зонд: {query[:30]}",
            description_ru=f"Диагностический опрос для: {query}",
            probe_type="powershell",
            probe_script="Get-PnpDevice -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json",
            instructions="Выполнить опрос PnP устройств хоста.",
        )

    async def execute_probe(self, plan: DynamicToolPlan) -> Tuple[Any, Optional[str]]:
        """Исполнение зонда на хосте Windows через ToolRegistry."""
        if plan.collector_name:
            res = await self.registry.execute("windows_collector", collector_name=plan.collector_name)
            return res.data, res.command_executed

        if plan.probe_script:
            # Создаем и исполняем динамический инструмент через фабрику
            tool = self.factory.create_and_register(
                tool_name=plan.tool_name,
                tool_title=plan.tool_title,
                description_ru=plan.description_ru,
                probe_script=plan.probe_script,
                instructions=plan.instructions,
            )
            res = await tool.execute()
            return res.data, plan.probe_script

        return {"status": "ok", "message": "Опрос выполнен через базовый WinAPI интерфейс"}, None

    def build_synthesis_prompt(
        self,
        query: str,
        plan: DynamicToolPlan,
        probe_data: Any,
        conversation_id: Optional[str] = None,
    ) -> str:
        """Формирует структурированный промпт для LLM."""
        session_history = self.sessions.get(conversation_id) if conversation_id else None
        return self.agent_loop.build_synthesis_prompt(
            query=query,
            tool_name=plan.tool_name,
            tool_title=plan.tool_title,
            data=probe_data,
            session_history=session_history,
        )

    async def synthesize_response_stream(
        self,
        query: str,
        plan: DynamicToolPlan,
        probe_data: Any,
        command_used: Optional[str],
        conversation_id: Optional[str] = None,
    ):
        """Потоковый синтез ответа чанками с сохранением в историю сессии."""
        if isinstance(probe_data, dict) and any(
            k in probe_data for k in ("InstanceId", "FriendlyName", "Name", "DeviceID", "DriverName")
        ):
            probe_data = [probe_data]

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
            for line in full_reply.split("\n"):
                yield line + "\n"
                await asyncio.sleep(0.015)
            return

        model = await self._get_model()
        full_text_acc = []

        if model:
            try:
                prompt = self.build_synthesis_prompt(
                    query=query,
                    plan=plan,
                    probe_data=probe_data,
                    conversation_id=conversation_id,
                )

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
                logger.debug(f"[DynamicWindowsToolEngine] Streaming fallback: {e}")

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

        if conversation_id:
            self.sessions.setdefault(conversation_id, []).append({"role": "user", "content": query})
            self.sessions[conversation_id].append({"role": "model", "content": full_reply_str})

    async def synthesize_response(
        self,
        query: str,
        plan: DynamicToolPlan,
        probe_data: Any,
        command_used: Optional[str],
        conversation_id: Optional[str] = None,
    ) -> str:
        """Синтез структурированного отчета (синхронно / целиком)."""
        reply_result = ""

        # Специализированное форматирование для SoftwareCollector
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

        elif isinstance(probe_data, dict) and any(
            k in probe_data for k in ("InstanceId", "FriendlyName", "Name", "DeviceID", "DriverName")
        ):
            probe_data = [probe_data]

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
            model = await self._get_model()
            if model:
                try:
                    prompt = self.build_synthesis_prompt(
                        query=query,
                        plan=plan,
                        probe_data=probe_data,
                        conversation_id=conversation_id,
                    )
                    if hasattr(model, "ask"):
                        res = await model.ask(prompt)
                        if res:
                            reply_result = res
                except Exception as e:
                    logger.debug(f"[DynamicWindowsToolEngine] LLM synthesis fallback: {e}")

            if not reply_result:
                reply_result = (
                    f"### 🔍 {plan.tool_title}\n"
                    f"Запрос: *«{query}»*\n\n"
                    f"**Результаты системного опроса:**\n"
                    f"```json\n{json.dumps(probe_data, ensure_ascii=False, indent=2)[:1500]}\n```\n"
                    + (f"\nКоманда проверки: `{command_used}`" if command_used else "")
                )

        if conversation_id:
            self.sessions.setdefault(conversation_id, []).append({"role": "user", "content": query})
            self.sessions[conversation_id].append({"role": "model", "content": reply_result})

        return reply_result

    def save_skill(self, plan: DynamicToolPlan, command_used: Optional[str]) -> Dict[str, Any]:
        """Автоматическое сохранение сгенерированного навыка в .skills/ и .agents/skills/."""
        tool = DynamicSynthesizedTool(
            name=plan.tool_name,
            title=plan.tool_title,
            description=plan.description_ru,
            probe_script=command_used or plan.probe_script or "",
            instructions=plan.instructions,
        )
        return self.factory.save_as_skill(tool)

    def extract_remediation_actions(self, probe_data: Any, reply: str = "") -> List[Dict[str, Any]]:
        """Извлекает список доступных SafeOps-исправлений из данных коллектора и текста ответа."""
        actions: List[Dict[str, Any]] = []
        seen_ids = set()

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

    def get_execution_metadata(self, plan: DynamicToolPlan, probe_data: Any, use_rag: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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

        _, _, model_display_name = self._resolve_model_info()

        agents.append({
            "name": model_display_name,
            "role": "Анализ системных фактов и синтез ответа",
            "type": "llm",
            "icon": "🤖",
        })

        if use_rag:
            agents.append({
                "name": "KnowledgeBaseRAG",
                "role": "Поиск документации и контекста в базе знаний",
                "type": "rag",
                "icon": "📚",
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

        if use_rag:
            knowledge.append({
                "title": "База знаний RAG (AI Breadboard)",
                "description": "Индексированная системная документация и регламенты сценариев",
                "type": "rag",
                "badge": "RAG Store",
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

    async def process_query(
        self,
        query: str,
        auto_create_skill: bool = False,
        conversation_id: Optional[str] = None,
        keep_context: bool = False,
        use_rag: bool = True,
    ) -> Dict[str, Any]:
        """Полный конвейер: планирование инструмента -> сбор фактов -> синтез ответа -> сохранение навыка."""
        active_conv_id = conversation_id if keep_context else None
        logger.info(f"[DynamicWindowsToolEngine] Обработка запроса (сессия={active_conv_id}, keep_context={keep_context}, use_rag={use_rag}): '{query}'")

        plan = await self.plan_tool(query, conversation_id=active_conv_id)
        logger.info(f"[DynamicWindowsToolEngine] Сгенерирован план инструмента: {plan.tool_name} ({plan.probe_type})")

        probe_data, command_used = await self.execute_probe(plan)
        reply = await self.synthesize_response(query, plan, probe_data, command_used, conversation_id=active_conv_id)

        created_skill = None
        if auto_create_skill:
            created_skill = self.save_skill(plan, command_used)

        remediation_actions = self.extract_remediation_actions(probe_data, reply)
        agents_used, knowledge_used = self.get_execution_metadata(plan, probe_data, use_rag=use_rag)
        generated_prompt = self.build_synthesis_prompt(query, plan, probe_data, conversation_id=active_conv_id)

        return {
            "reply": reply,
            "command_executed": command_used,
            "created_skill": created_skill,
            "generated_prompt": generated_prompt,
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
        self,
        query: str,
        auto_create_skill: bool = False,
        conversation_id: Optional[str] = None,
        keep_context: bool = False,
        use_rag: bool = True,
    ):
        """Потоковый генератор этапов зондирования и фрагментов ответа в реальном времени."""
        active_conv_id = conversation_id if keep_context else None
        logger.info(f"[DynamicWindowsToolEngine] Потоковая обработка запроса (сессия={active_conv_id}, keep_context={keep_context}, use_rag={use_rag}): '{query}'")

        yield {
            "type": "stage",
            "stage": "init",
            "title": "Инициализация подсистем",
            "message": "🔌 Подключение к локальной подсистеме Windows API и сервисам хоста...",
            "details": "Подготовка системных интерфейсов WMI/PnP, коллекторов и контекста сессии",
        }

        if use_rag:
            yield {
                "type": "stage",
                "stage": "rag",
                "title": "Поиск в базе знаний RAG",
                "message": "📚 Поиск релевантного контекста в локальной базе знаний RAG...",
                "details": f"Поиск знаний и контекста для: «{query[:45]}»",
            }

        yield {
            "type": "stage",
            "stage": "planning",
            "title": "Семантический анализ & ReAct",
            "message": "🧠 Анализ семантики запроса и выбор/создание инструмента...",
            "details": f"Сопоставление с ToolRegistry и мета-инструментом create_custom_tool для: «{query[:45]}»",
        }
        plan = await self.plan_tool(query, conversation_id=active_conv_id)

        plan_detail = f"Инструмент: {plan.tool_title} | Тип: {plan.probe_type}"
        if plan.collector_name:
            plan_detail += f" ({plan.collector_name})"
        if plan.probe_script:
            plan_detail += f" | Скрипт: {plan.probe_script[:70]}..."

        yield {
            "type": "stage",
            "stage": "planned",
            "title": "План инструмента",
            "message": f"📋 Сформирован план: {plan.tool_title} ({plan.probe_type})",
            "tool_name": plan.tool_name,
            "tool_title": plan.tool_title,
            "probe_type": plan.probe_type,
            "collector_name": plan.collector_name,
            "description_ru": plan.description_ru,
            "probe_script": plan.probe_script,
            "details": plan_detail,
        }

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

        _, _, model_display_name = self._resolve_model_info()
        generated_prompt = self.build_synthesis_prompt(query, plan, probe_data, conversation_id=active_conv_id)

        yield {
            "type": "stage",
            "stage": "synthesizing",
            "title": "Синтез отчета",
            "message": f"✍️ Синтез структурированного отчета через {model_display_name}...",
            "model": model_display_name,
            "command_used": command_used,
            "generated_prompt": generated_prompt,
            "details": f"Генерация профессионального отчета на русском языке через {model_display_name}",
        }

        full_reply_chunks = []
        async for chunk in self.synthesize_response_stream(
            query, plan, probe_data, command_used, conversation_id=active_conv_id
        ):
            if chunk:
                full_reply_chunks.append(chunk)
                yield {
                    "type": "chunk",
                    "content": chunk,
                }

        final_reply = "".join(full_reply_chunks)

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
            "generated_prompt": generated_prompt,
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

