# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Выполнение поиска через GeminiCliWebSearcher.
# =============================================================================
# Description:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к веб-поиску
#
# File: gemini_cli_search_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

from core.logger import logger
from plugins.web_search.gemini_cli_searcher import GeminiCliWebSearcher

if FastMCP:
    mcp = FastMCP("Gemini-CLI-Search-Server")
else:
    mcp = None

async def _run_gemini_cli_search(query: str, model: str = "gemini-3.1-flash-lite") -> str:
    """Выполнение поиска через GeminiCliWebSearcher."""
    try:
        searcher = GeminiCliWebSearcher(model_id=model)
        result_markdown = await searcher.search_and_extract(query=query, model=model)
        return result_markdown
    except Exception as e:
        logger.error(f"[gemini_cli_search_mcp_server] Error поиска: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

async def gemini_cli_web_search(query: str, model: str = "gemini-3.1-flash-lite") -> str:
    """Выполнить веб-поиск через локальный терминальный агент Google Gemini CLI.

    Args:
        query: Поисковый запрос пользователя.
        model: Идентификатор модели (по умолчанию 'gemini-3.1-flash-lite').
    """
    return await _run_gemini_cli_search(query=query, model=model)

if mcp:
    mcp.tool()(gemini_cli_web_search)

if __name__ == "__main__":
    if mcp:
        mcp.run()
