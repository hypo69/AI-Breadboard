# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User dialogue indexing and semantic search
# =============================================================================
# Description:
#   Dialog indexing, caching, and semantic search across previously provided responses.
#
# File: user_rag.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from logger import logger
from src.ai.gemini.user_query_rag import index_user_query, search_user_context
from src.ai.gemini.approved_responses_store import save_approved_response
from src.user_manager.user_profile import get_recommendation_context

async def search_user_history(
    user_identifier: str,
    api_key: str,
    query: str,
    top_k: int = 2,
    threshold: float = 0.45,
    rag_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Поиск релевантного контекста из предшествующих обсуждений конкретной RAG базы.

    Args:
        user_identifier (str): Идентификатор пользователя.
        api_key (str): Ключ API для векторного поиска.
        query (str): Текст запроса.
        top_k (int): Количество результатов.
        threshold (float): Порог минимального сходства.
        rag_name (Optional[str]): Имя целевой RAG базы знаний (роли).

    Returns:
        List[Dict[str, Any]]: Найденные фрагменты обсуждения.
    """
    if not user_identifier or not api_key or len(query.strip()) < 5:
        return []

    try:
        results = await asyncio.to_thread(
            search_user_context, user_identifier, api_key, query, top_k, threshold, rag_name
        )
        return results or []
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка поиска контекста пользователя: {ex}")
        return []

async def get_user_preferences_context(user_identifier: str) -> str:
    """Возвращает текстовый контекст предпочтений пользователя.

    Args:
        user_identifier (str): Идентификатор пользователя.

    Returns:
        str: Текстовое представление предпочтений.
    """
    if not user_identifier:
        return ""
    try:
        pref = await asyncio.to_thread(get_recommendation_context, user_identifier)
        return pref or ""
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка чтения предпочтений пользователя: {ex}")
        return ""

def save_user_approved_response(
    user_identifier: str,
    query: str,
    chat_text: str,
    voice_text: str,
    rag_name: Optional[str] = None,
) -> bool:
    """Сохраняет одобренный пользователем ответ в постоянный архив JSON.

    Args:
        user_identifier (str): Идентификатор пользователя.
        query (str): Текст запроса.
        chat_text (str): Текст ответа в формате чата.
        voice_text (str): Текст ответа в формате озвучки.
        rag_name (Optional[str]): Имя целевой RAG базы знаний (роли).

    Returns:
        bool: Флаг успеха сохранения записи.
    """
    try:
        tags = ['tc']
        if rag_name and rag_name.strip():
            tags.append(rag_name.strip().lower())
        return save_approved_response(user_identifier, query, chat_text, voice_text, tags=tags)
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка сохранения ответа в архив: {ex}")
        return False

def index_user_interaction(
    user_identifier: str,
    api_key: str,
    query: str,
    content_to_index: str,
    rag_name: Optional[str] = None,
) -> bool:
    """Векторизует и сохраняет взаимодействие в персональный RAG индекс (по роли/имени).

    Args:
        user_identifier (str): Идентификатор пользователя.
        api_key (str): Ключ API для векторизации.
        query (str): Текст запроса пользователя.
        content_to_index (str): Содержимое для индексации.
        rag_name (Optional[str]): Имя целевой RAG базы знаний (роли).

    Returns:
        bool: Флаг успешного сохранения в индекс.
    """
    if not user_identifier or not api_key or not content_to_index.strip():
        return False
    try:
        return index_user_query(user_identifier, api_key, query, content_to_index, rag_name=rag_name)
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка индексации взаимодействия в RAG ({rag_name}): {ex}")
        return False
