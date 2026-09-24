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

from typing import Any, Optional

import asyncio
import re
import time

import requests

from logger.logger import logger
from src.ai.orchestration.model_pool_state import mark_model_exhausted, switch_model

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

        # 1. Authorization error (invalid API key)
        if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
            logger.warning(f'GoogleGenerativeAI: Authorization error (API key invalid/expired). Rotating key...', exc_info=False)
            self._invalidate_api_key(self.api_key)
            return self._switch_api_key()

        # 2. Model not found / outdated / incompatible modalities (404 / 400 with modality mismatch)
        if any(
            k in ex_str
            for k in [
                '404',
                'NOT_FOUND',
                'is no longer available',
                'not found for API version',
                'not supported for generateContent',
                'response modalities',
                'response_modalities',
                'not supported by the model',
            ]
        ):
            logger.warning(f'GoogleGenerativeAI: Model {active_model} is unsupported or deprecated ({ex_str}). Switching model...', exc_info=False)
            add_unsupported_model(active_model, reason=ex_str)
            return self._switch_model()

        # 3. Service temporarily unavailable (503 UNAVAILABLE / High demand / Spike)
        if '503' in ex_str or 'UNAVAILABLE' in ex_str or 'high demand' in ex_str.lower():
            mark_model_exhausted('gemini', active_model)
            self._unavailable_attempts += 1
            if self._unavailable_attempts <= 3:
                wait: int = 2 ** min(self._unavailable_attempts, 5)
                logger.warning(
                    f'GoogleGenerativeAI: 503 UNAVAILABLE ({active_model}). '
                    f'High demand / service load (attempt {attempt + 1}/{max_attempts}). '
                    f'Waiting {wait}s...',
                    exc_info=False,
                )
                await asyncio.sleep(wait)
                return True
            else:
                logger.warning(
                    f'GoogleGenerativeAI: Model {active_model} is experiencing persistent high demand after '
                    f'{self._unavailable_attempts} attempts. Switching to alternative model...',
                    exc_info=False,
                )
                if self._switch_model():
                    self._unavailable_attempts = 0
                    return True
                else:
                    logger.error(
                        'GoogleGenerativeAI: No alternative models available for gemini provider',
                        exc_info=False,
                    )
                    self._unavailable_attempts = 0
                    return False

        # 4. Превышение квоты запросов (429 RESOURCE_EXHAUSTED)
        if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
            # Проверка на нулевой лимит квоты (квота не выделена, 0 в регионе или заблокирована)
            is_zero_quota: bool = (
                "quota_limit_value': '0'" in ex_str
                or 'quota_limit_value": "0"' in ex_str
                or "'quota_limit_value': 0" in ex_str
                or '"quota_limit_value": 0' in ex_str
            )

            is_per_minute: bool = not is_zero_quota and any(
                k in ex_str.lower()
                for k in [
                    '1/min',
                    'perminute',
                    'per_minute',
                    'requestsperminute',
                    'apirequestsperminute',
                    'rate_limit_exceeded',
                ]
            )
            is_daily: bool = not is_per_minute and any(
                k in ex_str.lower()
                for k in ['perday', 'per_day', 'requestsperday', 'daily_quota']
            )

            if is_zero_quota or is_daily:
                logger.warning(
                    'GoogleGenerativeAI: Исчерпана суточная квота или лимит равен 0 для ключа. Ротация ключа...',
                    exc_info=False,
                )
                self._mark_key_exhausted(self.api_key)
                if self._switch_api_key():
                    return True
                return self._switch_model()

            # Если 429 повторяется более 2 раз подряд, эскалируем на ротацию ключа/модели
            if attempt >= 2:
                logger.warning(
                    f'GoogleGenerativeAI: Повторяющийся лимит 429 (попытка {attempt + 1}). '
                    'Выполняется ротация ключа или переключение модели...',
                    exc_info=False,
                )
                if self._switch_api_key():
                    return True
                return self._switch_model()

            m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
            base_wait: int = int(float(m.group(1))) + 2 if m else 5
            wait_time: int = min(base_wait * (2 ** min(attempt, 3)), 60)
            logger.info(f'GoogleGenerativeAI: 429 Rate Limit (Per-Minute/Burst). Ожидание {wait_time}s перед повтором...')
            await asyncio.sleep(wait_time)
            return True

        # 5. Network request errors
        if isinstance(ex, requests.exceptions.RequestException):
            if attempt < 5:
                logger.warning('GoogleGenerativeAI: Network Error. Waiting 10s...', exc_info=False)
                await asyncio.sleep(10)
                return True
            return False

        # 6. General unexpected errors
        if attempt < max_attempts - 1:
            logger.warning(
                f'GoogleGenerativeAI: API Error on attempt {attempt + 1}/{max_attempts}: {ex_str}. Retrying...',
                exc_info=False,
            )
            await asyncio.sleep(2 ** min(attempt, 4))
            return True

        logger.error(f'GoogleGenerativeAI: API Error (exhausted {max_attempts} attempts): {ex_str}')
        return False
