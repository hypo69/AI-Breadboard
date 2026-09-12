# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Вспомогательный Module для работы с конфигурацией 
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: config_helper.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Вспомогательный Module для работы с конфигурацией в MCP серверах.

Предоставляет кроссплатформенные функции для работы с config.json и путями.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

def get_project_root() -> Path:
    """
    Получить корень проекта.
    
    Поиск ведется по наличию config.json или main.py.
    """
    # Начинаем от директории .mcp
    current = Path(__file__).parent.parent
    
    # Проверяем, находимся ли мы уже в корне
    if (current / "config.json").exists() or (current / "main.py").exists():
        return current
    
    # Проверяем переменную окружения
    if "AIBREADBOARD_DIR" in os.environ:
        return Path(os.environ["AIBREADBOARD_DIR"])
    
    # Fallback - текущая директория
    return Path.cwd()

def load_config() -> Dict[str, Any]:
    """
    Загрузить конфигурацию проекта.
    
    Returns:
        Dictionary конфигурации из config.json
    """
    config_path = get_project_root() / "config.json"
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Error чтения config.json: {e}")
        return {}

def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Получить значение из конфигурации используя нотацию точек.
    
    Args:
        key_path: Путь ключей через точку (например: "server.port")
        default: Значение по умолчанию
    
    Returns:
        Значение или default
    """
    config = load_config()
    keys = key_path.split(".")
    
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

def get_server_url() -> str:
    """
    Получить базовый URL сервера FastAPI.
    
    Returns:
        URL в формате http://host:port
    """
    host = get_config_value("server.host", "localhost")
    port = get_config_value("server.port", 8000)
    
    # Если host 0.0.0.0, использовать localhost
    if host == "0.0.0.0":
        host = "localhost"
    
    # Проверить SSL
    use_ssl = get_config_value("server.use_ssl", False)
    protocol = "https" if use_ssl else "http"
    
    return f"{protocol}://{host}:{port}"

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Получить переменную окружения.
    
    Приоритет: система > .env > default
    
    Args:
        key: Имя переменной
        default: Значение по умолчанию
    
    Returns:
        Значение или None
    """
    # 1. Системная переменная
    if key in os.environ:
        return os.environ[key]
    
    # 2. Из .env файла
    env_file = get_project_root() / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        env_key, env_value = line.split("=", 1)
                        if env_key.strip() == key:
                            return env_value.strip().strip('"').strip("'")
        except Exception:
            pass
    
    # 3. Default
    return default

def get_certs_dir() -> Path:
    """
    Получить директорию SSL сертификатов (кроссплатформенно).
    
    Returns:
        Path к директории сертификатов
    """
    if sys.platform == "win32":
        return Path.home() / ".certs"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Certs"
    else:
        # Linux
        return Path.home() / ".local" / "share" / "ca-certificates"

def get_data_dir() -> Path:
    """
    Получить директорию данных приложения (кроссплатформенно).
    
    Returns:
        Path к директории данных
    """
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(localappdata) / "AI-Breadboard"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AI-Breadboard"
    else:
        # Linux
        return Path.home() / ".local" / "share" / "AI-Breadboard"

def is_port_open(host: str = "127.0.0.1", port: int = 8000, timeout: float = 1.0) -> bool:
    """
    Проверить, открыт ли порт.
    
    Args:
        host: IP адрес
        port: Номер порта
        timeout: Timeout для подключения
    
    Returns:
        True если порт открыт, False иначе
    """
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

# Экспортируемые функции
__all__ = [
    "get_project_root",
    "load_config",
    "get_config_value",
    "get_server_url",
    "get_env_var",
    "get_certs_dir",
    "get_data_dir",
    "is_port_open",
]
