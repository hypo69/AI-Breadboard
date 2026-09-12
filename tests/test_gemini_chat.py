# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Gemini chat adapter and streaming
# =============================================================================
# Description:
#   Validates GeminiChatBase streaming response yields, multi-turn history,
#   model normalization, and compatibility with unified chat interfaces.
#
# File: test_gemini_chat.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for GeminiChatBase streaming and adapter functionality."""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.providers.gemini.chat import GeminiChatBase
from src.ai.gemini_chat import GeminiChatBase as GeminiChatProxy


class TestGeminiChat:
    """Tests for GeminiChatBase provider adapter."""

    def test_proxy_import(self):
        """Verify proxy module re-exports GeminiChatBase correctly."""
        assert GeminiChatProxy is GeminiChatBase

    def test_normalize_model_id(self):
        """Verify model identifier normalization."""
        assert GeminiChatBase.normalize_model_id("") == "gemini-flash-latest"
        assert GeminiChatBase.normalize_model_id("gemini:gemini-3.7-flash") == "gemini-3.7-flash"
        assert GeminiChatBase.normalize_model_id("models/gemini-2.5-pro") == "gemini-2.5-pro"
        assert GeminiChatBase.normalize_model_id("gemini-2.5-flash") == "gemini-2.5-flash"

    def test_capabilities_and_availability(self):
        """Verify provider capabilities and availability checking."""
        caps = GeminiChatBase.get_capabilities()
        assert "chat" in caps
        assert "vision" in caps

        with patch.dict(os.environ, {"GEMINI_API_KEY_1": "AIzaSyTestKey"}):
            assert GeminiChatBase.is_available() is True

    @pytest.mark.asyncio
    async def test_chat_stream_tokens(self):
        """Verify chat_stream yields tokens sequentially in real-time."""
        chat = GeminiChatBase(model_id="gemini-3.7-flash", system_prompt="Test instruction")

        async def _fake_stream(q, **kwargs):
            for token in ["Hello", " ", "from", " ", "Gemini!"]:
                yield token

        with patch.object(chat.model, "chat_stream", side_effect=_fake_stream):
            tokens = []
            async for chunk in chat.chat_stream("Say hello"):
                tokens.append(chunk)

            assert "".join(tokens) == "Hello from Gemini!"
            assert len(tokens) == 5

    @pytest.mark.asyncio
    async def test_stream_chat_alias(self):
        """Verify stream_chat acts as an alias to chat_stream."""
        chat = GeminiChatBase(model_id="gemini-flash-latest")

        async def _fake_stream(q, **kwargs):
            for token in ["Chunk1", "Chunk2"]:
                yield token

        with patch.object(chat.model, "chat_stream", side_effect=_fake_stream):
            chunks = []
            async for chunk in chat.stream_chat("Test alias"):
                chunks.append(chunk)

            assert "".join(chunks) == "Chunk1Chunk2"

    @pytest.mark.asyncio
    async def test_ask_method(self):
        """Verify ask method delegates to underlying model."""
        chat = GeminiChatBase(model_id="gemini-3.7-flash")

        with patch.object(chat.model, "ask", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = "Answer from Gemini"
            result = await chat.ask("What is 2+2?")

            assert result == "Answer from Gemini"
            mock_ask.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_multi_turn_history(self):
        """Verify chat method accumulates history turns."""
        chat = GeminiChatBase(model_id="gemini-3.7-flash")

        async def _fake_stream(q, **kwargs):
            yield f"Echo: {q}"

        with patch.object(chat.model, "chat_stream", side_effect=_fake_stream):
            res1 = await chat.chat("Hello 1")
            assert res1 == "Echo: Hello 1"
            assert len(chat.history) == 2
            assert chat.history[0] == {"role": "user", "content": "Hello 1"}
            assert chat.history[1] == {"role": "model", "content": "Echo: Hello 1"}

            res2 = await chat.chat("Hello 2")
            assert res2 == "Echo: Hello 2"
            assert len(chat.history) == 4

            chat.clear_history()
            assert len(chat.history) == 0

    def test_model_id_and_system_prompt_properties(self):
        """Verify model_id and system_prompt property updates."""
        chat = GeminiChatBase(model_id="gemini-flash-latest", system_prompt="Initial prompt")
        assert chat.model_id == "gemini-flash-latest"
        assert chat.system_instruction == "Initial prompt"

        chat.model_id = "gemini:gemini-3.7-flash"
        assert chat.model_id == "gemini-3.7-flash"
        assert chat.model.model_name == "gemini-3.7-flash"

        chat.system_instruction = "Updated instruction"
        assert chat.system_instruction == "Updated instruction"
        assert chat.model.system_instruction == "Updated instruction"

    @pytest.mark.asyncio
    async def test_chat_stream_with_model_name_kwargs(self):
        """Verify chat_stream handles model_name in kwargs without duplicate argument errors."""
        chat = GeminiChatBase(model_id="gemini-3.7-flash")

        async def _fake_stream(q, **kwargs):
            assert kwargs.get("model_name") == "custom-gemini-model"
            yield "Success"

        with patch.object(chat.model, "chat_stream", side_effect=_fake_stream):
            tokens = []
            async for chunk in chat.chat_stream("Hello", model_name="custom-gemini-model"):
                tokens.append(chunk)

            assert "".join(tokens) == "Success"

    @pytest.mark.asyncio
    async def test_ask_with_model_name_kwargs(self):
        """Verify ask method handles model_name in kwargs without error."""
        chat = GeminiChatBase(model_id="gemini-3.7-flash")

        with patch.object(chat.model, "ask", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = "Answer"
            result = await chat.ask("Prompt", model_name="custom-gemini-model")

            assert result == "Answer"
            mock_ask.assert_called_once()

