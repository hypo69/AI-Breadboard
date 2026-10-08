# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Api Single Module
# =============================================================================
# Description:
#   Класс для выполнения одиночных запросов к API Gemini (ask).
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.api_single import GoogleGenerativeAISingleRequest
#
#     service = GoogleGenerativeAISingleRequest()
#
# File: api_single.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 10:47:35
# =============================================================================

"""Класс для выполнения одиночных запросов к API Gemini (ask)."""

import asyncio
import json
from logger import logger
from src.ai.gemini.gemini_api_key_state import update_last_run
from .core import GoogleGenerativeAICore
from .errors import GoogleGenerativeAIErrorMixin
from .history import GoogleGenerativeAIHistoryMixin
from .config import GoogleGenerativeAIConfigMixin


class GoogleGenerativeAISingleRequest(
    GoogleGenerativeAICore,
    GoogleGenerativeAIErrorMixin,
    GoogleGenerativeAIHistoryMixin,
    GoogleGenerativeAIConfigMixin,
):
    """Класс для выполнения одиночных запросов к API Gemini (ask)."""

    async def ask(self, q: str, attempts: int=15, generation_config: dict={}) -> str:
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
        self._log_request_details(method='ask', model=self.model_name, q=q, generation_config=generation_config)
        for attempt in range(attempts):
            try:
                config = self._build_content_config(generation_config=generation_config)
                response = self._client.models.generate_content(model=self.model_name, contents=q, config=config)
                if response and response.text:
                    response_text: str = self._normalize_text(response.text)
                    response_text = self._remove_html_blocks(response_text)
                    self._log_response_details(method='ask', model=self.model_name, response_text=response_text, attempt=attempt + 1)
                    update_last_run(self._key_names_active[0] if self._key_names_active else '')
                    self._unavailable_attempts = 0
                    return response_text
                err_empty = {
                    'error': {
                        'code': 204,
                        'status': 'EMPTY_RESPONSE',
                        'message': f'Empty model response on attempt {attempt + 1}',
                        'model': self.model_name,
                        'attempt': attempt + 1,
                    }
                }
                logger.warning(f'GoogleGenerativeAISingleRequest: Empty model response:\n{json.dumps(err_empty, ensure_ascii=False, indent=2)}')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return f'Model error: {self._last_exception or str(ex)}'
        return self._get_exhausted_error_msg()