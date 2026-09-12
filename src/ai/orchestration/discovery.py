# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Dynamic Provider and Backend Discovery
# =============================================================================
# Description:
#   Probes running local daemons (Foundry Local, Ollama), hardware accelerators,
#   Windows AI components, and API credentials to build the live capability map.
#
# File: discovery.py
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

import os
import asyncio
import aiohttp
from typing import Any, Dict, List
from src.logger import logger
from .hardware import probe_hardware, HardwareProfile
from src.ai.providers.windows_ai import probe_windows_ai_components


class DiscoveryEngine:
    """Discovers available backends, models, and hardware capabilities dynamically."""

    def __init__(
        self,
        foundry_base_url: str = "http://localhost:54837",
        ollama_base_url: str = "http://localhost:11434",
    ):
        self.foundry_base_url = foundry_base_url
        self.ollama_base_url = ollama_base_url

    async def probe_foundry_local(self) -> Dict[str, Any]:
        """Probe Foundry Local OpenAI-compatible REST server."""
        url = f"{self.foundry_base_url}/v1/models"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1.5)) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m.get("id") for m in data.get("data", []) if "id" in m]
                        return {"available": True, "models": models, "url": self.foundry_base_url}
        except Exception:
            pass
        return {"available": False, "models": [], "url": self.foundry_base_url}

    async def probe_ollama(self) -> Dict[str, Any]:
        """Probe local Ollama daemon."""
        url = f"{self.ollama_base_url}/api/tags"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1.5)) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m.get("name") for m in data.get("models", []) if "name" in m]
                        return {"available": True, "models": models, "url": self.ollama_base_url}
        except Exception:
            pass
        return {"available": False, "models": [], "url": self.ollama_base_url}

    def probe_cloud_credentials(self) -> Dict[str, bool]:
        """Check presence of cloud API keys."""
        return {
            "gemini": bool(os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        }

    async def run_full_discovery(self) -> Dict[str, Any]:
        """Perform comprehensive discovery across all local and cloud backends.

        Returns:
            Dict[str, Any]: Aggregated discovery result.
        """
        hardware = probe_hardware()
        win_ai = probe_windows_ai_components()
        foundry_task = self.probe_foundry_local()
        ollama_task = self.probe_ollama()

        foundry_res, ollama_res = await asyncio.gather(foundry_task, ollama_task)
        cloud_creds = self.probe_cloud_credentials()

        return {
            "hardware": hardware.to_dict(),
            "windows_ai": win_ai,
            "foundry_local": foundry_res,
            "ollama": ollama_res,
            "cloud_providers": cloud_creds,
        }
