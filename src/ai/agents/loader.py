# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Universal Agent Loader & Registry
# =============================================================================
# Description:
#   Универсальный загрузчик и реестр агентов из внешнего каталога манифестов .agents.
#   Поддерживает загрузку классов по class_path или создание универсальных агентов
#   на основе декларативных манифестов JSON для CLI (gemini cli, agy cli) и API.
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.loader import load_agent_from_manifest, list_available_agents
#
#     agent = load_agent_from_manifest("windows_controller_agent")
#     agents_list = list_available_agents()
#
# File: loader.py
# Project: ai-breadboard
# Package: src.ai.agents
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 08:31:00
# =============================================================================

from __future__ import annotations
"""Универсальный загрузчик и реестр агентов из внешнего каталога манифестов .agents."""

import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from header import __root__
from logger import logger

# Каталог манифестов агентов – единая точка конфигурации в корне проекта
_MANIFEST_ROOT = __root__ / ".agents"


class UniversalDeclarativeAgent:
    """Универсальный агент, динамически создаваемый на основе декларативного JSON-манифеста."""

    def __init__(self, manifest: Dict[str, Any]) -> None:
        """Инициализирует агента по параметрам манифеста.

        Args:
            manifest: Словарь параметров из agent.json.
        """
        self.manifest = manifest
        self.agent_id = manifest.get("id", "generic_agent")
        self.name = manifest.get("name", self.agent_id)
        self.description = manifest.get("description", "")
        self.model = manifest.get("model", "gemini-3.1-flash")
        self.temperature = manifest.get("temperature", 0.1)
        self.max_steps = manifest.get("max_steps", 15)
        self.timeout = manifest.get("timeout_seconds", 60)
        self.system_prompt = manifest.get("system_prompt", "")
        self.declared_tools = manifest.get("tools", [])

    async def search(self, query: str) -> Dict[str, Any]:
        """Выполняет обработку запроса через языковую модель и инструменты.

        Args:
            query: Запрос пользователя.

        Returns:
            Dict[str, Any]: Результат работы агента.
        """
        from src.api.routers.core.router_chat import get_chat_model
        model = get_chat_model()
        prompt = f"{self.system_prompt}\n\nЗапрос пользователя: {query}" if self.system_prompt else query
        try:
            resp = await model.ask(prompt)
            return {"action": "agent_report", "agent_id": self.agent_id, "text": resp}
        except Exception as e:
            logger.error(f"[{self.agent_id}] Ошибка выполнения: {e}")
            return {"action": "error", "error": str(e)}

    async def search_stream(self, query: str):
        """Потоковая передача выполнения задачи."""
        yield {"status": f"🔍 Инициализация агента {self.name}..."}
        res = await self.search(query)
        yield {"result": res}


def list_available_agents() -> List[Dict[str, Any]]:
    """Возвращает список всех зарегистрированных манифестов агентов из каталога .agents.

    Returns:
        List[Dict[str, Any]]: Список словарей с метаданными агентов.
    """
    agents: List[Dict[str, Any]] = []
    if not _MANIFEST_ROOT.exists():
        return agents

    for manifest_path in _MANIFEST_ROOT.glob("*.json"):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "id" in data:
                data["manifest_file"] = manifest_path.name
                agents.append(data)
        except Exception as exc:
            logger.warning(f"[AgentLoader] Ошибка чтения манифеста {manifest_path.name}: {exc}")
    return agents


def load_agent_from_manifest(name_or_id: str) -> Any:
    """Загрузить и инициализировать агент по его имени манифеста или идентификатору.

    Args:
        name_or_id: Имя файла (без .json) или поле 'id' агента.

    Returns:
        Экземпляр класса агента или UniversalDeclarativeAgent.
    """
    clean_name = name_or_id.replace(".json", "").strip()
    manifest_path = _MANIFEST_ROOT / f"{clean_name}.json"

    # Если прямого файла нет, ищем по полю id среди всех манифестов
    if not manifest_path.is_file():
        for f in _MANIFEST_ROOT.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("id") == clean_name:
                    manifest_path = f
                    break
            except Exception:
                continue

    if not manifest_path.is_file():
        raise FileNotFoundError(f"Манифест агента '{clean_name}' не найден в {_MANIFEST_ROOT}")

    with manifest_path.open(encoding="utf-8") as f:
        manifest_data = json.load(f)

    class_path = manifest_data.get("class_path")
    if class_path:
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls()
        except Exception as exc:
            logger.warning(f"[AgentLoader] Не удалось загрузить класс {class_path}, используется универсальный исполнитель: {exc}")

    return UniversalDeclarativeAgent(manifest_data)
