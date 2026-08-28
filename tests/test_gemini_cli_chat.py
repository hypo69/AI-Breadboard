# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование интеграции Google Gemini CLI
# =============================================================================
# Описание:
#   Unit-тесты для адаптера GeminiCliChatBase, маршрутизации UnifiedChatModel
#   и управления пулом моделей в model_manager.
#
# File: test_gemini_cli_chat.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from core.ai.gemini_cli_chat import GeminiCliChatBase
from core.ai.model_manager import get_available_models, load_unsupported_models, add_unsupported_model
from core.ai.unified_chat import UnifiedChatModel
from core.fastapi.router_chat import get_chat_model


class TestGeminiCliChat:
    """Тестирование класса GeminiCliChatBase."""

    def test_normalize_model_id_defaults(self):
        """Проверка нормализации идентификатора модели по умолчанию."""
        assert GeminiCliChatBase.normalize_model_id("") == "gemini-3.1-flash-lite"
        assert GeminiCliChatBase.normalize_model_id("gemini_cli:gemini-3.1-flash-lite") == "gemini-3.1-flash-lite"
        assert GeminiCliChatBase.normalize_model_id("gemini-cli-gemini-2.5-flash") == "gemini-2.5-flash"
        assert GeminiCliChatBase.normalize_model_id("models/gemini-2.5-pro") == "gemini-2.5-pro"

    @pytest.mark.asyncio
    async def test_ask_mock_subprocess(self):
        """Тестирование метода ask с моком подпроцесса."""
        chat = GeminiCliChatBase(model_id="gemini-3.1-flash-lite", system_prompt="Test sys prompt")
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Test CLI answer", b""))

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)) as mock_exec:
            res = await chat.ask("Hello CLI")
            assert res == "Test CLI answer"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_saves_history(self):
        """Тестирование метода chat с сохранением истории."""
        chat = GeminiCliChatBase(model_id="gemini-3.1-flash-lite")
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Response 1", b""))

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
            res = await chat.chat("Hi")
            assert res == "Response 1"
            assert len(chat.history) == 2
            assert chat.history[0] == {"role": "user", "content": "Hi"}
            assert chat.history[1] == {"role": "model", "content": "Response 1"}

    @pytest.mark.asyncio
    async def test_chat_stream(self):
        """Тестирование потокового получения данных chat_stream."""
        chat = GeminiCliChatBase(model_id="gemini-3.1-flash-lite")
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock(return_value=0)

        # Мок readline
        lines = [b"Chunk 1\n", b"Chunk 2\n", b""]
        mock_proc.stdout.readline = AsyncMock(side_effect=lines)

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
            chunks = []
            async for c in chat.chat_stream("Stream prompt"):
                chunks.append(c)

            assert len(chunks) == 2
            assert chunks[0] == "Chunk 1\n"
            assert chunks[1] == "Chunk 2\n"


class TestModelManagerGeminiCli:
    """Тестирование управления моделями Gemini CLI в model_manager."""

    def test_get_available_models_gemini_cli(self):
        """Проверка получения списка моделей Gemini CLI."""
        models = get_available_models(provider="gemini_cli", force_refresh=True)
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gemini-3.1-flash-lite" in models
        assert models[0] == "gemini-3.1-flash-lite"

    def test_unsupported_models_filter(self):
        """Проверка фильтрации неподдерживаемых моделей."""
        unsupported = load_unsupported_models("gemini_cli")
        assert isinstance(unsupported, set)


class TestRouterChatGeminiCliIntegration:
    """Тестирование фабрики роутера get_chat_model."""

    def test_get_chat_model_gemini_cli(self):
        """Проверка создания экземпляра GeminiCliChatBase через get_chat_model."""
        model = get_chat_model("gemini_cli:gemini-3.1-flash-lite", system_instruction="Test")
        assert isinstance(model, GeminiCliChatBase)
        assert model.model_id == "gemini-3.1-flash-lite"
        assert model.system_instruction == "Test"


class TestUnifiedChatGeminiCliIntegration:
    """Тестирование роутинга в UnifiedChatModel."""

    @pytest.mark.asyncio
    async def test_unified_chat_gemini_cli_dispatch(self):
        """Проверка перенаправления запросов к Gemini CLI через UnifiedChatModel."""
        unified = UnifiedChatModel(
            api_key_names=[],
            system_instruction="Default system",
            foundry_model_id="qwen2.5-1.5b-instruct-generic-cpu:4",
        )

        active_model, active_name = unified._get_active_model("gemini_cli:gemini-3.1-flash-lite")
        assert isinstance(active_model, GeminiCliChatBase)
        assert active_name == "gemini_cli:gemini-3.1-flash-lite"
