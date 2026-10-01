# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Tests - Test Models
# =============================================================================
# Description:
#   Тесты моделей данных системы контрольных точек Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.system_checkpoints.tests.test_models import test_enums
#
#     res = test_enums()
#
# File: test_models.py
# Project: ai-breadboard
# Package: apps.windows.modules.system_checkpoints.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Тесты моделей данных системы контрольных точек Windows."""

from apps.windows.system_checkpoints.models import (
    CheckpointType,
    RecoveryMechanism,
    FreshnessLevel,
    SystemDriftMetrics,
    FreshnessReport,
    WinREStatus,
    SystemImageMetadata,
    SystemCheckpointRecord,
    CheckpointCreateRequest,
)


def test_enums():
    """Проверка доступности всех типов контрольных точек и уровней свежести."""
    assert CheckpointType.BASELINE.value == "BASELINE"
    assert CheckpointType.POST_CONFIG.value == "POST_CONFIG"
    assert CheckpointType.PRE_UPDATE.value == "PRE_UPDATE"
    assert CheckpointType.PRE_EXPERIMENT.value == "PRE_EXPERIMENT"
    assert CheckpointType.PERIODIC.value == "PERIODIC"

    assert RecoveryMechanism.SYSTEM_IMAGE.value == "SYSTEM_IMAGE"
    assert RecoveryMechanism.WINRE_ENVIRONMENT.value == "WINRE"
    assert RecoveryMechanism.RESTORE_POINT.value == "RESTORE_POINT"

    assert FreshnessLevel.HIGH.value == "HIGH"
    assert FreshnessLevel.MEDIUM.value == "MEDIUM"
    assert FreshnessLevel.LOW.value == "LOW"
    assert FreshnessLevel.CRITICAL_OUTDATED.value == "CRITICAL"


def test_system_image_metadata_gb():
    """Проверка расчета размера WIM-образа в гигабайтах."""
    meta = SystemImageMetadata(
        image_path="C:\\Recovery\\test.wim",
        file_size_bytes=10 * (1024 ** 3),
        created_at="2026-09-30 12:00:00",
        is_baseline=True,
    )
    assert meta.file_size_gb == 10.0
    d = meta.to_dict()
    assert d["file_size_gb"] == 10.0
    assert d["is_baseline"] is True


def test_system_drift_metrics_dict():
    """Проверка сериализации метрик дрейфа системы."""
    drift = SystemDriftMetrics(
        days_since_creation=5,
        changed_components_count=2,
        installed_apps_count=1,
        updated_drivers_count=0,
        recent_kbs=["KB5001234"],
        recent_apps=["VSCode"],
    )
    d = drift.to_dict()
    assert d["days_since_creation"] == 5
    assert d["changed_components_count"] == 2
    assert d["installed_apps_count"] == 1
    assert "KB5001234" in d["recent_kbs"]


def test_freshness_report_dict():
    """Проверка сериализации отчета актуальности."""
    report = FreshnessReport(
        last_image_name="Recovery_2026-09-30.wim",
        last_image_date="2026-09-30 10:00:00",
        age_days=0,
        freshness_level=FreshnessLevel.HIGH,
        freshness_label_ru="Высокая (образ актуален)",
        can_restore_safely=True,
    )
    d = report.to_dict()
    assert d["last_image_name"] == "Recovery_2026-09-30.wim"
    assert d["freshness_level"] == "HIGH"
    assert d["can_restore_safely"] is True


def test_checkpoint_create_request_validation():
    """Проверка валидации Pydantic модели запроса."""
    req = CheckpointCreateRequest(
        checkpoint_type=CheckpointType.BASELINE,
        title="Чистая Windows",
        create_restore_point=True,
        create_wim_image=True,
    )
    assert req.checkpoint_type == CheckpointType.BASELINE
    assert req.title == "Чистая Windows"
    assert req.create_restore_point is True
