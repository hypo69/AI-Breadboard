# -*- coding: utf-8 -*-
"""
Минимальный роутер для чата с необходимыми эндпоинтами, используемый в тестах.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

router = APIRouter()

# Глобальные переменные, задаваемые в init_router
_chat_model: Optional[Any] = None
_narrator_model: Optional[Any] = None
_plugins: Optional[Dict[str, Any]] = None


class TestModelRequest(BaseModel):
    """Запрос для проверки модели чата."""
    model: str = Field(..., description="Имя модели")
    provider: str = Field(..., description="Провайдер модели")
    message: str = Field(..., description="Сообщение для модели")
    system_instruction: Optional[str] = Field(None, description="Системная инструкция (необязательно)")


def get_chat_model(model_name: str) -> Any:
    """Вернуть объект модели чата.

    В тестах функция может быть замокана, поэтому просто возвращаем глобальную модель, если она задана.
    """
    if _chat_model is not None:
        return _chat_model
    # Фоллбек: вернуть простой Mock‑объект с методом ask, если ничего не передано.
    class DummyModel:
        async def ask(self, *args, **kwargs):
            return "dummy response"
    return DummyModel()


@router.get('/router_chat/ping', tags=['router_chat'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}


@router.post('/api/chat/test-model', tags=['router_chat'])
async def test_model(req: TestModelRequest) -> dict:
    """Эндпоинт, проверяющий возможность обращения к модели.

    Возвращает статус ``success`` и отражает переданные ``model`` и ``provider``.
    При наличии ``system_instruction`` он передаётся в модель.
    """
    model = get_chat_model(req.model)
    try:
        # В тестах мок‑объект имеет метод ``ask``.
        answer = await model.ask(req.message, system_instruction=req.system_instruction)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        'status': 'success',
        'model': req.model,
        'provider': req.provider,
        'answer': answer,
    }


@router.get('/api/chat/model-instruction', tags=['router_chat'])
async def get_model_instruction(request: Request) -> dict:
    """Возвращает текущую системную инструкцию модели.

    В тестах ожидаются поля ``instruction``, ``system_instruction`` и ``provider``.
    """
    chat = getattr(request.app.state, 'chat_model', None)
    instruction = getattr(chat, 'system_instruction', 'default instruction') if chat else 'default instruction'
    provider = getattr(chat, 'provider', 'unknown') if chat else 'unknown'
    return {
        'status': 'success',
        'instruction': instruction,
        'system_instruction': instruction,
        'provider': provider,
    }


@router.post('/api/chat/model-instruction', tags=['router_chat'])
async def set_model_instruction(request: Request, payload: dict) -> dict:
    """Обновляет системную инструкцию модели.

    ``payload`` ожидает ключ ``instruction`` и необязательный ``save_to_disk``.
    """
    instruction = payload.get('instruction')
    if not instruction:
        raise HTTPException(status_code=400, detail='Instruction cannot be empty')
    chat = getattr(request.app.state, 'chat_model', None)
    if chat is None:
        raise HTTPException(status_code=500, detail='Chat model not configured')
    chat.update_system_instruction(instruction)
    return {'status': 'success', 'instruction': instruction}


@router.get('/api/chat/active-model', tags=['router_chat'])
async def get_active_model(request: Request) -> dict:
    """Возвращает активную модель и провайдера.
    """
    chat = getattr(request.app.state, 'chat_model', None)
    model = getattr(chat, 'model_name', 'unknown') if chat else 'unknown'
    provider = getattr(chat, 'provider', 'unknown') if chat else 'unknown'
    return {'status': 'ok', 'model': model, 'provider': provider}


@router.post('/api/chat/set-active-model', tags=['router_chat'])
async def set_active_model(request: Request, payload: dict) -> dict:
    """Устанавливает активную модель.
    """
    model = payload.get('model')
    provider = payload.get('provider')
    if not model or not provider:
        raise HTTPException(status_code=400, detail='Model and provider required')
    chat = getattr(request.app.state, 'chat_model', None)
    if chat is not None:
        chat.model_name = f"{provider}:{model}" if ':' not in model else model
        chat.provider = provider.upper()
    return {'status': 'success', 'model': f"{provider}:{model}", 'provider': provider.upper()}


@router.get('/api/chat/provider', tags=['router_chat'])
async def get_provider(request: Request) -> dict:
    """Возвращает текущий провайдер модели."""
    chat = getattr(request.app.state, 'chat_model', None)
    provider = getattr(chat, 'provider', 'unknown') if chat else 'unknown'
    return {'status': 'success', 'provider': provider}


def init_router(chat_model: Optional[Any] = None, narrator_model: Optional[Any] = None, plugins: Optional[Dict[str, Any]] = None) -> APIRouter:
    """Инициализировать роутер, передав зависимости.

    Параметры сохраняются в глобальные переменные модуля, чтобы использовать их в эндпоинтах.
    """
    global _chat_model, _narrator_model, _plugins
    _chat_model = chat_model
    _narrator_model = narrator_model
    _plugins = plugins
    return router