# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Tests - Test Coordinator
# =============================================================================
# Description:
#   Тесты главного координатора контрольных точек системы.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.tests.test_coordinator import test_coordinator_catalog_save_and_load
#
#     res = test_coordinator_catalog_save_and_load()
#
# File: test_coordinator.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Тесты главного координатора контрольных точек системы."""

from unittest.mock import MagicMock, patch
from apps.windows.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator
from apps.windows.system_checkpoints.models import (
    CheckpointCreateRequest,
    CheckpointType,
    RecoveryMechanism,
    SystemCheckpointRecord,
    WinREStatus,
)


def test_coordinator_catalog_save_and_load(tmp_path):
    """Проверка сохранения и чтения каталога контрольных точек."""
    cat_file = tmp_path / "catalog.json"
    coordinator = CheckpointCoordinator(catalog_path=str(cat_file))

    record = SystemCheckpointRecord(
        checkpoint_id="chk_test_001",
        checkpoint_type=CheckpointType.BASELINE,
        mechanisms=[RecoveryMechanism.SYSTEM_IMAGE, RecoveryMechanism.RESTORE_POINT],
        created_at="2026-09-30 12:00:00",
        title="Тестовая базовая точка",
        description="Описание теста",
    )
    saved = coordinator.save_catalog([record])
    assert saved is True

    loaded = coordinator.load_catalog()
    assert len(loaded) == 1
    assert loaded[0].checkpoint_id == "chk_test_001"
    assert loaded[0].checkpoint_type == CheckpointType.BASELINE
    assert RecoveryMechanism.SYSTEM_IMAGE in loaded[0].mechanisms


def test_coordinator_delete_checkpoint(tmp_path):
    """Проверка удаления точки из каталога."""
    cat_file = tmp_path / "catalog.json"
    coordinator = CheckpointCoordinator(catalog_path=str(cat_file))

    rec1 = SystemCheckpointRecord(
        checkpoint_id="chk_1",
        checkpoint_type=CheckpointType.BASELINE,
        mechanisms=[RecoveryMechanism.RESTORE_POINT],
        created_at="2026-09-30 10:00:00",
        title="Точка 1",
    )
    rec2 = SystemCheckpointRecord(
        checkpoint_id="chk_2",
        checkpoint_type=CheckpointType.PERIODIC,
        mechanisms=[RecoveryMechanism.RESTORE_POINT],
        created_at="2026-09-30 11:00:00",
        title="Точка 2",
    )
    coordinator.save_catalog([rec1, rec2])

    deleted = coordinator.delete_checkpoint("chk_1")
    assert deleted is True
    assert len(coordinator.load_catalog()) == 1
    assert coordinator.load_catalog()[0].checkpoint_id == "chk_2"


def test_coordinator_create_checkpoint_mock(tmp_path):
    """Проверка создания контрольной точки через координатора с моками."""
    cat_file = tmp_path / "catalog.json"
    coordinator = CheckpointCoordinator(catalog_path=str(cat_file))

    mock_sr = MagicMock()
    mock_sr.create_restore_point.return_value = {"success": True, "description": "🟢 [Базовая] Чистая Windows"}
    mock_sr.list_restore_points.return_value = [{"sequence_number": 101}]

    with patch.object(coordinator, "_get_restore_manager", return_value=mock_sr):
        req = CheckpointCreateRequest(
            checkpoint_type=CheckpointType.BASELINE,
            title="Чистая Windows",
            description="Свежая установка",
            create_restore_point=True,
            create_wim_image=False,
        )
        res = coordinator.create_checkpoint(req)

        assert res["success"] is True
        assert "chk_" in res["checkpoint_id"]
        assert len(coordinator.load_catalog()) == 1


def test_coordinator_comprehensive_health(tmp_path):
    """Проверка сводного отчета здоровья системы."""
    cat_file = tmp_path / "catalog.json"
    coordinator = CheckpointCoordinator(catalog_path=str(cat_file))

    with patch.object(coordinator.winre_manager, "get_status", return_value=WinREStatus(enabled=True)):
        health = coordinator.get_comprehensive_health()
        assert "health_score" in health
        assert health["winre"]["enabled"] is True
        assert "system_restore" in health
        assert "freshness" in health
