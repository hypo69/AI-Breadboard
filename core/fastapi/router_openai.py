# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Входящий OpenAI-совместимый API роутер
# =============================================================================
# Описание:
#   Предоставляет стандартные эндпоинты спецификации OpenAI для внешних клиентов:
#     - GET  /v1/models
#     - POST /v1/chat/completions
#
#   Поддерживает потоковую (SSE) и обычную генерацию ответов,
#   маршрутизируя запросы ко всем внутренним провайдерам ai-assistant
#   (Gemini, Gemini CLI, AGY, Foundry, Ollama, Hugging Face, ONNX, OpenAI Compat).
#
# File: core/fastapi/router_openai.py
# Project: ai-assistant
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from core.ai.model_manager import get_available_models
from core.fastapi.router_chat import get_chat_model
from core.logger.logger import logger

router = APIRouter(tags=["openai"])


def map_to_openai_id(provider_prefixed_id: str) -> str:
    """Преобразование внутреннего идентификатора модели в формат OpenAI."""
    if "::" in provider_prefixed_id:
        return provider_prefixed_id.replace("::", "-", 1)
    if ":" in provider_prefixed_id:
        return provider_prefixed_id.replace(":", "-", 1)
    return provider_prefixed_id


def map_from_openai_id(openai_id: str) -> str:
    """Преобразование OpenAI ID обратно во внутренний формат с префиксом."""
    for provider in ("foundry", "ollama", "hf", "onnx", "openai", "gemini_cli", "agy"):
        prefix = f"{provider}-"
        if openai_id.startswith(prefix):
            return f"{provider}:{openai_id[len(prefix):]}"
    return openai_id


def _collect_all_models_sync() -> List[Dict[str, Any]]:
    """Сбор всех моделей по всем провайдерам для OpenAPI каталога."""
    providers = ["gemini", "gemini_cli", "agy", "foundry", "ollama", "hf", "onnx"]
    models_list: List[Dict[str, Any]] = []

    for prov in providers:
        try:
            prov_models = get_available_models(prov)
            for m in prov_models:
                openai_id = map_to_openai_id(f"{prov}:{m}" if not m.startswith(f"{prov}:") else m)
                models_list.append({
                    "id": openai_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": prov,
                    "permission": [],
                    "root": openai_id,
                    "parent": "",
                })
        except Exception as e:
            logger.warning(f"[RouterOpenAI] Не удалось собрать модели для {prov}: {e}")

    return models_list


@router.get("/v1/models")
@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """Список всех доступных моделей в формате OpenAI API."""
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, _collect_all_models_sync)
    return {
        "object": "list",
        "data": data,
    }


@router.post("/v1/chat/completions")
@router.post("/chat/completions")
async def chat_completions(request: Request) -> Any:
    """Универсальный эндпоинт OpenAI /chat/completions."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    messages = body.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages is required and must be a non-empty list")

    system_parts: List[str] = []
    user_parts: List[str] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                str(part.get("text", "")) if isinstance(part, dict) else str(part)
                for part in content
            )
        if role == "system":
            system_parts.append(str(content))
        else:
            user_parts.append(f"{role.title()}: {content}")

    prompt = "\n".join(user_parts).strip()
    system_instruction = "\n".join(system_parts).strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="User message content cannot be empty")

    requested_model = body.get("model", "")
    internal_model = map_from_openai_id(requested_model) if requested_model else "gemini-flash-latest"

    temperature = float(body.get("temperature", 0.7))
    max_tokens = int(body.get("max_tokens", body.get("max_completion_tokens", 2048)))
    stream = bool(body.get("stream", False))

    now = int(time.time())
    completion_id = f"chatcmpl-{now}"

    try:
        chat_model = get_chat_model(internal_model, system_instruction=system_instruction)
    except Exception as e:
        logger.error(f"[RouterOpenAI] Ошибка инициализации модели {internal_model}: {e}")
        raise HTTPException(status_code=502, detail=f"Model initialization error: {e}")

    if stream:
        async def event_generator():
            try:
                if hasattr(chat_model, "generate_content_stream"):
                    async for chunk in chat_model.generate_content_stream(
                        prompt, temperature=temperature, max_tokens=max_tokens
                    ):
                        data = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": now,
                            "model": requested_model or internal_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"role": "assistant", "content": chunk},
                                    "finish_reason": "",
                                }
                            ],
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                else:
                    full_text = await chat_model.generate_content(
                        prompt, temperature=temperature, max_tokens=max_tokens
                    )
                    data = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": now,
                        "model": requested_model or internal_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": full_text},
                                "finish_reason": "",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                final_data = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": now,
                    "model": requested_model or internal_model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as exc:
                logger.error(f"[RouterOpenAI] Ошибка в SSE стриме: {exc}")
                yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    try:
        content = await chat_model.generate_content(
            prompt, temperature=temperature, max_tokens=max_tokens
        )
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": now,
            "model": requested_model or internal_model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(prompt.split()) + len(content.split()),
            },
        }
    except Exception as e:
        logger.error(f"[RouterOpenAI] Ошибка генерации для модели {internal_model}: {e}")
        raise HTTPException(status_code=502, detail=f"Generation failed: {e}")
