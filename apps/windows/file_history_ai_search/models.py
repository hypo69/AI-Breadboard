"""Модели данных для системы поиска по истории файлов Windows."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FileHistoryItem(BaseModel):
    """Модель элемента истории файла.

    Attributes:
        item_id (str): Уникальный идентификатор записи.
        file_path (str): Полный путь к файлу.
        file_name (str): Имя файла.
        source_type (str): Источник (file_history_xml, recent_lnk, activity_db, fs_scan).
        event_type (str): Тип события (backed_up, opened, modified, scanned).
        timestamp (str): Изо-строка времени события.
        content_preview (str): Текстовый отрывок или содержимое файла.
        file_size (int): Размер файла в байтах.
        metadata (Dict[str, Any]): Дополнительные метаданные (версия, приложение и т.д.).
    """

    item_id: str
    file_path: str
    file_name: str
    source_type: str
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_preview: str = ""
    file_size: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_rag_document(self) -> Dict[str, Any]:
        """Преобразование элемента истории файла в формат документа RAG.

        Returns:
            Dict[str, Any]: Словарь с `id`, `text` и `meta`.
        """
        text_content = (
            f"Файл: {self.file_name}\n"
            f"Путь: {self.file_path}\n"
            f"Источник: {self.source_type}\n"
            f"Событие: {self.event_type}\n"
            f"Время: {self.timestamp}\n"
            f"Размер: {self.file_size} байт\n"
            f"Содержимое/Описание: {self.content_preview}"
        )
        return {
            "id": self.item_id,
            "text": text_content,
            "meta": {
                "file_path": self.file_path,
                "file_name": self.file_name,
                "source_type": self.source_type,
                "event_type": self.event_type,
                "timestamp": self.timestamp,
                "file_size": self.file_size,
                **self.metadata,
            },
        }


class SearchQuery(BaseModel):
    """Модель поискового запроса RAG.

    Attributes:
        query (str): Поисковая строка.
        top_k (int): Количество запрашиваемых результатов.
        threshold (float): Порог минимального сходства (0.0 - 1.0).
        source_type (Optional[str]): Фильтр по источнику.
    """

    query: str
    top_k: int = 5
    threshold: float = 0.0
    source_type: Optional[str] = None


class SearchResultItem(BaseModel):
    """Модель отдельного элемента в результатах поиска.

    Attributes:
        item_id (str): Идентификатор документа.
        file_path (str): Путь к файлу.
        file_name (str): Имя файла.
        score (float): Оценка релевантности / косинусное сходство.
        snippet (str): Текстовый отрывок.
        source_type (str): Источник данных.
        timestamp (str): Время события.
        metadata (Dict[str, Any]): Метаданные.
    """

    item_id: str
    file_path: str
    file_name: str
    score: float
    snippet: str
    source_type: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Модель ответа семантического поиска.

    Attributes:
        query (str): Исходный запрос.
        total_found (int): Найдено результатов.
        results (List[SearchResultItem]): Список найденных элементов.
        execution_time_ms (float): Время выполнения поиска в миллисекундах.
    """

    query: str
    total_found: int
    results: List[SearchResultItem]
    execution_time_ms: float = 0.0


class RAGStatus(BaseModel):
    """Статус состояния RAG-индекса истории файлов.

    Attributes:
        total_indexed_documents (int): Количество проиндексированных элементов.
        last_indexed_at (Optional[str]): Время последнего индексирования.
        index_file_path (str): Путь к файлу индекса FAISS.
        scheduler_running (bool): Флаг работы фонового планировщика.
        update_interval_minutes (int): Интервал автообновления в минутах.
    """

    total_indexed_documents: int
    last_indexed_at: Optional[str] = None
    index_file_path: str = ""
    scheduler_running: bool = False
    update_interval_minutes: int = 15


class SchedulerConfig(BaseModel):
    """Конфигурация автообновления RAG-индекса.

    Attributes:
        interval_minutes (int): Периодичность запуска в минутах.
        enabled (bool): Включен ли планировщик.
        target_directories (List[str]): Список целевых директорий для сканирования.
    """

    interval_minutes: int = 15
    enabled: bool = True
    target_directories: List[str] = Field(default_factory=list)
