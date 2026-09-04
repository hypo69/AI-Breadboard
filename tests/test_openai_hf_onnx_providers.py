# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test bidirectional model identifier mapping
# =============================================================================
# Description:
#   Test bidirectional mapping between internal and OpenAI-format model identifiers.
#
# File: test_openai_hf_onnx_providers.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Test OpenAI-compatible, HuggingFace, and ONNX provider integration.

Tests model ID mapping, provider routing, and chat completion endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

from src.fastapi.router_openai import map_to_openai_id, map_from_openai_id
from src.ai.hf_chat import hf_client, HFChatBase
from src.ai.onnx_chat import onnx_client, ONNXChatBase
from src.ai.openai_compat_chat import OpenAICompatChat
from src.ai.converter.gguf_to_onnx import gguf_converter
from src.ai.model_manager import get_available_models
from main import app

def test_openai_id_mapping():
    """Test bidirectional model identifier mapping.
    
    Verifies that internal model IDs map to OpenAI format and back.
    """
    assert map_to_openai_id("foundry:qwen2.5-1.5b") == "foundry-qwen2.5-1.5b"
    assert map_to_openai_id("hf:Qwen/Qwen2.5-0.5B-Instruct") == "hf-Qwen/Qwen2.5-0.5B-Instruct"
    assert map_to_openai_id("onnx:models/gemma") == "onnx-models/gemma"
    assert map_to_openai_id("openai:gpt-4o") == "openai-gpt-4o"

    assert map_from_openai_id("foundry-qwen2.5-1.5b") == "foundry:qwen2.5-1.5b"
    assert map_from_openai_id("hf-Qwen/Qwen2.5-0.5B-Instruct") == "hf:Qwen/Qwen2.5-0.5B-Instruct"
    assert map_from_openai_id("onnx-models/gemma") == "onnx:models/gemma"
    assert map_from_openai_id("openai-gpt-4o") == "openai:gpt-4o"

def test_model_manager_new_providers():
    """Test model list retrieval for HuggingFace, ONNX, and OpenAI providers.
    
    Verifies that each provider returns a non-empty list of available models.
    """
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
    """Test GGUF converter availability status.
    
    Verifies that converter and optimizer availability can be checked.
    """
    status = gguf_converter.is_available()
    assert isinstance(status, dict)
    assert "converter" in status
    assert "optimizer" in status

def test_openai_compat_chat_generate():
    """Test content generation via OpenAICompatChat with mocked aiohttp.
    
    Verifies that the OpenAI-compatible client can generate responses.
    """
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
    """Test GET /v1/models endpoint.
    
    Verifies that the endpoint returns a list of models in OpenAI format.
    """
    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data.get("object") == "list"
    assert isinstance(data.get("data"), list)
    assert len(data.get("data")) > 0
    # Check for required fields
    first_model = data["data"][0]
    assert "id" in first_model
    assert "object" in first_model
    assert "owned_by" in first_model

def test_router_openai_chat_completions():
    """Test POST /v1/chat/completions endpoint.
    
    Verifies that the endpoint processes chat completion requests correctly.
    """
    client = TestClient(app)
    with patch("src.fastapi.router_openai.get_chat_model") as mock_get_model:
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
    """Test ask() and chat() methods with history for OpenAICompatChat.
    
    Verifies both single requests and multi-turn conversations work correctly.
    """
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
    """Test factory method create_for_provider.
    
    Verifies that the factory correctly initializes clients for different providers.
    """
    client_deepseek = OpenAICompatChat.create_for_provider("deepseek", "deepseek-chat")
    assert client_deepseek.model_id == "deepseek-chat"
    assert "deepseek.com" in client_deepseek.base_url

    client_groq = OpenAICompatChat.create_for_provider("groq", "llama-3.3-70b")
    assert client_groq.model_id == "llama-3.3-70b"
    assert "groq.com" in client_groq.base_url

def test_unified_chat_openai_routing():
    """Test UnifiedChatModel routing to OpenAICompatChat.
    
    Verifies that the unified model correctly routes to OpenAI-compatible provider.
    """
    async def _run():
        from src.ai.unified_chat import UnifiedChatModel
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
    """Test GET /api/chat/models endpoint returns all providers.
    
    Verifies that the endpoint includes OpenAI, HuggingFace, ONNX and other providers.
    """
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
