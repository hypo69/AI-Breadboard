# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модуль RAG пользовательских ответов (User RAG)
# =============================================================================
# Описание:
#   Индексация диалогов, кэширование и семантический поиск по ранее данным ответам
#   пользователя и его профилю предпочтений.
#
# File: user_rag.py
# Project: ai-assistant
# Package: core.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from core.logger import logger
from core.ai.gemini.user_query_rag import index_user_query, search_user_context
from core.ai.gemini.chat_response_store import save_approved_response
from core.user_manager.user_profile import get_recommendation_context


async def search_user_history(
    user_identifier: str,
    api_key: str,
    query: str,
    top_k: int = 2,
    threshold: float = 0.45
) -> List[Dict[str, Any]]:
    """
    ## hypo69 docblock
    Ищет релевантный контекст из предыдущих обсуждений пользователя.

    Args:
        user_identifier (str): Идентификатор пользователя.
        api_key (str): Ключ API для векторизации.
        query (str): Текст запроса.
        top_k (int): Число результатов.
        threshold (float): Порог схожести.

    Returns:
        List[Dict[str, Any]]: Найденные фрагменты обсуждений.
    """
    if not user_identifier or not api_key or len(query.strip()) < 5:
        return []

    try:
        results = await asyncio.to_thread(
            search_user_context, user_identifier, api_key, query, top_k, threshold
        )
        return results or []
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка поиска контекста пользователя: {ex}")
        return []


async def get_user_preferences_context(user_identifier: str) -> str:
    """
    ## hypo69 docblock
    Возвращает текстовый контекст предпочтений пользователя.
    """
    if not user_identifier:
        return ""
    try:
        pref = await asyncio.to_thread(get_recommendation_context, user_identifier)
        return pref or ""
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка чтения предпочтений: {ex}")
        return ""


def save_user_approved_response(
    user_identifier: str,
    query: str,
    chat_text: str,
    voice_text: str
) -> bool:
    """
    ## hypo69 docblock
    Сохраняет одобренный ответ в постоянное JSON-хранилище архива.
    """
    try:
        return save_approved_response(user_identifier, query, chat_text, voice_text)
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка сохранения ответа в архив: {ex}")
        return False


def index_user_interaction(
    user_identifier: str,
    api_key: str,
    query: str,
    content_to_index: str
) -> bool:
    """
    ## hypo69 docblock
    Векторизует и сохраняет взаимодействие в FAISS-индекс пользователя.
    """
    if not user_identifier or not api_key or not content_to_index.strip():
        return False
    try:
        return index_user_query(user_identifier, api_key, query, content_to_index)
    except Exception as ex:
        logger.error(f"[UserRAG] Ошибка индексации взаимодействия: {ex}")
        return False
