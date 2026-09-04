# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Error Handling
# =============================================================================
# Description:
#   Centralized error handling and retry logic for Google Generative AI API.
#   Handles API key rotation, model switching, and exponential backoff.
#
# File: errors.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import re
import time

import requests

from src.logger.logger import logger

from .core import add_unsupported_model


class GoogleGenerativeAIErrorMixin:
    """Mixin class for centralized error handling in GoogleGenerativeAI.

    Provides methods for handling API errors, switching API keys, and model rotation.
    """

    async def _handle_api_error(
        self,
        ex: Exception,
        active_model: str,
        attempt: int,
        max_attempts: int,
    ) -> bool:
        """Centralized handling of API exceptions and retry coordination.

        Args:
            ex (Exception): Raised exception.
            active_model (str): Name of model being used.
            attempt (int): Current attempt number.
            max_attempts (int): Maximum number of attempts.

        Returns:
            bool: True if retry needed, False if error is unrecoverable.
        """
        self._record_error(ex)
        ex_str: str = str(ex)
        logger.error(f'GoogleGenerativeAI: API Error (attempt {attempt + 1}/{max_attempts}): {ex_str}')

        # 1. Authorization error (invalid API key)
        if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
            self._invalidate_api_key(self.api_key)
            return self._switch_api_key()

        # 2. Model not found / outdated (404)
        if any(
            k in ex_str
            for k in [
                '404',
                'NOT_FOUND',
                'is no longer available',
                'not found for API version',
                'not supported for generateContent',
            ]
        ):
            add_unsupported_model(active_model, reason=ex_str)
            return self._switch_model()

        # 3. Service temporarily unavailable (503 UNAVAILABLE)
        if '503' in ex_str or 'UNAVAILABLE' in ex_str:
            self._unavailable_attempts += 1
            if self._unavailable_attempts < 6:
                wait: int = 2 ** min(self._unavailable_attempts, 5)
                logger.info(f'GoogleGenerativeAI: 503 UNAVAILABLE. Waiting {wait}s...')
                await asyncio.sleep(wait)
                return True
            else:
                switched: bool = self._switch_model_down()
                self._unavailable_attempts = 0
                return switched

        # 4. Request quota exceeded (429 RESOURCE_EXHAUSTED)
        if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
            is_daily: bool = any(
                k in ex_str.lower()
                for k in ['perday', 'per_day', 'exceeded your current quota', "quota_limit_value': '0'"]
            )
            if is_daily:
                self._mark_key_exhausted(self.api_key)
                if self._switch_api_key():
                    return True
                return self._switch_model()

            m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
            base_wait: int = int(float(m.group(1))) + 2 if m else 5
            wait_time: int = min(base_wait * (2 ** min(attempt, 3)), 60)
            logger.info(f'GoogleGenerativeAI: 429 Rate Limit. Waiting {wait_time}s before retry...')
            await asyncio.sleep(wait_time)
            return True

        # 5. Network request errors
        if isinstance(ex, requests.exceptions.RequestException):
            if attempt < 5:
                logger.warning('GoogleGenerativeAI: Network Error. Waiting 10s...')
                await asyncio.sleep(10)
                return True
            return False

        # 6. General unexpected errors
        if attempt < max_attempts - 1:
            await asyncio.sleep(2 ** min(attempt, 4))
            return True

        return False
