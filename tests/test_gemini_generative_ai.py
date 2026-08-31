# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for GoogleGenerativeAI class and related utilities
# =============================================================================
# Description:
#   Comprehensive test suite for core/ai/gemini/generative_ai.py module.
#
# File: test_gemini_generative_ai.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Tests for GoogleGenerativeAI class and Gemini module utilities."""

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
# Section: Happy Path — Normal usage scenarios
# =============================================================================

class TestGoogleGenerativeAI_HappyPath:
    """Tests for normal and expected GoogleGenerativeAI usage scenarios.

    Covers: successful initialization, ask, chat, chat_stream, embed,
    describe_image, upload_file, ask_with_tools.
    """

    @pytest.mark.asyncio
    async def test_ask_happy_path(self):
        """Test single ask request with correct model response.

        Validates: method returns cleaned and normalized text.
        Dependencies: raised in many plugins and API endpoints.
        """
        # --- Setup (Arrange) ---
        # Text query from user for generation verification
        query_text: str = 'What is the capital of France?'

        # Prepare mock Google SDK response
        mock_response: MagicMock = MagicMock()
        mock_response.text = '```html<div>Paris</div>```\nThe capital of France is Paris.'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        # Initialize model with mocked SDK and active key
        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(api_key_names=['key_dev'])

            # --- Execution (Act) ---
            result: str = await ai_instance.ask(query_text)

            # --- Assertion (Assert) ---
            assert 'Paris' in result, (
                f'ask() must return model response text, got: {result!r}'
            )
            assert '```html' not in result, (
                f'ask() must remove HTML blocks from model response, got: {result!r}'
            )

    @pytest.mark.asyncio
    async def test_chat_happy_path_with_history(self):
        """Test dialogue chat with history preservation.

        Validates: messages are added to chat_history and response is returned.
        """
        # --- Setup (Arrange) ---
        user_message: str = 'Hello, how are you?'
        model_reply_text: str = 'Hello! All good.'

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

            # --- Execution (Act) ---
            result: str = await ai_instance.chat(user_message)

            # --- Assertion (Assert) ---
            assert result == model_reply_text, (
                f'chat() must return model response, got: {result!r}'
            )
            assert len(ai_instance.chat_history) == 2, (
                f'chat() must save 2 messages (user and model), history has: {len(ai_instance.chat_history)}'
            )

    @pytest.mark.asyncio
    async def test_chat_stream_happy_path(self):
        """Test streaming model response generation.

        Validates: generator sequentially yields text chunks.
        """
        # --- Setup (Arrange) ---
        user_prompt: str = 'Tell me a joke'
        chunk1: MagicMock = MagicMock()
        chunk1.text = 'A bear '
        chunk2: MagicMock = MagicMock()
        chunk2.text = 'walks...'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=False)

            # --- Execution (Act) ---
            chunks: list[str] = []
            async for chunk in ai_instance.chat_stream(user_prompt):
                chunks.append(chunk)

            # --- Assertion (Assert) ---
            assert len(chunks) == 2, (
                f'chat_stream() must return 2 chunks, got: {len(chunks)}'
            )
            assert ''.join(chunks) == 'A bear walks...', (
                f'Chunk content must merge correctly, got: {"".join(chunks)!r}'
            )

    @pytest.mark.asyncio
    async def test_embed_happy_path(self):
        """Test vector embedding generation.

        Validates: returns numpy.ndarray with numbers.
        """
        # --- Setup (Arrange) ---
        input_text: str = 'Text to vectorize'
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

            # --- Execution (Act) ---
            result = await ai_instance.embed(input_text)

            # --- Assertion (Assert) ---
            assert isinstance(result, np.ndarray), (
                f'embed() must return numpy.ndarray, got: {type(result)}'
            )
            assert len(result) == 4, (
                f'embed() vector size must be 4, got: {len(result)}'
            )

    @pytest.mark.asyncio
    async def test_ask_with_tools_happy_path(self):
        """Test agentic loop with function call and final response."""
        # --- Setup (Arrange) ---
        q: str = 'What is the temperature in Paris?'

        # Step 1: model requests function call get_weather
        call_part: MagicMock = MagicMock()
        call_part.function_call = MagicMock()
        call_part.function_call.name = 'get_weather'
        call_part.function_call.args = {'city': 'Paris'}
        call_part.text = ''

        response_step1: MagicMock = MagicMock()
        candidate1: MagicMock = MagicMock()
        candidate1.content.parts = [call_part]
        response_step1.candidates = [candidate1]

        # Step 2: model returns final text
        text_part: MagicMock = MagicMock()
        text_part.function_call = False
        text_part.text = 'The temperature in Paris is currently 20 degrees.'

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

            # --- Execution (Act) ---
            result = await ai_instance.ask_with_tools(q, tools=['tool_def'], tool_dispatcher=dispatcher_mock)

            # --- Assertion (Assert) ---
            assert result == 'The temperature in Paris is currently 20 degrees.', (
                f'ask_with_tools() must return final response, got: {result!r}'
            )
            dispatcher_mock.assert_called_once_with('get_weather', {'city': 'Paris'})

# =============================================================================
# Section: Edge Cases — Edge cases and empty data
# =============================================================================

class TestGoogleGenerativeAI_EdgeCases:
    """Tests for behavior with empty and non-standard input data."""

    @pytest.mark.asyncio
    async def test_ask_empty_query_returns_empty_string(self):
        """Check early return when passing empty query to ask."""
        # --- Setup (Arrange) ---
        empty_query: str = ''

        with patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.genai.Client'), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result: str = await ai_instance.ask(empty_query)

            # --- Assertion (Assert) ---
            assert result == '', (
                f'ask() with empty question must return empty string, got: {result!r}'
            )

    @pytest.mark.asyncio
    async def test_chat_empty_query_returns_empty_string(self):
        """Check early return when passing empty message to chat."""
        # --- Setup (Arrange) ---
        empty_message: str = ''

        with patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.genai.Client'), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result: str = await ai_instance.chat(empty_message)

            # --- Assertion (Assert) ---
            assert result == '', (
                f'chat() with empty question must return empty string, got: {result!r}'
            )

    @pytest.mark.asyncio
    async def test_embed_empty_text_returns_false(self):
        """Check early return False when text is empty for embedding."""
        # --- Setup (Arrange) ---
        empty_text: str = ''

        with patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.genai.Client'), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result = await ai_instance.embed(empty_text)

            # --- Assertion (Assert) ---
            assert result is False, (
                f'embed() with empty text must return False, got: {result!r}'
            )

    def test_normalize_text_and_remove_html_empty(self):
        """Check formatting utilities on empty strings."""
        # --- Execution and Assertion (Act & Assert) ---
        assert normalize_text('') == '', 'normalize_text("") must return ""'
        assert remove_html_blocks('') == '', 'remove_html_blocks("") must return ""'

# =============================================================================
# Section: Type Variants — valid type variants
# =============================================================================

class TestGoogleGenerativeAI_TypeVariants:
    """Tests for handling various parameter types (Path, bytes, IOBase)."""

    @pytest.mark.asyncio
    async def test_describe_image_with_bytes_and_path(self):
        """Check describe_image when passing bytes directly and via Path."""
        # --- Setup (Arrange) ---
        raw_bytes: bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # Simulate JPEG

        mock_response: MagicMock = MagicMock()
        mock_response.text = 'A nature image'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result_bytes = await ai_instance.describe_image(raw_bytes)

            # --- Assertion (Assert) ---
            assert result_bytes == 'A nature image', (
                f'describe_image() with bytes must return description, got: {result_bytes!r}'
            )

    @pytest.mark.asyncio
    async def test_upload_file_with_descriptor(self):
        """Check upload_file when passing BytesIO."""
        # --- Setup (Arrange) ---
        stream_file: BytesIO = BytesIO(b'Sample data')

        mock_client: MagicMock = MagicMock()
        mock_client.files.upload.return_value = MagicMock(name='uploaded_file')

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result: bool = await ai_instance.upload_file(stream_file, file_name='sample.txt')

            # --- Assertion (Assert) ---
            assert result is True, (
                f'upload_file() with file descriptor must return True, got: {result!r}'
            )

# =============================================================================
# Section: Boundary Values — Edge Cases
# =============================================================================

class TestGoogleGenerativeAI_BoundaryValues:
    """Tests for attempt limits and boundary delays."""

    @pytest.mark.asyncio
    async def test_ask_exceeds_max_attempts(self):
        """Check ask behavior when attempts=1 and constant failures."""
        # --- Setup (Arrange) ---
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError('SDK connection error')

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result: str = await ai_instance.ask('Any question', attempts=1)

            # --- Assertion (Assert) ---
            assert 'Error' in result or 'exhausted' in result, (
                f'ask() after exhausting attempts must return diagnostic message, got: {result!r}'
            )

# =============================================================================
# Section: Error Scenarios — resilience and error handling
# =============================================================================

class TestGoogleGenerativeAI_ErrorScenarios:
    """Tests for key rotation, model switching, and API error handling (401, 404, 503, 429)."""

    @pytest.mark.asyncio
    async def test_error_401_invalid_key_switches_key(self):
        """Error 401 API_KEY_INVALID must invalidate key and switch to second."""
        # --- Setup (Arrange) ---
        error_401: Exception = RuntimeError('401 API_KEY_INVALID: Key not valid')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with second key'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_401, success_response]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['bad_key', 'good_key'], ['k_bad', 'k_good'], ['k_bad', 'k_good'])), \
             patch('core.ai.gemini.generative_ai.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result: str = await ai_instance.ask('Test 401')

            # --- Assertion (Assert) ---
            assert result == 'Success with second key', (
                f'On 401 error must transition to valid key, got: {result!r}'
            )
            assert 'bad_key' not in ai_instance.api_keys, (
                'Invalid key must be removed from active pool'
            )

    @pytest.mark.asyncio
    async def test_error_404_unsupported_model_switches_model(self):
        """Error 404 NOT_FOUND must add model to unsupported and switch it."""
        # --- Setup (Arrange) ---
        error_404: Exception = RuntimeError('404 NOT_FOUND: Model is no longer available')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with new model'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_404, success_response]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), \
             patch('core.ai.gemini.generative_ai.get_status'), \
             patch('core.ai.gemini.generative_ai.GoogleGenerativeAI.get_available_models', return_value=['gemini-old', 'gemini-new']), \
             patch('core.ai.gemini.generative_ai.add_unsupported_model') as mock_add_unsupp:

            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(model_name='gemini-old')

            # --- Execution (Act) ---
            result: str = await ai_instance.ask('Test 404')

            # --- Assertion (Assert) ---
            assert result == 'Success with new model', (
                f'On 404 error must transition to available model, got: {result!r}'
            )
            assert ai_instance.model_name == 'gemini-new', (
                f'Active model name must update to gemini-new, current: {ai_instance.model_name}'
            )
            mock_add_unsupp.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_429_daily_quota_exhausted(self):
        """Error 429 PerDay quota must mark key exhausted and switch it."""
        # --- Setup (Arrange) ---
        error_429_daily: Exception = RuntimeError("429 RESOURCE_EXHAUSTED: quota_limit_value': '0'")
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with second key after 429'

        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_429_daily, success_response]

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['key1', 'key2'], ['k1', 'k2'], ['k1', 'k2'])), \
             patch('core.ai.gemini.generative_ai.get_status'), \
             patch('core.ai.gemini.generative_ai.mark_exhausted') as mock_mark:

            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()

            # --- Execution (Act) ---
            result: str = await ai_instance.ask('Test 429 Daily')

            # --- Assertion (Assert) ---
            assert result == 'Success with second key after 429', (
                f'On daily 429 must transition to next key, got: {result!r}'
            )
            mock_mark.assert_called_once_with('k1')

# =============================================================================
# Section: Regression — integration and regression scenarios
# =============================================================================

class TestGoogleGenerativeAI_Regression:
    """Regression testing for integration with UnifiedChatModel and exports."""

    def test_default_model_exported_correctly(self):
        """Check presence and string type of _DEFAULT_MODEL."""
        # --- Setup and Assertion (Act & Assert) ---
        from core.ai.gemini.generative_ai import _DEFAULT_MODEL
        assert isinstance(_DEFAULT_MODEL, str), '_DEFAULT_MODEL must be a string'
        assert len(_DEFAULT_MODEL) > 0, '_DEFAULT_MODEL must not be an empty string'

    @pytest.mark.asyncio
    async def test_unified_chat_model_integration(self):
        """Check UnifiedChatModel integration with updated GoogleGenerativeAI class."""
        # --- Setup (Arrange) ---
        from core.ai.unified_chat import UnifiedChatModel

        mock_client: MagicMock = MagicMock()
        mock_response: MagicMock = MagicMock()
        mock_response.text = 'Response via UnifiedChatModel'
        mock_client.models.generate_content.return_value = mock_response

        mock_chat: MagicMock = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat

        with patch('core.ai.gemini.generative_ai.genai.Client', return_value=mock_client), \
             patch('core.ai.gemini.generative_ai.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('core.ai.gemini.generative_ai.get_status'):

            unified_model: UnifiedChatModel = UnifiedChatModel(
                api_key_names=['key_dev'],
                system_instruction='Test instruction',
                foundry_model_id='test-foundry',
                use_foundry=False,
            )

            # --- Execution (Act) ---
            result = await unified_model.chat('Test request to unified')

            # --- Assertion (Assert) ---
            assert result == 'Response via UnifiedChatModel', (
                f'UnifiedChatModel must correctly call chat() on Gemini, got: {result!r}'
            )
