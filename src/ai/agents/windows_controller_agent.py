# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Windows Controller Agent Module
# =============================================================================
# Description:
#   Автономный агент управления операционной системой Windows.
#   Диагностирует состояние ОС, выполняет аудит, управляет службами и параметрами.
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_controller_agent import WindowsControllerAgent
#
#     agent = WindowsControllerAgent()
#     result = await agent.search("Проверь статус защиты системы и состояние служб")
#     print(result)
#
# File: windows_controller_agent.py
# Project: ai-breadboard
# Package: src.ai.agents
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 01:58:00
# =============================================================================

from __future__ import annotations
"""Автономный агент управления операционной системой Windows."""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional
from logger import logger
from src.utils.jjson import j_loads_ns
from .prompts import (
    WINDOWS_CONTROLLER_SYSTEM_PROMPT,
    WINDOWS_SAFETY_PROTOCOL,
    WINDOWS_TOOL_SELECTION_GUIDELINES,
    RESULT_FORMAT_INSTRUCTIONS,
)
from .tools import (
    web_search,
    rag_search,
    python_eval,
    file_read,
    windows_collector_audit,
    windows_execute_atomic_op,
    windows_manage_service,
    windows_manage_process,
    windows_manage_restore_point,
    windows_manage_sys_param,
    windows_safe_probe,
    windows_execute_powershell,
)
from .mcp_client import MCPClientManager


class WindowsControllerAgent:
    """Автономный агент управления операционной системой Windows.

    Использует возможности Gemini и нативный инструментарий Windows:
    - Аудит 13 доменов телеметрии (windows_collector_audit)
    - Исполнение проверенных атомарных утилит (windows_execute_atomic_op)
    - Управление службами и процессами (windows_manage_service, windows_manage_process)
    - Управление контрольными точками восстановления (windows_manage_restore_point)
    - Управление параметрами системы SafeOps (windows_manage_sys_param)
    - Безопасные PowerShell/WMI запросы (windows_safe_probe)
    - Прямое выполнение команд и скриптов PowerShell (windows_execute_powershell)
    - Поиск документации и регламентов (rag_search, web_search)
    """

    def __init__(self, config_path: Path = Path('config.json'), ai_model: Any = None) -> None:
        """Инициализация агента Windows Controller.

        Args:
            config_path: Путь к файлу конфигурации системы.
            ai_model: Опциональный экземпляр внешней модели.
        """
        self.config_path = config_path
        self.config = j_loads_ns(config_path) if config_path.exists() else None
        self.ai_model = ai_model
        langchain_cfg = getattr(self.config, 'langchain', object()) if self.config else object()
        self.llm_type = getattr(langchain_cfg, 'default_llm', 'gemini')
        self.max_steps = getattr(langchain_cfg, 'max_agent_steps', 20)
        self.timeout = getattr(langchain_cfg, 'search_timeout_seconds', 90)
        self._llm = None
        self._langchain_cfg = langchain_cfg
        self.native_tools = [
            windows_collector_audit,
            windows_execute_atomic_op,
            windows_manage_service,
            windows_manage_process,
            windows_manage_restore_point,
            windows_manage_sys_param,
            windows_safe_probe,
            windows_execute_powershell,
            rag_search,
            web_search,
            python_eval,
            file_read,
        ]
        logger.info(f'[WindowsControllerAgent] Инициализирован: llm={self.llm_type}, max_steps={self.max_steps}, timeout={self.timeout}')

    def _get_llm(self) -> Any:
        """Ленивая инициализация LLM-модели."""
        if self._llm is not None:
            return self._llm
        if self.llm_type == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = getattr(self._langchain_cfg, 'gemini_model', 'gemini-2.5-flash')
            api_key = os.environ.get('GEMINI_API_KEY', '')
            if not api_key:
                from src.ai.gemini.gemini_api_key_state import load_api_keys
                loaded, _, _ = load_api_keys()
                aiza_keys = [k for k in loaded if k.startswith('AIzaSy')]
                if aiza_keys:
                    api_key = aiza_keys[0]
                elif loaded:
                    api_key = loaded[0]
            if not api_key:
                logger.error('[WindowsControllerAgent] GEMINI_API_KEY не установлен в окружении')
                raise EnvironmentError('GEMINI_API_KEY не установлен')
            self._llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.1)
        else:
            from langchain_ollama import ChatOllama
            model_name = getattr(self._langchain_cfg, 'ollama_model', 'qwen2.5:7b')
            base_url = getattr(self._langchain_cfg, 'ollama_base_url', 'http://localhost:11434')
            self._llm = ChatOllama(model=model_name, base_url=base_url, temperature=0.1)
        logger.info(f'[WindowsControllerAgent] LLM создан: {self.llm_type}')
        return self._llm

    def _build_system_prompt(self) -> str:
        """Сборка полного системного промпта агента."""
        return '\n\n'.join([
            WINDOWS_CONTROLLER_SYSTEM_PROMPT,
            WINDOWS_SAFETY_PROTOCOL,
            WINDOWS_TOOL_SELECTION_GUIDELINES,
            RESULT_FORMAT_INSTRUCTIONS,
        ])

    async def search(self, query: str) -> Dict[str, Any]:
        """Выполняет автономный анализ и управление операционной системой Windows по запросу.

        Args:
            query: Запрос пользователя или задача администрирования.

        Returns:
            Dict[str, Any]: Результат работы агента с аналитическим отчетом и выполненными действиями.
        """
        try:
            try:
                from langgraph.prebuilt import create_react_agent
            except ImportError:
                create_react_agent = None

            llm = self._get_llm()
            system_prompt = self._build_system_prompt()
            all_tools = list(self.native_tools)

            # Подключаем MCP-инструменты при наличии конфигурации
            if self.config_path.exists():
                try:
                    async with MCPClientManager(str(self.config_path)) as mcp:
                        mcp_tools = await mcp.get_tools()
                        if mcp_tools:
                            all_tools.extend(mcp_tools)
                            logger.info(f'[WindowsControllerAgent] Подключено {len(mcp_tools)} MCP инструментов')
                except Exception as mcp_err:
                    logger.warning(f'[WindowsControllerAgent] MCP недоступны, работаем с нативными инструментами: {mcp_err}')

            logger.info(f'[WindowsControllerAgent] Запуск ReAct агента ({len(all_tools)} инструментов) для: "{query}"')

            if create_react_agent is not None:
                try:
                    agent_executor = create_react_agent(llm, all_tools, prompt=system_prompt)
                except TypeError:
                    agent_executor = create_react_agent(llm, all_tools, state_modifier=system_prompt)

                result = await asyncio.wait_for(
                    agent_executor.ainvoke({'messages': [('user', query)]}),
                    timeout=self.timeout
                )
                messages = result.get('messages', [])
                if not messages:
                    return {'action': 'error', 'data': {'message': 'Агент не вернул сообщений'}}
                last_message = messages[-1]
                raw_content = getattr(last_message, 'content', '')
            elif hasattr(llm, 'ainvoke'):
                res = await llm.ainvoke([('system', system_prompt), ('user', query)])
                raw_content = getattr(res, 'content', str(res))
            elif hasattr(llm, 'ask'):
                raw_content = await llm.ask(f'{system_prompt}\n\nUser: {query}')
            else:
                raw_content = str(llm)

            if isinstance(raw_content, list):
                content = ''.join([c.get('text', '') if isinstance(c, dict) else str(c) for c in raw_content])
            else:
                content = str(raw_content)

            cleaned_content = content.strip()
            if cleaned_content.startswith('`'):
                cleaned_content = re.sub('^`(?:json)?\\s*', '', cleaned_content)
                cleaned_content = re.sub('\\s*`$', '', cleaned_content).strip()

            try:
                parsed = json.loads(cleaned_content)
                if isinstance(parsed, dict):
                    action = parsed.get('action', 'windows_control_report')
                    return {'action': action, **parsed}
                return {'action': 'windows_control_report', 'text': content}
            except (json.JSONDecodeError, ValueError):
                return {'action': 'windows_control_report', 'text': content}

        except asyncio.TimeoutError:
            logger.error(f'[WindowsControllerAgent] Таймаут ({self.timeout}с) при выполнении: "{query}"')
            return {'action': 'error', 'data': {'message': f'Превышен таймаут выполнения операции ({self.timeout}с)'}}
        except Exception as e:
            logger.error(f'[WindowsControllerAgent] Ошибка выполнения: {e}', exc_info=True)
            return {'action': 'error', 'data': {'message': str(e)}}

    async def search_stream(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """Потоковая передача промежуточных статусов и результатов выполнения задачи.

        Args:
            query: Запрос пользователя.

        Yields:
            Dict[str, Any]: Словарь со статусом или финальным результатом.
        """
        yield {'status': '🔍 Инициализация Windows Controller: анализ запроса и выбор доменных инструментов...'}
        yield {'status': '📊 Сбор первичной телеметрии и аудит состояния подсистемы...'}
        try:
            result = await self.search(query)
            action = result.get('action', 'windows_control_report')
            if action != 'error':
                yield {'status': '✨ Операции завершены, формирование итогового системного отчета...'}
            else:
                yield {'status': '⚠️ Операция завершилась с предупреждением'}
            yield {'result': result}
        except Exception as e:
            logger.error(f'[WindowsControllerAgent] Ошибка в потоковом поиске: {e}', exc_info=True)
            yield {'status': f'❌ Ошибка: {e}'}
            yield {'result': {'action': 'error', 'data': {'message': str(e)}}}


__all__ = ['WindowsControllerAgent']
