"""Фоновый планировщик регулярного обновления RAG-индекса истории файлов."""
import asyncio
import threading
import time
from datetime import datetime, timezone
from typing import Optional
from logger import logger
from apps.windows.file_history_ai_search.collector import WindowsFileHistoryCollector
from apps.windows.file_history_ai_search.rag_service import FileHistoryRAGService


class FileHistoryScheduler:
    """Планировщик фоновой периодической синхронизации истории файлов и RAG-индекса.

    Обеспечивает автоматическое регулярное обновление индекса в фоновом потоке без блокировки основного приложения.
    """

    def __init__(
        self,
        collector: WindowsFileHistoryCollector,
        rag_service: FileHistoryRAGService,
        interval_minutes: int = 15,
    ) -> None:
        """Инициализация фонового планировщика.

        Args:
            collector (WindowsFileHistoryCollector): Сборщик истории файлов.
            rag_service (FileHistoryRAGService): Сервис векторизации и поиска.
            interval_minutes (int): Интервал между обновлениями в минутах.
        """
        self.collector = collector
        self.rag_service = rag_service
        self.interval_seconds = interval_minutes * 60
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_run_time: Optional[str] = None
        self.last_indexed_count: int = 0

    @property
    def is_running(self) -> bool:
        """Флаг активности фонового планировщика."""
        return self._is_running and (self._thread is not None and self._thread.is_alive())

    def start(self) -> bool:
        """Запуск фонового потока планировщика.

        Returns:
            bool: True если планировщик успешно запущен.
        """
        if self.is_running:
            logger.warning("[FileHistoryScheduler] Планировщик уже запущен")
            return False

        self._stop_event.clear()
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, name="FileHistoryRAGScheduler", daemon=True)
        self._thread.start()
        logger.info(f"[FileHistoryScheduler] Фоновый планировщик запущен (интервал {self.interval_seconds // 60} мин)")
        return True

    def stop(self) -> bool:
        """Остановка фонового планировщика.

        Returns:
            bool: True если планировщик остановлен.
        """
        if not self.is_running:
            return False

        logger.info("[FileHistoryScheduler] Сигнал остановки планировщика...")
        self._is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("[FileHistoryScheduler] Фоновый планировщик остановлен")
        return True

    def trigger_now(self) -> int:
        """Принудительное однократное сканирование и индексирование истории файлов.

        Returns:
            int: Количество проиндексированных файлов.
        """
        logger.info("[FileHistoryScheduler] Ручной запуск сканирования и RAG-индексации...")
        try:
            items = self.collector.collect_all()
            indexed_count = self.rag_service.index_items(items)
            self.last_run_time = datetime.now(timezone.utc).isoformat()
            self.last_indexed_count = indexed_count
            logger.info(f"[FileHistoryScheduler] Завершено ручное обновление RAG: {indexed_count} элементов")
            return indexed_count
        except Exception as e:
            logger.error(f"[FileHistoryScheduler] Ошибка выполнения обновления RAG: {e}")
            return 0

    def _run_loop(self) -> None:
        """Фоновый цикл выполнения задач сканирования и индексации."""
        logger.info("[FileHistoryScheduler] Выполняем первоначальное сканирование при старте...")
        self.trigger_now()

        while not self._stop_event.is_set():
            # Ожидание заданного интервала с регулярной проверкой флага остановки
            wait_step = 1.0
            elapsed = 0.0
            while elapsed < self.interval_seconds and not self._stop_event.is_set():
                time.sleep(wait_step)
                elapsed += wait_step

            if not self._stop_event.is_set():
                logger.info("[FileHistoryScheduler] Наступление планового интервала обновления RAG...")
                self.trigger_now()
