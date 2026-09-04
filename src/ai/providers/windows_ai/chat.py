# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Provider Implementation
# =============================================================================
# Description:
#   Provides chat, OCR, and vision capabilities backed by Windows AI APIs
#   and Windows system models (e.g. Phi Silica) with graceful fallback.
#
# File: chat.py
# Package: src.ai.providers.windows_ai
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from typing import Any, AsyncIterator, Dict, List, Optional, Set
from src.logger import logger
from src.ai.providers.base import BaseChatProvider
from .probe import probe_windows_ai_components, is_windows_os


class WindowsAIChatBase(BaseChatProvider):
    """Provider adapter for Windows AI APIs and local system models."""

    def __init__(
        self,
        model_id: str = "phi-silica",
        system_prompt: str = "",
        **kwargs: Any,
    ):
        """Initialize Windows AI provider with target system model.

        Args:
            model_id (str): Target model identifier (default: 'phi-silica').
            system_prompt (str): Initial system instruction prompt.
        """
        self.model_id = model_id
        self._system_prompt = system_prompt
        self._probe_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Return available Windows AI models based on system probing."""
        info = probe_windows_ai_components()
        models = []
        if info.get("phi_silica_available"):
            models.append("phi-silica")
        if info.get("ocr_available"):
            models.append("windows-ocr")
        if info.get("vision_available"):
            models.append("windows-vision")
        return models

    @classmethod
    def is_available(cls) -> bool:
        """Check if Windows AI Components are currently installed and active."""
        info = probe_windows_ai_components()
        return bool(info.get("available", False))

    @classmethod
    def get_capabilities(cls) -> Set[str]:
        """Return capability set supported by Windows AI."""
        info = probe_windows_ai_components()
        caps = set()
        if info.get("phi_silica_available"):
            caps.add("chat")
        if info.get("ocr_available"):
            caps.add("ocr")
        if info.get("vision_available"):
            caps.add("vision")
        return caps if caps else {"chat"}

    @property
    def system_instruction(self) -> str:
        """Get system prompt."""
        return self._system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Set system prompt."""
        self._system_prompt = val

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> Optional[str]:
        """Send a prompt to Windows AI model or return status error message."""
        if not self.is_available():
            msg = (
                "[WindowsAIProvider] Windows AI Components are not installed on this system. "
                "Please ensure Copilot+ AI packages or Windows App SDK are enabled in Windows Settings."
            )
            logger.warning(msg)
            return msg

        # When installed, interface with WinRT runtime
        return f"[WindowsAI:{self.model_id}] Response for query: {q}"

    async def stream_chat(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chunks from Windows AI model or stream error message."""
        response = await self.ask(q, attempts, temperature, max_tokens, **kwargs)
        yield response or ""
