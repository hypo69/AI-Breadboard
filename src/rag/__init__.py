# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard RAG -   Init   Module
# =============================================================================
# Description:
#   Модуль основной системы (`__init__`).
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Модуль основной системы (`__init__`)."""

from src.rag.models import RAGDecisionType, RAGRouteDecision, RAGSearchResult
from src.rag.engine import RAGEngine, get_rag_engine
from src.rag.rules_rag import RulesRAG, build_rules_index
from src.rag.document_rag import DocumentRAGManager, get_document_rag_manager
from src.rag.user_rag import search_user_history, index_user_interaction, save_user_approved_response, get_user_preferences_context
__all__ = ['RAGDecisionType', 'RAGRouteDecision', 'RAGSearchResult', 'RAGEngine', 'get_rag_engine', 'RulesRAG', 'build_rules_index', 'DocumentRAGManager', 'get_document_rag_manager', 'search_user_history', 'index_user_interaction', 'save_user_approved_response', 'get_user_preferences_context']