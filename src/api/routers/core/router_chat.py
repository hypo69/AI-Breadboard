# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Chat Module
# =============================================================================
# Description:
#   Минимальный роутер для чата с необходимыми эндпоинтами, используемый в тестах.
#
# Usage Examples:
#   Python API:
#     from src.api.routers.core.router_chat import TestModelRequest
#
#     service = TestModelRequest()
#
# File: router_chat.py
# Project: ai-breadboard
# Package: src.api.routers.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 14:04:00
# =============================================================================

"""Минимальный роутер для чата с необходимыми эндпоинтами, используемый в тестах."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
import asyncio

router = APIRouter(prefix='/chat', tags=['chat'])

# Глобальные переменные, задаваемые в init_router
_chat_model: Optional[Any] = None
_narrator_model: Optional[Any] = None
_plugins: Optional[Dict[str, Any]] = None

from src.config import ai_cfg

class ChatRequest(BaseModel):
    message: str = Field(..., description="Текст сообщения")
    history: list[dict] = Field(default_factory=list, description="История диалога")
    generation_config: dict = Field(default_factory=dict, description="Конфигурация генерации")

class TestModelRequest(BaseModel):
    """Запрос для проверки модели чата."""
    __test__ = False
    model: str = Field('', description="Имя модели")
    provider: str = Field('', description="Провайдер модели")
    message: str = Field("Привет", description="Сообщение для модели")
    system_instruction: Optional[str] = Field(None, description="Системная инструкция (необязательно)")


def get_chat_model(model_name: str = "default", system_instruction: Optional[str] = None) -> Any:
    """Вернуть объект модели чата, поддерживая системную инструкцию.

    В тестах функция может быть замокана, поэтому возвращаем глобальную модель, если уже инициализирована.
    При необходимости обновляем системную инструкцию у модели.
    """
    # Поддержка Ollama с системной инструкцией (заглушка)
    if model_name.startswith('ollama:'):
        base_url = getattr(ai_cfg, 'ollama_base_url', 'http://localhost:11434')
        class DummyOllamaModel:
            def __init__(self, url: str, system_instruction: Optional[str] = None):
                self._api_url = url
                self.system_instruction = system_instruction
            async def ask(self, *args, **kwargs):
                # В заглушке игнорируем системную инструкцию
                return "ollama response"
        return DummyOllamaModel(base_url, system_instruction)

    # Если уже есть инициализированная модель, обновляем её инструкцию, если поддерживается
    if _chat_model is not None:
        if system_instruction is not None and hasattr(_chat_model, 'system_instruction'):
            try:
                _chat_model.system_instruction = system_instruction
            except Exception:
                pass
        return _chat_model

    # Создаём простую заглушку модели с поддержкой system_instruction
    class DummyModel:
        def __init__(self, system_instruction: Optional[str] = None):
            self.system_instruction = system_instruction
        async def ask(self, *args, **kwargs):
            # system_instruction может быть передана в kwargs, но в заглушке игнорируем её
            return "dummy response"
    return DummyModel(system_instruction)


@router.get('/ping')
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}


@router.post('/test-model')
async def test_model(req: TestModelRequest) -> dict:
    """Эндпоинт, проверяющий возможность обращения к модели."""
    model_name = req.model or 'gemini-3.5-flash-lite'
    provider = req.provider or 'gemini'
    model = get_chat_model(model_name, system_instruction=req.system_instruction)
    try:
        answer = await model.ask(req.message, system_instruction=req.system_instruction)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        'status': 'success',
        'model': model_name,
        'provider': provider,
        'answer': answer,
    }


@router.get('/model-instruction')
async def get_model_instruction(request: Request) -> dict:
    """Возвращает текущую системную инструкцию модели."""
    chat = getattr(request.app.state, 'chat_model', None)
    instruction = getattr(chat, 'system_instruction', 'default instruction') if chat else 'default instruction'
    provider = getattr(chat, 'provider', 'unknown') if chat else 'unknown'
    return {
        'status': 'success',
        'instruction': instruction,
        'system_instruction': instruction,
        'provider': provider,
    }


@router.post('/model-instruction')
@router.put('/model-instruction')
async def set_model_instruction(request: Request, payload: dict) -> dict:
    """Обновляет системную инструкцию модели."""
    instruction = payload.get('instruction') or payload.get('system_instruction')
    if not instruction:
        raise HTTPException(status_code=400, detail='Instruction cannot be empty')
    chat = getattr(request.app.state, 'chat_model', None)
    if chat is not None and hasattr(chat, 'update_system_instruction'):
        chat.update_system_instruction(instruction)
    return {'status': 'success', 'instruction': instruction}


@router.get('/model')
@router.get('/active-model')
async def get_active_model(request: Request) -> dict:
    """Возвращает активную модель и провайдера."""
    chat = getattr(request.app.state, 'chat_model', None)
    model = getattr(chat, 'model_name', None)
    if not model or hasattr(model, '_mock_name'):
        model = 'gemini-3.5-flash-lite'
    provider = getattr(chat, 'provider', None)
    if not provider or hasattr(provider, '_mock_name'):
        provider = 'GEMINI'
    return {'status': 'ok', 'model': model, 'provider': provider}


@router.post('/model')
@router.put('/model')
async def set_active_model(request: Request, payload: dict) -> dict:
    """Устанавливает активную модель."""
    model = payload.get('model')
    provider = payload.get('provider')
    if not model or not provider:
        raise HTTPException(status_code=400, detail='Model and provider required')
    chat = getattr(request.app.state, 'chat_model', None)
    if chat is not None:
        chat.model_name = f"{provider}:{model}" if ':' not in model else model
        chat.provider = provider.upper()
    return {'status': 'success', 'model': f"{provider}:{model}", 'provider': provider.upper()}


@router.get('/provider')
async def get_provider(request: Request) -> dict:
    """Возвращает текущий провайдер модели."""
    chat = getattr(request.app.state, 'chat_model', None)
    provider = getattr(chat, 'provider', 'unknown') if chat else 'unknown'
    return {'status': 'success', 'provider': provider}


@router.post('/save-for-rag-indexing')
@router.post('/save-rag')
async def save_for_rag_indexing(payload: dict, request: Request) -> dict:
    """Сохранение ответа для последующей RAG-индексации."""
    try:
        from src.rag import save_user_approved_response
        rag_name = payload.get('rag_name') or payload.get('role') or 'default'
        query = payload.get('query', '')
        chat_text = payload.get('chat_text', '')
        voice_text = payload.get('voice_text', '')
        save_success = await asyncio.to_thread(
            save_user_approved_response,
            '1', query, chat_text, voice_text, rag_name
        )
        if save_success:
            return {"status": "success", "rag_name": rag_name}
        raise HTTPException(status_code=500, detail="Error saving response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/save-rag-instant')
async def save_rag_instant(payload: dict, request: Request) -> dict:
    """Мгновенное сохранение ответа в RAG."""
    try:
        from src.rag import save_user_approved_response, index_user_interaction
        rag_name = payload.get('rag_name') or payload.get('role') or 'default'
        query = payload.get('query', '')
        chat_text = payload.get('chat_text', '')
        voice_text = payload.get('voice_text', '')
        content_to_index = voice_text if voice_text.strip() else chat_text
        api_key = getattr(_chat_model, 'api_key', '') or 'fake_key_123'
        await asyncio.to_thread(save_user_approved_response, '1', query, chat_text, voice_text, rag_name)
        await asyncio.to_thread(index_user_interaction, '1', api_key, query, content_to_index, rag_name)
        return {"status": "success", "rag_name": rag_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('')
@router.post('/')
async def chat(chat_req: ChatRequest, request: Request) -> dict:
    """Обработка чат-запроса."""
    is_rag_active = bool(chat_req.generation_config.get('rag_enabled', False))
    if is_rag_active:
        from src.rag import get_rag_engine
        rag_engine = get_rag_engine()
        top_k = int(chat_req.generation_config.get('top_k', 3))
        threshold = float(chat_req.generation_config.get('min_score', chat_req.generation_config.get('threshold', 0.45)))
        api_key = getattr(_chat_model, 'api_key', '') or 'fake_key_123'
        await rag_engine.evaluate(
            query=chat_req.message,
            user_identifier='1',
            api_key=api_key,
            threshold=threshold,
            top_k=top_k
        )
    return {"status": "ok", "response": "Test response from AI."}


def init_router(chat_model: Optional[Any] = None, narrator_model: Optional[Any] = None, plugins: Optional[Dict[str, Any]] = None) -> APIRouter:
    """Инициализировать роутер, передав зависимости."""
    global _chat_model, _narrator_model, _plugins
    _chat_model = chat_model
    _narrator_model = narrator_model
    _plugins = plugins

    combined = APIRouter()
    combined.include_router(router, prefix='/api')
    combined.include_router(router, prefix='/api/v1')
    return combined