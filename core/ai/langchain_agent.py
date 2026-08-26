# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: LangChain Breadboard Agent
# =============================================================================
# Описание:
#   Основной агент платформы AI Breadboard на базе ReAct-архитектуры.
#   Использует нативные инструменты (веб-поиск, RAG, Python-вычисления, чтение файлов).
#   Поддерживает Gemini и Ollama как LLM-бэкенды.
#
# File: langchain_agent.py
# Project: aibreadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import json
import asyncio
from pathlib import Path
from typing import AsyncIterator

from core.logger import logger
from core.utils.jjson import j_loads_ns

from core.ai.langchain_prompts import (
    GENERAL_AGENT_SYSTEM_PROMPT,
    MEDIA_SEARCH_SYSTEM_PROMPT,
    TOOL_SELECTION_GUIDELINES,
    RESULT_FORMAT_INSTRUCTIONS,
)
from core.ai.langchain_tools import (
    web_search,
    rag_search,
    python_eval,
    file_read,
)


class MediaSearchAgent:
    """Агент для автономной работы и рассуждений через LangChain + ReAct.

    Использует ReAct-агент с набором инструментов:
    - Поиск актуальной информации в интернете (web_search)
    - Поиск по базе знаний (rag_search)
    - Выполнение Python-кода (python_eval)
    - Чтение файлов проекта (file_read)
    """

    def __init__(self, config_path: Path = Path('config.json'), ai_model=...):
        """Инициализация агента.

        Args:
            config_path: Путь к config.json с секцией langchain.
            ai_model: Экземпляр AI-модели (передаётся из плагина, может не использоваться).
        """
        self.config = j_loads_ns(config_path)
        self.ai_model = ai_model

        langchain_cfg = getattr(self.config, 'langchain', object())
        self.llm_type = getattr(langchain_cfg, 'default_llm', 'gemini')
        self.max_steps = getattr(langchain_cfg, 'max_agent_steps', 15)
        self.timeout = getattr(langchain_cfg, 'search_timeout_seconds', 60)

        # Ленивая инициализация LLM (при первом вызове search)
        self._llm = ''
        self._langchain_cfg = langchain_cfg

        # Нативные инструменты (всегда доступны)
        self.native_tools = [
            web_search,
            rag_search,
            python_eval,
            file_read,
        ]

        logger.info(
            f'[BreadboardAgent] Инициализирован: llm={self.llm_type}, '
            f'max_steps={self.max_steps}, timeout={self.timeout}'
        )

    def _get_llm(self):
        """Ленивое создание LLM-инстанса при первом обращении."""
        if self._llm:
            return self._llm

        if self.llm_type == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = getattr(self._langchain_cfg, 'gemini_model', 'gemini-2.5-flash')
            api_key = os.environ.get('GOOGLE_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
            if not api_key:
                from core.secrets.api_key_state import load_api_keys
                loaded, _, _ = load_api_keys()
                aiza_keys = [k for k in loaded if k.startswith('AIzaSy')]
                if aiza_keys:
                    api_key = aiza_keys[0]
                elif loaded:
                    api_key = loaded[0]
            if not api_key:
                logger.error('[MediaSearchAgent] GOOGLE_API_KEY не задан в .env')
                raise EnvironmentError('GOOGLE_API_KEY не задан')
            self._llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.1,
            )
        else:
            from langchain_ollama import ChatOllama
            model_name = getattr(self._langchain_cfg, 'ollama_model', 'qwen2.5:7b')
            base_url = getattr(self._langchain_cfg, 'ollama_base_url', 'http://localhost:11434')
            self._llm = ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=0.1,
            )

        logger.info(f'[MediaSearchAgent] LLM создан: {self.llm_type}')
        return self._llm

    def _build_system_prompt(self) -> str:
        """Собирает полный системный промпт из компонентов."""
        return '\n\n'.join([
            MEDIA_SEARCH_SYSTEM_PROMPT,
            TOOL_SELECTION_GUIDELINES,
            RESULT_FORMAT_INSTRUCTIONS,
        ])

    async def search(self, query: str) -> dict:
        """Выполняет автономный поиск по запросу пользователя.

        Args:
            query: Текстовый запрос пользователя (напр. 'найди фильм Интерстеллар 1080p').

        Returns:
            dict с ключами:
            - action: 'player' | 'torrent' | 'info' | 'error'
            - data: словарь с результатами, зависящий от action
        """
        try:
            import re
            from langgraph.prebuilt import create_react_agent

            llm = self._get_llm()
            system_prompt = self._build_system_prompt()

            # Собираем инструменты: нативные + MCP (если доступен)
            all_tools = list(self.native_tools)

            # Пробуем подключить MCP-инструменты Playwright
            try:
                from core.ai.mcp_client import MCPClientManager
                async with MCPClientManager() as mcp:
                    mcp_tools = await mcp.get_tools()
                    if mcp_tools:
                        all_tools.extend(mcp_tools)
                        logger.info(f'[MediaSearchAgent] Подключено {len(mcp_tools)} MCP-инструментов')
            except Exception as mcp_err:
                logger.warning(f'[MediaSearchAgent] MCP недоступен, продолжаем без него: {mcp_err}')

            logger.info(f'[MediaSearchAgent] Запуск агента с {len(all_tools)} инструментами для: "{query}"')

            # Создаём ReAct-агент с поддержкой актуальной и устаревшей сигнатуры LangGraph
            try:
                agent_executor = create_react_agent(
                    llm,
                    all_tools,
                    prompt=system_prompt,
                )
            except TypeError:
                agent_executor = create_react_agent(
                    llm,
                    all_tools,
                    state_modifier=system_prompt,
                )

            # Запускаем с таймаутом
            result = await asyncio.wait_for(
                agent_executor.ainvoke({'messages': [('user', query)]}),
                timeout=self.timeout,
            )

            # Парсим ответ
            messages = result.get('messages', [])
            if not messages:
                return {'action': 'error', 'data': {'message': 'Агент не вернул ответ'}}

            last_message = messages[-1]
            raw_content = getattr(last_message, 'content', '')
            if isinstance(raw_content, list):
                content = "".join([
                    c.get('text', '') if isinstance(c, dict) else str(c)
                    for c in raw_content
                ])
            else:
                content = str(raw_content)

            cleaned_content = content.strip()
            if cleaned_content.startswith('```'):
                cleaned_content = re.sub(r'^```(?:json)?\s*', '', cleaned_content)
                cleaned_content = re.sub(r'\s*```$', '', cleaned_content).strip()

            # Пробуем распарсить JSON из ответа
            try:
                parsed = json.loads(cleaned_content)
                if isinstance(parsed, dict):
                    action = parsed.get('action', 'info')
                    return {'action': action, **parsed}
                return {'action': 'info', 'text': content}
            except (json.JSONDecodeError, ValueError):
                # LLM вернул текст вместо JSON — оборачиваем как info
                return {'action': 'info', 'text': content}

        except asyncio.TimeoutError:
            logger.error(f'[MediaSearchAgent] Таймаут ({self.timeout}с) при поиске: "{query}"')
            return {'action': 'error', 'data': {'message': f'Превышено время ожидания ({self.timeout}с)'}}
        except Exception as e:
            logger.error(f'[MediaSearchAgent] Ошибка при поиске: {e}')
            return {'action': 'error', 'data': {'message': str(e)}}

    async def search_stream(self, query: str) -> AsyncIterator[dict]:
        """Потоковый поиск с промежуточными статусами.

        Yields:
            dict с ключом 'status' (промежуточный) или 'result' (финальный).
        """
        yield {'status': '🔍 Анализирую запрос...'}

        yield {'status': '🤖 Запускаю LangChain агент...'}

        try:
            yield {'status': '⚙️ Подключаю инструменты поиска...'}

            result = await self.search(query)

            action = result.get('action', 'error')
            if action == 'torrent':
                yield {'status': '🧲 Найдены торренты!'}
            elif action == 'player':
                yield {'status': '▶️ Найден источник для просмотра!'}
            elif action == 'info':
                yield {'status': '📋 Получена информация о фильме'}
            else:
                yield {'status': '⚠️ Поиск завершён с ошибками'}

            yield {'result': result}

        except Exception as e:
            logger.error(f'[MediaSearchAgent] Ошибка в потоковом поиске: {e}')
            yield {'status': f'❌ Ошибка: {e}'}
            yield {'result': {'action': 'error', 'data': {'message': str(e)}}}
