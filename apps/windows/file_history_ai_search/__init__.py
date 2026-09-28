"""Пакет File History AI Search для поиска по истории файлов Windows с помощью RAG."""
from apps.windows.file_history_ai_search.collector import WindowsFileHistoryCollector
from apps.windows.file_history_ai_search.models import FileHistoryItem, SearchQuery, SearchResultItem, SearchResponse
from apps.windows.file_history_ai_search.rag_service import FileHistoryRAGService
from apps.windows.file_history_ai_search.scheduler import FileHistoryScheduler

__all__ = [
    "WindowsFileHistoryCollector",
    "FileHistoryItem",
    "SearchQuery",
    "SearchResultItem",
    "SearchResponse",
    "FileHistoryRAGService",
    "FileHistoryScheduler",
]
