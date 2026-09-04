# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Search for current information on the internet
# =============================================================================
# Description:
#   Набор нативных LangChain-инструментов для AI-агентов.
#
# File: langchain_tools.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict

try:
    from langchain_core.tools import tool
except ImportError:
    class DummyTool:
        def __init__(self, func):
            self.func = func
            self.__name__ = getattr(func, '__name__', 'DummyTool')
            self.__doc__ = getattr(func, '__doc__', '')

        def invoke(self, input_data=None, **kwargs):
            if isinstance(input_data, dict):
                return self.func(**input_data)
            elif input_data is not None:
                return self.func(input_data, **kwargs)
            return self.func(**kwargs)

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    def tool(func=None, *args, **kwargs):
        if func is not None:
            return DummyTool(func)
        return lambda f: DummyTool(f)

from src.logger import logger
from header import __root__

@tool
async def web_search(query: str) -> str:
    """Поиск актуальной информации в интернете через поисковые адаптеры.

    Args:
        query: Поисковый запрос.
    """
    try:
        from src.ai.unified_chat import get_chat_model
        model = get_chat_model()
        response = await model.ask(f"Найди в интернете актуальную информацию по запросу: {query}")
        return response
    except Exception as e:
        logger.error(f"[langchain_tools] Error веб-поиска: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
async def rag_search(query: str, top_k: int = 5) -> str:
    """Семантический поиск по локальной базе знаний и документам.

    Args:
        query: Запрос для семантического поиска.
        top_k: Максимальное количество фрагментов.
    """
    try:
        from src.rag.rag_manager import rag_manager
        results = await rag_manager.search(query=query, limit=top_k)
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[langchain_tools] Error RAG-поиска: {e}")
        return json.dumps([], ensure_ascii=False)

@tool
def python_eval(code: str) -> str:
    """Безопасное выполнение простых математических и строковых выражений Python.

    Args:
        code: Выражение или фрагмент кода для вычисления.
    """
    try:
        allowed_globals = {"__builtins__": {"abs": abs, "min": min, "max": max, "sum": sum, "round": round, "len": len}}
        result = eval(code, allowed_globals, {})
        return str(result)
    except Exception as e:
        return f"Error вычисления: {e}"

@tool
def file_read(file_path: str) -> str:
    """Чтение содержимого текстового файла проекта.

    Args:
        file_path: Относительный или абсолютный путь к файлу.
    """
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = __root__ / p
        if not p.exists() or not p.is_file():
            return f"Файл не найден: {file_path}"
        return p.read_text(encoding="utf-8", errors="replace")[:10000]
    except Exception as e:
        return f"Error чтения файла: {e}"

# --- Заглушки для обратной совместимости ---

@tool
async def search_torrents(query: str) -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps([], ensure_ascii=False)

@tool
async def get_movie_metadata(title: str) -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps({}, ensure_ascii=False)

@tool
def get_streaming_sources(title: str) -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps({}, ensure_ascii=False)

@tool
def build_player_url(url: str, provider: str = "") -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps({}, ensure_ascii=False)

@tool
async def add_torrent_download(url: str, source: str = "", title: str = "") -> str:
    """Устаревший инструмент (артефакт удален)."""
    return "Функциональность торрентов удалена."
