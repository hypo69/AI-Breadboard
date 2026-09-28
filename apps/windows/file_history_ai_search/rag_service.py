"""Сервис RAG-индексации и быстрого семантического поиска по истории файлов Windows."""
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from src.ai.gemini.rag import GeminiRAG
from apps.windows.file_history_ai_search.models import (
    FileHistoryItem,
    RAGStatus,
    SearchQuery,
    SearchResponse,
    SearchResultItem,
)


class FileHistoryRAGService:
    """Сервис векторного индексирования RAG и быстрых семантических запросов по истории файлов.

    Обеспечивает связь между сборщиком историй файлов Windows и векторной базой данных GeminiRAG.
    """

    def __init__(self, db_path: Optional[Path] = None, api_key: Optional[str] = None) -> None:
        """Инициализация сервиса RAG истории файлов.

        Args:
            db_path (Optional[Path]): Путь хранения индекса и метаданных FAISS.
            api_key (Optional[str]): Gemini API ключ.
        """
        configured_dir = Path("data/file_history_rag")
        self.db_path = db_path or (configured_dir / "file_history")
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.rag_engine = GeminiRAG(api_key=self.api_key, db_path=self.db_path)
        self.last_indexed_at: Optional[str] = None

    def index_items(self, items: List[FileHistoryItem]) -> int:
        """Инлексирование записей истории файлов в RAG-базу.

        Args:
            items (List[FileHistoryItem]): Список элементов истории файлов.

        Returns:
            int: Количество успешно проиндексированных элементов.
        """
        if not items:
            logger.info("[FileHistoryRAGService] Передан пустой список элементов для индексации")
            return 0

        docs = [item.to_rag_document() for item in items]

        try:
            indexed_count = self.rag_engine.add_documents(docs)
            self.last_indexed_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"[FileHistoryRAGService] Успешно проиндексировано {indexed_count} документов RAG")
            return indexed_count
        except Exception as e:
            logger.error(f"[FileHistoryRAGService] Ошибка векторной индексации через GeminiRAG: {e}")
            # Фолбэк на добавление без внешней векторизации для текстового поиска
            return self._fallback_index(docs)

    def _fallback_index(self, docs: List[Dict[str, Any]]) -> int:
        """Резервная локальная сохранность документов при отсутствии API ключей.

        Args:
            docs (List[Dict[str, Any]]): Документы RAG.

        Returns:
            int: Количество сохраненных документов.
        """
        existing_ids = {d["id"] for d in docs}
        self.rag_engine.metadatas = [m for m in self.rag_engine.metadatas if m.get("id") not in existing_ids]

        for doc in docs:
            # Заполняем нулями если вектора от API недоступны
            dummy_vec = [0.0] * self.rag_engine.dimension
            self.rag_engine.metadatas.append({
                "id": doc["id"],
                "text": doc["text"],
                "meta": doc.get("meta", {}),
                "vector": dummy_vec
            })

        self.rag_engine._save()
        self.last_indexed_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[FileHistoryRAGService] Документы сохранены в локальный fallback мета-хранилище ({len(docs)} шт.)")
        return len(docs)

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        source_type: Optional[str] = None,
    ) -> SearchResponse:
        """Быстрый семантический поиск по проиндексированной истории файлов.

        Args:
            query (str): Текст поискового запроса.
            top_k (int): Максимальное число возвращаемых результатов.
            threshold (float): Порог релевантности.
            source_type (Optional[str]): Фильтр по источнику (file_history_xml, recent_lnk и т.д.).

        Returns:
            SearchResponse: Результат поиска с метриками времени и релевантности.
        """
        start_time = time.perf_counter()

        if not query.strip():
            return SearchResponse(
                query=query,
                total_found=0,
                results=[],
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            )

        # Выполняем векторный поиск
        raw_results = self.rag_engine.search(query=query, top_k=top_k * 2, threshold=threshold)

        # Фолбэк на текстовый подстрочный / токенный поиск если векторные результаты пусты
        if not raw_results and self.rag_engine.metadatas:
            raw_results = self._fallback_text_search(query=query, top_k=top_k * 2)

        results: List[SearchResultItem] = []
        for r in raw_results:
            meta = r.get("meta", {})
            stype = meta.get("source_type", "unknown")

            if source_type and stype != source_type:
                continue

            item = SearchResultItem(
                item_id=r.get("id", ""),
                file_path=meta.get("file_path", r.get("id", "")),
                file_name=meta.get("file_name", Path(meta.get("file_path", "")).name),
                score=r.get("score", 1.0),
                snippet=r.get("text", "")[:300],
                source_type=stype,
                timestamp=meta.get("timestamp", ""),
                metadata=meta,
            )
            results.append(item)
            if len(results) >= top_k:
                break

        exec_time = round((time.perf_counter() - start_time) * 1000, 2)
        return SearchResponse(
            query=query,
            total_found=len(results),
            results=results,
            execution_time_ms=exec_time,
        )

    def _fallback_text_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Локальный полнотекстовый поиск по ключевым словам при отсутствии векторазатора.

        Args:
            query (str): Поисковая строка.
            top_k (int): Лимит результатов.

        Returns:
            List[Dict[str, Any]]: Отфильтрованные результаты.
        """
        query_words = [w.lower() for w in query.split() if len(w) > 1]
        matches = []

        for m in self.rag_engine.metadatas:
            text = m.get("text", "").lower()
            score = 0.0
            for word in query_words:
                if word in text:
                    score += 1.0 / len(query_words)

            if score > 0.0:
                matches.append({
                    "id": m.get("id"),
                    "text": m.get("text"),
                    "meta": m.get("meta", {}),
                    "score": round(score, 4)
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k]

    def clear(self) -> None:
        """Очистить RAG-индекс истории файлов."""
        self.rag_engine.clear()
        self.last_indexed_at = None
        logger.info("[FileHistoryRAGService] Индакс RAG очищен")

    def get_status(self, scheduler_running: bool = False, update_interval: int = 15) -> RAGStatus:
        """Получить текущее состояние RAG-индекса.

        Args:
            scheduler_running (bool): Флаг работы фонового планировщика.
            update_interval (int): Интервал обновления в минутах.

        Returns:
            RAGStatus: Модель статуса.
        """
        total_docs = len(self.rag_engine.metadatas)
        return RAGStatus(
            total_indexed_documents=total_docs,
            last_indexed_at=self.last_indexed_at,
            index_file_path=str(self.rag_engine.index_file),
            scheduler_running=scheduler_running,
            update_interval_minutes=update_interval,
        )
