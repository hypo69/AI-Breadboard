# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Client MCP Server
# =============================================================================
# Описание:
#   MCP-сервер на базе FastMCP, предоставляющий интерфейс к API бэкенда FastAPI
#   (чат, список медиафайлов, состояние qBittorrent).
#
# File: fastapi_mcp_server.py
# Project: ai-assistant
# Package: .mcp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import httpx
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from core.logger import logger
from core.utils.jjson import j_loads_ns

# Инициализация FastMCP сервера
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
        logger.warning(f"[fastapi_mcp_server] Ошибка чтения config.json, fallback к localhost:8000: {e}")
        return "http://localhost:8000"


@mcp.tool()
async def fastapi_chat(message: str) -> str:
    """Отправка сообщения в чат-роутер FastAPI backend."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{get_base_url()}/api/chat", json={"message": message})
            return response.text
    except Exception as e:
        logger.error(f"[fastapi_mcp_server] Ошибка fastapi_chat: {e}")
        return f"Ошибка запроса к /api/chat: {e}"


@mcp.tool()
async def fastapi_media_list() -> str:
    """Получение списка медиафайлов из медиа-роутера FastAPI."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{get_base_url()}/api/media")
            return response.text
    except Exception as e:
        logger.error(f"[fastapi_mcp_server] Ошибка fastapi_media_list: {e}")
        return f"Ошибка запроса к /api/media: {e}"


@mcp.tool()
async def fastapi_qbittorrent_info() -> str:
    """Получение информации о текущих торрентах из qBittorrent через FastAPI."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{get_base_url()}/api/torrents")
            return response.text
    except Exception as e:
        logger.error(f"[fastapi_mcp_server] Ошибка fastapi_qbittorrent_info: {e}")
        return f"Ошибка запроса к /api/torrents: {e}"


if __name__ == "__main__":
    logger.info("[fastapi_mcp_server] Запуск FastAPI FastMCP сервера...")
    mcp.run()
