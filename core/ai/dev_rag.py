# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG-индексация кодовой базы и документации
# =============================================================================
# Описание:
#   Построение RAG-индекса для технического контекста разработки.
#   Индексация файлов документации (.md) и исходного кода (.py).
#
# File: dev_rag.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import os
from pathlib import Path
from core.ai.gemini.rag import GeminiRAG
from core.logger import logger

# Путь к файлу индекса
DEV_RAG_DB = Path(__file__).parent.parent.parent / ".gemini" / "knowledge" / "dev_rag.db"

def _file_to_text(file_path: Path) -> str:
    """Извлечение текста из файла для векторизации.

    Args:
        file_path (Path): Путь к файлу.

    Returns:
        str: Содержимое файла.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        return f"Файл: {file_path.name}\nПуть: {file_path}\nСодержимое:\n{content}"
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {e}")
        return ""

def build_dev_rag(api_key: str) -> GeminiRAG:
    """Построение RAG-индекса для кода и документации.

    Индексирует файлы .py и .md из указанных директорий.

    Args:
        api_key (str): Ключ Gemini API.

    Returns:
        GeminiRAG: Индекс.
    """
    rag = GeminiRAG(api_key=api_key, db_path=str(DEV_RAG_DB))
    rag.clear()

    # Директории для индексации
    target_dirs = ["docs", "prompts", "core", "plugins"]
    docs = []

    for dir_name in target_dirs:
        for file_path in Path(dir_name).rglob("*"):
            if file_path.suffix in [".py", ".md"] and "__pycache__" not in str(file_path):
                text = _file_to_text(file_path)
                if text:
                    docs.append({
                        'id': str(file_path),
                        'text': text,
                        'meta': {'path': str(file_path), 'type': file_path.suffix}
                    })

    rag.add_documents(docs)
    logger.info(f"Индекс разработчика построен. Индексировано файлов: {len(docs)}")
    return rag

def get_dev_rag(api_key: str) -> GeminiRAG:
    """Получение индекса разработчика."""
    return GeminiRAG(api_key=api_key, db_path=DEV_RAG_DB)

def rag_search_tool(query: str, top_k: int = 3, api_key: str = '') -> str:
    """Семантический поиск по коду и документации через RAG-индекс.

    Args:
        query (str): Поисковый запрос.
        top_k (int): Количество результатов.
        api_key (str): Ключ Gemini API.

    Returns:
        str: JSON-строка со списком найденных файлов.
    """
    rag = get_dev_rag(api_key)
    if rag.count() == 0:
        return json.dumps({'error': 'Индекс разработчика пуст. Выполни rebuild_dev_rag'}, ensure_ascii=False)
    
    results = rag.search(query, top_k=top_k, threshold=0.3)
    return json.dumps(results, ensure_ascii=False, indent=2)
