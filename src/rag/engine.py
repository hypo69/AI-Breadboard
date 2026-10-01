# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard RAG - Engine Module
# =============================================================================
# Description:
#   Универсальный координатор поиска по базе знаний и маршрутизации RAG-First.
#
# Usage Examples:
#   Python API:
#     from src.rag.engine import RAGEngine
#
#     service = RAGEngine()
#
# File: engine.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Универсальный координатор поиска по базе знаний и маршрутизации RAG-First."""

import asyncio
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from logger import logger
from src.rag.models import RAGDecisionType, RAGRouteDecision, RAGSearchResult
from src.rag.user_rag import search_user_history, get_user_preferences_context
from src.rag.query_router import get_query_router, RoutingType
from src.rag.document_rag import get_document_rag_manager

class RAGEngine:
    """Универсальный координатор поиска по базе знаний и маршрутизации RAG-First.
    """

    def __init__(self, direct_threshold: float=0.85) -> None:
        """Initialization RAG-движка.

        Args:
            direct_threshold (float): Порог уверенности для прямого возврата ответа без вызова LLM.
        """
        self.direct_threshold = direct_threshold

    async def evaluate(self, query: str, user_identifier: str='', api_key: str='', threshold: Optional[float]=None, top_k: int=3) -> RAGRouteDecision:
        """Оценивает входящий запрос: ищет готовый ответ в базе или готовит контекст для LLM.

        Args:
            query (str): Запрос пользователя.
            user_identifier (str): Идентификатор пользователя.
            api_key (str): Ключ API.
            threshold (Optional[float]): Порог уверенности для прямого ответа.
            top_k (int): Количество возвращаемых фрагментов.

        Returns:
            RAGRouteDecision: Решение движка (прямой ответ или fallback к модели).
        """
        clean_query = query.strip()
        if not clean_query:
            return RAGRouteDecision(decision_type=RAGDecisionType.DIRECT_ANSWER, is_direct=True, direct_text='Пожалуйста, введите запрос.', direct_voice='Пожалуйста, введите запрос.')
        active_threshold = threshold if threshold is not None else self.direct_threshold
        context_parts: List[str] = []
        from src.ai.gemini.user_query_rag import is_garbage_query
        is_greeting = is_garbage_query(clean_query)
        if user_identifier and api_key and (len(clean_query) >= 3) and (not is_greeting):
            results = await search_user_history(user_identifier, api_key, clean_query, top_k=top_k, threshold=0.4)
            if results:
                best_match = results[0]
                best_score = float(best_match.get('score', 0.0))
                direct_cutoff = max(active_threshold, self.direct_threshold)
                if best_score >= direct_cutoff and best_match.get('text'):
                    matched_text = best_match['text'].strip()
                    logger.info(f'[RAGEngine] Найден прямой ответ в RAG (score={best_score:.2f} >= {direct_cutoff})')
                    return RAGRouteDecision(decision_type=RAGDecisionType.DIRECT_ANSWER, is_direct=True, direct_text=matched_text, direct_voice=matched_text, confidence_score=best_score, raw_results=results, status_message='⚡ Ответ найден в базе знаний...')
                snippets = [item['text'].strip() for item in results if item.get('text')]
                if snippets:
                    context_parts.append('[Контекст из базы знаний]:\n' + '\n---\n'.join(snippets))
        if user_identifier:
            pref_context = await get_user_preferences_context(user_identifier)
            if pref_context:
                context_parts.append(f'[Профиль предпочтений]:\n{pref_context}')
        return RAGRouteDecision(decision_type=RAGDecisionType.LLM_FALLBACK, is_direct=False, context_text='\n\n'.join(context_parts), confidence_score=0.0, status_message='Генерация ответа...')

    async def search_documents(self, query: str, top_k: int=5, min_score: float=0.0, api_key: str='', use_routing: bool=True) -> RAGRouteDecision:
        """Search documents (text and images) with optional smart routing.

        Analyzes query using QueryRouter to determine optimal search strategy:
        - text: Only search text documents
        - pixel: Only search images
        - hybrid: Search both (default)

        Args:
            query (str): User query string
            top_k (int): Maximum results per provider
            min_score (float): Minimum similarity threshold
            api_key (str): Optional Gemini API key for text embeddings
            use_routing (bool): Use QueryRouter for smart routing (default True)

        Returns:
            RAGRouteDecision: Search results with routing metadata
        """
        clean_query = query.strip()
        if not clean_query:
            return RAGRouteDecision(decision_type=RAGDecisionType.LLM_FALLBACK, is_direct=False, context_text='', status_message='Empty query')
        doc_rag = get_document_rag_manager()
        router = get_query_router()
        analysis = router.analyze(clean_query)
        routing_type = analysis.routing_type if use_routing else RoutingType.HYBRID
        logger.info(f'[RAGEngine] Query routing: {routing_type.value} (confidence={analysis.confidence:.2f}) - {analysis.reason}')
        search_results = doc_rag.search(query=clean_query, top_k=top_k, min_score=min_score, api_key=api_key, version_filter='latest')
        if routing_type == RoutingType.TEXT:
            search_results = [r for r in search_results if r.get('source_type') == 'text']
            filter_reason = 'Text-only routing applied'
        elif routing_type == RoutingType.PIXEL:
            search_results = [r for r in search_results if r.get('source_type') == 'pixel']
            filter_reason = 'Image-only routing applied'
        else:
            filter_reason = 'Hybrid search (no filtering)'
        logger.info(f'[RAGEngine] Search returned {len(search_results)} results ({filter_reason})')
        context_parts: List[str] = []
        context_parts.append(f"[Query Analysis]\nLanguage: {analysis.language.value}\nRouting: {routing_type.value}\nConfidence: {analysis.confidence:.2f}\nVisual keywords: {(', '.join(analysis.visual_keywords) if analysis.visual_keywords else 'none')}")
        if search_results:
            context_parts.append('[Search Results]:')
            for i, result in enumerate(search_results[:top_k], 1):
                source_type = result.get('source_type', 'unknown')
                doc_name = result.get('doc_name', 'unknown')
                score = result.get('score', 0.0)
                if source_type == 'text':
                    text_snippet = result.get('text', '')[:200]
                    context_parts.append(f'\n{i}. [{doc_name}] (score={score:.3f})\n{text_snippet}...')
                elif source_type == 'pixel':
                    image_path = result.get('source_path', result.get('text', ''))
                    context_parts.append(f'\n{i}. [IMAGE: {doc_name}] (score={score:.3f})\nPath: {image_path}')
        if search_results:
            best_score = max((r.get('score', 0.0) for r in search_results))
            if best_score >= 0.9 and search_results[0].get('source_type') == 'text':
                direct_text = search_results[0].get('text', '')
                if direct_text:
                    logger.info(f'[RAGEngine] Direct answer from document search (score={best_score:.3f})')
                    return RAGRouteDecision(decision_type=RAGDecisionType.DIRECT_ANSWER, is_direct=True, direct_text=direct_text, direct_voice=direct_text, confidence_score=best_score, raw_results=[asdict(r) if hasattr(r, '__dict__') else r for r in search_results[:3]], status_message=f'📚 Found in documents (score={best_score:.2f})', context_text='\n\n'.join(context_parts))
            logger.info(f'[RAGEngine] Using document search results as LLM context')
            return RAGRouteDecision(decision_type=RAGDecisionType.LLM_FALLBACK, is_direct=False, context_text='\n\n'.join(context_parts), confidence_score=best_score, raw_results=[asdict(r) if hasattr(r, '__dict__') else r for r in search_results[:3]], status_message=f'📚 Found {len(search_results)} document matches')
        logger.info(f'[RAGEngine] No document search results found')
        return RAGRouteDecision(decision_type=RAGDecisionType.LLM_FALLBACK, is_direct=False, context_text='\n'.join(context_parts), confidence_score=0.0, status_message='No matches in document search')
_engine_instance: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    """Returns синглтон RAGEngine.
    """
    global _engine_instance
    if not _engine_instance:
        _engine_instance = RAGEngine()
    return _engine_instance