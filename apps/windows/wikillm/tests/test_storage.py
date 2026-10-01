# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Storage
# =============================================================================
# Description:
#   Тесты для SQLite хранилища, FTS5 поиска, наблюдений и связей сущностей.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_storage import memory_storage
#
#     res = memory_storage()
#
# File: test_storage.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для SQLite хранилища, FTS5 поиска, наблюдений и связей сущностей."""

import pytest
from apps.windows.wikillm.models import (
    ArtifactType,
    Claim,
    DiagnosticKnowledge,
    Evidence,
    KnowledgeEntity,
    KnowledgeSource,
    ResolutionAction,
)
from apps.windows.wikillm.storage import WikiStorage


@pytest.fixture
def memory_storage() -> WikiStorage:
    """Фикстура изолированного хранилища в памяти."""
    return WikiStorage(":memory:")


def test_save_and_get_entity(memory_storage: WikiStorage) -> None:
    """Проверка сохранения и загрузки полной сущности базы знаний."""
    diag = DiagnosticKnowledge(
        possible_causes=["Недостаточно прав DCOM"],
        remediation_steps=[
            ResolutionAction(
                title="Настроить dcomcnfg",
                description="Открыть Component Services и настроить права",
                command="dcomcnfg",
                risk_level="safe",
            )
        ],
        related_components=["DistributedCOM", "svchost.exe"],
    )

    entity = KnowledgeEntity(
        canonical_key="windows_event:DistributedCOM:10016",
        entity_type=ArtifactType.WINDOWS_EVENT,
        name="DCOM Permission Warning",
        summary="Параметры разрешений для конкретного приложения не дают разрешения Локально Активация",
        category="system",
        severity="warning",
        confidence=0.9,
        provenance_source=KnowledgeSource.OBSERVED,
        fingerprint="dcom_10016_fp",
        diagnostic_info=diag,
        claims=[
            Claim(statement="Обычно безвредно для работы системы", confidence=0.95, verified=True)
        ],
        evidence=[
            Evidence(description="Наблюдалось при запуске DCOM сервера", sample_value="AppID {1234}")
        ],
        tags=["dcom", "event10016"],
    )

    memory_storage.save_entity(entity)

    loaded = memory_storage.get_entity("windows_event:DistributedCOM:10016")
    assert loaded is not None
    assert loaded.name == "DCOM Permission Warning"
    assert loaded.severity == "warning"
    assert loaded.diagnostic_info is not None
    assert len(loaded.diagnostic_info.remediation_steps) == 1
    assert loaded.diagnostic_info.remediation_steps[0].command == "dcomcnfg"
    assert len(loaded.claims) == 1
    assert loaded.claims[0].verified is True


def test_find_by_fingerprint(memory_storage: WikiStorage) -> None:
    """Проверка поиска по отпечатку."""
    entity = KnowledgeEntity(
        canonical_key="win32:0x80070490",
        entity_type=ArtifactType.WINDOWS_ERROR,
        name="ERROR_NOT_FOUND",
        summary="Элемент не найден",
        fingerprint="fp_0x80070490_test",
    )
    memory_storage.save_entity(entity)

    found = memory_storage.find_by_fingerprint("fp_0x80070490_test")
    assert found is not None
    assert found.canonical_key == "win32:0x80070490"


def test_fts5_search(memory_storage: WikiStorage) -> None:
    """Проверка полнотекстового поиска FTS5."""
    entity1 = KnowledgeEntity(
        canonical_key="service:wuauserv",
        entity_type=ArtifactType.SERVICE,
        name="Windows Update Service",
        summary="Служба автоматического обновления операционной системы Windows",
        tags=["updates", "windows_update"],
    )
    entity2 = KnowledgeEntity(
        canonical_key="service:spooler",
        entity_type=ArtifactType.SERVICE,
        name="Print Spooler",
        summary="Диспетчер очереди печати принтеров",
        tags=["print", "spooler"],
    )
    memory_storage.save_entity(entity1)
    memory_storage.save_entity(entity2)

    results = memory_storage.search_fts("автоматического обновления")
    assert len(results) == 1
    assert results[0].canonical_key == "service:wuauserv"


def test_record_observations_and_co_occurrences(memory_storage: WikiStorage) -> None:
    """Проверка счетчиков наблюдений и графа совместных появлений."""
    obs1 = memory_storage.record_observation("process:svchost.exe", co_occurring_keys=["service:dcom"])
    assert obs1.total_occurrences == 1
    assert obs1.co_occurrences.get("service:dcom") == 1

    obs2 = memory_storage.record_observation(
        "process:svchost.exe", co_occurring_keys=["service:dcom", "win32:0x80070005"]
    )
    assert obs2.total_occurrences == 2
    assert obs2.co_occurrences.get("service:dcom") == 2
    assert obs2.co_occurrences.get("win32:0x80070005") == 1

    stats = memory_storage.get_stats()
    assert stats["total_observation_events"] == 2
