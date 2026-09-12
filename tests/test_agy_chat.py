# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for Antigravity SDK chat adapter
# =============================================================================
# Description:
#   Validates persistent Agent lifecycle, streaming response yields, and error handling.
#
# File: test_agy_chat.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for AgyChatBase persistent Agent session and streaming."""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

if "USERPROFILE" not in os.environ:
    os.environ["USERPROFILE"] = os.path.expanduser("~") or "C:\\Users\\Default"

from src.ai.providers.agy.chat import AgyChatBase


class TestAgyChat:
    """Tests for AgyChatBase adapter."""

    def test_normalize_model_id(self):
        """Verify model identifier normalization."""
        assert AgyChatBase.normalize_model_id("") == "gemini-flash-lite-latest"
        assert AgyChatBase.normalize_model_id("flash") == "gemini-flash-lite-latest"
        assert AgyChatBase.normalize_model_id("agy-flash") == "gemini-flash-lite-latest"
        assert AgyChatBase.normalize_model_id("pro") == "gemini-pro-latest"
        assert AgyChatBase.normalize_model_id("agy-pro") == "gemini-pro-latest"
        assert AgyChatBase.normalize_model_id("2.5-flash") == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_persistent_agent_streaming(self):
        """Test persistent agent re-use across streaming calls."""
        chat = AgyChatBase(model_id="agy-flash", system_prompt="Test sys")

        mock_agent = MagicMock()
        mock_agent.is_started = True
        mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_agent.__aexit__ = AsyncMock(return_value=None)

        async def fake_stream_1(prompt):
            for token in ["Hello", " ", "World"]:
                yield token

        async def fake_stream_2(prompt):
            for token in ["Second", " ", "Turn"]:
                yield token

        mock_google_agy = MagicMock()
        mock_google_agy.Agent = MagicMock(return_value=mock_agent)
        mock_google_agy.LocalAgentConfig = MagicMock()
        mock_google_agy.CapabilitiesConfig = MagicMock()

        mock_agent.chat = AsyncMock(side_effect=[fake_stream_1("q1"), fake_stream_2("q2")])

        with patch.dict(sys.modules, {"google.antigravity": mock_google_agy}):
            # First turn
            tokens_1 = []
            async for chunk in chat.chat_stream("Hello"):
                tokens_1.append(chunk)

            assert "".join(tokens_1) == "Hello World"
            assert mock_google_agy.Agent.call_count == 1
            mock_agent.__aenter__.assert_called_once()
            mock_agent.__aexit__.assert_not_called()

            # Second turn - should reuse existing agent instance
            tokens_2 = []
            async for chunk in chat.chat_stream("Second message"):
                tokens_2.append(chunk)

            assert "".join(tokens_2) == "Second Turn"
            assert mock_google_agy.Agent.call_count == 1
            mock_agent.__aenter__.assert_called_once()
            mock_agent.__aexit__.assert_not_called()

            # Explicit close terminates session
            await chat.close()
            mock_agent.__aexit__.assert_called_once()
            assert chat._agent is None
