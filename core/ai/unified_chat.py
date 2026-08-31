# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wrapper class for transparent routing between Gemi
# =============================================================================
# Description:
#   A wrapper model class that aggregates GoogleGenerativeAI and FoundryChatBase
#
# File: unified_chat.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import inspect
import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
from core.ai.gemini import GoogleGenerativeAI
from core.ai.foundry_chat import FoundryChatBase
from core.logger import logger

class UnifiedChatModel:
    """
    Wrapper class for transparent routing between Gemini and Foundry models.
    """
    def __init__(
        self,
        api_key_names: List[str],
        system_instruction: str,
        foundry_model_id: str,
        use_foundry: bool = False,
        use_ollama: bool = False,
        ollama_model_id: str = "llama3.1",
        ollama_base_url: str = "http://localhost:11434",
    ):
        self.gemini_model = GoogleGenerativeAI(
            api_key_names=api_key_names,
            system_instruction=system_instruction,
            sleep_on_exhausted=False,
        )
        self.foundry_model = False
        self.use_foundry = use_foundry
        self.foundry_model_id = foundry_model_id
        
        self.ollama_model = False
        self.use_ollama = use_ollama
        self.ollama_model_id = ollama_model_id
        self.ollama_base_url = ollama_base_url
        
        if use_foundry:
            self.foundry_model = FoundryChatBase(
                model_id=foundry_model_id,
                system_prompt=system_instruction,
            )
            
        if use_ollama:
            from core.ai.ollama_chat import OllamaChatBase
            self.ollama_model = OllamaChatBase(
                model_id=ollama_model_id,
                system_prompt=system_instruction,
                api_url=ollama_base_url,
            )
            
        from core.ai.gemini.generative_ai import _DEFAULT_MODEL
        if use_ollama:
            self.default_model = f"ollama:{ollama_model_id}"
        elif use_foundry:
            self.default_model = f"foundry:{foundry_model_id}"
        else:
            self.default_model = _DEFAULT_MODEL
            
        self._model_name = self.default_model
        self._model_name = self.default_model
        

    def update_system_instruction(self, new_instruction: str) -> None:
        """Dynamically update system instruction for all initialized models."""
        self.system_instruction = new_instruction
        if hasattr(self, 'gemini_model') and self.gemini_model:
            self.gemini_model.system_instruction = new_instruction
        if hasattr(self, 'foundry_model') and self.foundry_model:
            self.foundry_model.system_prompt = new_instruction
        if hasattr(self, 'ollama_model') and self.ollama_model:
            self.ollama_model.system_prompt = new_instruction
        if hasattr(self, 'agy_model') and self.agy_model:
            self.agy_model.system_prompt = new_instruction
        if hasattr(self, 'gemini_cli_model') and self.gemini_cli_model:
            self.gemini_cli_model.system_prompt = new_instruction
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[UnifiedChatModel] Системная инструкция successfully обновлена")
        
    @property
    def model_name(self) -> str:
        return self._model_name
        
    @model_name.setter
    def model_name(self, val: str):
        self._model_name = val
        if self.foundry_model:
            self.foundry_model.model_id = val.replace("foundry:", "")
        if self.ollama_model:
            self.ollama_model.model_id = val.replace("ollama:", "")
        if hasattr(self, 'gemini_cli_model') and self.gemini_cli_model:
            self.gemini_cli_model.model_id = val
        if self.gemini_model:
            self.gemini_model.model_name = val
            
    @property
    def model_id(self) -> str:
        return self._model_name
        
    @model_id.setter
    def model_id(self, val: str):
        self._model_name = val
        if self.foundry_model:
            self.foundry_model.model_id = val.replace("foundry:", "")
        if self.ollama_model:
            self.ollama_model.model_id = val.replace("ollama:", "")
        if hasattr(self, 'gemini_cli_model') and self.gemini_cli_model:
            self.gemini_cli_model.model_id = val
        if self.gemini_model:
            self.gemini_model.model_name = val

    @property
    def api_key(self) -> str:
        return getattr(self.gemini_model, 'api_key', '') or ''

    @property
    def system_instruction(self) -> str:
        return getattr(self.gemini_model, 'system_instruction', '')

    @system_instruction.setter
    def system_instruction(self, val: str):
        if hasattr(self, 'gemini_model') and self.gemini_model:
            self.gemini_model.system_instruction = val

    def _get_active_model(self, model_name: Optional[str] = "") -> tuple[Any, str]:
        active_name = model_name or self._model_name
        
        if active_name.startswith("gemini_cli:") or active_name.startswith("gemini-cli-"):
            if not hasattr(self, 'gemini_cli_model') or not self.gemini_cli_model:
                from core.ai.gemini_cli_chat import GeminiCliChatBase
                self.gemini_cli_model = GeminiCliChatBase(
                    model_id=active_name,
                    system_prompt=self.system_instruction or "",
                )
            else:
                self.gemini_cli_model.model_id = active_name
            return self.gemini_cli_model, active_name

        if active_name.startswith("ollama:"):
            if not self.ollama_model:
                from core.ai.ollama_chat import OllamaChatBase
                self.ollama_model = OllamaChatBase(
                    model_id=active_name.replace("ollama:", ""),
                    system_prompt=self.system_instruction or "",
                    api_url=self.ollama_base_url,
                )
            else:
                self.ollama_model.model_id = active_name.replace("ollama:", "")
            return self.ollama_model, active_name

        if active_name.startswith("agy-") or 'agy' in active_name.lower():
            if not hasattr(self, 'agy_model') or not self.agy_model:
                from core.ai.agy_chat import AgyChatBase
                self.agy_model = AgyChatBase(
                    model_id=active_name,
                    system_prompt=self.system_instruction or "",
                )
            else:
                self.agy_model.model_id = active_name
            return self.agy_model, active_name
            
        if active_name.startswith("foundry:"):
            if not self.foundry_model:
                self.foundry_model = FoundryChatBase(
                    model_id=active_name.replace("foundry:", ""),
                    system_prompt=self.system_instruction or "",
                )
            else:
                self.foundry_model.model_id = active_name.replace("foundry:", "")
            return self.foundry_model, active_name

        if active_name.startswith("hf:") or active_name.startswith("hf::"):
            model_id = active_name.split(":", 1)[-1].lstrip(":")
            from core.ai.hf_chat import HFChatBase
            return HFChatBase(model_id=model_id, system_prompt=self.system_instruction or ""), active_name

        if active_name.startswith("onnx:") or active_name.startswith("onnx::"):
            model_id = active_name.split(":", 1)[-1].lstrip(":")
            from core.ai.onnx_chat import ONNXChatBase
            return ONNXChatBase(model_id=model_id, system_prompt=self.system_instruction or ""), active_name

        openai_prefixes = ("openai:", "openai::", "deepseek:", "groq:", "openrouter:", "lmstudio:", "local:", "compat:")
        if any(active_name.startswith(p) for p in openai_prefixes):
            prov_part, model_part = active_name.split(":", 1)
            model_id = model_part.lstrip(":")
            prov_name = prov_part.lower().rstrip(":")
            if prov_name == "compat":
                prov_name = "openai"
            from core.ai.openai_compat_chat import OpenAICompatChat
            return OpenAICompatChat.create_for_provider(
                provider_name=prov_name,
                model_id=model_id,
                system_prompt=self.system_instruction or "",
            ), active_name

        return self.gemini_model, active_name

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        model_name: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> Optional[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] chat: prompt={repr(q[:100])}... using model={active_name}")
        
        sig = inspect.signature(model_instance.chat)
        call_kwargs = {
            "q": q,
            "history": history,
            "system_instruction": system_instruction,
            "attempts": attempts,
        }
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        if "temperature" in sig.parameters and temperature:
            call_kwargs["temperature"] = temperature
        if "max_tokens" in sig.parameters and max_tokens:
            call_kwargs["max_tokens"] = max_tokens

        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v
                
        try:
            res = await model_instance.chat(**call_kwargs)
            logger.info(f"[UnifiedChatModel] chat success: response={repr(res[:100]) if res else 'None'}...")
            return res
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] chat error with model={active_name}", ex)
            raise

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        generation_config: Dict[str, Any] = None,
        model_name: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs
    ) -> Optional[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] ask: prompt={repr(q[:100])}... using model={active_name}")
        
        sig = inspect.signature(model_instance.ask)
        call_kwargs = {
            "q": q,
            "attempts": attempts,
        }
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        if "generation_config" in sig.parameters:
            call_kwargs["generation_config"] = generation_config
            
        if "temperature" in sig.parameters and temperature:
            call_kwargs["temperature"] = temperature
        if "max_tokens" in sig.parameters and max_tokens:
            call_kwargs["max_tokens"] = max_tokens

        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v
                
        try:
            res = await model_instance.ask(**call_kwargs)
            logger.info(f"[UnifiedChatModel] ask success: response={repr(res[:100]) if res else 'None'}...")
            return res
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] ask error with model={active_name}", ex)
            raise

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        model_name: Optional[str] = "",
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        generation_config: Dict[str, Any] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] chat_stream: prompt={repr(q[:100])}... using model={active_name}")
        
        sig = inspect.signature(model_instance.chat_stream)
        call_kwargs = {
            "q": q,
            "history": history,
            "system_instruction": system_instruction,
            "attempts": attempts,
        }
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        if "generation_config" in sig.parameters:
            call_kwargs["generation_config"] = generation_config
            
        if "temperature" in sig.parameters and temperature:
            call_kwargs["temperature"] = temperature
        if "max_tokens" in sig.parameters and max_tokens:
            call_kwargs["max_tokens"] = max_tokens

        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v

        try:
            async for chunk in model_instance.chat_stream(**call_kwargs):
                yield chunk
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] chat_stream error with model={active_name}", ex)
            raise

    async def ask_with_tools_stream(
        self,
        q: str,
        tools: List[Any],
        tool_dispatcher: Any,
        system_instruction: Optional[str] = "",
        model_name: Optional[str] = "",
        history: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] ask_with_tools_stream: prompt={repr(q[:100])}... using model={active_name}")
        
        if not hasattr(model_instance, 'ask_with_tools_stream'):
            raise NotImplementedError(f"Model {active_name} does not support ask_with_tools_stream")
            
        sig = inspect.signature(model_instance.ask_with_tools_stream)
        call_kwargs = {
            "q": q,
            "tools": tools,
            "tool_dispatcher": tool_dispatcher,
            "system_instruction": system_instruction,
            "history": history,
        }
        
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v

        try:
            async for chunk in model_instance.ask_with_tools_stream(**call_kwargs):
                yield chunk
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] ask_with_tools_stream error with model={active_name}", ex)
            raise
