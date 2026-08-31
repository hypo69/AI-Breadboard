# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Выполнить веб-поиск в Google через Gemini Search G
# =============================================================================
# Description:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к веб-поиску Google
#
# File: gemini_search_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from core.logger.logger import logger
from plugins.web_search.gemini_searcher import GeminiWebSearcher, GeminiKeyPool

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("Gemini-Search-Server")
except ImportError:
    FastMCP = None
    mcp = None

async def _run_gemini_search(query: str, model: str = "gemini-2.5-flash") -> str:
    try:
        searcher = GeminiWebSearcher()
        result_markdown = await searcher.search_and_extract(query=query, model=model)
        return result_markdown
    except Exception as e:
        logger.error(f"[gemini_search_mcp_server] Error поиска: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def _run_key_pool_status() -> str:
    try:
        pool = GeminiKeyPool()
        return json.dumps({
            "status": "ok",
            "total_keys": len(pool.api_keys),
            "active_key_masked": f"...{pool._current_key[-6:]}" if len(pool._current_key) >= 6 else "***"
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[gemini_search_mcp_server] Error статуса пула ключей: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

async def gemini_web_search(query: str, model: str = "gemini-2.5-flash") -> str:
    """Выполнить веб-поиск в Google через Gemini Search Grounding."""
    return await _run_gemini_search(query=query, model=model)

def gemini_key_pool_status() -> str:
    """Получить status пула API-ключей Gemini и активного ключа."""
    return _run_key_pool_status()

if mcp:
    mcp.tool()(gemini_web_search)
    mcp.tool()(gemini_key_pool_status)

if __name__ == "__main__":
    if mcp:
        mcp.run()
