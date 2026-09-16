# Руководство по созданию стандартных Python ReAct-агентов (Core Code Agents)

> **Цель:** Изучить разработку бэкенд-агентов на Python на базе ReAct-архитектуры, LangChain и LangGraph в каталоге `src/ai/agents/`.

---

## 📋 Содержание

1. [Введение](#введение)
2. [Структура бэкенд-агента](#структура-бэкенд-агента)
3. [Шаг 1: Создание файла агента](#шаг-1-создание-файла-агента)
4. [Шаг 2: Подключение инструментов (Tools)](#шаг-2-подключение-инструментов-tools)
5. [Шаг 3: Настройка LLM провайдера и системного промпта](#шаг-3-настройка-llm-провайдера-и-системного-промпта)
6. [Шаг 4: Регистрация API эндпоинта](#шаг-4-регистрация-api-эндпоинта)
7. [Шаг 5: Написание тестов](#шаг-5-написание-тестов)

---

## Введение

**Стандартный Python-агент (Core Code Agent)** — это серверный сервис в `src/ai/agents/`, который решает автономные задачи посредством ReAct-цикла (`Thought` $\rightarrow$ `Action` $\rightarrow$ `Observation` $\rightarrow$ `Final Answer`).

Пример существующего агента в системе:
- `src/ai/agents/agent.py` — `MediaSearchAgent` (автономный агент поиска фильмов и сериалов через RAG, Web-Search и Python REPL).
- `src/ai/agents/travel_agent.py` — `TravelAgent` (агент поиска авиабилетов и маршрутов).

---

## Структура бэкенд-агента

```
src/ai/agents/
├── agent.py               # MediaSearchAgent (основной агент)
├── prompts.py             # Шаблоны системных промптов
├── tools.py               # Инструменты для агентов (web_search, rag_search, etc.)
├── travel_agent.py        # Специализированный travel-агент
└── my_custom_agent.py     # Ваш новый агент
```

---

## Шаг 1: Создание файла агента

Создайте файл `src/ai/agents/my_custom_agent.py`:

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Custom Python ReAct Agent
# Description: Агент для автономного выполнения пользовательских задач.
# File: my_custom_agent.py
# Project: ai-breadboard
# Package: src.ai.agents
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, Any

from src.logger import logger
from src.utils.jjson import j_loads_ns
from .tools import web_search, rag_search, python_eval


class CustomTaskAgent:
    """Агент для выполнения кастомных задач через ReAct паттерн."""

    def __init__(self, config_path: Path = Path('config.json'), ai_model=None):
        """Инициализация агента и загрузка конфигурации."""
        self.config = j_loads_ns(config_path)
        self.ai_model = ai_model
        self.tools = [web_search, rag_search, python_eval]
        self.timeout = 60

        logger.info("[CustomTaskAgent] Агент успешно инициализирован")

    def _get_llm(self):
        """Создает инстанс LLM провайдера (Gemini / Ollama)."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        import os

        api_key = os.environ.get('GEMINI_API_KEY', '')
        return ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            google_api_key=api_key,
            temperature=0.1,
        )

    async def run(self, query: str) -> Dict[str, Any]:
        """Выполняет ReAct-цикл рассуждения и действий по запросу."""
        from langgraph.prebuilt import create_react_agent

        llm = self._get_llm()
        system_prompt = "You are a helpful assistant. Use tools to satisfy the query."

        agent_executor = create_react_agent(
            llm,
            self.tools,
            prompt=system_prompt,
        )

        try:
            result = await asyncio.wait_for(
                agent_executor.ainvoke({'messages': [('user', query)]}),
                timeout=self.timeout,
            )
            messages = result.get('messages', [])
            last_message = messages[-1].content if messages else ''
            return {'status': 'success', 'result': last_message}

        except asyncio.TimeoutError:
            logger.error(f"[CustomTaskAgent] Таймаут при выполнении: {query}")
            return {'status': 'error', 'message': 'Timeout exceeded'}
        except Exception as ex:
            logger.error(f"[CustomTaskAgent] Ошибка: {ex}", exc_info=True)
            return {'status': 'error', 'message': str(ex)}
```

---

## Шаг 2: Подключение инструментов (Tools)

Инструменты оборачиваются декоратором `@tool` из `langchain_core.tools`:

```python
from langchain_core.tools import tool

@tool
def calculate_metrics(data_str: str) -> str:
    """Вычисляет сводные метрики для переданных данных в формате JSON.
    
    Args:
        data_str: Строка JSON с массивом чисел.
    """
    import json
    data = json.loads(data_str)
    return f"Sum: {sum(data)}, Count: {len(data)}"
```

---

## Шаг 3: Регистрация API эндпоинта

В файле `src/api/router_agents.py` добавьте маршрут для FastAPI:

```python
from fastapi import APIRouter, HTTPException
from src.ai.agents.my_custom_agent import CustomTaskAgent

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@router.post("/custom-agent/run")
async def run_custom_agent(payload: dict):
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    agent = CustomTaskAgent()
    result = await agent.run(query)
    return result
```

---

## Шаг 4: Написание тестов

Создайте файл `tests/test_custom_agent.py`:

```python
import pytest
from src.ai.agents.my_custom_agent import CustomTaskAgent

@pytest.mark.asyncio
async def test_custom_agent_initialization():
    agent = CustomTaskAgent()
    assert agent is not None
    assert len(agent.tools) == 3
```

---

## 🔗 Связанные документы

- [`creating-agents.md`](creating-agents.md) — Главный индекс создания агентов
- [`dynamic-subagents.md`](dynamic-subagents.md) — Руководство по динамическим субагентам
- [`developing-skills.md`](developing-skills.md) — Разработка навыков
