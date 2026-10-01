# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps File_History_Ai_Search -   Init  
# =============================================================================
# Description:
#   Пакет File History AI Search для поиска по истории файлов с помощью RAG.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.file_history_ai_search
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет File History AI Search для поиска по истории файлов с помощью RAG."""

from apps.file_history_ai_search.collector import WindowsFileHistoryCollector
from apps.file_history_ai_search.models import FileHistoryItem, SearchQuery, SearchResultItem, SearchResponse
from apps.file_history_ai_search.rag_service import FileHistoryRAGService
from apps.file_history_ai_search.scheduler import FileHistoryScheduler

__all__ = [
    "WindowsFileHistoryCollector",
    "FileHistoryItem",
    "SearchQuery",
    "SearchResultItem",
    "SearchResponse",
    "FileHistoryRAGService",
    "FileHistoryScheduler",
]
