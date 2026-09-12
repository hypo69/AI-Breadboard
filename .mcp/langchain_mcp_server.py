# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Выполнить автономный поиск и решение задачи через 
# =============================================================================
# Description:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к ReAct-агенту AI Breadboard
#
# File: langchain_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from src.logger import logger
from src.ai.langchain_agent import MediaSearchAgent
from src.ai.langchain_tools import (
    web_search,
    rag_search,
    python_eval,
    file_read,
)

# Initialization FastMCP сервера
mcp = FastMCP("LangChain-Breadboard-Agent")

# Путь к конфигурации
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

@mcp.tool()
async def agent_query(query: str) -> str:
    """Выполнить автономный поиск и решение задачи через ReAct-агента.

    Args:
        query: Запрос пользователя.
    """
    try:
        agent = MediaSearchAgent(config_path=_CONFIG_PATH)
        result = await agent.search(query)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Error agent_query: {e}")
        return json.dumps({"action": "error", "message": str(e)}, ensure_ascii=False)

@mcp.tool()
async def agent_web_search(query: str) -> str:
    """Поиск актуальной информации в интернете через поисковый адаптер.

    Args:
        query: Поисковый запрос.
    """
    try:
        return await web_search.ainvoke(query)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Error agent_web_search: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def agent_rag_search(query: str, top_k: int = 5) -> str:
    """Семантический поиск по базе знаний RAG.

    Args:
        query: Поисковый запрос.
        top_k: Количество результатов.
    """
    try:
        return await rag_search.ainvoke({"query": query, "top_k": top_k})
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Error agent_rag_search: {e}")
        return json.dumps([], ensure_ascii=False)

@mcp.tool()
def agent_python_eval(code: str) -> str:
    """Выполнение математических выражений на Python.

    Args:
        code: Выражение для вычисления.
    """
    try:
        return python_eval.invoke(code)
    except Exception as e:
        logger.error(f"[langchain_mcp_server] Error agent_python_eval: {e}")
        return f"Error: {e}"

if __name__ == "__main__":
    logger.info("[langchain_mcp_server] Запуск LangChain Breadboard FastMCP сервера...")
    mcp.run()
