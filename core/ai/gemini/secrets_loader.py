# -*- coding: utf-8 -*-
"""Модуль загрузки API ключей Gemini из secrets.json."""

import json
from pathlib import Path
from typing import Dict, List, Tuple

# Путь к файлу secrets.json относительно корня проекта
_SECRETS_FILE = Path(__file__).parent / 'secrets.json'


def load_secrets() -> Dict[str, str]:
    """
    Загружает API ключи из secrets.json.
    
    Returns:
        Dict[str, str]: Словарь email -> API_key
    """
    if not _SECRETS_FILE.exists():
        return {}
    
    try:
        content = _SECRETS_FILE.read_text(encoding='utf-8')
        return json.loads(content)
    except Exception as ex:
        print(f"Ошибка загрузки secrets.json: {ex}")
        return {}


def get_all_keys() -> List[str]:
    """
    Возвращает список всех API ключей.
    
    Returns:
        List[str]: Список API ключей
    """
    secrets = load_secrets()
    return list(secrets.values())


def get_all_key_names() -> List[str]:
    """
    Возвращает список всех имён ключей (email).
    
    Returns:
        List[str]: Список имён ключей
    """
    secrets = load_secrets()
    return list(secrets.keys())


def get_key_by_name(name: str) -> str | None:
    """
    Возвращает API ключ по имени.
    
    Args:
        name: Имя ключа (email)
        
    Returns:
        str | None: API ключ или None если не найден
    """
    secrets = load_secrets()
    return secrets.get(name)


def load_api_keys(names: List[str] = []) -> Tuple[List[str], List[str], List[str]]:
    """
    Возвращает (api_keys, key_names, key_names) отсортированные по last_run.
    Фильтрует: только status == 'active' и не забаненные (дневная квота).
    
    Args:
        names: Опциональный список имён; если None — берёт все из файла.
        
    Returns:
        Tuple[List[str], List[str], List[str]]: (api_keys, key_names, key_names)
    """
    from core.secrets.api_key_state import load_api_keys as state_load_api_keys
    
    # Используем существующую функцию, но передаём имена из secrets.json
    all_names = get_all_key_names()
    
    if names:
        # Фильтруем только имена, которые есть в secrets.json
        names = [n for n in names if n in all_names]
    
    return state_load_api_keys(names)
