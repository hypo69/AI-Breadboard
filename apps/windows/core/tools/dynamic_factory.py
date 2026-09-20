# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Dynamic Tool Factory & Meta-Tool
# =============================================================================
# Description:
#   Фабрика динамических инструментов (DynamicToolFactory) и системный мета-инструмент
#   `create_custom_tool`, позволяющий модели на лету синтезировать, валидировать,
#   регистрировать в рантайме и выполнять новые специализированные инструменты.
#
# Examples:
#   >>> from apps.windows.core.tools.dynamic_factory import DynamicToolFactory, CreateCustomToolMetaTool
#   >>> factory = DynamicToolFactory(registry)
#   >>> meta_tool = CreateCustomToolMetaTool(factory)
#
# File: dynamic_factory.py
# Project: AI-Breadboard
# Package: apps.windows.core.tools
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Фабрика динамических инструментов и мета-инструмент create_custom_tool."""

from __future__ import annotations

import asyncio
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from header import __root__
from src.logger import logger
from apps.windows.core.models import RiskLevel
from apps.windows.core.tools.base import BaseTool, ToolExecutionResult
from apps.windows.core.tools.registry import ToolRegistry


def to_ascii_slug(text: str) -> str:
    """Преобразует строку в безопасный ASCII-слаг для имени инструмента."""
    translit_map = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya", " ": "-",
    }
    res = []
    for char in text.lower():
        if char in translit_map:
            res.append(translit_map[char])
        elif char.isalnum() or char in ("-", "_"):
            res.append(char)
        else:
            res.append("-")
    slug = "".join(res)
    slug = re.sub(r"-+", "-", slug).strip("-_")
    return slug or "custom-tool"


class DynamicSynthesizedTool(BaseTool):
    """Инструмент, синтезированный моделью на лету в процессе диалога."""

    is_dynamic = True

    def __init__(
        self,
        name: str,
        title: str,
        description: str,
        probe_script: str,
        parameters_schema: Optional[Dict[str, Any]] = None,
        instructions: str = "",
        risk_level: RiskLevel = RiskLevel.SAFE,
    ) -> None:
        """Инициализация динамического инструмента."""
        self.name = to_ascii_slug(name)
        self.title = title or self.name
        self.description = description or f"Динамический инструмент {self.title}"
        self.probe_script = probe_script.strip()
        self.instructions = instructions or "Выполнить системный зонд и вернуть структурированные данные."
        self.parameters_schema = parameters_schema or {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }
        self.risk_level = risk_level

    async def execute(self, **kwargs: Any) -> ToolExecutionResult:
        """Исполнение динамического PowerShell скрипта с подстановкой параметров."""
        if platform.system() != "Windows":
            return ToolExecutionResult(
                tool_name=self.name,
                status="ok",
                data={"mock": True, "message": "Платформа не является Windows, зонд симулирован."},
                command_executed=self.probe_script,
            )

        # Подготовка скрипта с подстановкой параметров
        exec_script = self.probe_script
        for k, v in kwargs.items():
            val_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
            exec_script = exec_script.replace(f"${k}", val_str)

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", exec_script],
                capture_output=True,
                text=True,
                timeout=12,
            )

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            if proc.returncode != 0 and not stdout:
                return ToolExecutionResult(
                    tool_name=self.name,
                    status="error",
                    data={"stderr": stderr},
                    message=f"Ошибка выполнения динамического инструмента: {stderr or 'код ' + str(proc.returncode)}",
                    command_executed=exec_script,
                )

            try:
                parsed = json.loads(stdout) if stdout else []
            except json.JSONDecodeError:
                parsed = stdout

            return ToolExecutionResult(
                tool_name=self.name,
                status="ok",
                data=parsed,
                message=f"Инструмент '{self.title}' успешно выполнил сбор данных.",
                command_executed=exec_script,
                metadata={
                    "is_dynamic": True,
                    "instructions": self.instructions,
                    "description_ru": self.description,
                },
            )
        except subprocess.TimeoutExpired:
            return ToolExecutionResult(
                tool_name=self.name,
                status="error",
                data=None,
                message="Превышен таймаут выполнения динамического инструмента (12 сек).",
                command_executed=exec_script,
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name=self.name,
                status="error",
                data=None,
                message=f"Сбой исполнения динамического инструмента: {e}",
                command_executed=exec_script,
            )


class DynamicToolFactory:
    """Фабрика создания, регистрации и сохранения динамических инструментов."""

    def __init__(self, registry: ToolRegistry) -> None:
        """Инициализация фабрики."""
        self.registry = registry

    def create_and_register(
        self,
        tool_name: str,
        tool_title: str,
        description_ru: str,
        probe_script: str,
        parameters_schema: Optional[Dict[str, Any]] = None,
        instructions: str = "",
        risk_level: str = "safe",
    ) -> DynamicSynthesizedTool:
        """Создает динамический инструмент и немедленно регистрирует его в активном реестре."""
        r_level = RiskLevel.SAFE
        try:
            r_level = RiskLevel(risk_level.lower())
        except Exception:
            pass

        tool = DynamicSynthesizedTool(
            name=tool_name,
            title=tool_title,
            description=description_ru,
            probe_script=probe_script,
            parameters_schema=parameters_schema,
            instructions=instructions,
            risk_level=r_level,
        )
        self.registry.register(tool, overwrite=True)
        return tool

    def save_as_skill(self, tool: DynamicSynthesizedTool) -> Dict[str, Any]:
        """Сохраняет динамический инструмент как постоянный навык в .skills/ и .agents/skills/."""
        safe_name = tool.name
        target_dirs = [
            __root__ / ".skills" / safe_name,
            __root__ / ".agents" / "skills" / safe_name,
        ]

        already_existed = any((t_dir / "SKILL.md").exists() for t_dir in target_dirs)

        skill_md_content = f"""---
name: {safe_name}
description: Automated assistant skill for: {tool.description}
---

# {tool.title}

## 🎯 Назначение (Purpose)
{tool.description}

## 🚀 Триггеры и применение (When to Use & Triggers)
Используется при запросах пользователя о конфигурации хоста, экспресс-диагностике и аудите в интерфейсе Test Computer (/tc).

## ⚙️ Протокол выполнения (Execution Protocol)
{tool.instructions}
"""

        created_path = ""
        for t_dir in target_dirs:
            try:
                t_dir.mkdir(parents=True, exist_ok=True)
                skill_file = t_dir / "SKILL.md"
                skill_file.write_text(skill_md_content, encoding="utf-8")
                if tool.probe_script and not tool.probe_script.startswith("apps.windows"):
                    scripts_dir = t_dir / "scripts"
                    scripts_dir.mkdir(parents=True, exist_ok=True)
                    (scripts_dir / "probe.ps1").write_text(tool.probe_script, encoding="utf-8")
                if not created_path:
                    created_path = str(skill_file.relative_to(__root__))
            except Exception as e:
                logger.warning(f"[DynamicToolFactory] Не удалось записать навык в {t_dir}: {e}")

        if not created_path:
            created_path = f".skills/{safe_name}/SKILL.md"

        return {
            "name": safe_name,
            "title": tool.title,
            "path": created_path,
            "description_ru": tool.description,
            "is_new": not already_existed,
        }


class CreateCustomToolMetaTool(BaseTool):
    """Системный мета-инструмент для создания новых инструментов моделью на лету."""

    name = "create_custom_tool"
    title = "Создание инструмента на лету"
    description = (
        "Создает, валидирует и регистрирует новый специализированный инструмент в памяти системы. "
        "Используй этот инструмент, когда встроенных инструментов недостаточно для точного ответа на вопрос пользователя "
        "(например: опрос специфических мышей, принтеров, Bluetooth, сетевых папок SMB, реестра или PnP устройств)."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Краткий идентификатор инструмента в kebab-case (например: 'mouse-history-inspector', 'usb-device-auditor')",
            },
            "tool_title": {
                "type": "string",
                "description": "Человекочитаемое название инструмента на русском языке",
            },
            "description_ru": {
                "type": "string",
                "description": "Подробное описание назначения инструмента на русском языке",
            },
            "probe_script": {
                "type": "string",
                "description": "PowerShell скрипт опроса с выводом в JSON (| ConvertTo-Json). Должен быть безопасным и read-only.",
            },
            "instructions": {
                "type": "string",
                "description": "Пошаговый протокол выполнения инструмента",
            },
        },
        "required": ["tool_name", "tool_title", "description_ru", "probe_script"],
    }
    risk_level = RiskLevel.SAFE

    def __init__(self, factory: DynamicToolFactory) -> None:
        """Инициализация мета-инструмента."""
        self.factory = factory

    async def execute(
        self,
        tool_name: str,
        tool_title: str,
        description_ru: str,
        probe_script: str,
        instructions: str = "",
        **kwargs: Any,
    ) -> ToolExecutionResult:
        """Регистрация нового инструмента и немедленный пробный запуск."""
        try:
            tool = self.factory.create_and_register(
                tool_name=tool_name,
                tool_title=tool_title,
                description_ru=description_ru,
                probe_script=probe_script,
                instructions=instructions,
            )

            # Немедленно запускаем созданный инструмент для получения данных
            exec_res = await tool.execute()

            return ToolExecutionResult(
                tool_name=self.name,
                status="ok" if exec_res.status == "ok" else "warn",
                data=exec_res.data,
                message=f"Инструмент '{tool.title}' успешно создан, зарегистрирован в рантайме и выполнен.",
                command_executed=tool.probe_script,
                metadata={
                    "created_tool_name": tool.name,
                    "created_tool_title": tool.title,
                    "created_tool_description": tool.description,
                    "is_new_tool": True,
                    "instructions": tool.instructions,
                },
            )
        except Exception as e:
            logger.error(f"[CreateCustomToolMetaTool] Сбой создания инструмента '{tool_name}': {e}", exc_info=True)
            return ToolExecutionResult(
                tool_name=self.name,
                status="error",
                data=None,
                message=f"Ошибка создания инструмента '{tool_name}': {e}",
            )

