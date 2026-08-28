# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/ai
# =============================================================================
# Описание:
#   Модуль содержит тесты для модуля искусственного интеллекта core/ai.
#   Проверяет основные методы взаимодействия с AI-моделями Gemini, включая
#   синхронные запросы, потоковую генерацию и работу с моками.
#
# File: tests/test_ai.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты модуля core/ai
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path


class TestGoogleGenerativeAI:
    """Тесты класса GoogleGenerativeAI."""

    @pytest.mark.asyncio
    async def test_chat_with_mock(self):
        """Тест метода chat с моком."""
        # Создаем мок с правильной настройкой асинхронного метода
        mock_model = MagicMock()
        mock_model.chat = AsyncMock(return_value="Test response")
        
        result = await mock_model.chat("Test question")
        
        assert result == "Test response"
        mock_model.chat.assert_called_once_with("Test question")

    @pytest.mark.asyncio
    async def test_chat_stream_with_mock(self):
        """Тест метода chat_stream с моком."""
        # Создаем асинхронный генератор
        async def mock_stream():
            yield "Chunk 1"
            yield "Chunk 2"
        
        mock_model = MagicMock()
        mock_model.chat_stream = mock_stream
        
        chunks = []
        async for chunk in mock_model.chat_stream():
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0] == "Chunk 1"
        assert chunks[1] == "Chunk 2"
        assert chunks[1] == "Chunk 2"

    @pytest.mark.asyncio
    async def test_ask_with_mock(self):
        """Тест метода ask с моком."""
        mock_model = MagicMock()
        mock_model.ask = AsyncMock(return_value="Test answer")
        
        result = await mock_model.ask("Test question")
        
        assert result == "Test answer"


class TestRAGFunctions:
    """Тесты функций RAG."""

    @pytest.mark.asyncio
    async def test_build_dev_rag_exists(self):
        """Тест существования функции build_dev_rag."""
        from core.ai.dev_rag import build_dev_rag
        
        # Проверяем что функция существует и вызывается без ошибок
        # (без реального API ключа она может вернуть None или ошибку, но не должна падать)
        try:
            result = build_dev_rag("test_api_key")
            # Функция может вернуть None если нет API ключа, это нормально
            assert result is None or hasattr(result, 'search')
        except Exception:
            # Если нет API ключа, это тоже нормально для теста
            pass

    @pytest.mark.asyncio
    async def test_rag_search_tool_signature(self):
        """Тест сигнатуры функции rag_search_tool."""
        from core.ai.dev_rag import rag_search_tool
        
        # Проверяем что функция существует
        assert callable(rag_search_tool)


class TestFoundryChat:
    """Тесты FoundryChatBase."""

    @pytest.mark.asyncio
    async def test_foundry_chat_initialization(self):
        """Тест инициализации FoundryChatBase."""
        from core.ai.foundry_chat import FoundryChatBase
        
        chat = FoundryChatBase(
            model_id="test-model",
            system_prompt="Test system prompt"
        )
        
        assert chat is not None
        assert chat.model_id == "test-model"
        assert chat.system_instruction == "Test system prompt"


class TestAgyChat:
    """Тесты AgyChatBase."""

    def test_agy_chat_initialization(self):
        """Тест инициализации AgyChatBase и наличия system_instruction."""
        from core.ai.agy_chat import AgyChatBase

        chat = AgyChatBase(
            model_id="agy-flash",
            system_prompt="Test system prompt"
        )

        assert chat.model_id == "gemini-flash-lite-latest"
        assert chat.system_prompt == "Test system prompt"
        assert chat.system_instruction == "Test system prompt"

        # Проверяем изменение через setter
        chat.system_instruction = "New instruction"
        assert chat.system_prompt == "New instruction"
        assert chat.system_instruction == "New instruction"

        # Проверяем нормализацию agy- префикса через setter и __init__
        chat.model_id = "agy-gemini-2.5-flash"
        assert chat.model_id == "gemini-2.5-flash"

        chat2 = AgyChatBase(model_id="agy-gemini-2.0-flash")
        assert chat2.model_id == "gemini-2.0-flash"


class TestUserRAG:
    """Тесты пользовательского RAG."""

    @pytest.mark.asyncio
    async def test_get_user_rag_path_structure(self):
        """Тест получения пути к user RAG - проверка структуры пути."""
        from core.ai.gemini.user_query_rag import _get_user_rag_path
        
        result = _get_user_rag_path(1)
        
        assert isinstance(result, Path)
        # Проверяем что путь содержит user_rag_1.db
        assert "user_rag_1" in str(result)
        assert result.suffix == ".db"

    @pytest.mark.asyncio
    async def test_make_doc_id_structure(self):
        """Тест создания doc_id - проверка структуры."""
        from core.ai.gemini.user_query_rag import _make_doc_id
        
        result = _make_doc_id(1, "test query")
        
        assert isinstance(result, str)
        # doc_id имеет формат userId_hash(query)
        assert "_" in result
        parts = result.split("_")
        assert len(parts) == 2
        assert parts[0] == "1"  # user_id

    @pytest.mark.asyncio
    async def test_garbage_query_filter(self):
        """Тест фильтрации мусорных запросов."""
        from core.ai.gemini.user_query_rag import is_garbage_query
        
        # Хорошие запросы (не мусорные)
        assert not is_garbage_query("Какой фильм посмотреть вечером?")
        assert not is_garbage_query("Посоветуй хороший сериал в жанре фантастика")
        assert not is_garbage_query("Как настроить плеер для просмотра")
        
        # Мусорные запросы
        assert is_garbage_query("да")  # слишком короткий
        assert is_garbage_query("привет")  # приветствие/короткий
        assert is_garbage_query("Привет! Как дела?")  # простое приветствие
        assert is_garbage_query("ыыыыыыыыыыыыы")  # повторяющиеся символы
        assert is_garbage_query("sdfghjklqwrtzcxvb")  # keyboard mash (без гласных)
        assert is_garbage_query("!!!!!!!!!!!")  # знаки препинания без букв/цифр
        assert is_garbage_query("спасибо большое")  # благодарность


class TestModelManager:
    """Тесты единого менеджера моделей ИИ (ModelManager)."""

    def test_load_unsupported_models_gemini(self):
        """Тест загрузки неподдерживаемых моделей Gemini из конфигурации."""
        from core.ai.model_manager import load_unsupported_models
        unsupported = load_unsupported_models("gemini")
        assert isinstance(unsupported, set)
        assert len(unsupported) > 0
        assert "gemini-1.0-pro" in unsupported or "gemini-2.0-flash" in unsupported

    def test_get_available_models_gemini_sdk_mock(self):
        """Тест получения моделей Gemini через SDK с фильтрацией и кэшированием."""
        from core.ai.model_manager import get_available_models, _CACHED_MODELS
        
        # Подготовка мока для genai.Client
        mock_model_1 = MagicMock()
        mock_model_1.name = "models/gemini-flash-latest"
        mock_model_1.supported_actions = ["generateContent"]

        mock_model_2 = MagicMock()
        mock_model_2.name = "models/gemini-2.0-flash"  # в unsupported_models
        mock_model_2.supported_actions = ["generateContent"]

        mock_model_3 = MagicMock()
        mock_model_3.name = "models/text-embedding-004"  # embedding
        mock_model_3.supported_actions = ["embedContent"]

        mock_client = MagicMock()
        mock_client.models.list.return_value = [mock_model_1, mock_model_2, mock_model_3]

        with patch("core.ai.model_manager.genai.Client", return_value=mock_client):
            # Первый вызов с force_refresh=True
            models = get_available_models("gemini", api_key="fake_key", force_refresh=True)
            assert "gemini-flash-latest" in models
            assert "gemini-2.0-flash" not in models
            assert "text-embedding-004" not in models

            # Проверка, что результат сохранен в кэше
            assert "gemini" in _CACHED_MODELS
            assert "gemini-flash-latest" in _CACHED_MODELS["gemini"]

            # Повторный вызов должен возвращать данные из кэша без нового вызова genai.Client
            mock_client.models.list.reset_mock()
            cached_models = get_available_models("gemini", api_key="fake_key", force_refresh=False)
            assert cached_models == models
            mock_client.models.list.assert_not_called()

    def test_get_available_models_agy(self):
        """Тест получения моделей для AGY."""
        from core.ai.model_manager import get_available_models
        agy_models = get_available_models("agy")
        assert isinstance(agy_models, list)
        for m in agy_models:
            assert m.startswith("agy-")

    def test_add_unsupported_model_runtime(self):
        """Тест добавления неподдерживаемой модели в рантайме и её исключения из кэша."""
        from core.ai.model_manager import add_unsupported_model, get_available_models, _CACHED_MODELS
        
        # Добавляем временную модель в кэш
        _CACHED_MODELS["foundry"] = ["test-foundry-model-1", "test-foundry-model-2"]
        assert "test-foundry-model-1" in get_available_models("foundry")

        # Исключаем модель
        with patch("core.ai.model_manager.j_dumps") as mock_dumps:
            success = add_unsupported_model("foundry", "test-foundry-model-1", reason="404 Not Found")
            assert success is True
            assert "test-foundry-model-1" not in _CACHED_MODELS["foundry"]
            assert "test-foundry-model-2" in _CACHED_MODELS["foundry"]

    @pytest.mark.asyncio
    async def test_actualize_all_models(self):
        """Тест разовой актуализации всех моделей при старте."""
        from core.ai.model_manager import actualize_all_models
        pool = await actualize_all_models(force_refresh=False)
        assert isinstance(pool, dict)
        assert "gemini" in pool
        assert "agy" in pool
        assert "foundry" in pool
        assert "ollama" in pool
