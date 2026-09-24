# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Centralized Model Error Hub
# =============================================================================
# Description:
#   Тестирование классификации, логирования, агрегации здоровья моделей
#   и оповещения слушателей централизованного хаба ошибок моделей.
#
# File: test_model_error_hub.py
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from datetime import datetime, timezone
from typing import List

from src.ai.orchestration.model_error_hub import (
    ModelErrorCategory,
    ModelErrorEvent,
    ModelErrorHub,
    classify_model_error,
    get_model_errors,
    get_model_health_summary,
    record_model_error,
)


def test_classify_model_error_503() -> None:
    """Проверка классификации ошибки 503 / перегрузки сервиса."""
    cat, code = classify_model_error("503 UNAVAILABLE: This model is currently experiencing high demand")
    assert cat == ModelErrorCategory.SERVICE_UNAVAILABLE
    assert code == 503

    cat2, _ = classify_model_error("Model is temporarily overloaded, please retry later")
    assert cat2 == ModelErrorCategory.SERVICE_UNAVAILABLE


def test_classify_model_error_429() -> None:
    """Проверка классификации ошибки 429 / превышения лимитов квоты."""
    cat, code = classify_model_error("429 RESOURCE_EXHAUSTED: Rate limit exceeded for quota")
    assert cat == ModelErrorCategory.RATE_LIMIT
    assert code == 429

    cat2, code2 = classify_model_error("Too Many Requests", status_code=429)
    assert cat2 == ModelErrorCategory.RATE_LIMIT
    assert code2 == 429


def test_classify_model_error_auth() -> None:
    """Проверка классификации ошибок аутентификации 401/403."""
    cat, code = classify_model_error("401 API_KEY_INVALID: Provided API key is not valid")
    assert cat == ModelErrorCategory.AUTH_ERROR
    assert code == 401

    cat2, code2 = classify_model_error("403 PERMISSION_DENIED: The caller does not have permission")
    assert cat2 == ModelErrorCategory.AUTH_ERROR
    assert code2 == 403


def test_classify_model_error_not_found() -> None:
    """Проверка классификации ошибок 404 / устаревшей модели."""
    cat, code = classify_model_error("404 NOT_FOUND: models/gemini-1.0 is no longer available")
    assert cat == ModelErrorCategory.NOT_FOUND
    assert code == 404


def test_classify_model_error_context_and_safety() -> None:
    """Проверка классификации переполнения контекста и срабатывания фильтров безопасности."""
    cat_ctx, _ = classify_model_error("maximum context length is 8192 tokens. However, you requested 10000 tokens")
    assert cat_ctx == ModelErrorCategory.CONTEXT_OVERFLOW

    cat_safety, _ = classify_model_error("Response was blocked by SAFETY policies: HARM_CATEGORY_DANGEROUS_CONTENT")
    assert cat_safety == ModelErrorCategory.SAFETY_BLOCK


def test_classify_model_error_connection() -> None:
    """Проверка классификации сетевых ошибок."""
    cat, _ = classify_model_error("ConnectionRefusedError: [WinError 10061] No connection could be made")
    assert cat == ModelErrorCategory.CONNECTION_ERROR

    cat2, _ = classify_model_error("Request timed out after 30.0s")
    assert cat2 == ModelErrorCategory.CONNECTION_ERROR


def test_model_error_hub_record_and_query() -> None:
    """Проверка записи ошибок и выборки из кольцевого буфера хаба."""
    hub = ModelErrorHub(max_events=10)
    hub.clear()

    event = hub.record_error(
        provider="gemini",
        model_name="gemini-3.1-flash-lite-preview",
        error="503 UNAVAILABLE: High demand spike",
        attempt=1,
        max_attempts=5,
        action_taken="retry",
        retry_delay_seconds=2.0,
    )

    assert isinstance(event, ModelErrorEvent)
    assert event.category == ModelErrorCategory.SERVICE_UNAVAILABLE
    assert event.status_code == 503
    assert event.provider == "gemini"
    assert event.model_name == "gemini-3.1-flash-lite-preview"
    assert event.attempt == 1
    assert event.action_taken == "retry"
    assert event.retry_delay_seconds == 2.0

    recent = hub.get_recent_errors(provider="gemini")
    assert len(recent) == 1
    assert recent[0].model_name == "gemini-3.1-flash-lite-preview"

    # Запись других провайдеров
    hub.record_error(provider="ollama", model_name="llama3.1", error="Connection refused", action_taken="failed")
    hub.record_error(provider="agy", model_name="agy-flash", error="429 Rate limit", action_taken="rotate_key")

    all_recent = hub.get_recent_errors()
    assert len(all_recent) == 3

    ollama_recent = hub.get_recent_errors(provider="ollama")
    assert len(ollama_recent) == 1
    assert ollama_recent[0].provider == "ollama"


def test_model_error_hub_listeners() -> None:
    """Проверка вызова зарегистрированных коллбэков-слушателей при фиксации ошибки."""
    hub = ModelErrorHub()
    dispatched: List[ModelErrorEvent] = []

    def on_error(evt: ModelErrorEvent) -> None:
        dispatched.append(evt)

    hub.register_listener(on_error)
    hub.record_error(
        provider="gemini_cli",
        model_name="gemini-3.1-flash-lite",
        error="503 High demand",
        action_taken="retry",
    )

    assert len(dispatched) == 1
    assert dispatched[0].provider == "gemini_cli"

    hub.unregister_listener(on_error)
    hub.record_error(provider="foundry", model_name="qwen2.5-1.5b", error="404 Not Found")
    assert len(dispatched) == 1  # Больше не вызывается после отписки


def test_model_health_summary() -> None:
    """Проверка генерации сводного отчета о здоровье моделей и провайдеров."""
    hub = ModelErrorHub()
    hub.clear()

    hub.record_error("gemini", "gemini-3.1-flash", "503 Unavailable", action_taken="retry")
    hub.record_error("gemini", "gemini-3.1-flash", "429 Quota", action_taken="rotate_key")
    hub.record_error("ollama", "llama3.1", "Connection timed out", action_taken="failed")

    summary = hub.get_health_summary()
    assert "total_errors" in summary
    assert summary["total_errors"] == 3
    assert "by_provider" in summary
    assert summary["by_provider"]["gemini"] == 2
    assert summary["by_provider"]["ollama"] == 1
    assert "by_category" in summary
    assert summary["by_category"]["SERVICE_UNAVAILABLE"] == 1
    assert summary["by_category"]["RATE_LIMIT"] == 1
    assert summary["by_category"]["CONNECTION_ERROR"] == 1


@pytest.mark.asyncio
async def test_gemini_error_mixin_records_to_hub() -> None:
    """Проверка, что GoogleGenerativeAIErrorMixin автоматически логирует ошибки в центральный хаб."""
    from src.ai.gemini.errors import GoogleGenerativeAIErrorMixin
    from src.ai.orchestration.model_error_hub import get_error_hub

    hub = get_error_hub()
    hub.clear()

    class DummyClient(GoogleGenerativeAIErrorMixin):
        def __init__(self):
            self.api_key = "test_key"
            self._key_names_active = ["key1"]
            self._key_errors = {}
            self._last_exception = ""
            self._unavailable_attempts = 0
            self.api_keys = ["test_key"]
            self.api_key_owners = ["owner1"]

        def _record_error(self, ex: Exception | str) -> None:
            self._last_exception = str(ex)

        def _switch_model(self) -> bool:
            return True

        def _switch_api_key(self) -> bool:
            return True

    client = DummyClient()
    ex_503 = Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")
    should_retry = await client._handle_api_error(ex_503, "gemini-3.1-flash-lite-preview", 0, 5)

    assert should_retry is True
    errors = hub.get_recent_errors(provider="gemini")
    assert len(errors) >= 1
    assert errors[0].category == ModelErrorCategory.SERVICE_UNAVAILABLE
    assert errors[0].status_code == 503
    assert errors[0].model_name == "gemini-3.1-flash-lite-preview"


@pytest.mark.asyncio
async def test_router_chat_model_errors_endpoints() -> None:
    """Проверка REST эндпоинтов /api/chat/model-errors и /api/chat/model-health."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.api.router_chat import init_router
    from src.ai.orchestration.model_error_hub import record_model_error, get_error_hub

    hub = get_error_hub()
    hub.clear()

    record_model_error("gemini", "gemini-3.7-flash", "429 Quota Exceeded", status_code=429)

    class DummyModel:
        pass

    chat_router = init_router(DummyModel(), DummyModel())
    test_app = FastAPI()
    test_app.include_router(chat_router)
    client = TestClient(test_app)

    res = client.get("/api/chat/model-errors")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["count"] >= 1
    assert data["errors"][0]["provider"] == "gemini"

    res_health = client.get("/api/chat/model-health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "success"
    assert "health" in health_data



