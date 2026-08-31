# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Клиент для работы с Ollama."""
#
# File: ollama.py
# Project: ai-breadboard
# Package: core.clients
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import aiohttp
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class OllamaClient:
    """Клиент для работы с Ollama."""
    
    def __init__(self, base_url: Optional[str] = "") -> None:
        """Initialization клиента."""
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.session: Any = False
        logger.info(f"OllamaClient initialized with base_url={self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        messages: Optional[List[Dict[str, str]]] = [],
    ) -> Dict[str, Any]:
        """Генерация текста через OpenAI-совместимый API Ollama."""
        session = await self._get_session()
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
        }
            
        if not messages:
            messages = [{"role": "user", "content": prompt}]
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            logger.info(f"Sending request to Ollama API: {url}")
            async with session.post(url, json=payload, headers=headers, timeout=120) as response:
                if response.status == 200:
                    data = await response.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return {"success": True, "content": content}
                    return {"success": False, "error": "Empty choices in response"}
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error status {response.status}: {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"Exception during generate_text: {e}")
            return {"success": False, "error": str(e)}

    async def close(self) -> None:
        """Closing сессии клиента."""
        if self.session and not self.session.closed:
            await self.session.close()
