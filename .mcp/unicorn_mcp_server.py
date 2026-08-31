# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Запуск сервиса Run-Unicorn.ps1 в фоновом режиме.
# =============================================================================
# Description:
#   MCP-сервер на базе FastMCP для управления сервисом Uvicorn / Unicorn
#
# File: unicorn_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from core.logger import logger

# Initialization FastMCP сервера
mcp = FastMCP("Unicorn-Manager")

# Путь к скрипту запуска
_ROOT = Path(__file__).resolve().parent.parent
_UNICORN_SCRIPT = _ROOT / "launchers" / "Run-Unicorn.ps1"
if not _UNICORN_SCRIPT.exists():
    _UNICORN_SCRIPT = _ROOT / "Run-Unicorn.ps1"

@mcp.tool()
async def unicorn_start() -> str:
    """Запуск сервиса Run-Unicorn.ps1 в фоновом режиме."""
    try:
        if not _UNICORN_SCRIPT.exists():
            return f"Файл скрипта не найден: {_UNICORN_SCRIPT}"
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_UNICORN_SCRIPT)],
            shell=True,
        )
        logger.info("[unicorn_mcp_server] Запущен процесс Run-Unicorn.ps1")
        return "Сервис Unicorn successfully запущен в фоновом режиме."
    except Exception as e:
        logger.error(f"[unicorn_mcp_server] Error запуска unicorn_start: {e}")
        return f"Error при запуске Unicorn: {e}"

@mcp.tool()
async def unicorn_stop() -> str:
    """Остановка процессов Uvicorn/Unicorn."""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "uvicorn.exe", "/T"], capture_output=True, text=True)
        logger.info("[unicorn_mcp_server] Выполнена команда остановки процессов uvicorn.exe")
        return "Команда остановки процесса Unicorn выполнена."
    except Exception as e:
        logger.error(f"[unicorn_mcp_server] Error остановки unicorn_stop: {e}")
        return f"Error при остановке Unicorn: {e}"

@mcp.tool()
async def unicorn_status() -> str:
    """Check текущего статуса работы процесса Unicorn (uvicorn.exe)."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq uvicorn.exe"],
            capture_output=True,
            text=True,
        )
        if "uvicorn.exe" in result.stdout:
            return "Сервис Unicorn (uvicorn.exe) активен и работает."
        return "Сервис Unicorn (uvicorn.exe) не запущен."
    except Exception as e:
        logger.error(f"[unicorn_mcp_server] Error unicorn_status: {e}")
        return f"Error проверки статуса: {e}"

if __name__ == "__main__":
    logger.info("[unicorn_mcp_server] Запуск Unicorn FastMCP сервера...")
    mcp.run()
