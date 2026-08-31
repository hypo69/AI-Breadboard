# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тесты класса GoogleGenerativeAI и сопутствующих ут
# =============================================================================
# Description:
#   Комплексный набор тестов для модуля core/ai/gemini/generative_ai.py.
#
# File: test_gemini_generative_ai.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты класса GoogleGenerativeAI и сопутствующих утилит модуля Gemini."""

import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from core.ai.gemini.generative_ai import (
    GoogleGenerativeAI,
    add_unsupported_model,
    load_unsupported_models,
    normalize_text,
    remove_html_blocks,
)

# =============================================================================
# Section: Happy Path — Normal Scenarios использования
# =============================================================================

class TestGoogleGenerativeAI_HappyPath:
    """Тестирование нормальных (ожидаемых) сценариев работы GoogleGenerativeAI.

    Покрывает: успешную инициализацию, ask, chat, chat_stream, embed,
    describe_image, upload_file, ask_with_tools.
    """

    @pytest.mark.asyncio
    async def test_ask_happy_path(self):
        """Тестирование одиночного запроса ask с корректным ответом модели.

        Check: method Returns очищенный нормализованный текст.
        Зависимости: Raisesся во многих плагинах и API endpoint'ах.
        """
        # --- Подготовка (Arrange) ---
        # Текстовый вопрос пользователя для проверки генерации
        query_text: str = 'Назови столицу Франции'

        # Подготовка мока ответа Google SDK
        mock_response: MagicMock = MagicMock()
        mock_response.text = '```html<div>Париж</div>```\nСтолица Франции — Париж.'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        # Initialization модели с моком SDK и активным ключом
        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(api_key_names=['key_dev'])

            # --- Выполнение (Act) ---
            result: str = await ai_instance.ask(query_text)

            # --- Check (Assert) ---
            assert 'Париж' in result, (
                f'ask() обязан вернуть текст ответа модели, получено: {result!r}'
            )
            assert '```html' not in result, (
                f'ask() обязан удалять HTML-блоки из ответа модели, получено: {result!r}'
            )

    @pytest.mark.asyncio
    async def test_chat_happy_path_with_history(self):
        """Тестирование диалогового чата с сохранением истории.

        Check: сообщения добавляются в chat_history и Returnsся ответ.
        """
        # --- Подготовка (Arrange) ---
        user_message: str = 'Привет, как дела?'
        model_reply_text: str = 'Привет! Все отлично.'

        mock_response: MagicMock = MagicMock()
        mock_response.text = model_reply_text

        mock_chat_session: MagicMock = MagicMock()
        mock_chat_session.send_message.return_value = mock_response

        mock_client: MagicMock = MagicMock()
        mock_client.chats.create.return_value = mock_chat_session

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=True)

            # --- Выполнение (Act) ---
            result: str = await ai_instance.chat(user_message)

            # --- Check (Assert) ---
            assert result == model_reply_text, (
                f'chat() обязан вернуть ответ модели, получено: {result!r}'
            )
            assert len(ai_instance.chat_history) == 2, (
                f'chat() обязан сохранить 2 сообщения (user и model), в истории: {len(ai_instance.chat_history)}'
            )

    @pytest.mark.asyncio
    async def test_chat_stream_happy_path(self):
        """Тестирование потоковой генерации ответа модели.

        Check: генератор последовательно отдает чанки текста.
        """
        # --- Подготовка (Arrange) ---
        user_prompt: str = 'Расскажи анекдот'
        chunk1: MagicMock = MagicMock()
        chunk1.text = 'Идет '
        chunk2: MagicMock = MagicMock()
        chunk2.text = 'медведь...'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=False)

            # --- Выполнение (Act) ---
            chunks: list[str] = []
            async for chunk in ai_instance.chat_stream(user_prompt):
                chunks.append(chunk)

            # --- Check (Assert) ---
            assert len(chunks) == 2, (
                f'chat_stream() обязан отдать 2 чанка, получено: {len(chunks)}'
            )
            assert ''.join(chunks) == 'Идет медведь...', (
                f'Содержимое чанков должно корректно объединяться, получено: {"".join(chunks)!r}'
            )

    @pytest.mark.asyncio
    async def test_embed_happy_path(self):
        """Тестирование генерации векторных эмбеддингов.

        Check: Returnsся numpy.ndarray с числами.
        """
        # --- Подготовка (Arrange) ---
        input_text: str = 'Векторизуемый текст'
        vector_data: list[float] = [0.1, 0.2, 0.3, 0.4]

        mock_embedding_obj: MagicMock = MagicMock()
        mock_embedding_obj.values = vector_data

        mock_response: MagicMock = MagicMock()
        mock_response.embeddings = [mock_embedding_obj]

        mock_client: MagicMock = MagicMock()
        mock_client.models.embed_content.return_value = mock_response

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result = await ai_instance.embed(input_text)

            # --- Check (Assert) ---
            assert isinstance(result, np.ndarray), (
                f'embed() обязан вернуть numpy.ndarray, получено: {type(result)}'
            )
            assert len(result) == 4, (
                f'embed() размер вектора должен быть 4, получено: {len(result)}'
            )

    @pytest.mark.asyncio
    async def test_ask_with_tools_happy_path(self):
        """Тестирование agentic loop с вызовом функции и финальным ответом."""
        # --- Подготовка (Arrange) ---
        q: str = 'Какая температура в Париже?'

        # 1-й шаг: модель запрашивает вызов функции get_weather
        call_part: MagicMock = MagicMock()
        call_part.function_call = MagicMock()
        call_part.function_call.name = 'get_weather'
        call_part.function_call.args = {'city': 'Paris'}
        call_part.text = ''

        response_step1: MagicMock = MagicMock()
        candidate1: MagicMock = MagicMock()
        candidate1.content.parts = [call_part]
        response_step1.candidates = [candidate1]

        # 2-й шаг: модель выдает финальный текст
        text_part: MagicMock = MagicMock()
        text_part.function_call = False
        text_part.text = 'В Париже сейчас 20 градусов.'

        response_step2: MagicMock = MagicMock()
        candidate2: MagicMock = MagicMock()
        candidate2.content.parts = [text_part]
        response_step2.candidates = [candidate2]

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [response_step1, response_step2]

        dispatcher_mock = MagicMock(return_value='+20 C, Sunny')

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result = await ai_instance.ask_with_tools(q, tools=['tool_def'], tool_dispatcher=dispatcher_mock)

            # --- Check (Assert) ---
            assert result == 'В Париже сейчас 20 градусов.', (
                f'ask_with_tools() должен вернуть финальный ответ, получено: {result!r}'
            )
            dispatcher_mock.assert_called_once_with('get_weather', {'city': 'Paris'})

# =============================================================================
# Section: Edge Cases — Edge Cases и пустые данные
# =============================================================================

class TestGoogleGenerativeAI_EdgeCases:
    """Тестирование поведения при пустых и нестандартных входных данных."""

    @pytest.mark.asyncio
    async def test_ask_empty_query_returns_empty_string(self):
        """Check раннего возврата при передаче пустого запроса в ask."""
        # --- Подготовка (Arrange) ---
        empty_query: str = ''

        with patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.genai.Client'), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result: str = await ai_instance.ask(empty_query)

            # --- Check (Assert) ---
            assert result == '', (
                f'ask() при пустом вопросе обязан возвращать пустую строку, получено: {result!r}'
            )

    @pytest.mark.asyncio
    async def test_chat_empty_query_returns_empty_string(self):
        """Check раннего возврата при передаче пустого сообщения в chat."""
        # --- Подготовка (Arrange) ---
        empty_message: str = ''

        with patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.genai.Client'), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result: str = await ai_instance.chat(empty_message)

            # --- Check (Assert) ---
            assert result == '', (
                f'chat() при пустом вопросе обязан возвращать пустую строку, получено: {result!r}'
            )

    @pytest.mark.asyncio
    async def test_embed_empty_text_returns_false(self):
        """Check раннего возврата False при пустом тексте для эмбеддинга."""
        # --- Подготовка (Arrange) ---
        empty_text: str = ''

        with patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.genai.Client'), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result = await ai_instance.embed(empty_text)

            # --- Check (Assert) ---
            assert result is False, (
                f'embed() при пустом тексте обязан возвращать False, получено: {result!r}'
            )

    def test_normalize_text_and_remove_html_empty(self):
        """Check утилит форматирования на пустых строках."""
        # --- Выполнение и check (Act & Assert) ---
        assert normalize_text('') == '', 'normalize_text("") должен возвращать ""'
        assert remove_html_blocks('') == '', 'remove_html_blocks("") должен возвращать ""'

# =============================================================================
# Section: Type Variants — варианты допустимых типов
# =============================================================================

class TestGoogleGenerativeAI_TypeVariants:
    """Тестирование обработки различных типов параметров (Path, bytes, IOBase)."""

    @pytest.mark.asyncio
    async def test_describe_image_with_bytes_and_path(self):
        """Check describe_image при передаче байтов напрямую и через Path."""
        # --- Подготовка (Arrange) ---
        raw_bytes: bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # Симуляция JPEG

        mock_response: MagicMock = MagicMock()
        mock_response.text = 'Изображение природы'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result_bytes = await ai_instance.describe_image(raw_bytes)

            # --- Check (Assert) ---
            assert result_bytes == 'Изображение природы', (
                f'describe_image() с bytes должен вернуть описание, получено: {result_bytes!r}'
            )

    @pytest.mark.asyncio
    async def test_upload_file_with_descriptor(self):
        """Check upload_file при передаче BytesIO."""
        # --- Подготовка (Arrange) ---
        stream_file: BytesIO = BytesIO(b'Sample data')

        mock_client: MagicMock = MagicMock()
        mock_client.files.upload.return_value = MagicMock(name='uploaded_file')

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result: bool = await ai_instance.upload_file(stream_file, file_name='sample.txt')

            # --- Check (Assert) ---
            assert result is True, (
                f'upload_file() с файловым дескриптором должен вернуть True, получено: {result!r}'
            )

# =============================================================================
# Section: Boundary Values — Edge Cases
# =============================================================================

class TestGoogleGenerativeAI_BoundaryValues:
    """Тестирование лимитов попыток и граничных задержек."""

    @pytest.mark.asyncio
    async def test_ask_exceeds_max_attempts(self):
        """Check поведения ask при попытке attempts=1 и постоянных сбоях."""
        # --- Подготовка (Arrange) ---
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError('SDK connection error')

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result: str = await ai_instance.ask('Любой вопрос', attempts=1)

            # --- Check (Assert) ---
            assert 'Error модели' in result or 'исчерпаны' in result, (
                f'ask() после исчерпания попыток должен вернуть диагностическое сообщение, получено: {result!r}'
            )

# =============================================================================
# Section: Error Scenarios — отказоустойчивость и обработка сбоев
# =============================================================================

class TestGoogleGenerativeAI_ErrorScenarios:
    """Тестирование ротации ключей, моделей и реакции на ошибки API (401, 404, 503, 429)."""

    @pytest.mark.asyncio
    async def test_error_401_invalid_key_switches_key(self):
        """Error 401 API_KEY_INVALID должна инвалидировать ключ и переключить на второй."""
        # --- Подготовка (Arrange) ---
        error_401: Exception = RuntimeError('401 API_KEY_INVALID: Key not valid')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success со вторым ключом'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_401, success_response]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['bad_key', 'good_key'], ['k_bad', 'k_good'], ['k_bad', 'k_good'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result: str = await ai_instance.ask('Тест 401')

            # --- Check (Assert) ---
            assert result == 'Success со вторым ключом', (
                f'При ошибке 401 должен произойти transition на valid ключ, получено: {result!r}'
            )
            assert 'bad_key' not in ai_instance.api_keys, (
                'Invalid ключ обязан быть удален из активного пула'
            )

    @pytest.mark.asyncio
    async def test_error_404_unsupported_model_switches_model(self):
        """Error 404 NOT_FOUND должна добавить модель в unsupported и сменить её."""
        # --- Подготовка (Arrange) ---
        error_404: Exception = RuntimeError('404 NOT_FOUND: Model is no longer available')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success с новой моделью'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_404, success_response]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), \
             patch('core.ai.gemini.generative_ai.get_status'), \
             patch('core.ai.gemini.generative_ai.GoogleGenerativeAI.get_available_models', return_value=['gemini-old', 'gemini-new']), \
             patch('core.ai.gemini.generative_ai.add_unsupported_model') as mock_add_unsupp:

            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(model_name='gemini-old')

            # --- Выполнение (Act) ---
            result: str = await ai_instance.ask('Тест 404')

            # --- Check (Assert) ---
            assert result == 'Success с новой моделью', (
                f'При ошибке 404 должен произойти transition на доступную модель, получено: {result!r}'
            )
            assert ai_instance.model_name == 'gemini-new', (
                f'Имя активной модели должно обновиться на gemini-new, текущее: {ai_instance.model_name}'
            )
            mock_add_unsupp.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_429_daily_quota_exhausted(self):
        """Error 429 PerDay квоты должна пометить ключ exhausted и переключить его."""
        # --- Подготовка (Arrange) ---
        error_429_daily: Exception = RuntimeError("429 RESOURCE_EXHAUSTED: quota_limit_value': '0'")
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success со вторым ключом после 429'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_429_daily, success_response]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['key1', 'key2'], ['k1', 'k2'], ['k1', 'k2'])), \
             patch('core.ai.gemini.generative_ai.get_status'), \
             patch('core.ai.gemini.generative_ai.mark_exhausted') as mock_mark:

            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Выполнение (Act) ---
            result: str = await ai_instance.ask('Тест 429 Daily')

            # --- Check (Assert) ---
            assert result == 'Success со вторым ключом после 429', (
                f'При суточной 429 должен произойти transition на следующий ключ, получено: {result!r}'
            )
            mock_mark.assert_called_once_with('k1')

# =============================================================================
# Section: Regression — интеграционные и регрессионные сценарии
# =============================================================================

class TestGoogleGenerativeAI_Regression:
    """Регрессионное тестирование интеграции с UnifiedChatModel и экспортов."""

    def test_default_model_exported_correctly(self):
        """Check наличия и строкового типа _DEFAULT_MODEL."""
        # --- Подготовка и check (Act & Assert) ---
        from core.ai.gemini.generative_ai import _DEFAULT_MODEL
        assert isinstance(_DEFAULT_MODEL, str), '_DEFAULT_MODEL обязан быть строкой'
        assert len(_DEFAULT_MODEL) > 0, '_DEFAULT_MODEL не должен быть empty строкой'

    @pytest.mark.asyncio
    async def test_unified_chat_model_integration(self):
        """Check работы UnifiedChatModel с обновленным классом GoogleGenerativeAI."""
        # --- Подготовка (Arrange) ---
        from core.ai.unified_chat import UnifiedChatModel

        mock_client: MagicMock = MagicMock()
        mock_response: MagicMock = MagicMock()
        mock_response.text = 'Ответ через UnifiedChatModel'
        mock_client.models.generate_content.return_value = mock_response

        mock_chat: MagicMock = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):

            unified_model: UnifiedChatModel = UnifiedChatModel(
                api_key_names=['key_dev'],
                system_instruction='Тестовая инструкция',
                foundry_model_id='test-foundry',
                use_foundry=False,
            )

            # --- Выполнение (Act) ---
            result = await unified_model.chat('Тестовый запрос в unified')

            # --- Check (Assert) ---
            assert result == 'Ответ через UnifiedChatModel', (
                f'UnifiedChatModel обязан корректно вызывать chat() у Gemini, получено: {result!r}'
            )
