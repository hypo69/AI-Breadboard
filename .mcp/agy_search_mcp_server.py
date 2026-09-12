# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Выполнить веб-поиск через агентный поиск Google An
# =============================================================================
# Description:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к поиску в интернете
#
# File: agy_search_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from src.logger.logger import logger
from plugins.web_search.agy_searcher import AgyWebSearcher

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("Antigravity-Search-Server")
except ImportError:
    FastMCP = None
    mcp = None

async def _run_agy_search(query: str, model: str = "agy-flash") -> str:
    try:
        searcher = AgyWebSearcher(model_id=model)
        result = await searcher.search_and_extract(query=query)
        return result
    except Exception as e:
        logger.error(f"[agy_search_mcp_server] Error agy_web_search: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

async def agy_web_search(query: str, model: str = "agy-flash") -> str:
    """Выполнить веб-поиск через агентный поиск Google Antigravity."""
    return await _run_agy_search(query=query, model=model)

if mcp:
    mcp.tool()(agy_web_search)

if __name__ == "__main__":
    if mcp:
        mcp.run()
