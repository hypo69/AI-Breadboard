# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Tests - Test Freshness Auditor
# =============================================================================
# Description:
#   Тесты аудитора актуальности образов восстановления и дрейфа системы.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.tests.test_freshness_auditor import test_assess_freshness_no_images
#
#     res = test_assess_freshness_no_images()
#
# File: test_freshness_auditor.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Тесты аудитора актуальности образов восстановления и дрейфа системы."""

from apps.windows.system_checkpoints.core.freshness_auditor import FreshnessAuditor
from apps.windows.system_checkpoints.models import (
    FreshnessLevel,
    SystemDriftMetrics,
    SystemImageMetadata,
)


def test_assess_freshness_no_images():
    """Проверка оценки актуальности при отсутствии образов."""
    auditor = FreshnessAuditor()
    report = auditor.assess_freshness(latest_image=None)
    assert report.freshness_level == FreshnessLevel.UNKNOWN
    assert report.can_restore_safely is False
    assert "отсутствуют" in report.freshness_label_ru.lower()


def test_assess_freshness_high():
    """Проверка оценки свежего образа (High freshness)."""
    auditor = FreshnessAuditor()
    img = SystemImageMetadata(
        image_path="C:\\Recovery\\Recovery_2026-09-30.wim",
        created_at="2026-09-30 12:00:00",
    )
    drift = SystemDriftMetrics(
        days_since_creation=2,
        changed_components_count=1,
        installed_apps_count=2,
        updated_drivers_count=0,
    )
    report = auditor.assess_freshness(latest_image=img, manual_drift=drift)
    assert report.freshness_level == FreshnessLevel.HIGH
    assert report.can_restore_safely is True
    assert "высокая" in report.freshness_label_ru.lower()


def test_assess_freshness_medium():
    """Проверка оценки умеренно измененного образа (Medium freshness)."""
    auditor = FreshnessAuditor()
    img = SystemImageMetadata(
        image_path="C:\\Recovery\\Recovery_Old.wim",
        created_at="2026-08-01 12:00:00",
    )
    drift = SystemDriftMetrics(
        days_since_creation=60,
        changed_components_count=10,
        installed_apps_count=15,
        updated_drivers_count=2,
    )
    report = auditor.assess_freshness(latest_image=img, manual_drift=drift)
    assert report.freshness_level == FreshnessLevel.MEDIUM
    assert report.can_restore_safely is True


def test_assess_freshness_critical_outdated():
    """Проверка оценки критически устаревшего образа."""
    auditor = FreshnessAuditor()
    img = SystemImageMetadata(
        image_path="C:\\Recovery\\Recovery_Ancient.wim",
        created_at="2025-01-01 12:00:00",
    )
    drift = SystemDriftMetrics(
        days_since_creation=300,
        changed_components_count=40,
        installed_apps_count=50,
        updated_drivers_count=15,
    )
    report = auditor.assess_freshness(latest_image=img, manual_drift=drift)
    assert report.freshness_level == FreshnessLevel.CRITICAL_OUTDATED
    assert report.can_restore_safely is False
