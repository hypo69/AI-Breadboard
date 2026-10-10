# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Unified Chat Module
# =============================================================================
# Description:
#   Transparent routing wrapper across all configured AI providers.
#
# Usage Examples:
#   Python API:
#     from src.ai.orchestration.unified_chat import UnifiedChatModel
#
#     service = UnifiedChatModel()
#     result = service.model_name()
#     print(result)
#
# File: unified_chat.py
# Project: ai-breadboard
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 06:47:00
# =============================================================================

"""Transparent routing wrapper across all configured AI providers."""

import inspect
import sys
from typing import Any, AsyncIterator, Dict, List, Optional
from src.config import is_debug_mode

# Унифицированный паттерн гарантированного импорта логгера
try:
    from logger import logger
except ImportError:
    # Фолбэк на стандартный логгер при автономном запуске без модуля logger.py
    import logging
    logger = logging.getLogger("AITelemetryFallback")
    if not logger.handlers:
        _handler = logging.StreamHandler(sys.stderr)
        _formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s"
        )
        _handler.setFormatter(_formatter)
        logger.addHandler(_handler)
        logger.setLevel(logging.DEBUG)

class UnifiedChatModel:
    """Transparent routing wrapper across all configured AI providers.

    Model selection is based on string prefixes of the ``model_name`` argument:

    ============  ====================
    Prefix        Provider
    ============  ====================
    ``gemini_cli:`` GeminiCliChatBase
    ``ollama:``     OllamaChatBase
    ``agy:`` / ``agy-``  AgyChatBase
    ``foundry:``    FoundryChatBase
    ``hf:``         HFChatBase
    ``onnx:``       ONNXChatBase
    ``openai:`` / ``deepseek:`` / ``groq:`` etc.  OpenAICompatChat
    ``gemini:`` / *(default)*   GoogleGenerativeAI
    ============  ====================
    """

    def __init__(self, system_instruction: str='', provider: str='', model: str='', **kwargs: Any) -> None:
        """UnifiedChatModel требует явно указанные provider и model. Никаких хардкодов по умолчанию!
        
        Args:
            system_instruction: Системная инструкция для всех моделей.
            provider: Имя провайдера (gemini, gemini_cli, agy, foundry, ollama и т.д.).
            model: Имя модели для указанного провайдера.
            **kwargs: Дополнительные параметры.
        """
        if not provider or not model:
            raise ValueError('[UnifiedChatModel] Требуется явно указать provider и model. Получено: provider={}, model={}'.format(repr(provider), repr(model)))
        
        if 'api_key_names' in kwargs:
            logger.warning('[UnifiedChatModel] Параметр api_key_names устарел и не используется в UnifiedChatModel. Управление ключами выполняется непосредственно провайдерами моделей.')
        from src.config import ai_cfg
        providers = getattr(ai_cfg, 'providers', {}) if ai_cfg else {}
        
        self.gemini_model: Any = False
        self.foundry_model: Any = False
        self.ollama_model: Any = False
        self.gemini_cli_model: Any = False
        self.agy_model: Any = False
        
        # Используем переданные provider и model
        provider_upper = provider.upper()
        default_model = ''
        
        if provider_upper == 'GEMINI':
            from src.ai.gemini import GoogleGenerativeAI
            self.gemini_model = GoogleGenerativeAI(system_instruction=system_instruction, sleep_on_exhausted=False)
            default_model = f'gemini:{model}'
            self._provider = 'GEMINI'
            self.gemini_model.model_name = model
        elif provider_upper == 'GEMINI_CLI':
            default_model = f'gemini_cli:{model}'
            self._provider = 'GEMINI_CLI'
            from src.ai.providers.gemini_cli import GeminiCliChatBase
            self.gemini_cli_model = GeminiCliChatBase(model_id=model, system_prompt=system_instruction)
        elif provider_upper == 'AGY':
            default_model = f'agy-{model}'
            self._provider = 'AGY'
            from src.ai.providers.agy import AgyChatBase
            self.agy_model = AgyChatBase(model_id=model, system_prompt=system_instruction)
        elif provider_upper == 'FOUNDRY':
            default_model = f'foundry:{model}'
            self._provider = 'FOUNDRY'
            from src.ai.providers.foundry import FoundryChatBase
            self.foundry_model = FoundryChatBase(model_id=model, system_prompt=system_instruction)
        elif provider_upper == 'OLLAMA':
            default_model = f'ollama:{model}'
            self._provider = 'OLLAMA'
            from src.ai.providers.ollama import OllamaChatBase
            ollama_base_url = providers.get('ollama', {}).get('base_url', 'http://localhost:11434') if isinstance(providers, dict) else 'http://localhost:11434'
            self.ollama_model = OllamaChatBase(model_id=model, system_prompt=system_instruction, api_url=ollama_base_url)
        else:
            raise ValueError(f'[UnifiedChatModel] Неизвестный провайдер: {provider}')
        
        self._model_name = default_model

    def _sync_model_id(self, val: str) -> None:
        """Propagate a new model identifier to all initialised sub-models.

        Shared implementation used by both ``model_name`` and ``model_id``
        setters to eliminate code duplication.
        """
        self._model_name = val
        if self.foundry_model:
            self.foundry_model.model_id = val.replace('foundry:', '')
        if self.ollama_model:
            self.ollama_model.model_id = val.replace('ollama:', '')
        if self.gemini_cli_model:
            self.gemini_cli_model.model_id = val
        if self.gemini_model:
            self.gemini_model.model_name = val

    def _build_call_kwargs(self, sig: inspect.Signature, model_instance: Any, active_name: str, base_kwargs: Dict[str, Any], optional_kwargs: Dict[str, Any], extra_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Build the keyword-argument dict for a provider method call.

        Handles model routing (``model_name`` vs ``model_id``), optional
        parameters that differ across providers, and passthrough of extra
        caller kwargs.

        Args:
            sig: Inspected signature of the provider method.
            model_instance: The target provider instance.
            active_name: Resolved model name string.
            base_kwargs: Mandatory arguments always included.
            optional_kwargs: Arguments included only when accepted by ``sig``.
            extra_kwargs: Caller ``**kwargs`` — included when accepted by ``sig``.

        Returns:
            Dict ready to unpack as ``provider_method(**result)``.
        """
        call_kwargs: Dict[str, Any] = dict(base_kwargs)
        if 'model_name' in sig.parameters:
            call_kwargs['model_name'] = active_name
        elif hasattr(model_instance, 'model_id'):
            model_instance.model_id = active_name
        for param, value in optional_kwargs.items():
            if param in sig.parameters and value:
                call_kwargs[param] = value
        for k, v in extra_kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v
        return call_kwargs

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, val: str) -> None:
        self._sync_model_id(val)

    @property
    def model_id(self) -> str:
        return self._model_name

    @model_id.setter
    def model_id(self, val: str) -> None:
        self._sync_model_id(val)

    @property
    def api_key(self) -> str:
        return getattr(self.gemini_model, 'api_key', '') or ''

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def system_instruction(self) -> str:
        if self.gemini_model:
            return self.gemini_model.system_instruction
        return ''

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        if self.gemini_model:
            self.gemini_model.system_instruction = val

    def update_system_instruction(self, new_instruction: str) -> None:
        """Dynamically update system instruction for all initialised models."""
        self.system_instruction = new_instruction
        for attr in ('gemini_model', 'foundry_model', 'ollama_model', 'agy_model', 'gemini_cli_model'):
            model = getattr(self, attr, None)
            if not model:
                continue
            if hasattr(model, 'system_instruction'):
                model.system_instruction = new_instruction
            elif hasattr(model, 'system_prompt'):
                model.system_prompt = new_instruction
        logger.info('[UnifiedChatModel] System instruction updated successfully')

    def _get_active_model(self, model_name: Optional[str]='') -> tuple[Any, str]:
        """Resolve model name to a provider instance.

        Performs lazy initialisation of providers on first use.
        If model_name is not provided, uses self._model_name from initialization.
        """
        if not model_name:
            model_name = self._model_name
        
        active_name = model_name
        if active_name.startswith('gemini_cli:') or active_name.startswith('gemini-cli-'):
            if not self.gemini_cli_model:
                from src.ai.providers.gemini_cli import GeminiCliChatBase
                self.gemini_cli_model = GeminiCliChatBase(model_id=active_name.replace('gemini_cli:', '').replace('gemini-cli-', ''), system_prompt=self.system_instruction or '')
            else:
                self.gemini_cli_model.model_id = active_name.replace('gemini_cli:', '').replace('gemini-cli-', '')
            return (self.gemini_cli_model, active_name)
        if active_name.startswith('ollama:'):
            if not self.ollama_model:
                from src.config import ai_cfg
                providers = getattr(ai_cfg, 'providers', {}) if ai_cfg else {}
                ollama_cfg = providers.get('ollama', {}) if isinstance(providers, dict) else {}
                ollama_base_url = ollama_cfg.get('base_url', 'http://localhost:11434')
                from src.ai.providers.ollama import OllamaChatBase
                self.ollama_model = OllamaChatBase(model_id=active_name.replace('ollama:', ''), system_prompt=self.system_instruction or '', api_url=ollama_base_url)
            else:
                self.ollama_model.model_id = active_name.replace('ollama:', '')
            return (self.ollama_model, active_name)
        if active_name.startswith('agy:') or active_name.startswith('agy-') or 'agy' in active_name.lower():
            if not self.agy_model:
                from src.ai.providers.agy import AgyChatBase
                self.agy_model = AgyChatBase(model_id=active_name, system_prompt=self.system_instruction or '')
            else:
                self.agy_model.model_id = active_name
            return (self.agy_model, active_name)
        if active_name.startswith('foundry:'):
            if not self.foundry_model:
                from src.ai.providers.foundry import FoundryChatBase
                self.foundry_model = FoundryChatBase(model_id=active_name.replace('foundry:', ''), system_prompt=self.system_instruction or '')
            else:
                self.foundry_model.model_id = active_name.replace('foundry:', '')
            return (self.foundry_model, active_name)
        if active_name.startswith('hf:') or active_name.startswith('hf::'):
            model_id = active_name.split(':', 1)[-1].lstrip(':')
            from src.ai.providers.huggingface import HFChatBase
            return (HFChatBase(model_id=model_id, system_prompt=self.system_instruction or ''), active_name)
        if active_name.startswith('onnx:') or active_name.startswith('onnx::'):
            model_id = active_name.split(':', 1)[-1].lstrip(':')
            from src.ai.providers.onnx import ONNXChatBase
            return (ONNXChatBase(model_id=model_id, system_prompt=self.system_instruction or ''), active_name)
        openai_prefixes = ('openai:', 'openai::', 'deepseek:', 'groq:', 'openrouter:', 'lmstudio:', 'local:', 'compat:')
        if any((active_name.startswith(p) for p in openai_prefixes)):
            prov_part, model_part = active_name.split(':', 1)
            model_id = model_part.lstrip(':')
            prov_name = prov_part.lower().rstrip(':')
            if prov_name == 'compat':
                prov_name = 'openai'
            from src.ai.providers.openai import OpenAICompatChat
            return (OpenAICompatChat.create_for_provider(provider_name=prov_name, model_id=model_id, system_prompt=self.system_instruction or ''), active_name)
        return (self.gemini_model, active_name)

    async def chat(self, q: str, history: Optional[List[Dict[str, Any]]]=None, system_instruction: Optional[str]='', attempts: int=15, model_name: Optional[str]='', temperature: Optional[float]=0.0, max_tokens: Optional[int]=0, **kwargs: Any) -> Optional[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f'[UnifiedChatModel] chat: prompt={repr(q[:100])}... using model={active_name}')
        sig = inspect.signature(model_instance.chat)
        call_kwargs = self._build_call_kwargs(sig=sig, model_instance=model_instance, active_name=active_name, base_kwargs={'q': q, 'history': history, 'system_instruction': system_instruction, 'attempts': attempts}, optional_kwargs={'temperature': temperature, 'max_tokens': max_tokens}, extra_kwargs=kwargs)
        try:
            res = await model_instance.chat(**call_kwargs)
            logger.info(f"[UnifiedChatModel] chat success: response={(repr(res[:100]) if res else 'None')}...")
            if is_debug_mode() and res and any(res.startswith(p) for p in ('Model error:', 'Error:', 'Chat error:')):
                raise RuntimeError(f'[UnifiedChatModel] Ошибка в ответе модели {active_name}: {res}')
            return res
        except Exception as ex:
            logger.error(f'[UnifiedChatModel] chat error with model={active_name}', ex)
            raise

    async def ask(self, q: str, attempts: int=15, generation_config: Optional[Dict[str, Any]]=None, model_name: Optional[str]='', temperature: Optional[float]=0.0, max_tokens: Optional[int]=0, **kwargs: Any) -> Optional[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f'[UnifiedChatModel] ask: prompt={repr(q[:100])}... using model={active_name}')
        sig = inspect.signature(model_instance.ask)
        call_kwargs = self._build_call_kwargs(sig=sig, model_instance=model_instance, active_name=active_name, base_kwargs={'q': q, 'attempts': attempts}, optional_kwargs={'generation_config': generation_config, 'temperature': temperature, 'max_tokens': max_tokens}, extra_kwargs=kwargs)
        try:
            res = await model_instance.ask(**call_kwargs)
            logger.info(f"[UnifiedChatModel] ask success: response={(repr(res[:100]) if res else 'None')}...")
            if is_debug_mode() and res and any(res.startswith(p) for p in ('Model error:', 'Error:', 'Chat error:')):
                raise RuntimeError(f'[UnifiedChatModel] Ошибка в ответе модели {active_name}: {res}')
            return res
        except Exception as ex:
            logger.error(f'[UnifiedChatModel] ask error with model={active_name}', ex)
            raise

    async def chat_stream(self, q: str, history: Optional[List[Dict[str, Any]]]=None, system_instruction: Optional[str]='', attempts: int=15, model_name: Optional[str]='', temperature: Optional[float]=0.0, max_tokens: Optional[int]=0, generation_config: Optional[Dict[str, Any]]=None, **kwargs: Any) -> AsyncIterator[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f'[UnifiedChatModel] chat_stream: prompt={repr(q[:100])}... using model={active_name}')
        sig = inspect.signature(model_instance.chat_stream)
        call_kwargs = self._build_call_kwargs(sig=sig, model_instance=model_instance, active_name=active_name, base_kwargs={'q': q, 'history': history, 'system_instruction': system_instruction, 'attempts': attempts}, optional_kwargs={'generation_config': generation_config, 'temperature': temperature, 'max_tokens': max_tokens}, extra_kwargs=kwargs)
        try:
            async for chunk in model_instance.chat_stream(**call_kwargs):
                yield chunk
        except Exception as ex:
            logger.error(f'[UnifiedChatModel] chat_stream error with model={active_name}', ex)
            raise

    async def ask_with_tools_stream(self, q: str, tools: List[Any], tool_dispatcher: Any, system_instruction: Optional[str]='', model_name: Optional[str]='', history: Optional[List[Dict[str, Any]]]=None, **kwargs: Any) -> AsyncIterator[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f'[UnifiedChatModel] ask_with_tools_stream: prompt={repr(q[:100])}... using model={active_name}')
        if not hasattr(model_instance, 'ask_with_tools_stream'):
            raise NotImplementedError(f'Model {active_name} does not support ask_with_tools_stream')
        sig = inspect.signature(model_instance.ask_with_tools_stream)
        call_kwargs = self._build_call_kwargs(sig=sig, model_instance=model_instance, active_name=active_name, base_kwargs={'q': q, 'tools': tools, 'tool_dispatcher': tool_dispatcher, 'system_instruction': system_instruction, 'history': history}, optional_kwargs={}, extra_kwargs=kwargs)
        try:
            async for chunk in model_instance.ask_with_tools_stream(**call_kwargs):
                yield chunk
        except Exception as ex:
            logger.error(f'[UnifiedChatModel] ask_with_tools_stream error with model={active_name}', ex)
            raise