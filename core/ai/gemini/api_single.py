# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI API Methods - Single Request
# =============================================================================
# Description:
#   Implementation of single request API methods for Google Generative AI.
#   Provides ask method for single text query with retry logic and
#   quota exhaustion handling.
#
# File: api_single.py
# Project: ai-breadboard
# Package: core.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio

from core.logger.logger import logger
from core.secrets.api_key_state import update_last_run

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
    """Class for single request API methods."""

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
