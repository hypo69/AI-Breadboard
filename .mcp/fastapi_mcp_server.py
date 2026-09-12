# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Получение базового URL FastAPI-сервера из config.j
# =============================================================================
# Description:
#   MCP-сервер на базе FastMCP, предоставляющий интерфейс к API бэкенда FastAPI
#
# File: fastapi_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import httpx
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from src.logger import logger
from src.utils.jjson import j_loads_ns

# Initialization FastMCP сервера
mcp = FastMCP("FastAPI-Media-Client")

# Путь к конфигурации сервера
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

def get_base_url() -> str:
    """Получение базового URL FastAPI-сервера из config.json."""
    try:
        cfg = j_loads_ns(_CONFIG_PATH)
        server_cfg = getattr(cfg, "server", object())
        host = getattr(server_cfg, "host", "localhost")
        if host == "0.0.0.0":
            host = "localhost"
        port = getattr(server_cfg, "port", 8000)
        return f"http://{host}:{port}"
    except Exception as e:
        logger.warning(f"[fastapi_mcp_server] Error чтения config.json, fallback к localhost:8000: {e}")
        return "http://localhost:8000"

@mcp.tool()
async def fastapi_chat(message: str) -> str:
    """Отправка сообщения в чат-роутер FastAPI backend."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{get_base_url()}/api/chat", json={"message": message})
            return response.text
    except Exception as e:
        logger.error(f"[fastapi_mcp_server] Error fastapi_chat: {e}")
        return f"Error запроса к /api/chat: {e}"

@mcp.tool()
async def fastapi_media_list() -> str:
    """Получение списка медиафайлов из медиа-роутера FastAPI."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{get_base_url()}/api/media")
            return response.text
    except Exception as e:
        logger.error(f"[fastapi_mcp_server] Error fastapi_media_list: {e}")
        return f"Error запроса к /api/media: {e}"

@mcp.tool()
async def fastapi_qbittorrent_info() -> str:
    """Получение информации о текущих торрентах из qBittorrent через FastAPI."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{get_base_url()}/api/torrents")
            return response.text
    except Exception as e:
        logger.error(f"[fastapi_mcp_server] Error fastapi_qbittorrent_info: {e}")
        return f"Error запроса к /api/torrents: {e}"

if __name__ == "__main__":
    logger.info("[fastapi_mcp_server] Запуск FastAPI FastMCP сервера...")
    mcp.run()
