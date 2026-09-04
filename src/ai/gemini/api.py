# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI API Methods
# =============================================================================
# Description:
#   Implementation of API methods for Google Generative AI.
#   Provides ask, chat, chat_stream, ask_with_tools, ask_with_tools_stream methods.
#   Handles retries, quota exhaustion, model switching, and streaming responses.
#
# File: api.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
from typing import Any, AsyncGenerator

from google.genai import types

from src.logger.logger import logger
from src.secrets.api_key_state import update_last_run
from src.utils.jjson import j_loads

from .core import GoogleGenerativeAICore
from .errors import GoogleGenerativeAIErrorMixin
from .history import GoogleGenerativeAIHistoryMixin
from .config import GoogleGenerativeAIConfigMixin


class GoogleGenerativeAI(
    GoogleGenerativeAICore,
    GoogleGenerativeAIErrorMixin,
    GoogleGenerativeAIHistoryMixin,
    GoogleGenerativeAIConfigMixin,
):
    """Class for interaction with Google Generative AI (Gemini) models.

    Attributes:
        api_key (str): Active API key for requests.
        model_name (str): Name of the Gemini model being used.
        generation_config (dict): Generation parameters by default.
        system_instruction (str): Base system instruction.
        api_key_names (list[str]): List of allowed key names.
        save_history_chat (bool): Flag for saving chat history context.
        sleep_on_exhausted (bool): Flag for waiting on quota exhaustion.
    """

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        generation_config: dict = {},
    ) -> str:
        """Send single text request to model.

        Args:
            q (str): Query text.
            attempts (int): Maximum number of attempts. Default: 15.
            generation_config (dict): Additional generation parameters.

        Returns:
            str: Model response or error message.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> ans = await ai.ask("What is the capital of France?")
        """
        if not q:
            return ''

        self._key_errors = {}
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                return self._get_exhausted_error_msg()
            self._all_keys_exhausted = False

        for attempt in range(attempts):
            try:
                config = self._build_content_config(generation_config=generation_config)
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=q,
                    config=config,
                )
                if response and response.text:
                    response_text: str = self._normalize_text(response.text)
                    response_text = self._remove_html_blocks(response_text)
                    update_last_run(self._key_names_active[0] if self._key_names_active else '')
                    self._unavailable_attempts = 0
                    return response_text

                logger.debug(f'GoogleGenerativeAI: Empty model response on attempt {attempt + 1}')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return f'Model error: {self._last_exception or str(ex)}'

        return self._get_exhausted_error_msg()

    async def chat(
        self,
        q: str,
        history: list[dict] = (),
        flag: str = 'save_chat',
        system_instruction: str = '',
        attempts: int = 15,
        model_name: str = '',
        **kwargs,
    ) -> str:
        """Process message in chat dialog context.

        Args:
            q (str): User message.
            history (list[dict]): External message history for context restoration.
            flag (str): History management flag ('save_chat', 'clear', 'start_new').
            system_instruction (str): Override system instruction.
            attempts (int): Maximum number of retry attempts.
            model_name (str): Explicit model override for request.
            **kwargs: Additional unused parameters.

        Returns:
            str: Model response or diagnostic error message.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> ans = await ai.chat("Hello!", flag="start_new")
        """
        if not q:
            return ''

        self._key_errors = {}
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                return self._get_exhausted_error_msg()
            self._all_keys_exhausted = False

        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name

        for attempt in range(attempts):
            try:
                # 1. Stateless mode (no history saving)
                if not self.save_history_chat:
                    config = self._build_content_config(instruction)
                    response = self._client.models.generate_content(
                        model=active_model,
                        contents=q,
                        config=config,
                    )
                    if response and response.text:
                        response_text: str = self._normalize_text(response.text)
                        response_text = self._remove_html_blocks(response_text)
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return response_text

                    await asyncio.sleep(2 ** min(attempt, 4))
                    continue

                # 2. Chat mode with history preservation
                if history:
                    self.chat_history = list(history)
                    self._restore_chat_from_history()
                elif flag in ['clear', 'start_new']:
                    self.chat_history = []
                    self._chat = self._start_chat()

                response = self._chat.send_message(q)
                if response and response.text:
                    response_text = self._normalize_text(response.text)
                    response_text = self._remove_html_blocks(response_text)
                    self.chat_history.append({'role': 'user', 'parts': [q]})
                    self.chat_history.append({'role': 'model', 'parts': [response_text]})
                    self._unavailable_attempts = 0
                    return response_text

                logger.error('GoogleGenerativeAI: Empty model response in chat')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, attempt, attempts)
                if not should_retry:
                    return f'Chat error: {self._last_exception or str(ex)}'

        return self._get_exhausted_error_msg()

    async def chat_stream(
        self,
        q: str,
        history: list[dict] = (),
        flag: str = 'save_chat',
        system_instruction: str = '',
        attempts: int = 15,
        model_name: str = '',
        generation_config: dict = {},
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream-generate model response as async generator.

        Args:
            q (str): User question.
            history (list[dict]): Message history.
            flag (str): History management flag.
            system_instruction (str): System instruction.
            attempts (int): Maximum retry attempts.
            model_name (str): Model override.
            generation_config (dict): Generation settings.

        Yields:
            str: Next generated text fragment (chunk).
        """
        if not q:
            return

        self._key_errors = {}
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                yield self._get_exhausted_error_msg()
                return
            self._all_keys_exhausted = False

        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name

        for attempt in range(attempts):
            try:
                if not self.save_history_chat:
                    config = self._build_content_config(instruction, generation_config=generation_config)
                    contents = self._prepare_contents(q, history)

                    def _collect_stateless(_client=self._client, _m=active_model, _c=contents, _cfg=config):
                        res: list[str] = []
                        for chunk in _client.models.generate_content_stream(model=_m, contents=_c, config=_cfg):
                            if chunk.text:
                                res.append(chunk.text)
                        return res

                    chunks = await asyncio.to_thread(_collect_stateless)
                    if chunks:
                        for chunk_text in chunks:
                            yield chunk_text
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return

                    await asyncio.sleep(2 ** min(attempt, 4))
                    continue

                if history:
                    self.chat_history = list(history)
                    self._restore_chat_from_history()
                elif flag in ['clear', 'start_new']:
                    self.chat_history = []
                    self._chat = self._start_chat()

                _chat_ref = self._chat

                def _collect_chat(_chat=_chat_ref, _query=q):
                    res: list[str] = []
                    for chunk in _chat.send_message_stream(_query):
                        if chunk.text:
                            res.append(chunk.text)
                    return res

                chunks = await asyncio.to_thread(_collect_chat)
                full_text: str = ''.join(chunks)
                if full_text:
                    for chunk_text in chunks:
                        yield chunk_text
                    normalized: str = self._remove_html_blocks(self._normalize_text(full_text))
                    self.chat_history.append({'role': 'user', 'parts': [q]})
                    self.chat_history.append({'role': 'model', 'parts': [normalized]})
                    self._unavailable_attempts = 0
                    return

                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, attempt, attempts)
                if not should_retry:
                    yield f'Streaming error: {self._last_exception or str(ex)}'
                    return

    async def ask_with_tools(
        self,
        q: str,
        tools: list,
        tool_dispatcher: Any,
        system_instruction: str = '',
        model_name: str = '',
    ) -> str:
        """Execute request with external function calling support (Agentic loop).

        Args:
            q (str): User text query.
            tools (list): List of tool definitions types.Tool.
            tool_dispatcher (Any): Function call dispatcher (name, args) -> str.
            system_instruction (str): System instruction.
            model_name (str): Model name to use.

        Returns:
            str: Final model text response.

        Examples:
            >>> ans = await ai.ask_with_tools("Weather in Paris", tools, dispatcher)
        """
        if not q:
            return ''

        contents: list[types.Content] = [types.Content(role='user', parts=[types.Part.from_text(text=q)])]
        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name
        config = self._build_content_config(instruction, tools)

        for _ in range(10):
            response = self._client.models.generate_content(
                model=active_model,
                contents=contents,
                config=config,
            )
            candidate = response.candidates[0] if response and response.candidates else False
            if not candidate:
                break

            tool_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p.text for p in candidate.content.parts if p.text]

            if not tool_calls:
                return '\n'.join(text_parts)

            contents.append(candidate.content)
            tool_results: list[types.Part] = []
            for part in tool_calls:
                fc = part.function_call
                result = tool_dispatcher(fc.name, dict(fc.args))
                tool_results.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={'result': result},
                    )
                )
            contents.append(types.Content(role='tool', parts=tool_results))

        return ''

    async def ask_with_tools_stream(
        self,
        q: str,
        tools: list,
        tool_dispatcher: Any,
        system_instruction: str = '',
        model_name: str = '',
        history: list[dict] = (),
    ) -> AsyncGenerator[dict[str, str], None]:
        """Execute request with function calling and stream final response.

        Args:
            q (str): User request.
            tools (list): List of tools.
            tool_dispatcher (Any): Function call dispatcher.
            system_instruction (str): System instruction.
            model_name (str): Model name.
            history (list[dict]): Message history.

        Yields:
            dict[str, str]: Events like {"text": "chunk"} or {"status": "message"}.
        """
        if not q:
            return

        contents: list[types.Content] = self._prepare_contents(q, history)
        instruction: str = system_instruction or self.system_instruction or ''
        active_model: str = model_name or self.model_name
        config = self._build_content_config(instruction, tools)

        for _ in range(10):
            try:
                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=active_model,
                    contents=contents,
                    config=config,
                )
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, 0, 3)
                if should_retry:
                    active_model = self.model_name
                    continue
                yield {'status': f'Error generate_content: {str(ex)}'}
                return

            candidate = response.candidates[0] if response and response.candidates else False
            if not candidate:
                break

            tool_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p.text for p in candidate.content.parts if p.text]

            if not tool_calls:
                try:
                    response_stream = self._client.models.generate_content_stream(
                        model=active_model,
                        contents=contents,
                        config=config,
                    )
                    for chunk in response_stream:
                        if chunk.text:
                            yield {'text': chunk.text}
                except Exception as ex:
                    logger.error(f'GoogleGenerativeAI: Error streaming ask_with_tools_stream: {ex}')
                    if text_parts:
                        yield {'text': ''.join(text_parts)}
                return

            contents.append(candidate.content)
            tool_results: list[types.Part] = []
            for part in tool_calls:
                fc = part.function_call
                args_json: str = json.dumps(dict(fc.args), ensure_ascii=False)
                yield {'status': f'Function call {fc.name}({args_json})'}
                result = tool_dispatcher(fc.name, dict(fc.args))
                tool_results.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={'result': result},
                    )
                )
            contents.append(types.Content(role='tool', parts=tool_results))
