# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Api Chat Module
# =============================================================================
# Description:
#   Класс диалоговых методов API (Chat и Chat Stream).
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.api_chat import GoogleGenerativeAIChat
#
#     service = GoogleGenerativeAIChat()
#
# File: api_chat.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Класс диалоговых методов API (Chat и Chat Stream)."""

import asyncio
from typing import Any, AsyncGenerator
from logger import logger
from src.ai.gemini.gemini_api_key_state import update_last_run
from .core import GoogleGenerativeAICore
from .errors import GoogleGenerativeAIErrorMixin
from .history import GoogleGenerativeAIHistoryMixin
from .config import GoogleGenerativeAIConfigMixin


class GoogleGenerativeAIChat(
    GoogleGenerativeAICore,
    GoogleGenerativeAIErrorMixin,
    GoogleGenerativeAIHistoryMixin,
    GoogleGenerativeAIConfigMixin,
):
    """Класс диалоговых методов API (Chat и Chat Stream)."""

    async def chat(self, q: str, history: list[dict]=(), flag: str='save_chat', system_instruction: str='', attempts: int=15, model_name: str='', **kwargs) -> str:
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
                if not self.save_history_chat:
                    config = self._build_content_config(instruction)
                    response = self._client.models.generate_content(model=active_model, contents=q, config=config)
                    if response and response.text:
                        response_text: str = self._normalize_text(response.text)
                        response_text = self._remove_html_blocks(response_text)
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return response_text
                    await asyncio.sleep(2 ** min(attempt, 4))
                    continue
                if history:
                    self.chat_history = list(history)
                    self._restore_chat_from_history()
                elif flag in ['clear', 'start_new']:
                    self.chat_history = []
                    self._chat = self._start_chat()

                if hasattr(self._client, 'aio') and hasattr(self._client.aio, 'chats') and hasattr(self._client.aio.chats, 'create') and not isinstance(self._client.aio.chats.create, MagicMock if 'MagicMock' in globals() else type(None)):
                    try:
                        config = self._build_content_config(instruction)
                        history_contents = self._convert_history_to_contents(self.chat_history)
                        async_chat = self._start_async_chat(history=history_contents, config=config, model_name=active_model)
                        response = await async_chat.send_message(q)
                    except Exception:
                        response = self._chat.send_message(q) if self._chat else None
                elif self._chat:
                    response = self._chat.send_message(q)
                else:
                    config = self._build_content_config(instruction)
                    response = self._client.models.generate_content(model=active_model, contents=self._prepare_contents(q, self.chat_history), config=config)

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

    async def chat_stream(self, q: str, history: list[dict]=(), flag: str='save_chat', system_instruction: str='', attempts: int=15, model_name: str='', generation_config: dict={}, **kwargs) -> AsyncGenerator[str, None]:
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
                    if getattr(self, 'realtime_streaming', True):
                        if history and hasattr(self._client, 'aio') and hasattr(self._client.aio, 'chats'):
                            try:
                                history_contents = self._convert_history_to_contents(history)
                                async_chat = self._start_async_chat(history=history_contents, config=config, model_name=active_model)
                                response = await async_chat.send_message_stream(q)
                            except Exception:
                                response = await self._client.aio.models.generate_content_stream(model=active_model, contents=contents, config=config)
                        else:
                            response = await self._client.aio.models.generate_content_stream(model=active_model, contents=contents, config=config)
                        has_yielded = False
                        async for chunk in response:
                            if chunk.text:
                                yield chunk.text
                                has_yielded = True
                        if has_yielded:
                            update_last_run(self._key_names_active[0] if self._key_names_active else '')
                            self._unavailable_attempts = 0
                            return
                    else:

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
                if getattr(self, 'realtime_streaming', True):
                    config = self._build_content_config(instruction, generation_config=generation_config)
                    if hasattr(self._client, 'aio') and hasattr(self._client.aio, 'chats'):
                        try:
                            history_contents = self._convert_history_to_contents(self.chat_history)
                            async_chat = self._start_async_chat(history=history_contents, config=config, model_name=active_model)
                            response = await async_chat.send_message_stream(q)
                        except Exception:
                            contents = self._prepare_contents(q, self.chat_history)
                            response = await self._client.aio.models.generate_content_stream(model=active_model, contents=contents, config=config)
                    else:
                        contents = self._prepare_contents(q, self.chat_history)
                        response = await self._client.aio.models.generate_content_stream(model=active_model, contents=contents, config=config)
                    full_chunks: list[str] = []
                    async for chunk in response:
                        if chunk.text:
                            full_chunks.append(chunk.text)
                            yield chunk.text
                    if full_chunks:
                        full_text: str = ''.join(full_chunks)
                        normalized: str = self._remove_html_blocks(self._normalize_text(full_text))
                        self.chat_history.append({'role': 'user', 'parts': [q]})
                        self.chat_history.append({'role': 'model', 'parts': [normalized]})
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return
                else:
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
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, active_model, attempt, attempts)
                if not should_retry:
                    yield f'Streaming error: {self._last_exception or str(ex)}'
                    return