# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Пример MCP сервера с кроссплатформенной поддержкой
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: example_mcp_server.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Пример MCP сервера с кроссплатформенной поддержкой.

Этот файл показывает рекомендуемые паттерны для написания MCP серверов
которые работают на Windows, Linux и macOS без изменений.

Использование:
    python .mcp/example_mcp_server.py
    python3 .mcp/example_mcp_server.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Добавить корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP

# Импортировать кроссплатформенный вспомогательный Module
try:
    from .config_helper import (
        get_project_root,
        load_config,
        get_config_value,
        get_server_url,
        get_env_var,
        get_certs_dir,
        get_data_dir,
        is_port_open,
    )
except ImportError:
    # Fallback если импорт не сработал
    from config_helper import (
        get_project_root,
        load_config,
        get_config_value,
        get_server_url,
        get_env_var,
        get_certs_dir,
        get_data_dir,
        is_port_open,
    )

try:
    from core.logger import logger
except ImportError:
    # Fallback логирование если Module недоступен
    class SimpleLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = SimpleLogger()

# Initialization FastMCP сервера
mcp = FastMCP("Example-Server")

# ============================================================================
# Examples КРОССПЛАТФОРМЕННЫХ ФУНКЦИЙ
# ============================================================================

@mcp.tool()
def get_project_info() -> str:
    """
    Получить информацию о проекте (кроссплатформенно).
    
    Returns:
        JSON со сведениями о проекте
    """
    try:
        root = get_project_root()
        config = load_config()
        
        info = {
            "project_root": str(root),
            "platform": sys.platform,
            "python_version": sys.version,
            "config_exists": (root / "config.json").exists(),
            "env_exists": (root / ".env").exists(),
            "server_url": get_server_url(),
        }
        
        return str(info)
    except Exception as e:
        logger.error(f"Error getting project info: {e}")
        return f"Error: {e}"

@mcp.tool()
def get_directories() -> str:
    """
    Получить важные директории (кроссплатформенно).
    
    Returns:
        JSON с путями до директорий
    """
    try:
        dirs = {
            "project_root": str(get_project_root()),
            "certs_dir": str(get_certs_dir()),
            "data_dir": str(get_data_dir()),
            "home": str(Path.home()),
        }
        
        return str(dirs)
    except Exception as e:
        logger.error(f"Error getting directories: {e}")
        return f"Error: {e}"

@mcp.tool()
def check_server_status() -> str:
    """
    Проверить status сервера (кроссплатформенно).
    
    Returns:
        JSON со статусом сервера
    """
    try:
        server_url = get_server_url()
        port = get_config_value("server.port", 8000)
        host = "127.0.0.1"  # Проверяем локально
        
        is_open = is_port_open(host, port)
        
        status = {
            "server_url": server_url,
            "port": port,
            "is_open": is_open,
            "status": "Running" if is_open else "Not responding",
        }
        
        return str(status)
    except Exception as e:
        logger.error(f"Error checking server status: {e}")
        return f"Error: {e}"

@mcp.tool()
def read_config_value(key_path: str) -> str:
    """
    Прочитать значение из конфигурации.
    
    Args:
        key_path: Путь ключей через точку (например: "server.port")
    
    Returns:
        Значение или Error
    """
    try:
        value = get_config_value(key_path)
        return f"Value for '{key_path}': {value}"
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return f"Error: {e}"

@mcp.tool()
def read_env_variable(var_name: str) -> str:
    """
    Прочитать переменную окружения.
    
    Args:
        var_name: Имя переменной
    
    Returns:
        Значение или сообщение что не найдено
    """
    try:
        value = get_env_var(var_name)
        if value:
            return f"Environment variable '{var_name}': {value}"
        else:
            return f"Environment variable '{var_name}' not found"
    except Exception as e:
        logger.error(f"Error reading env variable: {e}")
        return f"Error: {e}"

@mcp.tool()
def list_certs() -> str:
    """
    List SSL сертификатов в кроссплатформенной директории.
    
    Returns:
        List файлов сертификатов
    """
    try:
        certs_dir = get_certs_dir()
        
        if not certs_dir.exists():
            return f"Certs directory does not exist: {certs_dir}"
        
        certs = list(certs_dir.glob("*.pem")) + list(certs_dir.glob("*.crt"))
        
        result = f"Certificates in {certs_dir}:\n"
        for cert in certs:
            result += f"  - {cert.name}\n"
        
        return result if certs else f"No certificates found in {certs_dir}"
    except Exception as e:
        logger.error(f"Error listing certs: {e}")
        return f"Error: {e}"

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Главная function запуска сервера"""
    logger.info("Starting Example MCP Server")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
