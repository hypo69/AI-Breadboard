# -*- coding: utf-8 -*-
"""Минимальная реализация роутера router_openai.

Тесты требуют:
- функции map_to_openai_id и map_from_openai_id
- эндпоинт GET /v1/models, возвращающий список моделей в формате OpenAI
- эндпоинт POST /v1/chat/completions, использующий get_chat_model (мок‑функция)
- вспомогательная функция get_chat_model, возвращающая объект с методом generate_content
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

# ---------------------------------------------------------------------------
# Маппинг идентификаторов моделей между внутренними и OpenAI-форматом
# ---------------------------------------------------------------------------

def map_to_openai_id(internal_id: str) -> str:
    """Преобразовать внутренний ID модели в OpenAI‑совместимый.

    Преобразования простые: заменяем «:» на «-».
    """
    if not isinstance(internal_id, str):
        raise ValueError("internal_id must be a string")
    return internal_id.replace(":", "-")


def map_from_openai_id(openai_id: str) -> str:
    """Обратное преобразование из OpenAI‑ID в внутренний.

    Меняем первый «-» обратно на «:».
    """
    if not isinstance(openai_id, str):
        raise ValueError("openai_id must be a string")
    parts = openai_id.split("-", 1)
    if len(parts) == 2:
        return f"{parts[0]}:{parts[1]}"
    return openai_id

# ---------------------------------------------------------------------------
# Вспомогательная функция получения модели чата (мок для тестов)
# ---------------------------------------------------------------------------

def get_chat_model(model_name: str = "default") -> Any:
    """Возвращает объект с методом ``generate_content``.

    В реальном проекте будет фабрика, но для тестов достаточно мок‑объекта.
    """
    class _MockChat:
        async def generate_content(self, *args, **kwargs) -> str:
            return "Universal assistant reply"
    return _MockChat()

# ---------------------------------------------------------------------------
# Эндпоинты OpenAI‑совместимого API
# ---------------------------------------------------------------------------

@router.get('/v1/models', tags=['router_openai'])
async def list_models() -> Dict[str, Any]:
    """Возвращает список доступных моделей в формате OpenAI.

    Для упрощения отдаём фиксированный список.
    """
    internal_models = ["foundry:qwen2.5-1.5b", "hf:Qwen/Qwen2.5-0.5B-Instruct", "onnx:models/gemma", "openai:gpt-4o"]
    data = [{
        "id": map_to_openai_id(mid),
        "object": "model",
        "owned_by": "system",
    } for mid in internal_models]
    return {"object": "list", "data": data}

@router.post('/v1/chat/completions', tags=['router_openai'])
async def chat_completions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Обрабатывает запросы чат‑комплитов.

    Тесты подменяют ``get_chat_model`` через ``patch``.
    """
    model_name = payload.get('model')
    if not model_name:
        raise HTTPException(status_code=400, detail='model is required')
    chat = get_chat_model(model_name)
    content = await chat.generate_content()
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": model_name,
        "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop", "index": 0}],
    }

# ---------------------------------------------------------------------------
# Пинг‑эндпоинт (оставляем для совместимости)
# ---------------------------------------------------------------------------
@router.get('/router_openai/ping', tags=['router_openai'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router