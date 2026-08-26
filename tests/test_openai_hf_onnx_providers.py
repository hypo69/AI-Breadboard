# -*- coding: utf-8 -*-
# =============================================================================
# Тесты для HuggingFace, ONNX и OpenAI-совместимых провайдеров
# =============================================================================

import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

from core.fastapi.router_openai import map_to_openai_id, map_from_openai_id
from core.ai.hf_chat import hf_client, HFChatBase
from core.ai.onnx_chat import onnx_client, ONNXChatBase
from core.ai.openai_compat_chat import OpenAICompatChat
from core.ai.converter.gguf_to_onnx import gguf_converter
from core.ai.model_manager import get_available_models
from main import app


def test_openai_id_mapping():
    """Проверка двустороннего маппинга идентификаторов моделей."""
    assert map_to_openai_id("foundry:qwen2.5-1.5b") == "foundry-qwen2.5-1.5b"
    assert map_to_openai_id("hf:Qwen/Qwen2.5-0.5B-Instruct") == "hf-Qwen/Qwen2.5-0.5B-Instruct"
    assert map_to_openai_id("onnx:models/gemma") == "onnx-models/gemma"
    assert map_to_openai_id("openai:gpt-4o") == "openai-gpt-4o"

    assert map_from_openai_id("foundry-qwen2.5-1.5b") == "foundry:qwen2.5-1.5b"
    assert map_from_openai_id("hf-Qwen/Qwen2.5-0.5B-Instruct") == "hf:Qwen/Qwen2.5-0.5B-Instruct"
    assert map_from_openai_id("onnx-models/gemma") == "onnx:models/gemma"
    assert map_from_openai_id("openai-gpt-4o") == "openai:gpt-4o"


def test_model_manager_new_providers():
    """Проверка возврата списков моделей для hf, onnx и openai."""
    hf_models = get_available_models("hf", force_refresh=True)
    assert isinstance(hf_models, list)
    assert len(hf_models) > 0

    openai_models = get_available_models("openai", force_refresh=True)
    assert isinstance(openai_models, list)
    assert len(openai_models) > 0
    assert "gpt-4o" in openai_models or "gpt-4o-mini" in openai_models

    onnx_models = get_available_models("onnx", force_refresh=True)
    assert isinstance(onnx_models, list)


def test_gguf_converter_availability():
    """Проверка статуса доступности конвертера."""
    status = gguf_converter.is_available()
    assert isinstance(status, dict)
    assert "converter" in status
    assert "optimizer" in status


def test_openai_compat_chat_generate():
    """Проверка генерации через OpenAICompatChat с моком aiohttp."""
    async def _run():
        client = OpenAICompatChat(model_id="gpt-4o-mini", api_key="test-key")
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Hello from OpenAI-compat!"}}]
            })
            mock_post.return_value.__aenter__.return_value = mock_response

            res = await client.generate_content("Hi")
            assert res == "Hello from OpenAI-compat!"

    import asyncio
    asyncio.run(_run())


def test_router_openai_list_models():
    """Проверка эндпоинта GET /v1/models."""
    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data.get("object") == "list"
    assert isinstance(data.get("data"), list)
    assert len(data.get("data")) > 0
    # Проверка наличия обязательных полей
    first_model = data["data"][0]
    assert "id" in first_model
    assert "object" in first_model
    assert "owned_by" in first_model


def test_router_openai_chat_completions():
    """Проверка эндпоинта POST /v1/chat/completions."""
    client = TestClient(app)
    with patch("core.fastapi.router_openai.get_chat_model") as mock_get_model:
        mock_chat = AsyncMock()
        mock_chat.generate_content = AsyncMock(return_value="Universal assistant reply")
        mock_get_model.return_value = mock_chat

        payload = {
            "model": "gemini-flash-latest",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Test prompt"}
            ],
            "temperature": 0.5,
            "max_tokens": 100,
            "stream": False
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("object") == "chat.completion"
        assert len(data.get("choices", [])) == 1
        assert data["choices"][0]["message"]["content"] == "Universal assistant reply"


def test_openai_compat_chat_ask_and_chat():
    """Проверка методов ask() и chat() с историей для OpenAICompatChat."""
    async def _run():
        client = OpenAICompatChat(model_id="gpt-4o", api_key="test-key", system_prompt="Sys prompt")
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Answer from GPT-4o"}}]
            })
            mock_post.return_value.__aenter__.return_value = mock_response

            # Test ask
            ans_ask = await client.ask("Hello")
            assert ans_ask == "Answer from GPT-4o"

            # Test chat with history
            history = [
                {"role": "user", "parts": ["Previous query"]},
                {"role": "model", "parts": ["Previous answer"]}
            ]
            ans_chat = await client.chat("Follow-up question", history=history)
            assert ans_chat == "Answer from GPT-4o"

    import asyncio
    asyncio.run(_run())


def test_openai_compat_provider_factory():
    """Проверка фабричного метода create_for_provider."""
    client_deepseek = OpenAICompatChat.create_for_provider("deepseek", "deepseek-chat")
    assert client_deepseek.model_id == "deepseek-chat"
    assert "deepseek.com" in client_deepseek.base_url

    client_groq = OpenAICompatChat.create_for_provider("groq", "llama-3.3-70b")
    assert client_groq.model_id == "llama-3.3-70b"
    assert "groq.com" in client_groq.base_url


def test_unified_chat_openai_routing():
    """Проверка маршрутизации UnifiedChatModel на OpenAICompatChat."""
    async def _run():
        from core.ai.unified_chat import UnifiedChatModel
        chat_model = UnifiedChatModel(
            api_key_names=[],
            system_instruction="Test system",
            foundry_model_id="qwen2.5",
        )
        with patch.object(OpenAICompatChat, "chat", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "Routed answer from OpenAI"
            res = await chat_model.chat("Test prompt", model_name="openai:gpt-4o")
            assert res == "Routed answer from OpenAI"

    import asyncio
    asyncio.run(_run())


def test_router_chat_models_endpoint():
    """Проверка, что GET /api/chat/models возвращает все провайдеры включая openai, hf, onnx."""
    client = TestClient(app)
    response = client.get("/api/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    models = data["models"]
    assert "gemini" in models
    assert "foundry" in models
    assert "ollama" in models
    assert "openai" in models
    assert "hf" in models
    assert "onnx" in models
