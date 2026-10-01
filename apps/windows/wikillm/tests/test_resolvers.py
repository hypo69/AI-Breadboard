# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Resolvers
# =============================================================================
# Description:
#   Тесты для 4 уровней резолверов (Exact, Fingerprint, Semantic, Gemini).
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_resolvers import storage
#
#     res = storage()
#
# File: test_resolvers.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для 4 уровней резолверов (Exact, Fingerprint, Semantic, Gemini)."""

import json
from unittest.mock import AsyncMock
import pytest
from apps.windows.wikillm.models import (
    ArtifactInput,
    ArtifactType,
    KnowledgeEntity,
    LookupLevel,
)
from apps.windows.wikillm.normalizer import CanonicalKeyNormalizer
from apps.windows.wikillm.resolvers.exact import ExactResolver
from apps.windows.wikillm.resolvers.fingerprint import FingerprintResolver
from apps.windows.wikillm.resolvers.gemini import GeminiKnowledgeResolver
from apps.windows.wikillm.resolvers.semantic import SemanticResolver
from apps.windows.wikillm.storage import WikiStorage


@pytest.fixture
def storage() -> WikiStorage:
    """Изолированное хранилище."""
    return WikiStorage(":memory:")


@pytest.mark.asyncio
async def test_exact_resolver_hit_and_miss(storage: WikiStorage) -> None:
    """Проверка Level 1 ExactResolver."""
    resolver = ExactResolver(storage)

    art = ArtifactInput(
        type=ArtifactType.WINDOWS_EVENT,
        provider="DistributedCOM",
        event_id=10016,
    )
    # 1. До сохранения - промах
    assert await resolver.resolve(art) is None

    # 2. Сохраняем сущность
    storage.save_entity(
        KnowledgeEntity(
            canonical_key="windows_event:DistributedCOM:10016",
            entity_type=ArtifactType.WINDOWS_EVENT,
            name="DCOM 10016",
            summary="DCOM Warning",
        )
    )

    # 3. После сохранения - точный хит
    res = await resolver.resolve(art)
    assert res is not None
    assert res.canonical_key == "windows_event:DistributedCOM:10016"


@pytest.mark.asyncio
async def test_fingerprint_resolver(storage: WikiStorage) -> None:
    """Проверка Level 2 FingerprintResolver."""
    resolver = FingerprintResolver(storage)

    template_art = ArtifactInput(
        provider="TestProv",
        event_id=5000,
        message="Failure in 0x7FFE1234 with GUID {12345678-1234-1234-1234-123456789abc}",
    )
    fp = CanonicalKeyNormalizer.compute_fingerprint(template_art)

    storage.save_entity(
        KnowledgeEntity(
            canonical_key="test:5000",
            entity_type=ArtifactType.WINDOWS_EVENT,
            name="Test Event",
            summary="Test summary",
            fingerprint=fp,
        )
    )

    # Приходит запрос с ДРУГИМ адресом и GUID, но тем же шаблоном
    incoming_art = ArtifactInput(
        provider="TestProv",
        event_id=5000,
        message="Failure in 0x7FFE9999 with GUID {87654321-4321-4321-4321-cba987654321}",
    )
    res = await resolver.resolve(incoming_art)
    assert res is not None
    assert res.canonical_key == "test:5000"


@pytest.mark.asyncio
async def test_semantic_resolver(storage: WikiStorage) -> None:
    """Проверка Level 3 SemanticResolver."""
    resolver = SemanticResolver(storage)

    storage.save_entity(
        KnowledgeEntity(
            canonical_key="win32:0x80070005",
            entity_type=ArtifactType.WINDOWS_ERROR,
            name="Access Denied",
            summary="Отказано в доступе из-за отсутствия привилегий администратора",
        )
    )

    art = ArtifactInput(raw_query="отсутствия привилегий администратора")
    res = await resolver.resolve(art)
    assert res is not None
    assert res.canonical_key == "win32:0x80070005"


@pytest.mark.asyncio
async def test_gemini_resolver_with_mock() -> None:
    """Проверка Level 4 GeminiKnowledgeResolver со структурированным JSON ответом."""
    mock_chat = AsyncMock()
    mock_payload = {
        "name": "ERROR_NOT_FOUND",
        "summary": "Элемент не найден в хранилище компонентов Windows",
        "category": "system",
        "severity": "error",
        "confidence": 0.88,
        "possible_causes": ["Повреждение хранилища WinSxS", "Неверный путь обновления"],
        "diagnostic_actions": [
            {
                "title": "Проверка DISM",
                "description": "Запуск сканирования хранилища",
                "command": "DISM.exe /Online /Cleanup-image /ScanHealth",
                "risk_level": "safe",
                "is_automated": True,
            }
        ],
        "remediation_steps": [
            {
                "title": "Восстановление DISM",
                "description": "Восстановление поврежденных компонентов",
                "command": "DISM.exe /Online /Cleanup-image /RestoreHealth",
                "risk_level": "safe",
                "is_automated": True,
            }
        ],
        "related_components": ["DISM", "WinSxS", "CBS"],
        "tags": ["dism", "winsxs", "0x80070490"],
    }
    mock_chat.ask.return_value = json.dumps(mock_payload)

    resolver = GeminiKnowledgeResolver(chat_model=mock_chat)
    art = ArtifactInput(type=ArtifactType.WINDOWS_ERROR, error_code="0x80070490")

    res = await resolver.resolve(art)
    assert res is not None
    assert res.canonical_key == "win32:0x80070490"
    assert res.name == "ERROR_NOT_FOUND"
    assert res.diagnostic_info is not None
    assert len(res.diagnostic_info.remediation_steps) == 1
    assert "DISM" in res.diagnostic_info.remediation_steps[0].command
    assert res.confidence == 0.88
