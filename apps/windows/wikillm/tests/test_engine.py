# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Engine
# =============================================================================
# Description:
#   Тесты для движка WikiLLMEngine, сквозного цикла самообучения (первый вызов Gemini ->
#
# Usage Examples:
#   Python API:
#     import apps.windows.wikillm.tests.test_engine as test_engine
#
# File: test_engine.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для движка WikiLLMEngine, сквозного цикла самообучения (первый вызов Gemini ->"""

import asyncio
import json
from unittest.mock import AsyncMock
import pytest
from apps.windows.wikillm.config import WikiLLMConfig
from apps.windows.wikillm.engine import WikiLLMEngine
from apps.windows.wikillm.models import ArtifactInput, ArtifactType, LookupLevel
from apps.windows.wikillm.storage import WikiStorage
from apps.windows.wikillm.telemetry_bridge import TelemetryWikiBridge


@pytest.mark.asyncio
async def test_progressive_learning_cycle() -> None:
    """Проверка полного цикла прогрессивного обучения:

    1. Первый запрос: UNKNOWN в кэше -> обращение к Gemini -> запись в SQLite.
    2. Второй запрос: KNOWN в SQLite -> Level 1 Exact Match, 0 обращений к Gemini, мгновенно.
    """
    storage = WikiStorage(":memory:")
    mock_chat = AsyncMock()
    mock_gemini_response = {
        "name": "ERROR_ACCESS_DENIED",
        "summary": "Отказано в доступе к системному объекту или ресурсу",
        "category": "security",
        "severity": "error",
        "confidence": 0.92,
        "possible_causes": ["Отсутствие прав администратора", "Блокировка UAC"],
        "diagnostic_actions": [],
        "remediation_steps": [
            {
                "title": "Перезапуск от администратора",
                "description": "Запустить терминал от имени администратора",
                "command": "powershell Start-Process -Verb runAs",
                "risk_level": "safe",
                "is_automated": False,
            }
        ],
        "related_components": ["Security", "UAC"],
        "tags": ["access_denied", "0x80070005"],
    }
    mock_chat.ask.return_value = json.dumps(mock_gemini_response)

    cfg = WikiLLMConfig(database_path=":memory:")
    engine = WikiLLMEngine(config=cfg, storage=storage, chat_model=mock_chat)

    art = ArtifactInput(type=ArtifactType.WINDOWS_ERROR, error_code="0x80070005")

    # --- ПЕРВЫЙ ЗАПРОС (Обучение) ---
    res1 = await engine.resolve(art, sync_gemini=True)
    assert res1.lookup_level == LookupLevel.GEMINI
    assert res1.cached is False
    assert res1.entity is not None
    assert res1.entity.name == "ERROR_ACCESS_DENIED"
    assert mock_chat.ask.call_count == 1

    # --- ВТОРОЙ ЗАПРОС (Мгновенный повтор) ---
    res2 = await engine.resolve(art, sync_gemini=True)
    assert res2.lookup_level == LookupLevel.EXACT
    assert res2.cached is True
    assert res2.entity is not None
    assert res2.entity.name == "ERROR_ACCESS_DENIED"
    # Счётчик вызовов Gemini НЕ увеличился!
    assert mock_chat.ask.call_count == 1

    # --- ТРЕТИЙ ЗАПРОС (Проверка счетчика наблюдений) ---
    res3 = await engine.resolve(art, sync_gemini=True)
    assert res3.lookup_level == LookupLevel.EXACT
    assert mock_chat.ask.call_count == 1

    # Проверка метрик кэша
    metrics = engine.get_metrics()
    assert metrics["lookup_stats"]["total_requests"] == 3
    assert metrics["lookup_stats"]["l1_exact_hits"] == 2
    assert metrics["lookup_stats"]["l4_gemini_resolutions"] == 1
    assert metrics["cache_hit_rate_pct"] > 60.0


@pytest.mark.asyncio
async def test_telemetry_bridge_incident_enrichment() -> None:
    """Проверка обогащения инцидента телеметрии через TelemetryWikiBridge."""
    storage = WikiStorage(":memory:")
    mock_chat = AsyncMock()
    mock_gemini_response = {
        "name": "Disk Anomaly",
        "summary": "Аномальная запись на диск процессом",
        "category": "storage",
        "severity": "warning",
        "confidence": 0.85,
        "possible_causes": ["Интенсивное резервное копирование"],
        "diagnostic_actions": [],
        "remediation_steps": [
            {
                "title": "Проверить диск",
                "description": "Проверить SMART статус",
                "command": "wmic diskdrive get status",
                "risk_level": "safe",
            }
        ],
        "related_components": ["Storage"],
        "tags": ["disk"],
    }
    mock_chat.ask.return_value = json.dumps(mock_gemini_response)

    cfg = WikiLLMConfig(database_path=":memory:")
    engine = WikiLLMEngine(config=cfg, storage=storage, chat_model=mock_chat)
    bridge = TelemetryWikiBridge(engine)

    raw_incident = {
        "id": "inc-123",
        "category": "storage",
        "trigger_type": "disk_burst",
        "description": "Disk write 500MB/s",
        "suspects": [{"name": "system.exe"}],
    }

    enriched = await bridge.enrich_incident(raw_incident, sync_gemini=True)
    assert "wiki_enrichment" in enriched
    assert len(enriched["wiki_enrichment"]["resolved_entities"]) > 0
    assert "Интенсивное резервное копирование" in enriched["wiki_enrichment"]["suggested_causes"]
