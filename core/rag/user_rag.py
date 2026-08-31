# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User dialogue indexing and semantic search
# =============================================================================
# Description:
#   Dialog indexing, caching, and semantic search across previously provided responses.
#
# File: user_rag.py
# Project: ai-breadboard
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
    """Search for relevant context from previous user discussions.

    Args:
        user_identifier (str): User identifier.
        api_key (str): API key for vectorization.
        query (str): Query text.
        top_k (int): Number of results to return.
        threshold (float): Similarity threshold.

    Returns:
        List[Dict[str, Any]]: Found discussion fragments matching the query.
    """
    if not user_identifier or not api_key or len(query.strip()) < 5:
        return []

    try:
        results = await asyncio.to_thread(
            search_user_context, user_identifier, api_key, query, top_k, threshold
        )
        return results or []
    except Exception as ex:
        logger.error(f"[UserRAG] Error searching user context: {ex}")
        return []

async def get_user_preferences_context(user_identifier: str) -> str:
    """Return text context of user preferences.

    Args:
        user_identifier (str): User identifier.

    Returns:
        str: Text representation of user preferences.
    """
    if not user_identifier:
        return ""
    try:
        pref = await asyncio.to_thread(get_recommendation_context, user_identifier)
        return pref or ""
    except Exception as ex:
        logger.error(f"[UserRAG] Error reading user preferences: {ex}")
        return ""

def save_user_approved_response(
    user_identifier: str,
    query: str,
    chat_text: str,
    voice_text: str
) -> bool:
    """Save approved response to permanent JSON archive storage.

    Args:
        user_identifier (str): User identifier.
        query (str): User query text.
        chat_text (str): Response text in chat format.
        voice_text (str): Response text in voice format.

    Returns:
        bool: Success flag indicating archive save operation.
    """
    try:
        return save_approved_response(user_identifier, query, chat_text, voice_text)
    except Exception as ex:
        logger.error(f"[UserRAG] Error saving response to archive: {ex}")
        return False

def index_user_interaction(
    user_identifier: str,
    api_key: str,
    query: str,
    content_to_index: str
) -> bool:
    """Vectorize and save interaction to user FAISS index.

    Args:
        user_identifier (str): User identifier.
        api_key (str): API key for vectorization.
        query (str): User query text.
        content_to_index (str): Content to be indexed.

    Returns:
        bool: Success flag indicating index operation.
    """
    if not user_identifier or not api_key or not content_to_index.strip():
        return False
    try:
        return index_user_query(user_identifier, api_key, query, content_to_index)
    except Exception as ex:
        logger.error(f"[UserRAG] Error indexing interaction: {ex}")
        return False
