# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Manager for MCP client lifecycle and tool discovery
# =============================================================================
# Description:
#   Wrapper and lifecycle manager for Model Context Protocol (MCP) clients
#   supporting multiple server connections, tool discovery, and connection testing.
#
# File: mcp_client.py
# Project: ai-breadboard
# Package: src.ai.agents
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError:
    MultiServerMCPClient = None

from src.logger import logger
from src.utils.jjson import j_loads_ns


class MCPClientManager:
    """Manager for Model Context Protocol (MCP) client lifecycle and tools."""

    def __init__(self, config_path: str = "config.json") -> None:
        """Initialize MCPClientManager with configuration path.

        Args:
            config_path: Relative or absolute path to application config JSON file.
        """
        self.config_path = Path(config_path)
        self._client: Optional[Any] = None
        self._config: Optional[Any] = None

    async def __aenter__(self) -> MCPClientManager:
        """Context manager entry point connecting to enabled MCP servers.

        Returns:
            Self instance with initialized client.
        """
        logger.info("Initializing MCPClientManager")
        if not MultiServerMCPClient:
            logger.warning("[MCPClientManager] langchain_mcp_adapters not installed")
            return self

        try:
            self._config = j_loads_ns(self.config_path)
            langchain_cfg = getattr(self._config, "langchain", None)
            mcp_servers_raw = getattr(langchain_cfg, "mcp_servers", None) if langchain_cfg else None

            if not mcp_servers_raw:
                logger.info("[MCPClientManager] No MCP servers configured in langchain.mcp_servers")
                return self

            connections: Dict[str, Dict[str, Any]] = {}

            if isinstance(mcp_servers_raw, dict):
                items = mcp_servers_raw.items()
            elif hasattr(mcp_servers_raw, "__dict__"):
                items = mcp_servers_raw.__dict__.items()
            else:
                items = []

            for server_name, server_cfg in items:
                # Check enabled flag
                is_enabled = getattr(server_cfg, "enabled", True) if not isinstance(server_cfg, dict) else server_cfg.get("enabled", True)
                if not is_enabled:
                    continue

                conn_def = self._build_connection_def(server_cfg)
                if conn_def:
                    connections[server_name] = conn_def

            if connections:
                logger.info(f"[MCPClientManager] Initializing MultiServerMCPClient with servers: {list(connections.keys())}")
                self._client = MultiServerMCPClient(connections=connections)
            else:
                logger.info("[MCPClientManager] No enabled MCP server configurations found")

        except Exception as e:
            logger.error(f"[MCPClientManager] Error initializing MCP servers: {e}")

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit point cleaning up MCP client sessions."""
        logger.info("Shutting down MCPClientManager")
        self._client = None

    @staticmethod
    def _build_connection_def(server_cfg: Any) -> Optional[Dict[str, Any]]:
        """Construct connection definition dictionary for MultiServerMCPClient.

        Args:
            server_cfg: Server configuration dictionary or SimpleNamespace.

        Returns:
            Dictionary suitable for MultiServerMCPClient connection entry or None.
        """
        if isinstance(server_cfg, dict):
            transport = server_cfg.get("transport", "stdio")
            command = server_cfg.get("command", "")
            args = server_cfg.get("args", [])
            env = server_cfg.get("env")
            url = server_cfg.get("url", "")
        else:
            transport = getattr(server_cfg, "transport", "stdio")
            command = getattr(server_cfg, "command", "")
            args = getattr(server_cfg, "args", [])
            env = getattr(server_cfg, "env", None)
            url = getattr(server_cfg, "url", "")

        if transport in ("sse", "streamable_http", "http"):
            if not url:
                return None
            return {
                "url": url,
                "transport": "sse" if transport == "sse" else "streamable_http",
            }
        else:
            # stdio transport
            if not command:
                return None
            conn: Dict[str, Any] = {
                "command": command,
                "args": list(args) if args else [],
                "transport": "stdio",
            }
            if env:
                conn["env"] = dict(env) if isinstance(env, dict) or hasattr(env, "__dict__") else {}
            return conn

    async def get_tools(self) -> List[Any]:
        """Get LangChain-compatible tools from all connected MCP servers.

        Returns:
            List of BaseTool instances provided by MCP servers.
        """
        if self._client:
            try:
                return await self._client.get_tools()
            except Exception as e:
                logger.warning(f"[MCPClientManager] Error retrieving MCP tools: {e}")
        return []

    @classmethod
    async def test_server_connection(cls, server_id: str, server_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to a specific MCP server and discover its tools.

        Args:
            server_id: Identifier of the server.
            server_cfg: Configuration dictionary for the server.

        Returns:
            Dictionary with status, tool list, schema definitions, and latency info.
        """
        if not MultiServerMCPClient:
            return {
                "status": "error",
                "message": "langchain_mcp_adapters package is not installed in the environment",
                "tools": [],
                "latency_ms": 0,
            }

        conn_def = cls._build_connection_def(server_cfg)
        if not conn_def:
            return {
                "status": "error",
                "message": f"Invalid server configuration for '{server_id}'. Missing command or URL.",
                "tools": [],
                "latency_ms": 0,
            }

        start_time = time.perf_counter()
        try:
            client = MultiServerMCPClient(connections={server_id: conn_def})
            async with client:
                tools = await asyncio.wait_for(client.get_tools(), timeout=15.0)

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            tools_info = []
            for t in tools:
                tool_dict: Dict[str, Any] = {
                    "name": getattr(t, "name", str(t)),
                    "description": getattr(t, "description", ""),
                    "args_schema": getattr(t, "args", {}),
                }
                if hasattr(t, "args_schema") and t.args_schema:
                    try:
                        tool_dict["args_schema"] = t.args_schema.schema() if hasattr(t.args_schema, "schema") else str(t.args_schema)
                    except Exception:
                        pass
                tools_info.append(tool_dict)

            return {
                "status": "ok",
                "message": f"Successfully connected to '{server_id}' and discovered {len(tools_info)} tools.",
                "server_id": server_id,
                "tools_count": len(tools_info),
                "tools": tools_info,
                "latency_ms": latency_ms,
            }

        except asyncio.TimeoutError:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "status": "error",
                "message": f"Connection to '{server_id}' timed out after 15 seconds.",
                "tools": [],
                "latency_ms": latency_ms,
            }
        except Exception as ex:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"[MCPClientManager] Test connection failed for '{server_id}': {ex}")
            return {
                "status": "error",
                "message": str(ex),
                "tools": [],
                "latency_ms": latency_ms,
            }
