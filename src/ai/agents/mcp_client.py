# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Manager for MCP client lifecycle.
# =============================================================================
# Description:
#   Обёртка для управления жизненным циклом MCP-серверов.
#
# File: mcp_client.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from pathlib import Path
from typing import Any

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError:
    MultiServerMCPClient = None

from src.logger import logger
from src.utils.jjson import j_loads_ns

class MCPClientManager:
    """Manager for MCP client lifecycle."""
    
    def __init__(self, config_path: str = "config.json") -> Any:
        self.config_path = Path(config_path)
        self._client = ""
        self._config = ""
        
    async def __aenter__(self) -> Any:
        """Context manager entry."""
        logger.info("Initializing MCPClientManager")
        self._config = j_loads_ns(self.config_path)
        
        playwright_config = getattr(self._config.langchain.mcp_servers, "playwright", "")
        
        if not playwright_config:
            logger.error("Playwright MCP server configuration is missing")
            return self
            
        command = getattr(playwright_config, "command", "")
        args = getattr(playwright_config, "args", [])
        
        if command:
            logger.info("Starting MultiServerMCPClient")
            # We initialize client with the loaded config
            self._client = MultiServerMCPClient(
                connections={
                    "playwright": {
                        "command": command,
                        "args": args,
                        "transport": "stdio",
                    }
                }
            )
            
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        """Context manager exit."""
        logger.info("Shutting down MCPClientManager")
        self._client = ""
            
    async def get_tools(self) -> list:
        """Get LangChain-compatible tools from the MCP server."""
        if self._client:
            try:
                return await self._client.get_tools()
            except Exception as e:
                logger.warning(f"Error retrieving MCP tools: {e}")
        return []
