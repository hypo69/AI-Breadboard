# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер управления и создания ИИ-агентов
# =============================================================================
# Описание:
#   CRUD для конфигурации агентов (системных и пользовательских).
#   Каталог инструментов, пула моделей и провайдеров.
#   AI Prompt & Agent Architect генератор и интерактивная песочница (Sandbox).
#
# File: router_agents.py
# Project: ai-assistant
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import time
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__
from core.logger import logger
from core.utils.jjson import j_loads_ns

_CONFIG_PATH = __root__ / 'config.json'

# ============================================================================
# Каталог доступных инструментов
# ============================================================================

_AVAILABLE_TOOLS = [
    {
        'id': 'web_search',
        'name': 'Интернет-поиск (MCP)',
        'icon': '🌐',
        'category': 'search',
        'description': 'Поиск актуальной информации в интернете через Google Grounding, AGY или Playwright.',
        'parameters': {'query': 'str'}
    },
    {
        'id': 'rag_search',
        'name': 'База знаний RAG',
        'icon': '🧠',
        'category': 'rag',
        'description': 'Семантический поиск по документам базы знаний и контексту предыдущих диалогов.',
        'parameters': {'query': 'str', 'top_k': 'int'}
    },
    {
        'id': 'python_eval',
        'name': 'Python Code Execution',
        'icon': '🐍',
        'category': 'code',
        'description': 'Выполнение вычислений и скриптов Python в безопасной песочнице.',
        'parameters': {'code': 'str'}
    },
    {
        'id': 'tts_generate',
        'name': 'Синтез речи (TTS)',
        'icon': '🗣️',
        'category': 'voice',
        'description': 'Озвучивание текстовых ответов агента через Edge-TTS или Silero.',
        'parameters': {'text': 'str', 'voice': 'str'}
    },
    {
        'id': 'file_system',
        'name': 'Файловые операции',
        'icon': '📁',
        'category': 'files',
        'description': 'Чтение и структурирование данных из локальных файлов проекта.',
        'parameters': {'file_path': 'str'}
    }
]


# ============================================================================
# Pydantic Модели
# ============================================================================

class AgentModel(BaseModel):
    id: str
    name: str
    description: str = ''
    is_system: bool = False
    enabled: bool = True
    provider: str = 'gemini'
    model: str = 'gemini-2.5-flash'
    temperature: float = 0.3
    max_steps: int = 15
    timeout_seconds: int = 60
    tools: List[str] = Field(default_factory=list)
    system_prompt: str = ''


class GeneratePromptRequest(BaseModel):
    task_description: str
    provider: str = 'gemini'
    model: str = 'gemini-2.5-flash'
    agent_name: str = ''


class TestAgentRequest(BaseModel):
    agent_id: str = ''
    inline_config: Optional[AgentModel] = Field(default_factory=dict) # type: ignore
    test_message: str


# ============================================================================
# Хелперы работы с config.json
# ============================================================================

def _load_raw_config() -> dict:
    """Загружает полный config.json."""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'[router_agents] Ошибка загрузки config.json: {e}')
        return {}


def _save_raw_config(data: dict) -> None:
    """Сохраняет config.json с форматированием."""
    try:
        with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f'[router_agents] Ошибка сохранения config.json: {e}')
        raise HTTPException(status_code=500, detail='Не удалось сохранить конфигурацию')


def _get_agents_list() -> List[dict]:
    """Возвращает список агентов из config.json."""
    cfg = _load_raw_config()
    agents_cfg = cfg.get('agents', {})
    if isinstance(agents_cfg, dict):
        return agents_cfg.get('items', [])
    return []


def _save_agents_list(items: List[dict]) -> None:
    """Сохраняет обновленный список агентов в config.json."""
    cfg = _load_raw_config()
    if 'agents' not in cfg or not isinstance(cfg['agents'], dict):
        cfg['agents'] = {}
    cfg['agents']['items'] = items
    _save_raw_config(cfg)


# ============================================================================
# Роутер FastAPI
# ============================================================================

def init_agents_router(prefix: str = '/api/agents') -> APIRouter:
    """Инициализирует и возвращает роутер управления агентами."""
    router = APIRouter(prefix=prefix, tags=['agents'])

    @router.get('')
    async def list_agents() -> List[dict]:
        """Получить список всех агентов (системных и пользовательских)."""
        return _get_agents_list()

    @router.get('/tools')
    async def list_tools() -> List[dict]:
        """Получить каталог всех доступных инструментов системы."""
        return _AVAILABLE_TOOLS

    @router.get('/providers')
    async def list_providers() -> dict:
        """Получить список провайдеров и моделей из пула проекта."""
        raw_cfg = _load_raw_config()
        ai_section = raw_cfg.get('ai', {})

        providers = {
            'gemini': {
                'name': 'Google Gemini',
                'description': 'Официальный Google GenAI SDK с пулом API-ключей',
                'models': [
                    {'id': 'gemini-2.5-flash', 'name': 'Gemini 2.5 Flash (Рекомендуется)'},
                    {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro (Сложный reasoning)'},
                    {'id': 'gemini-2.0-flash', 'name': 'Gemini 2.0 Flash'},
                    {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash'},
                    {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'}
                ],
                'default_model': 'gemini-2.5-flash'
            },
            'gemini_cli': {
                'name': 'Google Gemini CLI',
                'description': 'Автономная среда Gemini CLI (локальный агентный инструмент)',
                'models': [
                    {'id': 'gemini-3.1-flash-lite', 'name': 'Gemini 3.1 Flash Lite (По умолчанию)'},
                    {'id': 'gemini-2.5-flash', 'name': 'Gemini 2.5 Flash'},
                    {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro'},
                    {'id': 'gemini-3.1-pro-preview', 'name': 'Gemini 3.1 Pro Preview'},
                    {'id': 'gemini-3.1-flash-lite-preview', 'name': 'Gemini 3.1 Flash Lite Preview'}
                ],
                'default_model': ai_section.get('gemini_cli_model_id', 'gemini-3.1-flash-lite')
            },
            'agy': {
                'name': 'Google Antigravity (AGY)',
                'description': 'Агентная среда Antigravity с встроенным поиском',
                'models': [
                    {'id': 'agy-flash', 'name': 'AGY Flash'},
                    {'id': 'agy-gemma-4-26b-a4b-it', 'name': 'AGY Gemma 4-26B'},
                    {'id': 'agy-pro', 'name': 'AGY Pro'}
                ],
                'default_model': ai_section.get('agy_model_id', 'agy-flash')
            },
            'foundry': {
                'name': 'Microsoft Foundry',
                'description': 'Локальные модели Foundry (без отправки во внешний интернет)',
                'models': [
                    {'id': 'qwen2.5-1.5b-instruct-generic-cpu:4', 'name': 'Qwen 2.5 1.5B Instruct'},
                    {'id': 'deepseek-r1-distill-qwen-1.5b', 'name': 'DeepSeek R1 1.5B'},
                    {'id': 'phi-3-mini-4k-instruct', 'name': 'Phi-3 Mini'}
                ],
                'default_model': ai_section.get('foundry_model_id', 'qwen2.5-1.5b-instruct-generic-cpu:4')
            },
            'ollama': {
                'name': 'Ollama (Local)',
                'description': 'Локальный REST-сервер Ollama',
                'models': [
                    {'id': 'qwen2.5:7b', 'name': 'Qwen 2.5 7B'},
                    {'id': 'llama3.1:8b', 'name': 'Llama 3.1 8B'},
                    {'id': 'mistral:7b', 'name': 'Mistral 7B'}
                ],
                'default_model': raw_cfg.get('langchain', {}).get('ollama_model', 'qwen2.5:7b')
            }
        }
        return providers

    @router.post('')
    async def create_agent(agent: AgentModel) -> dict:
        """Создать нового кастомного агента."""
        items = _get_agents_list()
        
        # Проверка уникальности ID
        existing_ids = {a.get('id') for a in items}
        if agent.id in existing_ids:
            raise HTTPException(status_code=400, detail=f'Агент с ID "{agent.id}" уже существует')

        # Защита флага is_system для пользовательских агентов
        agent_dict = agent.dict()
        agent_dict['is_system'] = False

        items.append(agent_dict)
        _save_agents_list(items)
        logger.info(f'[router_agents] Создан новый агент: {agent.id} ({agent.name})')
        return {'status': 'ok', 'agent': agent_dict}

    @router.put('/{agent_id}')
    async def update_agent(agent_id: str, agent: AgentModel) -> dict:
        """Обновить существующего агента."""
        items = _get_agents_list()
        found_idx = -1
        for idx, item in enumerate(items):
            if item.get('id') == agent_id:
                found_idx = idx
                break

        if found_idx == -1:
            raise HTTPException(status_code=404, detail=f'Агент с ID "{agent_id}" не найден')

        old_item = items[found_idx]
        agent_dict = agent.dict()
        # Сохраняем системный статус исходного агента
        agent_dict['is_system'] = old_item.get('is_system', False)
        agent_dict['id'] = agent_id  # ID не меняется

        items[found_idx] = agent_dict
        _save_agents_list(items)
        logger.info(f'[router_agents] Обновлен агент: {agent_id}')
        return {'status': 'ok', 'agent': agent_dict}

    @router.delete('/{agent_id}')
    async def delete_agent(agent_id: str) -> dict:
        """Удалить кастомного агента (системные защищены)."""
        items = _get_agents_list()
        target = None
        for item in items:
            if item.get('id') == agent_id:
                target = item
                break

        if not target:
            raise HTTPException(status_code=404, detail=f'Агент с ID "{agent_id}" не найден')

        if target.get('is_system', False):
            raise HTTPException(status_code=403, detail='Системных агентов нельзя удалять. Вы можете отключить их.')

        items = [i for i in items if i.get('id') != agent_id]
        _save_agents_list(items)
        logger.info(f'[router_agents] Удален агент: {agent_id}')
        return {'status': 'ok', 'deleted_id': agent_id}

    @router.post('/generate-prompt')
    async def generate_prompt(req: GeneratePromptRequest) -> dict:
        """AI Prompt & Agent Architect: генерация системного промпта и настроек через модель из пула."""
        if not req.task_description.strip():
            raise HTTPException(status_code=400, detail='Описание задачи не может быть пустым')

        tool_ids = [t['id'] for t in _AVAILABLE_TOOLS]
        tool_desc = "\n".join([f"- {t['id']}: {t['name']} ({t['description']})" for t in _AVAILABLE_TOOLS])

        prompt_architect_query = f"""Ты опытный архитектор ИИ-агентов (AI Agent Architect).
Пользователь хочет создать специализированного агента для платформы ai-assistant.

Задача агента от пользователя:
"{req.task_description}"

Доступные в системе инструменты (Tools):
{tool_desc}

Сформируй полную спецификацию агента строго в формате валидного JSON без markdown-блоков:
{{
  "name": "Название агента (короткое, понятное)",
  "description": "Краткое описание роли агента (1-2 предложения)",
  "system_prompt": "Детальная системная инструкция: роль, правила рассуждения (ReAct), выбор инструментов, формат выдачи",
  "recommended_tools": ["id_инструментов_из_списка_выше"],
  "temperature": 0.2,
  "max_steps": 15
}}
"""

        try:
            from core.fastapi.router_chat import get_chat_model
            model_key = req.model
            if req.provider == 'gemini_cli' and not model_key.startswith('gemini_cli:'):
                model_key = f'gemini_cli:{model_key}'
            elif req.provider == 'foundry' and not model_key.startswith('foundry:'):
                model_key = f'foundry:{model_key}'
            elif req.provider == 'ollama' and not model_key.startswith('ollama:'):
                model_key = f'ollama:{model_key}'

            llm = get_chat_model(model_key, system_instruction="You are an expert AI Agent Architect. Always return pure JSON.")
            
            # Вызов модели
            if hasattr(llm, 'ask'):
                response_text = await llm.ask(prompt_architect_query)
            elif hasattr(llm, 'chat'):
                response_text = await llm.chat(prompt_architect_query)
            elif hasattr(llm, 'generate_response'):
                response_text = await llm.generate_response(prompt_architect_query)
            else:
                response_text = str(llm)

            # Очистка JSON от возможных ```json обёрток
            cleaned = response_text.strip()
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            parsed_data = json.loads(cleaned)
            # Валидация рекомендованных инструментов
            if 'recommended_tools' in parsed_data:
                parsed_data['recommended_tools'] = [
                    t for t in parsed_data['recommended_tools'] if t in tool_ids
                ]

            return {
                'status': 'ok',
                'data': parsed_data
            }
        except Exception as e:
            logger.error(f'[router_agents] Ошибка AI-генератора промпта: {e}')
            # Фолбэк на дефолтную структуру при сбое модели
            return {
                'status': 'fallback',
                'data': {
                    'name': req.agent_name or 'Пользовательский агент',
                    'description': req.task_description[:100],
                    'system_prompt': f"Ты специализированный агент ai-assistant.\nТвоя задача: {req.task_description}\nИспользуй предоставленные инструменты при необходимости и давай чёткие ответы.",
                    'recommended_tools': ['web_search'],
                    'temperature': 0.3,
                    'max_steps': 10
                },
                'error': str(e)
            }

    @router.post('/test')
    async def test_agent(req: TestAgentRequest) -> dict:
        """Интерактивная песочница: тестовый запуск агента с трассировкой шагов."""
        start_time = time.time()
        
        # Определяем конфигурацию агента
        target_config = {}
        if req.inline_config and isinstance(req.inline_config, AgentModel) and req.inline_config.name:
            target_config = req.inline_config.dict()
        elif req.agent_id:
            items = _get_agents_list()
            for item in items:
                if item.get('id') == req.agent_id:
                    target_config = item
                    break

        if not target_config:
            raise HTTPException(status_code=400, detail='Не задана конфигурация агента для тестирования')

        provider = target_config.get('provider', 'gemini')
        model_name = target_config.get('model', 'gemini-2.5-flash')
        sys_prompt = target_config.get('system_prompt', '')
        tools = target_config.get('tools', [])

        steps = []
        steps.append({
            'step': 1,
            'type': 'thought',
            'content': f"Инициализация агента '{target_config.get('name')}' [Провайдер: {provider}, Модель: {model_name}]"
        })

        if tools:
            steps.append({
                'step': 2,
                'type': 'tool_init',
                'content': f"Подключено инструментов ({len(tools)}): {', '.join(tools)}"
            })

        try:
            from core.fastapi.router_chat import get_chat_model
            model_key = model_name
            if provider == 'gemini_cli' and not model_key.startswith('gemini_cli:'):
                model_key = f'gemini_cli:{model_key}'
            elif provider == 'foundry' and not model_key.startswith('foundry:'):
                model_key = f'foundry:{model_key}'
            elif provider == 'ollama' and not model_key.startswith('ollama:'):
                model_key = f'ollama:{model_key}'

            llm = get_chat_model(model_key, system_instruction=sys_prompt)
            
            steps.append({
                'step': 3,
                'type': 'action',
                'content': f"Обработка входящего сообщения: '{req.test_message}'"
            })

            # Выполнение вызова
            if hasattr(llm, 'ask'):
                res = await llm.ask(req.test_message)
            elif hasattr(llm, 'chat'):
                res = await llm.chat(req.test_message)
            else:
                res = "Ответ модели получен."

            duration_ms = int((time.time() - start_time) * 1000)

            steps.append({
                'step': 4,
                'type': 'finish',
                'content': f"Завершено успешно за {duration_ms} мс."
            })

            return {
                'status': 'ok',
                'response': res,
                'duration_ms': duration_ms,
                'steps': steps
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f'[router_agents] Ошибка тестового прогона агента: {e}')
            steps.append({
                'step': len(steps) + 1,
                'type': 'error',
                'content': f"Ошибка выполнения: {str(e)}"
            })
            return {
                'status': 'error',
                'response': f"Ошибка при выполнении агента: {str(e)}",
                'duration_ms': duration_ms,
                'steps': steps
            }

    return router
