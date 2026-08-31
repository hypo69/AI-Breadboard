# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: RAG (Retrieval-Augmented Generation) subsystem
# =============================================================================
# Description:
#   Centralized domain-independent semantic search subsystem for context retrieval and augmentation.
#
# File: __init__.py
# Project: ai-breadboard
# Package: core.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from core.rag.models import RAGDecisionType, RAGRouteDecision, RAGSearchResult
from core.rag.engine import RAGEngine, get_rag_engine
from core.rag.rules_rag import RulesRAG, build_rules_index
from core.rag.user_rag import (
    search_user_history,
    index_user_interaction,
    save_user_approved_response,
    get_user_preferences_context,
)

__all__ = [
    "RAGDecisionType",
    "RAGRouteDecision",
    "RAGSearchResult",
    "RAGEngine",
    "get_rag_engine",
    "RulesRAG",
    "build_rules_index",
    "search_user_history",
    "index_user_interaction",
    "save_user_approved_response",
    "get_user_preferences_context",
]
