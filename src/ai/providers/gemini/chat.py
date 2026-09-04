# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Gemini Provider Adapter
# =============================================================================
# Description:
#   Wraps GoogleGenerativeAI into the unified BaseChatProvider interface.
#
# File: chat.py
# Package: src.ai.providers.gemini
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from typing import Any, AsyncIterator, Dict, List, Optional, Set
from src.ai.providers.base import BaseChatProvider
from src.ai.gemini.api import GoogleGenerativeAI
from src.ai.gemini.generative_ai import _DEFAULT_MODEL
from src.logger import logger


class GeminiChatBase(BaseChatProvider):
    """Provider adapter for Google Gemini Generative AI models."""

    def __init__(
        self,
        api_key_names: Optional[List[str]] = None,
        system_instruction: str = "",
        model_name: str = _DEFAULT_MODEL,
        **kwargs: Any,
    ):
        """Initialize Google Gemini chat provider."""
        self.model = GoogleGenerativeAI(
            api_key_names=api_key_names or ["GEMINI_API_KEY_1"],
            system_instruction=system_instruction,
            sleep_on_exhausted=False,
            **kwargs,
        )
        self._model_name = model_name

    @classmethod
    def get_capabilities(cls) -> Set[str]:
        """Return capabilities supported by Gemini."""
        return {"chat", "vision", "code", "embedding", "image_generation"}

    @classmethod
    def is_available(cls) -> bool:
        """Check if Gemini API keys are configured."""
        import os
        return bool(os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY"))

    @property
    def system_instruction(self) -> str:
        """Get system instruction."""
        return getattr(self.model, "system_instruction", "")

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Set system instruction."""
        self.model.system_instruction = val

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> Optional[str]:
        """Send prompt to Gemini model."""
        return await self.model.ask(
            q=q,
            attempts=attempts,
            model_name=self._model_name,
            **kwargs,
        )

    async def stream_chat(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response chunks from Gemini."""
        async for chunk in self.model.chat_stream(q=q, history=history or [], **kwargs):
            yield chunk

    async def close(self) -> None:
        """Close client sessions."""
        pass
