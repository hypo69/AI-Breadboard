# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard RAG - Models Module
# =============================================================================
# Description:
#   RAG router decision type.
#
# Usage Examples:
#   Python API:
#     from src.rag.models import RAGDecisionType
#
#     service = RAGDecisionType()
#
# File: models.py
# Project: ai-breadboard
# Package: src.rag
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""RAG router decision type."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

class RAGDecisionType(str, Enum):
    """RAG router decision type."""
    DIRECT_ANSWER = 'direct_answer'
    LLM_FALLBACK = 'llm_fallback'

@dataclass
class RAGSearchResult:
    """Result of semantic search in RAG index."""
    title: str = ''
    file: str = ''
    path: str = ''
    text: str = ''
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RAGRouteDecision:
    """Decision of RAG engine for processing user request."""
    decision_type: RAGDecisionType = RAGDecisionType.LLM_FALLBACK
    is_direct: bool = False
    direct_text: str = ''
    direct_voice: str = ''
    context_text: str = ''
    confidence_score: float = 0.0
    raw_results: List[Dict[str, Any]] = field(default_factory=list)
    status_message: str = ''