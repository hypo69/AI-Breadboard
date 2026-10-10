# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Closed Loop Remediation
# =============================================================================
# Description:
#   Тестирование замкнутого контура самоисцеления ClosedLoopAutoRemediationEngine.
#
# File: test_closed_loop_remediation.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:05:00
# =============================================================================

"""Юнит-тесты для замкнутого цикла самоисцеления ClosedLoopAutoRemediationEngine."""

import pytest
from apps.windows.sdk.core.closed_loop_remediation import ClosedLoopAutoRemediationEngine, RemediationLoopReport
from apps.windows.sdk.core.data_model import SystemState, MemoryInfo
from apps.windows.sdk.core.models import RemediationAction, ActionType, RiskLevel


@pytest.fixture
def sample_state() -> SystemState:
    """Фикстура создаёт валидное состояние системы."""
    return SystemState(
        hostname='TEST-REMEDIATION-PC',
        system_memory=MemoryInfo(working_set=2 * 1024 * 1024 * 1024)
    )


def test_closed_loop_remediation_success(sample_state: SystemState):
    """Проверяет прохождение успешного замкнутого цикла самоисцеления."""
    engine = ClosedLoopAutoRemediationEngine()
    action = RemediationAction(
        action_id='test_clean_temp',
        action_type=ActionType.CLEAN_DIRECTORY,
        title='Очистка Temp',
        description='Удаление временных файлов',
        target='C:\\Temp',
        risk=RiskLevel.SAFE,
        execution_command='echo cleaned'
    )
    
    report = engine.run_remediation_loop(action, sample_state)
    
    assert isinstance(report, RemediationLoopReport)
    assert report.action_id == 'test_clean_temp'
    assert report.backup_created is True
    assert report.executed_successfully is True
    assert report.rolled_back is False
    assert report.final_health_score >= 0.0


def test_calculate_health_score(sample_state: SystemState):
    """Проверяет расчет интегрального индекса здоровья системы."""
    engine = ClosedLoopAutoRemediationEngine()
    score = engine.calculate_health_score(sample_state)
    assert 0.0 <= score <= 100.0
