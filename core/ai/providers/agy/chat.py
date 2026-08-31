# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Antigravity SDK chat connection and request routing
# =============================================================================
# Description:
#   Chat adapter for interacting with Antigravity SDK models (agy-flash, agy-pro).
#   Implements standard chat interfaces for FastAPI router architecture compatibility.
#
# File: agy_chat.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Antigravity SDK chat connection and request routing adapter.

Implements chat interfaces (ask, chat_stream) for Antigravity SDK models with
API key management and local conversation history support."""

import os
import asyncio
from typing import Optional, List, Dict, AsyncGenerator

from core.logger.logger import logger
from core.secrets.api_key_state import load_api_keys

class AgyChatBase:
    """Chat adapter for Antigravity SDK models (agy-flash, agy-pro).

    Implements standard chat interfaces for FastAPI router compatibility.

    Attributes:
        model_id (str): Normalized model identifier (e.g., agy-flash).
        system_instruction (str): System instructions for LLM.
        history (List[Dict[str, str]]): Local conversation history.
        api_key (str): Active API key for agent initialization.
    """

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Get list of available models for AGY provider.
        
        Args:
            force_refresh (bool): Force refresh of model list.
            
        Returns:
            List[str]: List of available model identifiers.
        """
        from core.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="agy", force_refresh=force_refresh)

    @classmethod
    def normalize_model_id(cls, model_id: str) -> str:
        """Normalize model identifier for Antigravity SDK.
        
        Args:
            model_id (str): Raw model identifier.
            
        Returns:
            str: Normalized model identifier."""
        actual = (model_id or "").strip()
        while actual.startswith("agy-"):
            actual = actual[4:]
        if actual in ("flash", "flash-latest", "agy-flash", ""):
            return "gemini-flash-lite-latest"
        elif actual in ("pro", "pro-latest", "agy-pro"):
            return "gemini-pro-latest"
        elif not (actual.startswith("gemini-") or actual.startswith("gemma-") or actual.startswith("deep-research-") or actual.startswith("lyria-")):
            actual = f"gemini-{actual}"
        return actual

    def __init__(self, model_id: str, system_prompt: str = "") -> None:
        """Initialize connection to AGY SDK.
        
        Args:
            model_id (str): Model identifier.
            system_prompt (str): System prompt for the model."""
        self._model_id: str = self.normalize_model_id(model_id)
        self.system_prompt: str = system_prompt
        self.history: List[Dict[str, str]] = []
        valid_keys: List[str] = []
        agy_key = os.getenv('AGY_API_KEY', '').strip()
        if agy_key:
            valid_keys.append(agy_key)

        _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        loaded, _, _ = load_api_keys(_api_key_names if _api_key_names else [])
        for k in loaded:
            if k and k not in valid_keys:
                valid_keys.append(k)

        self.api_keys: List[str] = valid_keys
        self.api_key: str = valid_keys[0] if valid_keys else ""

    @property
    def model_id(self) -> str:
        """Get normalized model identifier.
        
        Returns:
            str: Normalized model identifier.
        """
        return self._model_id

    @model_id.setter
    def model_id(self, val: str) -> None:
        """Set and normalize model identifier.
        
        Args:
            val (str): Model identifier to set.
        """
        self._model_id = self.normalize_model_id(val)

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

    def _clean_output(self, text: str) -> str:
        """Clean response from SDK internal step messages.
        
        Args:
            text (str): Raw response text.
            
        Returns:
            str: Cleaned response text."""
        cleaned = text.strip()
        if "error executing cascade step:" in cleaned or "RESOURCE_EXHAUSTED" in cleaned or "GenerateContent failed:" in cleaned:
            if "]]]]" in cleaned:
                idx = cleaned.find("]]]]")
                cleaned = cleaned[idx + 4:].strip()
            elif "]]" in cleaned:
                idx = cleaned.rfind("]]")
                cleaned = cleaned[idx + 2:].strip()
            else:
                lines = cleaned.split("\n")
                filtered = [l for l in lines if not l.startswith("error executing cascade step:") and not l.startswith("GenerateContent failed:") and "RESOURCE_EXHAUSTED" not in l]
                cleaned = "\n".join(filtered).strip()
        return cleaned

    def clear_history(self) -> None:
        """Clear local chat history."""
        self.history = []

    async def ask(
        self,
        q: str,
        system_instruction: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> str:
        """Send single request to agent.
        
        Args:
            q (str): User question.
            system_instruction (Optional[str]): System instruction override.
            temperature (Optional[float]): Generation temperature (default 0.0).
            max_tokens (Optional[int]): Max tokens (0 for unlimited).
            **kwargs: Additional parameters.
            
        Returns:
            str: Agent response text."""
        if not q or not q.strip():
            return ""

        sys_prompt = system_instruction or self.system_prompt or ""

        try:
            from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
            config = LocalAgentConfig(
                model=self.model_id,
                system_instructions=sys_prompt,
                api_key=self.api_key,
                tools=[],
                policies=[],
                capabilities=CapabilitiesConfig(enable_subagents=False, enabled_tools=[])
            )
            async with Agent(config) as agent:
                response = await agent.chat(q)
                text = ""
                async for token in response:
                    text += token
                return self._clean_output(text)
        except Exception as e:
            err_str = str(e)
            if any(x in err_str for x in ('404', 'NOT_FOUND', 'not supported', 'is no longer available', 'not found')):
                from core.ai.model_manager import add_unsupported_model
                add_unsupported_model('agy', self.model_id, reason=err_str)
                add_unsupported_model('gemini', self.model_id, reason=err_str)
            logger.error("Error in AgyChatBase.ask", e, exc_info=True)
            return ""

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict]] = [],
        system_instruction: Optional[str] = "",
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> str:
        """Send chat request with conversation history.
        
        Args:
            q (str): User question.
            history (Optional[List[Dict]]): Conversation history.
            system_instruction (Optional[str]): System instruction override.
            save_history (bool): Save to local history (default True).
            temperature (Optional[float]): Generation temperature.
            max_tokens (Optional[int]): Max tokens.
            **kwargs: Additional parameters.
            
        Returns:
            str: Chat response text."""
        if not q or not q.strip():
            return ""
        
        # Build full response from chat_stream generator
        chunks = []
        async for chunk in self.chat_stream(
            q=q,
            history=history,
            system_instruction=system_instruction,
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
        history: Optional[List[Dict]] = [],
        system_instruction: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Send streaming request to agent.

        Args:
            q (str): User question text.
            history (Optional[List[Dict]]): Optional conversation history.
            system_instruction (Optional[str]): System instruction override.
            temperature (Optional[float]): Generation temperature (default 0.0).
            max_tokens (Optional[int]): Maximum tokens (0 for default).

        Yields:
            str: Response text chunks as generated.
        """
        if not q or not q.strip():
            return

        sys_prompt = system_instruction or self.system_prompt or ""
        
        # Integrate history into context
        context = ""
        if history:
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if not content and 'parts' in msg:
                    content = " ".join([p.get('text', '') if isinstance(p, dict) else str(p) for p in msg['parts']])
                context += f"\n[{role}]: {content}"

        if context:
            sys_prompt = f"{sys_prompt}\n\nConversation history:\n{context}"

        try:
            from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
            config = LocalAgentConfig(
                model=self.model_id,
                system_instructions=sys_prompt,
                api_key=self.api_key,
                tools=[],
                policies=[],
                capabilities=CapabilitiesConfig(enable_subagents=False, enabled_tools=[])
            )
            async with Agent(config) as agent:
                response = await agent.chat(q)
                async for token in response:
                    yield token
        except Exception as e:
            err_str = str(e)
            if any(x in err_str for x in ('404', 'NOT_FOUND', 'not supported', 'is no longer available', 'not found')):
                from core.ai.model_manager import add_unsupported_model
                add_unsupported_model('agy', self.model_id, reason=err_str)
                add_unsupported_model('gemini', self.model_id, reason=err_str)
            err_msg = f"Error Antigravity SDK: {err_str}"
            logger.error(err_msg, e, exc_info=True)
            yield err_msg
