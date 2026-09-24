# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Centralized Model Error and Health Hub
# =============================================================================
# Description:
#   Централизованный хаб классификации, мониторинга, маршрутизации и телеметрии
#   ошибок AI-моделей для всех провайдеров (Gemini, Gemini CLI, AGY, AGY CLI,
#   Foundry, Ollama, OpenAI-совместимых и др.).
#
# File: model_error_hub.py
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Централизованный модуль классификации, агрегации и оповещения об ошибках моделей."""

from __future__ import annotations

import collections
import re
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from logger.logger import logger


class ModelErrorCategory(str, Enum):
    """Категории типовых ошибок AI-моделей и провайдеров."""

    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"  # 503, перегрузка сервиса, High demand
    RATE_LIMIT = "RATE_LIMIT"                    # 429, ResourceExhausted, превышение RPM/RPD
    AUTH_ERROR = "AUTH_ERROR"                    # 401/403, невалидный/просроченный API-ключ
    NOT_FOUND = "NOT_FOUND"                      # 404, модель удалена, устарела или не существует
    CONTEXT_OVERFLOW = "CONTEXT_OVERFLOW"        # Превышен лимит контекстного окна токенов
    SAFETY_BLOCK = "SAFETY_BLOCK"                # Блокировка фильтрами безопасности / цензуры
    CONNECTION_ERROR = "CONNECTION_ERROR"        # Сетевой таймаут, сброс TCP, отказ в соединении
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"  # 500/502/504 внутренние ошибки сервиса
    GENERIC_ERROR = "GENERIC_ERROR"              # Прочие необработанные исключения


class ModelErrorEvent(BaseModel):
    """Модель отдельного события ошибки AI-модели."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Временная метка события в формате ISO 8601 UTC",
    )
    provider: str = Field(..., description="Имя AI-провайдера (gemini, agy, foundry, etc.)")
    model_name: str = Field(..., description="Идентификатор модели")
    category: ModelErrorCategory = Field(..., description="Классифицированная категория ошибки")
    raw_message: str = Field(..., description="Исходный текст ошибки или исключения")
    status_code: Optional[int] = Field(None, description="HTTP статус-код ответа, если применимо")
    attempt: int = Field(0, description="Номер текущей попытки обращения к модели")
    max_attempts: int = Field(1, description="Максимальное число попыток в цикле retry")
    action_taken: str = Field("none", description="Действие: retry, rotate_key, switch_model, failed")
    retry_delay_seconds: float = Field(0.0, description="Пауза перед повтором в секундах")


def classify_model_error(
    ex: Any,
    status_code: Optional[int] = None,
) -> Tuple[ModelErrorCategory, Optional[int]]:
    """Классифицировать исключение или строку ошибки AI-модели.

    Args:
        ex (Any): Исключение или текстовое описание ошибки.
        status_code (Optional[int]): Явный HTTP статус-код, если известен.

    Returns:
        Tuple[ModelErrorCategory, Optional[int]]: Кортеж (категория ошибки, статус-код).
    """
    ex_str: str = str(ex).strip()
    code: Optional[int] = status_code

    if code is None:
        # Извлечение статус-кода из текста ошибки (например: "503 UNAVAILABLE", "status code 429")
        match = re.search(r'\b(401|403|404|429|500|502|503|504)\b', ex_str)
        if match:
            code = int(match.group(1))

    low: str = ex_str.lower()

    # 1. 503 / Service Unavailable / High demand
    if code == 503 or '503' in ex_str or 'unavailable' in low or 'high demand' in low or 'overloaded' in low:
        return ModelErrorCategory.SERVICE_UNAVAILABLE, code or 503

    # 2. 429 / Rate Limit / Quota Exhausted
    if code == 429 or '429' in ex_str or 'resource_exhausted' in low or 'rate limit' in low or 'too many requests' in low:
        return ModelErrorCategory.RATE_LIMIT, code or 429

    # 3. 401 / 403 / Auth error
    if code in (401, 403) or '401' in ex_str or '403' in ex_str or 'api_key_invalid' in low or 'permission_denied' in low or 'unauthorized' in low:
        return ModelErrorCategory.AUTH_ERROR, code or 401

    # 4. 404 / Model Not Found / Unsupported
    if code == 404 or '404' in ex_str or 'not_found' in low or 'not found' in low or 'is no longer available' in low or 'unsupported' in low:
        return ModelErrorCategory.NOT_FOUND, code or 404

    # 5. Превышение контекстного окна токенов
    if any(k in low for k in ['context length', 'max tokens', 'token limit', 'context_window_exceeded', 'prompt is too long']):
        return ModelErrorCategory.CONTEXT_OVERFLOW, code

    # 6. Фильтры безопасности / Модерация
    if any(k in low for k in ['safety', 'harm_category', 'blocked by content policy', 'moderation', 'censorship']):
        return ModelErrorCategory.SAFETY_BLOCK, code

    # 7. Сетевые ошибки / Таймауты
    if any(k in low for k in ['connectionrefused', 'connection reset', 'timed out', 'timeout', 'network error', 'connecterror']):
        return ModelErrorCategory.CONNECTION_ERROR, code

    # 8. 500 / 502 / 504 Серверные ошибки
    if code in (500, 502, 504) or any(k in low for k in ['500 internal', 'bad gateway', 'gateway timeout']):
        return ModelErrorCategory.INTERNAL_SERVER_ERROR, code or 500

    return ModelErrorCategory.GENERIC_ERROR, code


class ModelErrorHub:
    """Централизованный диспетчер и реестр инцидентов ошибок AI-моделей."""

    def __init__(self, max_events: int = 200) -> None:
        """Инициализация хаба ошибок.

        Args:
            max_events (int): Максимальный размер кольцевого буфера истории событий.
        """
        self._max_events: int = max_events
        self._events: collections.deque[ModelErrorEvent] = collections.deque(maxlen=max_events)
        self._listeners: List[Callable[[ModelErrorEvent], None]] = []
        self._lock: threading.Lock = threading.Lock()

    def record_error(
        self,
        provider: str,
        model_name: str,
        error: Any,
        status_code: Optional[int] = None,
        attempt: int = 0,
        max_attempts: int = 1,
        action_taken: str = "none",
        retry_delay_seconds: float = 0.0,
    ) -> ModelErrorEvent:
        """Зафиксировать ошибку модели, классифицировать её и уведомить слушателей.

        Args:
            provider (str): Провайдер модели.
            model_name (str): Имя модели.
            error (Any): Исключение или сообщение об ошибке.
            status_code (Optional[int]): Статус-код ответа.
            attempt (int): Текущая попытка.
            max_attempts (int): Максимум попыток.
            action_taken (str): Действие (retry, rotate_key, switch_model, failed).
            retry_delay_seconds (float): Задержка повтора.

        Returns:
            ModelErrorEvent: Созданный объект события ошибки.
        """
        category, code = classify_model_error(error, status_code=status_code)
        event = ModelErrorEvent(
            provider=provider or "unknown",
            model_name=model_name or "unknown",
            category=category,
            raw_message=str(error),
            status_code=code,
            attempt=attempt,
            max_attempts=max_attempts,
            action_taken=action_taken,
            retry_delay_seconds=retry_delay_seconds,
        )

        with self._lock:
            self._events.append(event)
            listeners_snapshot = list(self._listeners)

        # Оповещение зарегистрированных слушателей без блокировки хаба
        for listener in listeners_snapshot:
            try:
                listener(event)
            except Exception as ex:
                logger.warning(f"Ошибка в слушателе ModelErrorHub: {ex}")

        return event

    def get_recent_errors(
        self,
        provider: Optional[str] = None,
        category: Optional[ModelErrorCategory] = None,
        limit: int = 50,
    ) -> List[ModelErrorEvent]:
        """Получить список недавних ошибок с фильтрацией.

        Args:
            provider (Optional[str]): Фильтр по провайдеру.
            category (Optional[ModelErrorCategory]): Фильтр по категории.
            limit (int): Максимальное число возвращаемых записей.

        Returns:
            List[ModelErrorEvent]: Список событий ошибок (от новых к старым).
        """
        with self._lock:
            events_list = list(self._events)

        events_list.reverse()
        result: List[ModelErrorEvent] = []

        for evt in events_list:
            if provider and evt.provider.lower() != provider.lower():
                continue
            if category and evt.category != category:
                continue
            result.append(evt)
            if len(result) >= limit:
                break

        return result

    def get_health_summary(self) -> Dict[str, Any]:
        """Сформировать агрегированную сводку по состоянию здоровья моделей и ошибкам.

        Returns:
            Dict[str, Any]: Сводная статистика по ошибкам и провайдерам.
        """
        with self._lock:
            events_list = list(self._events)

        by_provider: Dict[str, int] = collections.defaultdict(int)
        by_category: Dict[str, int] = collections.defaultdict(int)
        by_model: Dict[str, int] = collections.defaultdict(int)

        for evt in events_list:
            by_provider[evt.provider] += 1
            by_category[evt.category.value] += 1
            by_model[f"{evt.provider}:{evt.model_name}"] += 1

        return {
            "total_errors": len(events_list),
            "by_provider": dict(by_provider),
            "by_category": dict(by_category),
            "by_model": dict(by_model),
            "last_event": events_list[-1].model_dump() if events_list else None,
        }

    def register_listener(self, callback: Callable[[ModelErrorEvent], None]) -> None:
        """Зарегистрировать слушатель новых событий ошибок.

        Args:
            callback (Callable[[ModelErrorEvent], None]): Функция обратного вызова.
        """
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[ModelErrorEvent], None]) -> None:
        """Отписать слушатель событий ошибок.

        Args:
            callback (Callable[[ModelErrorEvent], None]): Функция обратного вызова.
        """
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def clear(self) -> None:
        """Очистить историю событий ошибок."""
        with self._lock:
            self._events.clear()


# Глобальный синглтон хаба ошибок
_global_error_hub = ModelErrorHub()


def get_error_hub() -> ModelErrorHub:
    """Получить глобальный экземпляр хаба ошибок моделей."""
    return _global_error_hub


def record_model_error(
    provider: str,
    model_name: str,
    error: Any,
    status_code: Optional[int] = None,
    attempt: int = 0,
    max_attempts: int = 1,
    action_taken: str = "none",
    retry_delay_seconds: float = 0.0,
) -> ModelErrorEvent:
    """Глобальный фасад для фиксации ошибки модели."""
    return _global_error_hub.record_error(
        provider=provider,
        model_name=model_name,
        error=error,
        status_code=status_code,
        attempt=attempt,
        max_attempts=max_attempts,
        action_taken=action_taken,
        retry_delay_seconds=retry_delay_seconds,
    )


def get_model_errors(
    provider: Optional[str] = None,
    category: Optional[ModelErrorCategory] = None,
    limit: int = 50,
) -> List[ModelErrorEvent]:
    """Глобальный фасад для получения списка ошибок моделей."""
    return _global_error_hub.get_recent_errors(provider=provider, category=category, limit=limit)


def get_model_health_summary() -> Dict[str, Any]:
    """Глобальный фасад для получения сводки здоровья моделей."""
    return _global_error_hub.get_health_summary()
