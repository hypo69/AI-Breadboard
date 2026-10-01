# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Engine
# =============================================================================
# Description:
#   Главный координатор прогрессивной базы знаний WikiLLM. Управляет 4-уровневым
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.engine import WikiLLMEngine
#
#     service = WikiLLMEngine()
#
# File: engine.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Главный координатор прогрессивной базы знаний WikiLLM. Управляет 4-уровневым"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from logger import logger
from .config import WikiLLMConfig, load_config
from .models import (
    ArtifactInput,
    KnowledgeEntity,
    LookupLevel,
    ResolutionResult,
)
from .normalizer import CanonicalKeyNormalizer
from .resolvers.exact import ExactResolver
from .resolvers.fingerprint import FingerprintResolver
from .resolvers.gemini import GeminiKnowledgeResolver
from .resolvers.semantic import SemanticResolver
from .storage import WikiStorage


class WikiLLMEngine:
    """Движок прогрессивного накопления знаний и 4-уровневой диспетчеризации запросов."""

    def __init__(
        self,
        config: Optional[WikiLLMConfig] = None,
        storage: Optional[WikiStorage] = None,
        chat_model: Optional[Any] = None,
    ) -> None:
        """Инициализирует WikiLLMEngine.

        Args:
            config: Конфигурация WikiLLMConfig или None для автоматической загрузки.
            storage: Экземпляр хранилища WikiStorage.
            chat_model: Экземпляр модели Gemini Chat.
        """
        self.config = config or load_config()
        self.storage = storage or WikiStorage(self.config.database_path)

        # Инициализация 4 уровней резолверов
        self.exact_resolver = ExactResolver(self.storage)
        self.fingerprint_resolver = FingerprintResolver(self.storage)
        self.semantic_resolver = SemanticResolver(self.storage)
        self.gemini_resolver = GeminiKnowledgeResolver(
            chat_model=chat_model,
            model_id=self.config.gemini_model_id,
        )

        # Очередь для асинхронного разрешения артефактов телеметрии
        self._async_queue: asyncio.Queue[ArtifactInput] = asyncio.Queue(
            maxsize=self.config.max_queue_size
        )
        self._worker_tasks: List[asyncio.Task] = []
        self._is_running = False

        # Метрики и статистика поиска
        self._stats = {
            "total_requests": 0,
            "l1_exact_hits": 0,
            "l2_fingerprint_hits": 0,
            "l3_semantic_hits": 0,
            "l4_gemini_resolutions": 0,
            "unresolved_count": 0,
        }

    async def start(self) -> None:
        """Запускает фоновые воркеры асинхронной очереди разрешения артефактов."""
        if self._is_running:
            return
        self._is_running = True
        for i in range(max(1, self.config.async_workers)):
            task = asyncio.create_task(self._queue_worker_loop(i), name=f"WikiLLM-Worker-{i}")
            self._worker_tasks.append(task)
        logger.info(f"WikiLLMEngine запущен с {len(self._worker_tasks)} фоновыми воркерами.")

    async def stop(self) -> None:
        """Останавливает фоновые воркеры."""
        self._is_running = False
        for task in self._worker_tasks:
            task.cancel()
        self._worker_tasks.clear()
        logger.info("WikiLLMEngine остановлен.")

    async def _queue_worker_loop(self, worker_id: int) -> None:
        """Фоновый цикл обработки артефактов из очереди."""
        while self._is_running:
            try:
                artifact = await self._async_queue.get()
                canonical_key = CanonicalKeyNormalizer.compute_canonical_key(artifact)
                # Проверяем, не разрешен ли уже артефакт
                existing = self.storage.get_entity(canonical_key)
                if not existing:
                    logger.debug(f"[Worker-{worker_id}] Асинхронное разрешение через Gemini: {canonical_key}")
                    entity = await self.gemini_resolver.resolve(artifact)
                    if entity:
                        self.storage.save_entity(entity)
                        self._stats["l4_gemini_resolutions"] += 1
                        logger.info(f"[Worker-{worker_id}] Артефакт {canonical_key} успешно сохранен в базе знаний.")
                self._async_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"[Worker-{worker_id}] Ошибка обработки артефакта из очереди: {exc}")
                await asyncio.sleep(1.0)

    async def resolve(
        self,
        artifact: ArtifactInput,
        sync_gemini: bool = True,
        record_observation: bool = True,
        co_occurring_keys: Optional[List[str]] = None,
    ) -> ResolutionResult:
        """Главный метод разрешения артефакта через 4-уровневый конвейер.

        Args:
            artifact: Входной артефакт (код ошибки, Event ID, процесс, симптом).
            sync_gemini: Разрешать ли неизвестные артефакты синхронно через Gemini.
            record_observation: Фиксировать ли наблюдение в счетчиках локальной машины.
            co_occurring_keys: Список ключей сопутствующих событий для графа связей.

        Returns:
            Результат ResolutionResult.
        """
        start_time = time.perf_counter()
        self._stats["total_requests"] += 1
        canonical_key = CanonicalKeyNormalizer.compute_canonical_key(artifact)

        # Фиксация наблюдения
        if record_observation and canonical_key and canonical_key != "unknown:unspecified":
            self.storage.record_observation(canonical_key, co_occurring_keys=co_occurring_keys)

        # Level 1: Exact Match (SQLite O(1))
        entity = await self.exact_resolver.resolve(artifact)
        if entity:
            self._stats["l1_exact_hits"] += 1
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ResolutionResult(
                canonical_key=canonical_key,
                lookup_level=LookupLevel.EXACT,
                cached=True,
                entity=entity,
                confidence=entity.confidence,
                execution_time_ms=elapsed_ms,
                message="Мгновенный ответ из локальной базы знаний (Level 1 Exact)",
            )

        # Level 2: Fingerprint Template Match
        entity = await self.fingerprint_resolver.resolve(artifact)
        if entity:
            self._stats["l2_fingerprint_hits"] += 1
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ResolutionResult(
                canonical_key=canonical_key,
                lookup_level=LookupLevel.FINGERPRINT,
                cached=True,
                entity=entity,
                confidence=entity.confidence * 0.95,
                execution_time_ms=elapsed_ms,
                message="Совпадение по структурному шаблону (Level 2 Fingerprint)",
            )

        # Level 3: Semantic / FTS5 Match
        if self.config.enable_semantic_search:
            entity = await self.semantic_resolver.resolve(artifact)
            if entity:
                self._stats["l3_semantic_hits"] += 1
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ResolutionResult(
                    canonical_key=canonical_key,
                    lookup_level=LookupLevel.SEMANTIC,
                    cached=True,
                    entity=entity,
                    confidence=entity.confidence * 0.85,
                    execution_time_ms=elapsed_ms,
                    message="Найдено по семантическому сходству FTS5 (Level 3 Semantic)",
                )

        # Level 4: Gemini Structured Resolver
        if sync_gemini:
            entity = await self.gemini_resolver.resolve(artifact)
            if entity:
                # Валидация и самообучение: сохранение в SQLite
                self.storage.save_entity(entity)
                self._stats["l4_gemini_resolutions"] += 1
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ResolutionResult(
                    canonical_key=canonical_key,
                    lookup_level=LookupLevel.GEMINI,
                    cached=False,
                    entity=entity,
                    confidence=entity.confidence,
                    execution_time_ms=elapsed_ms,
                    message="Новое знание сгенерировано через Gemini и сохранено в SQLite (Level 4)",
                )

        # Если sync_gemini = False, отправляем в очередь асинхронного обучения
        if not sync_gemini and self._is_running:
            try:
                self._async_queue.put_nowait(artifact)
            except asyncio.QueueFull:
                logger.warning("Очередь WikiLLM переполнена, артефакт пропущен.")

        self._stats["unresolved_count"] += 1
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return ResolutionResult(
            canonical_key=canonical_key,
            lookup_level=LookupLevel.UNKNOWN,
            cached=False,
            entity=None,
            confidence=0.0,
            execution_time_ms=elapsed_ms,
            message="Артефакт не найден и добавлен в очередь асинхронного разрешения"
            if not sync_gemini
            else "Не удалось разрешить артефакт",
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает метрики производительности и эффективность кэша."""
        total = self._stats["total_requests"]
        hits = (
            self._stats["l1_exact_hits"]
            + self._stats["l2_fingerprint_hits"]
            + self._stats["l3_semantic_hits"]
        )
        hit_rate = (hits / total * 100.0) if total > 0 else 0.0

        db_stats = self.storage.get_stats()
        return {
            "lookup_stats": self._stats,
            "cache_hit_rate_pct": round(hit_rate, 2),
            "queue_size": self._async_queue.qsize(),
            "storage_stats": db_stats,
        }
