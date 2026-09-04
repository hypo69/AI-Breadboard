# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Returns list of available models for Ollama
# =============================================================================
# Description:
#   Returns list доступных моделей для Ollama через единый менеджер моделей."""
#
# File: ollama_chat.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any

from src.logger.logger import logger

logger = logging.getLogger(__name__)

class OllamaChatBase:
    """
    Базовый class для чат-интерфейса с Ollama моделями.
    """

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Returns list доступных моделей для Ollama через единый менеджер моделей."""
        from src.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="ollama", force_refresh=force_refresh)

    def __init__(
        self,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "You are a helpful AI assistant.",
        api_url: Optional[str] = "",
    ):
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        
        self._client = False
        self._api_url = api_url
        self._history: List[Dict[str, str]] = []
        self._last_error: str = ""
        self._error_count: int = 0
        
        logger.info(f"OllamaChat initialized: model={model_id}")

    @property
    def system_instruction(self) -> str:
        """Returns системную инструкцию."""
        return self.system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Sets системную инструкцию."""
        self.system_prompt = val

    async def _get_client(self):
        if not self._client:
            from .client import OllamaClient
            self._client = OllamaClient(base_url=self._api_url)
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()

    def clear_history(self):
        self._history = []
        logger.debug("Chat history cleared")

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        generation_config: dict = {},
    ) -> Optional[str]:
        return await self.chat(
            q=q,
            history=[],
            save_history=False,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
            attempts=attempts,
        )

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict]] = [],
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        **kwargs,
    ) -> Optional[str]:
        client = await self._get_client()
        temp = temperature if temperature and temperature > 0 else self.temperature
        tokens = max_tokens if max_tokens and max_tokens > 0 else self.max_tokens
        sys_prompt = system_instruction or self.system_prompt

        messages = [{"role": "system", "content": sys_prompt}]
        
        current_history = history if history else self._history
        for msg in current_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            
        messages.append({"role": "user", "content": q})

        for attempt in range(1, attempts + 1):
            try:
                res = await client.generate_text(
                    prompt=q,
                    model=self.model_id,
                    temperature=temp,
                    max_tokens=tokens,
                    messages=messages,
                )
                
                if res.get("success"):
                    self._error_count = 0
                    content = res.get("content", "")
                    
                    if save_history and not history:
                        self._history.append({"role": "user", "content": q})
                        self._history.append({"role": "assistant", "content": content})
                        
                    return content
                else:
                    self._last_error = res.get("error", "Unknown error")
                    self._error_count += 1
                    if "404" in self._last_error or "not found" in self._last_error.lower():
                        from src.ai.model_manager import add_unsupported_model
                        add_unsupported_model('ollama', self.model_id, reason=self._last_error)
                        return ""
                    logger.warning(f"[{self.model_id}] Error in generate_text: {self._last_error}")
                    if attempt >= attempts:
                        return ""
                    time.sleep(2 ** min(attempt, 5))
                    
            except Exception as ex:
                self._error_count += 1
                logger.error(f"[{self.model_id}] chat exception: {ex}")
                self._last_error = str(ex)
                if "404" in self._last_error or "not found" in self._last_error.lower():
                    from src.ai.model_manager import add_unsupported_model
                    add_unsupported_model('ollama', self.model_id, reason=self._last_error)
                    return ""
                if attempt >= attempts:
                    return ""
                time.sleep(2 ** min(attempt, 5))

        return ""

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict]] = [],
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        model_name: Optional[str] = "",
        generation_config: dict = {},
        **kwargs,
    ):
        response = await self.chat(
            q=q,
            history=history,
            save_history=save_history,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
            attempts=attempts,
            **kwargs,
        )
        if response:
            yield response
        else:
            if self._last_error:
                raise Exception(self._last_error)
            else:
                raise Exception(f"Failed to generate response using model {self.model_id}")

    @property
    def history(self) -> List[Dict[str, str]]:
        return list(self._history)

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def error_count(self) -> int:
        return self._error_count
