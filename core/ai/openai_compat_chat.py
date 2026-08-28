# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Universal OpenAI-Compatible API Client & Chat Wrapper
# =============================================================================
# Описание:
#   Универсальный клиент для любых внешних и локальных OpenAI-совместимых сервисов
#   (OpenAI, DeepSeek, Groq, Together AI, LM Studio, LocalAI, vLLM).
#
# File: core/ai/openai_compat_chat.py
# Project: ai-breadboard
# Package: core.ai
# Module: OpenAICompatChat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from header import __root__
from core.logger.logger import logger
from core.utils.jjson import j_loads

_GLOBAL_CONFIG_PATH = __root__ / "config.json"

_KNOWN_PROVIDERS: Dict[str, Dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
    },
    "lmstudio": {
        "base_url": "http://localhost:1234/v1",
        "env_key": "LMSTUDIO_API_KEY",
    },
    "local": {
        "base_url": "http://localhost:1234/v1",
        "env_key": "",
    },
}


class OpenAICompatChat:
    """Универсальный чат-клиент для любого OpenAI-совместимого эндпоинта.
    
    Поддерживает OpenAI, DeepSeek, Groq, OpenRouter, LM Studio, LocalAI, vLLM
    с методами ask(), chat(), generate_content() и потоковым выводом.
    """

    @classmethod
    def create_for_provider(
        cls,
        provider_name: str,
        model_id: str,
        system_prompt: str = "",
        api_key: Optional[str] = "",
        base_url: Optional[str] = "",
    ) -> "OpenAICompatChat":
        """Фабричный метод для инициализации клиента под конкретного провайдера."""
        prov = provider_name.lower().strip()
        resolved_url = base_url or ""
        resolved_key = api_key or ""

        # 1. Попытка извлечь параметры из config.json
        if not resolved_url or not resolved_key:
            try:
                cfg = j_loads(_GLOBAL_CONFIG_PATH)
                if isinstance(cfg, dict):
                    prov_cfg = cfg.get("openai_compat", {}).get("providers", {}).get(prov, {})
                    if isinstance(prov_cfg, dict):
                        if not resolved_url:
                            resolved_url = prov_cfg.get("base_url", "")
            except Exception as e:
                logger.debug(f"[OpenAICompat] Не удалось прочитать config.json: {e}")

        # 2. Попытка извлечь из известных провайдеров / переменных окружения
        known = _KNOWN_PROVIDERS.get(prov, {})
        if not resolved_url:
            resolved_url = known.get("base_url", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        
        if not resolved_key:
            env_var = known.get("env_key", "OPENAI_API_KEY")
            resolved_key = os.getenv(env_var, "") or os.getenv("OPENAI_API_KEY", "")

        return cls(
            model_id=model_id,
            base_url=resolved_url,
            api_key=resolved_key,
            system_prompt=system_prompt,
        )

    def __init__(
        self,
        model_id: str,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = aiohttp.ClientTimeout(total=120)
        self._history: List[Dict[str, str]] = []

    @property
    def system_instruction(self) -> str:
        """Алиас системной инструкции для совместимости с UnifiedChatModel."""
        return self.system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        self.system_prompt = val

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def clear_history(self) -> None:
        """Очистка локальной истории чата."""
        self._history.clear()

    async def generate_content(
        self,
        prompt: str,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> str:
        """Генерация одиночного ответа через /chat/completions."""
        return await self.ask(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def ask(
        self,
        q: str,
        attempts: int = 5,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        **kwargs: Any,
    ) -> str:
        """Одиночный запрос к модели с автоматическими повторами при сбоях."""
        sys_prompt = system_instruction or self.system_prompt
        temp = temperature if temperature and temperature > 0 else self.temperature
        max_t = max_tokens if max_tokens and max_tokens > 0 else self.max_tokens

        messages: List[Dict[str, str]] = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": q})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_t,
            "stream": False,
        }

        url = f"{self.base_url}/chat/completions"
        last_error = ""

        for attempt in range(1, attempts + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(url, headers=self._headers(), json=payload) as resp:
                        if resp.status != 200:
                            err_text = await resp.text()
                            logger.warning(f"[OpenAICompat] Попытка {attempt}/{attempts} ошибка HTTP {resp.status} от {url}: {err_text[:120]}")
                            last_error = f"HTTP {resp.status}: {err_text}"
                            if resp.status in (401, 403, 404):
                                # Ошибки аутентификации или отсутствия модели не повторяем
                                break
                            if attempt < attempts:
                                await asyncio.sleep(min(2 ** attempt, 8))
                            continue

                        data = await resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "")
                        return ""
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[OpenAICompat] Попытка {attempt}/{attempts} исключение для {url}: {e}")
                if attempt < attempts:
                    await asyncio.sleep(min(2 ** attempt, 8))

        logger.error(f"[OpenAICompat] Все {attempts} попыток завершились неудачей для {self.model_id}: {last_error}")
        raise RuntimeError(f"OpenAICompat error: {last_error}")

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = [],
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 5,
        **kwargs: Any,
    ) -> str:
        """Многошаговый чат с поддержкой истории сообщений."""
        sys_prompt = system_instruction or self.system_prompt
        temp = temperature if temperature and temperature > 0 else self.temperature
        max_t = max_tokens if max_tokens and max_tokens > 0 else self.max_tokens

        messages: List[Dict[str, str]] = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        # Интеграция переданной истории
        source_history = history if history else self._history
        for item in source_history:
            role = item.get("role", "user")
            if role in ("model", "assistant"):
                role = "assistant"
            elif role != "system":
                role = "user"
            
            # Извлечение текста (поддержка формата Gemini parts или стандартного content)
            content = ""
            if "parts" in item:
                parts = item["parts"]
                if isinstance(parts, list) and parts:
                    p = parts[0]
                    content = p if isinstance(p, str) else p.get("text", "") if isinstance(p, dict) else ""
                elif isinstance(parts, str):
                    content = parts
            elif "content" in item:
                content = str(item["content"])

            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": q})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_t,
            "stream": False,
        }

        url = f"{self.base_url}/chat/completions"
        last_error = ""

        for attempt in range(1, attempts + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(url, headers=self._headers(), json=payload) as resp:
                        if resp.status != 200:
                            err_text = await resp.text()
                            logger.warning(f"[OpenAICompat] chat attempt {attempt}/{attempts} HTTP {resp.status}: {err_text[:120]}")
                            last_error = f"HTTP {resp.status}: {err_text}"
                            if resp.status in (401, 403, 404):
                                break
                            if attempt < attempts:
                                await asyncio.sleep(min(2 ** attempt, 8))
                            continue

                        data = await resp.json()
                        choices = data.get("choices", [])
                        ans = choices[0].get("message", {}).get("content", "") if choices else ""
                        if save_history and ans:
                            self._history.append({"role": "user", "content": q})
                            self._history.append({"role": "assistant", "content": ans})
                        return ans
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[OpenAICompat] chat attempt {attempt}/{attempts} error: {e}")
                if attempt < attempts:
                    await asyncio.sleep(min(2 ** attempt, 8))

        logger.error(f"[OpenAICompat] chat failed for {self.model_id}: {last_error}")
        raise RuntimeError(f"OpenAICompat chat error: {last_error}")

    async def generate_content_stream(
        self,
        prompt: str,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Потоковая генерация ответа через SSE /chat/completions."""
        async for chunk in self.stream_chat(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
            **kwargs,
        ):
            yield chunk

    async def stream_chat(
        self,
        q: str,
        history: Optional[List[Dict[str, Any]]] = [],
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Потоковый чат через SSE /chat/completions."""
        sys_prompt = system_instruction or self.system_prompt
        temp = temperature if temperature and temperature > 0 else self.temperature
        max_t = max_tokens if max_tokens and max_tokens > 0 else self.max_tokens

        messages: List[Dict[str, str]] = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        source_history = history if history else self._history
        for item in source_history:
            role = item.get("role", "user")
            if role in ("model", "assistant"):
                role = "assistant"
            elif role != "system":
                role = "user"
            
            content = ""
            if "parts" in item:
                parts = item["parts"]
                if isinstance(parts, list) and parts:
                    p = parts[0]
                    content = p if isinstance(p, str) else p.get("text", "") if isinstance(p, dict) else ""
                elif isinstance(parts, str):
                    content = parts
            elif "content" in item:
                content = str(item["content"])

            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": q})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_t,
            "stream": True,
        }

        url = f"{self.base_url}/chat/completions"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, headers=self._headers(), json=payload) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"[OpenAICompat] Стрим HTTP {resp.status} от {url}: {err_text}")
                        yield f"Error HTTP {resp.status}"
                        return

                    async for raw_line in resp.content:
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"[OpenAICompat] Ошибка в потоке генерации: {e}")
            yield f"[Stream error: {e}]"
