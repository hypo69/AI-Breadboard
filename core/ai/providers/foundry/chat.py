# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Base class for chat interface with Foundry models
# =============================================================================
# Description:
#   Parent class for Foundry model chat interactions with retry logic,
#   history management, and streaming support.
#
# File: foundry_chat.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Base class for chat interface with Foundry models.

Provides foundation chat interfaces (ask, chat, chat_stream) for Foundry model
interactions with automatic retry, history management, and error handling.

Example usage:
    ai = FoundryChatBase(model_id="qwen3-0.6b-generic-cpu:4")
    answer = await ai.ask("Hello, how are you?")
    answer = await ai.chat("Summarize previous", history=prev_history)
    ai.clear_history()
"""

import asyncio
import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from core.logger.logger import logger

logger = logging.getLogger(__name__)

class FoundryChatBase:
    """Chat interface for Foundry models.
    
    Manages single requests, multi-turn conversations, and streaming responses
    with automatic retry logic and error handling.

    Attributes:
        model_id (str): Foundry model identifier.
        temperature (float): Sampling temperature (0.0-2.0).
        max_tokens (int): Maximum tokens to generate.
        system_prompt (str): System instruction for chat mode.
    """

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Get list of available Foundry models.
        
        Args:
            force_refresh (bool): Force refresh of model list.
            
        Returns:
            List[str]: List of available model identifiers.
        """
        from core.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="foundry", force_refresh=force_refresh)

    def __init__(
        self,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "You are a helpful AI assistant.",
        api_url: Optional[str] = "",
    ):
        """Initialize Foundry chat instance.
        
        Args:
            model_id: Foundry model ID (e.g. 'qwen3-0.6b-generic-cpu:4').
            temperature: Sampling temperature (0.0-2.0). Default 0.7.
            max_tokens: Maximum tokens to generate. Default 2048.
            system_prompt: System instruction for chat mode.
            api_url: Optional custom Foundry API URL (auto-discovered if empty).
        """
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        
        # Import FoundryClient lazily to avoid circular dependencies
        self._client = False
        self._api_url = api_url
        
        # Chat history (memory mode only)
        self._history: List[Dict[str, str]] = []
        
        # Error tracking
        self._last_error: str = ""
        self._error_count: int = 0
        
        logger.info(f"FoundryChat initialized: model={model_id}")

    @property
    def system_instruction(self) -> str:
        """Get current system instruction.
        
        Returns:
            str: Current system instruction.
        """
        return self.system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Set system instruction.
        
        Args:
            val (str): System instruction to set.
        """
        self.system_prompt = val

    async def _get_client(self) -> Any:
        """Lazy initialization of FoundryClient.
        
        Returns:
            FoundryClient: Initialized client instance.
        """
        if not self._client:
            from .client import FoundryClient
            self._client = FoundryClient(base_url=self._api_url)
        return self._client

    async def close(self) -> None:
        """Close client session and clean up resources."""
        if self._client:
            await self._client.close()

    def clear_history(self) -> None:
        """Clear chat history."""
        self._history = []
        logger.debug("Chat history cleared")

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> Optional[str]:
        """Send single request to model (stateless).
        
        Does not save history between calls.

        Args:
            q (str): Request text.
            attempts (int): Maximum retry attempts. Default 15.
            temperature (Optional[float]): Override default temperature.
            max_tokens (Optional[int]): Override default max_tokens.
            **kwargs: Additional parameters (e.g., dynamic_context).

        Returns:
            Optional[str]: Model response or None on critical error.
        """
        if not q or not q.strip():
            logger.warning("Empty query, skipping")
            return None

        # RAG context lookup (if provided)
        context = kwargs.get('dynamic_context', '')

        prompt = q
        if context:
            prompt = f"{q}{context}"

        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"[{self.model_id}] ask attempt {attempt}/{attempts}")

                client = await self._get_client()
                result = await client.generate_text(
                    prompt=prompt,
                    model=self.model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if result.get("success") and result.get("content"):
                    content = result["content"]
                    self._error_count = 0  # Reset error count on success
                    logger.debug(f"[{self.model_id}] ask success: {content[:80]}...")
                    return content

                # Handle model not loaded error
                error_code = result.get("error_code")
                if error_code == "model_not_loaded":
                    logger.warning(f"Model {self.model_id} not loaded, attempting to load...")
                    load_result = await client.load_model(self.model_id)
                    if load_result.get("success"):
                        logger.info(f"Model {self.model_id} loaded successfully")
                        continue  # Retry after load
                    else:
                        load_err = load_result.get('error', '')
                        logger.error(f"Failed to load model {self.model_id}: {load_err}")
                        from core.ai.model_manager import add_unsupported_model
                        add_unsupported_model('foundry', self.model_id, reason=f"Load failed: {load_err}")
                        return None

                # Other error - log and retry
                error_msg = result.get("error", "Unknown error")
                if "404" in error_msg or "not found" in error_msg.lower():
                    from core.ai.model_manager import add_unsupported_model
                    add_unsupported_model('foundry', self.model_id, reason=error_msg)
                    return None
                logger.warning(f"[{self.model_id}] attempt {attempt} failed: {error_msg}")

                if attempt < attempts:
                    wait = 2 ** min(attempt, 5)  # Exponential backoff: 2, 4, 8, 16, 32s
                    logger.info(f"Waiting {wait}s before retry...")
                    time.sleep(wait)

            except Exception as ex:
                logger.error(f"[{self.model_id}] exception on attempt {attempt}: {ex}")
                self._last_error = str(ex)
                self._error_count += 1

                if attempt < attempts:
                    wait = 2 ** min(attempt, 5)
                    logger.info(f"Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    logger.error(f"[{self.model_id}] All {attempts} attempts failed")
                    return None

        return None

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = None,
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        flag: str = "save_chat",
        **kwargs: Any,
    ) -> Optional[str]:
        """Process chat request with history.
        
        Args:
            q (str): Request text.
            history (Optional[List[Dict]]): Chat history from database (optional).
            save_history (bool): Save new pair to local history. Default True.
            temperature (Optional[float]): Override default temperature.
            max_tokens (Optional[int]): Override default max_tokens.
            system_instruction (Optional[str]): Temporary system instruction.
            attempts (int): Maximum retry attempts. Default 15.
            flag (str): History control flag (for Gemini interface compatibility).
            **kwargs: Additional parameters (e.g., dynamic_context).

        Returns:
            Optional[str]: Model response text.
        """
        if not q or not q.strip():
            logger.warning("Empty chat message, skipping")
            return ""

        # If history is passed, use it instead of local _history
        if history:
            self._history = history.copy()
        elif flag == "clear" or flag == "start_new":
            self.clear_history()

        # RAG context lookup (if provided)
        context = kwargs.get('dynamic_context', '')

        eff_temp = temperature if temperature and temperature > 0 else self.temperature
        eff_tokens = max_tokens if max_tokens and max_tokens > 0 else self.max_tokens

        # Prepare messages with system prompt
        sys_prompt = system_instruction or self.system_prompt
        if context:
            sys_prompt = f"{sys_prompt}{context}"

        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": q})

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"[{self.model_id}] chat attempt {attempt}/{attempts}")

                client = await self._get_client()
                result = await client.generate_text(
                    prompt="",  # Not used when messages provided
                    model=self.model_id,
                    temperature=eff_temp,
                    max_tokens=eff_tokens,
                    messages=messages,
                )

                if result.get("success") and result.get("content"):
                    answer = result["content"]
                    
                    # Save to history
                    if save_history:
                        self._history.append({"role": "user", "content": q})
                        self._history.append({"role": "assistant", "content": answer})
                    
                    self._error_count = 0
                    logger.debug(f"[{self.model_id}] chat success: {answer[:80]}...")
                    return answer

                # Handle model not loaded error
                error_code = result.get("error_code")
                if error_code == "model_not_loaded":
                    logger.warning(f"Model {self.model_id} not loaded, attempting to load...")
                    load_result = await client.load_model(self.model_id)
                    if load_result.get("success"):
                        logger.info(f"Model {self.model_id} loaded successfully")
                        continue  # Retry after load
                    else:
                        load_err = load_result.get('error', '')
                        logger.error(f"Failed to load model {self.model_id}: {load_err}")
                        from core.ai.model_manager import add_unsupported_model
                        add_unsupported_model('foundry', self.model_id, reason=f"Load failed: {load_err}")
                        return ""

                error_msg = result.get("error", "Unknown error")
                logger.warning(f"[{self.model_id}] chat attempt {attempt} failed: {error_msg}")

                if attempt < attempts:
                    time.sleep(2 ** min(attempt, 5))

            except Exception as ex:
                logger.error(f"[{self.model_id}] chat exception: {ex}")
                self._last_error = str(ex)
                if attempt >= attempts:
                    return ""
                time.sleep(2 ** min(attempt, 5))

        return ""

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = None,
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        model_name: Optional[str] = "",
        generation_config: Dict[str, Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Streaming chat interface (returns generator with chunk responses).
        
        Args:
            q (str): Request text.
            history (Optional[List[Dict]]): Chat history.
            save_history (bool): Save to history. Default True.
            temperature (Optional[float]): Generation temperature.
            max_tokens (Optional[int]): Max tokens.
            system_instruction (Optional[str]): System instruction.
            attempts (int): Max retry attempts.
            model_name (Optional[str]): Model name override.
            generation_config (Optional[Dict]): Generation configuration.
            **kwargs: Additional parameters.

        Yields:
            str: Response text chunks as generated.
            
        Raises:
            Exception: If generation fails after all attempts.
        """
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
        """Get current chat history (without system prompt).
        
        Returns:
            List[Dict[str, str]]: Conversation history.
        """
        return list(self._history)

    @property
    def last_error(self) -> str:
        """Get last error message.
        
        Returns:
            str: Last error message.
        """
        return self._last_error

    @property
    def error_count(self) -> int:
        """Get consecutive error count.
        
        Returns:
            int: Number of consecutive errors.
        """
        return self._error_count


class FoundrySimpleChat(FoundryChatBase):
    """Simplified chat interface for Foundry models.
    
    Use when text generation is needed without history persistence.

    Example:
        chat = FoundrySimpleChat(model_id="qwen3-0.6b-generic-cpu:4")
        answer = await chat.ask("Hello")
    """

    def __init__(self, model_id: str, **kwargs):
        """Initialize simplified chat interface.
        
        Args:
            model_id (str): Foundry model identifier.
            **kwargs: Additional parameters for parent class.
        """
        super().__init__(model_id, **kwargs)
        logger.info(f"FoundrySimpleChat initialized: model={model_id}")


# Module-level functions for quick start

# Global instance (one per process)
_default_chat: Any = False

def get_foundry_chat(model_id: Optional[str] = "") -> FoundryChatBase:
    """Get global chat instance.
    
    Args:
        model_id (Optional[str]): If provided, creates new instance with this model.

    Returns:
        FoundryChatBase: Chat instance.
        
    Raises:
        ValueError: If no default chat initialized.
    """
    global _default_chat
    
    if model_id:
        _default_chat = FoundryChatBase(model_id=model_id)
    
    if not _default_chat:
        raise ValueError("No default chat initialized. Call get_foundry_chat(model_id='...') first")
    
    return _default_chat

def set_foundry_chat(chat: FoundryChatBase):
    """Set global chat instance.
    
    Args:
        chat (FoundryChatBase): Chat instance to set as global.
    """
    global _default_chat
    _default_chat = chat
    logger.info("Global FoundryChat instance set")


# Compatibility import
FoundryClient = FoundryChatBase
