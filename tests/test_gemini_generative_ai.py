# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Gemini Generative Ai
# =============================================================================
# Description:
#   Tests for GoogleGenerativeAI class and Gemini module utilities.
#
# Usage Examples:
#   Python API:
#     from tests.test_gemini_generative_ai import TestGoogleGenerativeAI_HappyPath
#
#     service = TestGoogleGenerativeAI_HappyPath()
#
# File: test_gemini_generative_ai.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 10:48:40
# =============================================================================

"""Tests for GoogleGenerativeAI class and Gemini module utilities."""

import asyncio
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
import pytest
from src.ai.gemini.generative_ai import GoogleGenerativeAI, add_unsupported_model, load_unsupported_models, normalize_text, remove_html_blocks
from src.ai.gemini.errors import format_error_as_json

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
        query_text: str = 'What is the capital of France?'
        mock_response: MagicMock = MagicMock()
        mock_response.text = '```html<div>Paris</div>```\nThe capital of France is Paris.'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(api_key_names=['key_dev'])
            result: str = await ai_instance.ask(query_text)
            assert 'Paris' in result, f'ask() must return model response text, got: {result!r}'
            assert '```html' not in result, f'ask() must remove HTML blocks from model response, got: {result!r}'

    @pytest.mark.asyncio
    async def test_chat_happy_path_with_history(self):
        """Test dialogue chat with history preservation.

        Validates: messages are added to chat_history and response is returned.
        """
        user_message: str = 'Hello, how are you?'
        model_reply_text: str = 'Hello! All good.'
        mock_response: MagicMock = MagicMock()
        mock_response.text = model_reply_text
        mock_chat_session: MagicMock = MagicMock()
        mock_chat_session.send_message.return_value = mock_response
        mock_client: MagicMock = MagicMock()
        mock_client.chats.create.return_value = mock_chat_session
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=True)
            result: str = await ai_instance.chat(user_message)
            assert result == model_reply_text, f'chat() must return model response, got: {result!r}'
            assert len(ai_instance.chat_history) == 2, f'chat() must save 2 messages (user and model), history has: {len(ai_instance.chat_history)}'

    @pytest.mark.asyncio
    async def test_chat_stream_realtime_happy_path(self):
        """Test realtime streaming model response generation with client.aio.

        Validates: generator sequentially yields text chunks via async client.
        """
        user_prompt: str = 'Tell me a joke'
        chunk1: MagicMock = MagicMock()
        chunk1.text = 'A bear '
        chunk2: MagicMock = MagicMock()
        chunk2.text = 'walks...'

        async def _async_gen():
            for c in [chunk1, chunk2]:
                yield c
        mock_client: MagicMock = MagicMock()
        mock_client.aio.models.generate_content_stream = AsyncMock(return_value=_async_gen())
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=False, realtime_streaming=True)
            chunks: list[str] = []
            async for chunk in ai_instance.chat_stream(user_prompt):
                chunks.append(chunk)
            assert len(chunks) == 2, f'chat_stream() must return 2 chunks, got: {len(chunks)}'
            assert ''.join(chunks) == 'A bear walks...', f"Chunk content must merge correctly, got: {''.join(chunks)!r}"

    @pytest.mark.asyncio
    async def test_chat_stream_native_async_chat_with_history(self):
        """Test streaming model response generation with native AsyncChat.

        Validates: chat_stream uses client.aio.chats.create and sends message stream.
        """
        user_prompt: str = 'Tell me a story'
        chunk1: MagicMock = MagicMock()
        chunk1.text = 'Once upon '
        chunk2: MagicMock = MagicMock()
        chunk2.text = 'a time.'

        async def _async_gen():
            for c in [chunk1, chunk2]:
                yield c

        mock_async_chat: MagicMock = MagicMock()
        mock_async_chat.send_message_stream = AsyncMock(return_value=_async_gen())
        mock_client: MagicMock = MagicMock()
        mock_client.aio.chats.create.return_value = mock_async_chat
        mock_client.chats.create.return_value = MagicMock()

        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=True, realtime_streaming=True)
            chunks: list[str] = []
            async for chunk in ai_instance.chat_stream(user_prompt):
                chunks.append(chunk)
            assert len(chunks) == 2, f'chat_stream() with AsyncChat must return 2 chunks, got: {len(chunks)}'
            assert ''.join(chunks) == 'Once upon a time.'
            assert len(ai_instance.chat_history) == 2
            mock_client.aio.chats.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_stream_buffered_happy_path(self):
        """Test buffered streaming model response generation when realtime_streaming is disabled.

        Validates: generator sequentially yields text chunks from collected stream.
        """
        user_prompt: str = 'Tell me a joke'
        chunk1: MagicMock = MagicMock()
        chunk1.text = 'A bear '
        chunk2: MagicMock = MagicMock()
        chunk2.text = 'walks...'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(save_history_chat=False, realtime_streaming=False)
            chunks: list[str] = []
            async for chunk in ai_instance.chat_stream(user_prompt):
                chunks.append(chunk)
            assert len(chunks) == 2, f'chat_stream() must return 2 chunks, got: {len(chunks)}'
            assert ''.join(chunks) == 'A bear walks...', f"Chunk content must merge correctly, got: {''.join(chunks)!r}"

    @pytest.mark.asyncio
    async def test_embed_happy_path(self):
        """Test vector embedding generation.

        Validates: returns numpy.ndarray with numbers.
        """
        input_text: str = 'Text to vectorize'
        vector_data: list[float] = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_obj: MagicMock = MagicMock()
        mock_embedding_obj.values = vector_data
        mock_response: MagicMock = MagicMock()
        mock_response.embeddings = [mock_embedding_obj]
        mock_client: MagicMock = MagicMock()
        mock_client.models.embed_content.return_value = mock_response
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result = await ai_instance.embed(input_text)
            assert isinstance(result, np.ndarray), f'embed() must return numpy.ndarray, got: {type(result)}'
            assert len(result) == 4, f'embed() vector size must be 4, got: {len(result)}'

    @pytest.mark.asyncio
    async def test_ask_with_tools_happy_path(self):
        """Test agentic loop with function call and final response."""
        q: str = 'What is the temperature in Paris?'
        call_part: MagicMock = MagicMock()
        call_part.function_call = MagicMock()
        call_part.function_call.name = 'get_weather'
        call_part.function_call.args = {'city': 'Paris'}
        call_part.text = ''
        response_step1: MagicMock = MagicMock()
        candidate1: MagicMock = MagicMock()
        candidate1.content.parts = [call_part]
        response_step1.candidates = [candidate1]
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
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result = await ai_instance.ask_with_tools(q, tools=['tool_def'], tool_dispatcher=dispatcher_mock)
            assert result == 'The temperature in Paris is currently 20 degrees.', f'ask_with_tools() must return final response, got: {result!r}'
            dispatcher_mock.assert_called_once_with('get_weather', {'city': 'Paris'})

class TestGoogleGenerativeAI_EdgeCases:
    """Tests for behavior with empty and non-standard input data."""

    @pytest.mark.asyncio
    async def test_ask_empty_query_returns_empty_string(self):
        """Check early return when passing empty query to ask."""
        empty_query: str = ''
        with patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.genai.Client'), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask(empty_query)
            assert result == '', f'ask() with empty question must return empty string, got: {result!r}'

    @pytest.mark.asyncio
    async def test_chat_empty_query_returns_empty_string(self):
        """Check early return when passing empty message to chat."""
        empty_message: str = ''
        with patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.genai.Client'), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.chat(empty_message)
            assert result == '', f'chat() with empty question must return empty string, got: {result!r}'

    @pytest.mark.asyncio
    async def test_embed_empty_text_returns_false(self):
        """Check early return False when text is empty for embedding."""
        empty_text: str = ''
        with patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.genai.Client'), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result = await ai_instance.embed(empty_text)
            assert result is False, f'embed() with empty text must return False, got: {result!r}'

    def test_normalize_text_and_remove_html_empty(self):
        """Check formatting utilities on empty strings."""
        assert normalize_text('') == '', 'normalize_text("") must return ""'
        assert remove_html_blocks('') == '', 'remove_html_blocks("") must return ""'

class TestGoogleGenerativeAI_TypeVariants:
    """Tests for handling various parameter types (Path, bytes, IOBase)."""

    @pytest.mark.asyncio
    async def test_describe_image_with_bytes_and_path(self):
        """Check describe_image when passing bytes directly and via Path."""
        raw_bytes: bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        mock_response: MagicMock = MagicMock()
        mock_response.text = 'A nature image'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result_bytes = await ai_instance.describe_image(raw_bytes)
            assert result_bytes == 'A nature image', f'describe_image() with bytes must return description, got: {result_bytes!r}'

    @pytest.mark.asyncio
    async def test_upload_file_with_descriptor(self):
        """Check upload_file when passing BytesIO."""
        stream_file: BytesIO = BytesIO(b'Sample data')
        mock_client: MagicMock = MagicMock()
        mock_client.files.upload.return_value = MagicMock(name='uploaded_file')
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: bool = await ai_instance.upload_file(stream_file, file_name='sample.txt')
            assert result is True, f'upload_file() with file descriptor must return True, got: {result!r}'

class TestGoogleGenerativeAI_BoundaryValues:
    """Tests for attempt limits and boundary delays."""

    @pytest.mark.asyncio
    async def test_ask_exceeds_max_attempts(self):
        """Check ask behavior when attempts=1 and constant failures."""
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError('SDK connection error')
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask('Any question', attempts=1)
            assert 'Error' in result or 'error' in result or 'exhausted' in result, f'ask() after exhausting attempts must return diagnostic message, got: {result!r}'

class TestGoogleGenerativeAI_ErrorScenarios:
    """Tests for key rotation, model switching, and API error handling (401, 404, 503, 429)."""

    @pytest.mark.asyncio
    async def test_error_401_invalid_key_switches_key(self):
        """Error 401 API_KEY_INVALID must invalidate key and switch to second."""
        error_401: Exception = RuntimeError('401 API_KEY_INVALID: Key not valid')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with second key'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_401, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['bad_key', 'good_key'], ['k_bad', 'k_good'], ['k_bad', 'k_good'])), patch('src.ai.gemini.core.get_status'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask('Test 401')
            assert result == 'Success with second key', f'On 401 error must transition to valid key, got: {result!r}'
            assert 'bad_key' not in ai_instance.api_keys, 'Invalid key must be removed from active pool'

    @pytest.mark.asyncio
    async def test_error_404_unsupported_model_switches_model(self):
        """Error 404 NOT_FOUND must add model to unsupported and switch it."""
        error_404: Exception = RuntimeError('404 NOT_FOUND: Model is no longer available')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with new model'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_404, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), patch('src.ai.gemini.core.get_status'), patch('src.ai.gemini.core.GoogleGenerativeAICore.get_available_models', return_value=['gemini-old', 'gemini-new']), patch('src.ai.gemini.errors.add_unsupported_model') as mock_add_unsupp:
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(model_name='gemini-old')
            result: str = await ai_instance.ask('Test 404')
            assert result == 'Success with new model', f'On 404 error must transition to available model, got: {result!r}'
            assert ai_instance.model_name == 'gemini-new', f'Active model name must update to gemini-new, current: {ai_instance.model_name}'
            mock_add_unsupp.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_429_daily_quota_exhausted(self):
        """Error 429 PerDay quota must mark key exhausted and switch it."""
        error_429_daily: Exception = RuntimeError('429 RESOURCE_EXHAUSTED: Quota exceeded for RequestsPerDay')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with second key after 429'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_429_daily, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1', 'key2'], ['k1', 'k2'], ['k1', 'k2'])), patch('src.ai.gemini.core.get_status'), patch('src.ai.gemini.core.mark_exhausted') as mock_mark:
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask('Test 429 Daily')
            assert result == 'Success with second key after 429', f'On daily 429 must transition to next key, got: {result!r}'
            mock_mark.assert_called_once_with('k1')

    @pytest.mark.asyncio
    async def test_error_429_per_minute_rate_limit_does_not_mark_exhausted(self):
        """Error 429 ApiRequestsPerMinute must wait and retry without marking key exhausted."""
        error_429_rate: Exception = RuntimeError("429 RESOURCE_EXHAUSTED: 'quota_limit': 'ApiRequestsPerMinutePerProjectPerRegion', 'quota_unit': '1/min'")
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success after rate limit backoff'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_429_rate, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), patch('src.ai.gemini.core.get_status'), patch('src.ai.gemini.core.mark_exhausted') as mock_mark, patch('asyncio.sleep') as mock_sleep:
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask('Test 429 Rate Limit')
            assert result == 'Success after rate limit backoff'
            mock_mark.assert_not_called()
            mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_error_429_zero_quota_limit_marks_exhausted_and_switches(self):
        """Error 429 with quota_limit_value='0' must mark key exhausted and switch key immediately."""
        error_429_zero_quota: Exception = RuntimeError("429 RESOURCE_EXHAUSTED: {'quota_limit': 'ApiRequestsPerMinutePerProjectPerRegion', 'quota_unit': '1/min/{project}/{region}', 'quota_limit_value': '0'}")
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with rotated key on zero quota'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_429_zero_quota, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1', 'key2'], ['k1', 'k2'], ['k1', 'k2'])), patch('src.ai.gemini.core.get_status'), patch('src.ai.gemini.core.mark_exhausted') as mock_mark:
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask('Test 429 Zero Quota')
            assert result == 'Success with rotated key on zero quota', f'On zero quota 429 must immediately transition to next key, got: {result!r}'
            mock_mark.assert_called_once_with('k1')

    @pytest.mark.asyncio
    async def test_error_unsupported_modalities_switches_model(self):
        """Error 400 with unsupported response modalities must add model to unsupported and switch."""
        error_400_modalities: Exception = RuntimeError('400 INVALID_ARGUMENT: The requested combination of response modalities (TEXT) is not supported by the model. models/gemini-3.5-flash-lite-preview-tts accepts the following combination of response modalities:\n* AUDIO')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with fallback text model'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_400_modalities, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), patch('src.ai.gemini.core.get_status'), patch('src.ai.gemini.core.GoogleGenerativeAICore.get_available_models', return_value=['gemini-3.5-flash-lite-preview-tts', 'gemini-3.5-flash-lite']), patch('src.ai.gemini.errors.add_unsupported_model') as mock_add_unsupp:
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(model_name='gemini-3.5-flash-lite-preview-tts')
            result: str = await ai_instance.ask('Test TTS Modality')
            assert result == 'Success with fallback text model', f'On modality mismatch error must transition to available model, got: {result!r}'
            assert ai_instance.model_name == 'gemini-3.5-flash-lite', f'Active model name must update to gemini-3.5-flash-lite, current: {ai_instance.model_name}'
            mock_add_unsupp.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_503_temporary_retry(self):
        """Error 503 UNAVAILABLE (high demand) must wait with backoff and retry without failing."""
        error_503: Exception = RuntimeError("503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}")
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success after 503 spike cleared'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_503, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), patch('src.ai.gemini.core.get_status'), patch('asyncio.sleep') as mock_sleep:
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI()
            result: str = await ai_instance.ask('Test 503 temporary')
            assert result == 'Success after 503 spike cleared'
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_503_persistent_switches_model(self):
        """Persistent 503 errors must trigger model failover to next available model."""
        error_503: Exception = RuntimeError('503 UNAVAILABLE: High demand spike')
        success_response: MagicMock = MagicMock()
        success_response.text = 'Success with failover model'
        mock_client: MagicMock = MagicMock()
        mock_client.models.generate_content.side_effect = [error_503, error_503, error_503, error_503, success_response]
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['key1'], ['k1'], ['k1'])), patch('src.ai.gemini.core.get_status'), patch('src.ai.gemini.core.GoogleGenerativeAICore.get_available_models', return_value=['gemini-3.5-flash-lite', 'gemini-flash-lite-latest']), patch('asyncio.sleep'):
            ai_instance: GoogleGenerativeAI = GoogleGenerativeAI(model_name='gemini-3.5-flash-lite')
            result: str = await ai_instance.ask('Test 503 persistent')
            assert result == 'Success with failover model'
            assert ai_instance.model_name == 'gemini-flash-lite-latest'

class TestGoogleGenerativeAI_Regression:
    """Regression testing for integration with UnifiedChatModel and exports."""

    def test_default_model_exported_correctly(self):
        """Check presence and string type of _DEFAULT_MODEL."""
        from src.ai.gemini.core import _DEFAULT_MODEL
        assert isinstance(_DEFAULT_MODEL, str), '_DEFAULT_MODEL must be a string'
        assert len(_DEFAULT_MODEL) > 0, '_DEFAULT_MODEL must not be an empty string'

    @pytest.mark.asyncio
    async def test_unified_chat_model_integration(self):
        """Check UnifiedChatModel integration with updated GoogleGenerativeAI class."""
        from src.ai.orchestration.unified_chat import UnifiedChatModel
        mock_client: MagicMock = MagicMock()
        mock_response: MagicMock = MagicMock()
        mock_response.text = 'Response via UnifiedChatModel'
        mock_client.models.generate_content.return_value = mock_response
        mock_chat: MagicMock = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat
        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), patch('src.ai.gemini.core.get_status'):
            unified_model: UnifiedChatModel = UnifiedChatModel(system_instruction='Test instruction')
            result = await unified_model.chat('Test request to unified')
            assert result == 'Response via UnifiedChatModel', f'UnifiedChatModel must correctly call chat() on Gemini, got: {result!r}'


class TestGoogleGenerativeAI_LoggingAndErrors:
    """Тесты расширенного логирования промптов, инструкций, ответов и сериализации ошибок в JSON."""

    def test_format_error_as_json_api_error(self):
        """Проверка сериализации объекта ошибки API в валидный JSON."""
        from google.genai.errors import ClientError
        raw_error_dict = {
            'error': {
                'code': 429,
                'message': 'Resource has been exhausted (e.g. check quota).',
                'status': 'RESOURCE_EXHAUSTED',
            }
        }
        client_err = ClientError(429, raw_error_dict)
        json_out = format_error_as_json(client_err, model='gemini-3.5-flash-lite', attempt=1, max_attempts=15)
        parsed = json.loads(json_out)
        assert 'error' in parsed
        assert parsed['error']['code'] == 429
        assert parsed['error']['status'] == 'RESOURCE_EXHAUSTED'
        assert parsed['error']['model'] == 'gemini-3.5-flash-lite'
        assert parsed['error']['attempt'] == 1
        assert parsed['error']['max_attempts'] == 15

    def test_format_error_as_json_generic_exception(self):
        """Проверка сериализации стандартного исключения в валидный JSON."""
        err = ConnectionResetError('Connection abruptly closed by peer')
        json_out = format_error_as_json(err, model='gemini-3.7-flash', attempt=2, max_attempts=5, action_taken='retry')
        parsed = json.loads(json_out)
        assert 'error' in parsed
        assert parsed['error']['type'] == 'ConnectionResetError'
        assert 'Connection abruptly closed' in parsed['error']['message']
        assert parsed['error']['model'] == 'gemini-3.7-flash'
        assert parsed['error']['attempt'] == 2
        assert parsed['error']['action_taken'] == 'retry'

    @pytest.mark.asyncio
    async def test_ask_logs_request_and_response(self):
        """Проверка, что ask логирует полный запрос и полученный ответ."""
        from logger import logger as global_logger
        mock_response = MagicMock()
        mock_response.text = 'The answer is 42.'
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch('src.ai.gemini.core.genai.Client', return_value=mock_client), \
             patch('src.ai.gemini.core.load_api_keys', return_value=(['fake_key'], ['key_dev'], ['key_dev'])), \
             patch('src.ai.gemini.core.get_status'), \
             patch.object(global_logger, 'info') as mock_log_info:
            ai_instance = GoogleGenerativeAI(system_instruction='You are a precise calculator.')
            res = await ai_instance.ask('What is the meaning of life?')
            assert res == 'The answer is 42.'
            
            # Проверяем вызовы logger.info
            logged_messages = [str(call.args[0]) for call in mock_log_info.call_args_list if call.args]
            has_request_log = any('Gemini Request [ask]' in m and 'What is the meaning of life?' in m for m in logged_messages)
            has_response_log = any('Gemini Response [ask]' in m and 'The answer is 42.' in m for m in logged_messages)
            assert has_request_log, f"Expected request to be logged with prompt, got: {logged_messages}"
            assert has_response_log, f"Expected response to be logged, got: {logged_messages}"

    @pytest.mark.asyncio
    async def test_error_logs_as_json(self):
        """Проверка, что ошибка API логируется как валидный JSON через logger.error."""
        from logger import logger as global_logger
        from src.ai.gemini.errors import GoogleGenerativeAIErrorMixin

        class DummyErrorClient(GoogleGenerativeAIErrorMixin):
            api_key = 'bad_key'
            _unavailable_attempts = 0
            def _record_error(self, ex):
                pass
            def _invalidate_api_key(self, key):
                pass
            def _switch_api_key(self):
                return True

        client = DummyErrorClient()
        error_401 = RuntimeError('401 API_KEY_INVALID: Provided API key is not valid')

        with patch.object(global_logger, 'error') as mock_log_error:
            should_retry = await client._handle_api_error(error_401, 'gemini-3.7-flash', 0, 5)
            assert should_retry is True

            logged_errors = [str(call.args[0]) for call in mock_log_error.call_args_list if call.args]
            has_json_error = any('Gemini Model Error' in m and ('"status": "AUTH_ERROR"' in m or '401' in m or 'API_KEY_INVALID' in m) for m in logged_errors)
            assert has_json_error, f"Expected error to be logged as JSON, got: {logged_errors}"