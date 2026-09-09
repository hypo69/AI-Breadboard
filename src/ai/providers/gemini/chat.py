# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Gemini Provider Adapter
# =============================================================================
# Description:
#   Wraps GoogleGenerativeAI into the unified BaseChatProvider interface.
#   Implements streaming (chat_stream), single ask, multi-turn chat,
#   model management and quota tracking for Gemini models.
#
# File: chat.py
# Package: src.ai.providers.gemini
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

"""Google Gemini provider adapter for streaming and non-streaming chat."""

import os
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Optional, Set

from src.ai.providers.base import BaseChatProvider
from src.ai.gemini.api import GoogleGenerativeAI
from src.ai.gemini.generative_ai import _DEFAULT_MODEL
from src.logger import logger


class GeminiChatBase(BaseChatProvider):
    """Provider adapter for Google Gemini Generative AI models.

    Implements unified chat interfaces (ask, chat, chat_stream) with
    API key rotation, history management, and token streaming.

    Attributes:
        model_id (str): Normalized Gemini model identifier.
        system_prompt (str): Active system instruction.
        history (List[Dict[str, Any]]): Local conversation history.
        model (GoogleGenerativeAI): Underlying client instance.
    """

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Retrieve list of available models for Gemini provider.

        Args:
            force_refresh (bool): Force cache refresh.

        Returns:
            List[str]: List of available Gemini model identifiers.
        """
        from src.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="gemini", force_refresh=force_refresh)

    @classmethod
    def normalize_model_id(cls, model_id: str) -> str:
        """Normalize model identifier for Gemini provider.

        Args:
            model_id (str): Raw model identifier.

        Returns:
            str: Normalized model identifier without provider prefix.
        """
        actual = (model_id or "").strip()
        if actual.startswith("gemini:"):
            actual = actual[7:]
        elif actual.startswith("models/"):
            actual = actual[7:]
        return actual or _DEFAULT_MODEL

    @classmethod
    def get_capabilities(cls) -> Set[str]:
        """Return capabilities supported by Gemini."""
        return {"chat", "vision", "code", "embedding", "image_generation"}

    @classmethod
    def is_available(cls) -> bool:
        """Check if Gemini API keys are configured."""
        return bool(
            os.environ.get("GEMINI_API_KEY_1")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GEMINI_API_KEY_NAMES")
        )

    def __init__(
        self,
        model_id: str = "",
        system_prompt: str = "",
        api_key_names: Optional[List[str]] = None,
        model_name: str = "",
        system_instruction: str = "",
        **kwargs: Any,
    ) -> None:
        """Initialize Google Gemini chat provider adapter.

        Args:
            model_id (str): Model identifier (e.g. 'gemini-flash-latest').
            system_prompt (str): System prompt / instruction.
            api_key_names (Optional[List[str]]): Specific API key names to use.
            model_name (str): Legacy alias for model_id.
            system_instruction (str): Legacy alias for system_prompt.
            **kwargs: Additional parameters for GoogleGenerativeAI.
        """
        raw_id = model_id or model_name or _DEFAULT_MODEL
        self._model_id: str = self.normalize_model_id(raw_id)
        self._system_prompt: str = system_prompt or system_instruction or ""
        self.history: List[Dict[str, Any]] = []

        active_key_names = api_key_names
        if not active_key_names:
            env_key_names = [n.strip() for n in os.getenv("GEMINI_API_KEY_NAMES", "").split(",") if n.strip()]
            if env_key_names:
                active_key_names = env_key_names

        self.model = GoogleGenerativeAI(
            api_key_names=active_key_names or [],
            system_instruction=self._system_prompt,
            model_name=self._model_id,
            sleep_on_exhausted=False,
            **kwargs,
        )

    @property
    def model_id(self) -> str:
        """Get normalized model identifier."""
        return self._model_id

    @model_id.setter
    def model_id(self, val: str) -> None:
        """Set and normalize model identifier."""
        normalized = self.normalize_model_id(val)
        self._model_id = normalized
        if hasattr(self.model, "model_name"):
            self.model.model_name = normalized

    @property
    def model_name(self) -> str:
        """Get model identifier (alias for model_id)."""
        return self.model_id

    @model_name.setter
    def model_name(self, val: str) -> None:
        """Set model identifier (alias for model_id)."""
        self.model_id = val

    @property
    def system_instruction(self) -> str:
        """Get current system instruction."""
        return self._system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Set system instruction on adapter and underlying model."""
        self._system_prompt = val or ""
        if hasattr(self.model, "system_instruction"):
            self.model.system_instruction = self._system_prompt

    @property
    def system_prompt(self) -> str:
        """Get system prompt."""
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, val: str) -> None:
        """Set system prompt."""
        self.system_instruction = val

    @property
    def api_key(self) -> str:
        """Get active API key from underlying model."""
        return getattr(self.model, "api_key", "") or ""

    def clear_history(self) -> None:
        """Clear local dialogue history."""
        self.history = []
        if hasattr(self.model, "clear_history"):
            self.model.clear_history()

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        system_instruction: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> Optional[str]:
        """Send a single-turn prompt to Gemini model.

        Args:
            q (str): Query text.
            attempts (int): Maximum retry attempts.
            system_instruction (Optional[str]): System instruction override.
            temperature (Optional[float]): Generation temperature.
            max_tokens (Optional[int]): Max output tokens.
            **kwargs: Additional parameters.

        Returns:
            Optional[str]: Generated response text.
        """
        if not q or not q.strip():
            return ""

        gen_cfg: Dict[str, Any] = dict(kwargs.pop("generation_config", {}))
        if temperature:
            gen_cfg["temperature"] = temperature
        if max_tokens:
            gen_cfg["max_output_tokens"] = max_tokens

        eff_inst = system_instruction or self._system_prompt or ""
        if eff_inst and hasattr(self.model, "system_instruction"):
            self.model.system_instruction = eff_inst

        kwargs.pop("model_name", None)

        return await self.model.ask(
            q=q,
            attempts=attempts,
            generation_config=gen_cfg,
            **kwargs,
        )

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = "",
        save_history: bool = True,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> str:
        """Send chat request with dialogue context.

        Args:
            q (str): User message.
            history (Optional[List[Dict]]): Conversation history.
            system_instruction (Optional[str]): System prompt override.
            save_history (bool): Save turn to local history.
            attempts (int): Max retry attempts.
            temperature (Optional[float]): Temperature.
            max_tokens (Optional[int]): Max tokens.
            **kwargs: Additional generation settings.

        Returns:
            str: Full response text.
        """
        if not q or not q.strip():
            return ""

        chunks: List[str] = []
        async for chunk in self.chat_stream(
            q=q,
            history=history,
            system_instruction=system_instruction,
            attempts=attempts,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            chunks.append(chunk)

        ans = "".join(chunks)
        if save_history and ans:
            self.history.append({"role": "user", "content": q})
            self.history.append({"role": "model", "content": ans})
        return ans

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks from Gemini model in real-time.

        Args:
            q (str): User message text.
            history (Optional[List[Dict]]): Message history entries.
            system_instruction (Optional[str]): System prompt override.
            attempts (int): Retry attempts limit.
            temperature (Optional[float]): Generation temperature.
            max_tokens (Optional[int]): Maximum tokens.
            **kwargs: Additional generation arguments.

        Yields:
            str: Generated text chunk.
        """
        if not q or not q.strip():
            return

        gen_cfg: Dict[str, Any] = dict(kwargs.pop("generation_config", {}))
        if temperature:
            gen_cfg["temperature"] = temperature
        if max_tokens:
            gen_cfg["max_output_tokens"] = max_tokens

        eff_inst = system_instruction or self._system_prompt or ""
        effective_history = history if history is not None else self.history
        model_name = kwargs.pop("model_name", None) or self._model_id

        async for chunk in self.model.chat_stream(
            q=q,
            history=effective_history,
            system_instruction=eff_inst,
            attempts=attempts,
            model_name=model_name,
            generation_config=gen_cfg,
            **kwargs,
        ):
            yield chunk

    async def stream_chat(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        history: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response chunks (BaseChatProvider interface alias).

        Args:
            q (str): Query prompt.
            attempts (int): Retry attempts.
            temperature (Optional[float]): Generation temperature.
            max_tokens (Optional[int]): Maximum tokens.
            history (Optional[List[Dict]]): Message history.
            **kwargs: Additional parameters.

        Yields:
            str: Response chunks.
        """
        async for chunk in self.chat_stream(
            q=q,
            history=history,
            attempts=attempts,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def close(self) -> None:
        """Close client sessions and clean up resources."""
        pass

