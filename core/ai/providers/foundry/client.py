# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Client for working with Microsoft AI Foundry
# =============================================================================
# Description:
#   Implementation of async client for interaction with Microsoft AI Foundry API.
#   Provides text generation, model loading, and model listing capabilities.
#
# File: foundry.py
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

class FoundryClient:
    """Client for working with Microsoft AI Foundry."""
    
    def __init__(self, base_url: Optional[str] = "") -> None:
        """Initialize client.

        Args:
            base_url (Optional[str]): Base URL of Foundry API.
        """
        from core.config import ai_cfg
        self.base_url = base_url or getattr(ai_cfg, "foundry_base_url", "http://localhost:54837")
        self.api_key = os.getenv("FOUNDRY_API_KEY", "")
        self.session: Any = False
        logger.info(f"FoundryClient initialized with base_url={self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
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
        """Generate text through Foundry API.

        Args:
            prompt (str): Input query (used if messages is empty).
            model (str): Model ID.
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum number of tokens.
            messages (Optional[List[Dict[str, str]]]): List of dialog messages.

        Returns:
            Dict[str, Any]: Result as dictionary.
        """
        session = await self._get_session()
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        if not messages:
            messages = [{"role": "user", "content": prompt}]
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            logger.info(f"Sending request to Foundry API: {url}")
            async with session.post(url, json=payload, headers=headers, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return {"success": True, "content": content}
                    return {"success": False, "error": "Empty choices in response"}
                else:
                    error_text = await response.text()
                    logger.error(f"Foundry API error status {response.status}: {error_text}")
                    if "model_not_loaded" in error_text.lower() or "not loaded" in error_text.lower() or response.status == 404:
                        return {"success": False, "error_code": "model_not_loaded", "error": error_text}
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"Exception during generate_text: {e}")
            return {"success": False, "error": str(e)}

    async def load_model(self, model_id: str) -> Dict[str, Any]:
        """Load model on Foundry server.

        Args:
            model_id (str): Model ID to load.

        Returns:
            Dict[str, Any]: Load result.
        """
        session = await self._get_session()
        url = f"{self.base_url}/models/load/{model_id}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        try:
            async with session.get(url, headers=headers, timeout=120) as response:
                if response.status in (200, 201):
                    return {"success": True}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_models(self) -> List[str]:
        """Get list of available models.

        Returns:
            List[str]: List of model IDs.
        """
        session = await self._get_session()
        url = f"{self.base_url}/v1/models"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get("data", []):
                        model_id = model.get("id")
                        if model_id:
                            models.append(model_id)
                    return models
                else:
                    error_text = await response.text()
                    logger.error(f"Foundry get_models API error {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Exception during Foundry get_models: {e}")
            return []

    async def close(self) -> None:
        """Close client session."""
        if self.session and not self.session.closed:
            await self.session.close()
