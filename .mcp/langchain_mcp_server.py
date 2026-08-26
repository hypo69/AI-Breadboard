# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: LangChain Breadboard MCP Server
# =============================================================================
# Описание:
#   MCP-сервер на базе FastMCP, предоставляющий доступ к ReAct-агенту AI Breadboard
#   и отдельным инструментам LangChain (веб-поиск, RAG, вычисления Python).
#
# File: langchain_mcp_server.py
# Project: aibreadboard
# Package: .mcp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from core.logger import logger
from core.ai.langchain_agent import MediaSearchAgent
from core.ai.langchain_tools import (
    web_search,
    rag_search,
    python_eval,
    file_read,
)

# Инициализация FastMCP сервера
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
        logger.error(f"[langchain_mcp_server] Ошибка agent_query: {e}")
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
        logger.error(f"[langchain_mcp_server] Ошибка agent_web_search: {e}")
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
        logger.error(f"[langchain_mcp_server] Ошибка agent_rag_search: {e}")
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
        logger.error(f"[langchain_mcp_server] Ошибка agent_python_eval: {e}")
        return f"Ошибка: {e}"


if __name__ == "__main__":
    logger.info("[langchain_mcp_server] Запуск LangChain Breadboard FastMCP сервера...")
    mcp.run()
