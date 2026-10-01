# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Router
# =============================================================================
# Description:
#   Тесты для REST API эндпоинтов WikiLLM с использованием TestClient.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_router import client
#
#     res = client()
#
# File: test_router.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для REST API эндпоинтов WikiLLM с использованием TestClient."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.windows.wikillm.config import WikiLLMConfig
from apps.windows.wikillm.engine import WikiLLMEngine
from apps.windows.wikillm.models import ArtifactType, KnowledgeEntity
from apps.windows.wikillm.router import init_router
from apps.windows.wikillm.storage import WikiStorage


@pytest.fixture
def client() -> TestClient:
    """Фикстура TestClient с изолированным движком WikiLLM."""
    app = FastAPI()
    storage = WikiStorage(":memory:")
    cfg = WikiLLMConfig(database_path=":memory:")
    engine = WikiLLMEngine(config=cfg, storage=storage)

    # Предзаполняем тестовой сущностью
    storage.save_entity(
        KnowledgeEntity(
            canonical_key="win32:0x80070005",
            entity_type=ArtifactType.WINDOWS_ERROR,
            name="Access Denied",
            summary="Access is denied test error",
            tags=["access", "security"],
        )
    )

    router = init_router(engine)
    app.include_router(router)
    return TestClient(app)


def test_resolve_endpoint(client: TestClient) -> None:
    """Проверка POST /api/windows/wikillm/resolve."""
    response = client.post(
        "/api/windows/wikillm/resolve",
        json={"raw_query": "0x80070005", "sync_gemini": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_key"] == "win32:0x80070005"
    assert data["cached"] is True
    assert data["lookup_level"] == "exact"
    assert data["entity"]["name"] == "Access Denied"


def test_get_entity_endpoint(client: TestClient) -> None:
    """Проверка GET /api/windows/wikillm/entities/{key}."""
    response = client.get("/api/windows/wikillm/entities/win32:0x80070005")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_key"] == "win32:0x80070005"
    assert data["name"] == "Access Denied"


def test_list_entities_endpoint(client: TestClient) -> None:
    """Проверка GET /api/windows/wikillm/entities."""
    response = client.get("/api/windows/wikillm/entities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_search_endpoint(client: TestClient) -> None:
    """Проверка GET /api/windows/wikillm/search."""
    response = client.get("/api/windows/wikillm/search", params={"q": "Access denied"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["canonical_key"] == "win32:0x80070005"


def test_stats_endpoint(client: TestClient) -> None:
    """Проверка GET /api/windows/wikillm/stats."""
    response = client.get("/api/windows/wikillm/stats")
    assert response.status_code == 200
    data = response.json()
    assert "lookup_stats" in data
    assert "storage_stats" in data
