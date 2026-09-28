"""FastAPI APIRouter для сервиса поиска по истории файлов Windows."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from apps.windows.file_history_ai_search.collector import WindowsFileHistoryCollector
from apps.windows.file_history_ai_search.models import (
    FileHistoryItem,
    RAGStatus,
    SearchQuery,
    SearchResponse,
)
from apps.windows.file_history_ai_search.rag_service import FileHistoryRAGService
from apps.windows.file_history_ai_search.scheduler import FileHistoryScheduler

router = APIRouter(prefix="/api/windows/file-history", tags=["file-history-rag"])

# Глобальные экземпляры сервисов модуля
_collector = WindowsFileHistoryCollector()
_rag_service = FileHistoryRAGService()
_scheduler = FileHistoryScheduler(collector=_collector, rag_service=_rag_service)


@router.get("/scan", response_model=List[FileHistoryItem])
async def scan_file_history() -> List[FileHistoryItem]:
    """Сканирование и считывание текущей истории файлов в системе Windows.

    Returns:
        List[FileHistoryItem]: Список обнаруженных элементов истории файлов.
    """
    try:
        return _collector.collect_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сканирования истории файлов: {e}")


@router.post("/index")
async def rebuild_rag_index() -> Dict[str, Any]:
    """Принудительное обновление RAG-индекса по сохраненной истории файлов.

    Returns:
        Dict[str, Any]: Информация о количестве проиндексированных записей.
    """
    try:
        indexed_count = _scheduler.trigger_now()
        return {
            "status": "success",
            "indexed_count": indexed_count,
            "timestamp": _rag_service.last_indexed_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка перестроения RAG индекса: {e}")


@router.post("/search", response_model=SearchResponse)
async def search_file_history(search_query: SearchQuery) -> SearchResponse:
    """Быстрый семантический поиск по RAG-индексу истории файлов.

    Args:
        search_query (SearchQuery): Модель поискового запроса.

    Returns:
        SearchResponse: Наденные элементы истории файлов.
    """
    try:
        return _rag_service.search(
            query=search_query.query,
            top_k=search_query.top_k,
            threshold=search_query.threshold,
            source_type=search_query.source_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения семантического поиска: {e}")


@router.get("/search", response_model=SearchResponse)
async def search_file_history_get(
    query: str = Query(..., description="Строка поискового запроса"),
    top_k: int = Query(5, description="Лимит результатов"),
    source_type: Optional[str] = Query(None, description="Фильтр по источнику"),
) -> SearchResponse:
    """GET-эндпоинт для быстрого поиска через строку URL.

    Args:
        query (str): Текст запроса.
        top_k (int): Лимит результатов.
        source_type (Optional[str]): Фильтр типа источника.

    Returns:
        SearchResponse: Результаты поиска.
    """
    try:
        return _rag_service.search(query=query, top_k=top_k, source_type=source_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {e}")


@router.get("/status", response_model=RAGStatus)
async def get_rag_status() -> RAGStatus:
    """Получение текущего статуса RAG-индекса и фонового планировщика.

    Returns:
        RAGStatus: Статус состояния индекса.
    """
    return _rag_service.get_status(
        scheduler_running=_scheduler.is_running,
        update_interval=int(_scheduler.interval_seconds // 60),
    )


@router.post("/scheduler/start")
async def start_scheduler(interval_minutes: int = 15) -> Dict[str, Any]:
    """Запуск фонового планировщика автообновления RAG-индекса.

    Args:
        interval_minutes (int): Интервал в минутах.

    Returns:
        Dict[str, Any]: Результат запуска.
    """
    _scheduler.interval_seconds = interval_minutes * 60
    started = _scheduler.start()
    return {
        "status": "started" if started else "already_running",
        "interval_minutes": interval_minutes,
    }


@router.post("/scheduler/stop")
async def stop_scheduler() -> Dict[str, Any]:
    """Остановка фонового планировщика автообновления.

    Returns:
        Dict[str, Any]: Результат остановки.
    """
    stopped = _scheduler.stop()
    return {"status": "stopped" if stopped else "not_running"}
