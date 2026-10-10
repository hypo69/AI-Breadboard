# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - WikiLLM Command Knowledge Test
# =============================================================================
# Description:
#   Модульные тесты для подсистемы WikiLLM: индексация команд, скриптов, коллекторов
#   телеметрии и прогрессивное разрешение (Exact, Fingerprint, Semantic).
#
# Usage Examples:
#   pytest tests/apps/windows/test_wikillm_command_knowledge.py -v
#
# File: test_wikillm_command_knowledge.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 07:57:30
# =============================================================================

from __future__ import annotations
"""Модульные тесты для базы знаний команд и телеметрии WikiLLM."""

import os
from pathlib import Path
import pytest

from apps.windows.wikillm.models import ArtifactInput, ArtifactType, LookupLevel
from apps.windows.wikillm.storage import WikiStorage
from apps.windows.wikillm.engine import WikiLLMEngine
from apps.windows.wikillm.command_indexer import CommandKnowledgeIndexer
from apps.windows.wikillm.normalizer import CanonicalKeyNormalizer


@pytest.fixture
def temp_wikillm_db(tmp_path: Path):
    """Фикстура для изолированной временной базы данных SQLite WikiLLM."""
    db_file = tmp_path / "test_knowledge.db"
    storage = WikiStorage(db_path=db_file)
    engine = WikiLLMEngine(storage=storage)
    indexer = CommandKnowledgeIndexer(storage=storage)
    yield storage, engine, indexer


def test_command_knowledge_indexing_all(temp_wikillm_db):
    """Проверка полной индексации команд, коллекторов, параметров и System32 утилит."""
    storage, engine, indexer = temp_wikillm_db
    
    results = indexer.index_all()
    assert results["atomic_capabilities"] > 0
    assert results["telemetry_collectors"] == 15
    assert results["system_params"] >= 8
    assert results["system32_tools"] >= 100
    assert results["total_commands_indexed"] > 150


@pytest.mark.asyncio
async def test_command_exact_resolution(temp_wikillm_db):
    """Проверка $O(1)$ точного разрешения атомарных команд по каноническому ключу."""
    storage, engine, indexer = temp_wikillm_db
    indexer.index_atomic_capabilities()
    
    # Разрешение команды списка дисков
    res = await engine.resolve("cmd:diskpart.disk.list")
    assert res is not None
    assert res.lookup_level == LookupLevel.EXACT
    assert res.entity is not None
    assert res.entity.entity_type == ArtifactType.COMMAND
    assert len(res.entity.diagnostic_info.remediation_steps) > 0
    assert "diskpart" in res.entity.diagnostic_info.remediation_steps[0].command


@pytest.mark.asyncio
async def test_collector_resolution(temp_wikillm_db):
    """Проверка разрешения коллекторов телеметрии по каноническому префиксу collector:"""
    storage, engine, indexer = temp_wikillm_db
    indexer.index_telemetry_collectors()
    
    res = await engine.resolve("collector:driver")
    assert res is not None
    assert res.lookup_level == LookupLevel.EXACT
    assert "driver" in res.entity.canonical_key
    assert "apps.windows.sdk.core.audits.driver_collector.collect()" in res.entity.diagnostic_info.remediation_steps[0].command


@pytest.mark.asyncio
async def test_system32_tool_resolution(temp_wikillm_db):
    """Проверка разрешения системных утилит System32 (sys32:netstat)."""
    storage, engine, indexer = temp_wikillm_db
    indexer.index_system32_catalog()
    
    res = await engine.resolve("sys32:netstat")
    assert res is not None
    assert res.lookup_level == LookupLevel.EXACT
    assert res.entity.name == "netstat.exe"
    assert "network_basic" in res.entity.category


def test_semantic_search_commands(temp_wikillm_db):
    """Проверка полнотекстового семантического поиска команд телеметрии через FTS5."""
    storage, engine, indexer = temp_wikillm_db
    indexer.index_all()
    
    # Поиск по ключевым словам на русском языке
    search_results = storage.search_fts("драйверы устройств PnP", limit=5)
    assert len(search_results) > 0
    
    # Проверяем, что в выдаче есть сущность коллектора драйверов
    keys = [item.canonical_key for item in search_results]
    assert any("driver" in k for k in keys)


def test_normalizer_prefixes():
    """Проверка нормализации префиксов команд и коллекторов."""
    assert CanonicalKeyNormalizer.compute_canonical_key(ArtifactInput(raw_query="cmd:diskpart.disk.list")) == "cmd:diskpart.disk.list"
    assert CanonicalKeyNormalizer.compute_canonical_key(ArtifactInput(raw_query="collector:storage")) == "collector:storage"
    assert CanonicalKeyNormalizer.compute_canonical_key(ArtifactInput(raw_query="sys32:tasklist.exe")) == "sys32:tasklist"
    assert CanonicalKeyNormalizer.compute_canonical_key(ArtifactInput(raw_query="sys_param:UAC_LEVEL")) == "sys_param:uac_level"
