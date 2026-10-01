# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Apps Windows - Test Sampling Controller
# =============================================================================
# Description:
#   Тесты контроллера режимов опроса телеметрии.
#
# Usage Examples:
#   Python API:
#     from tests.apps.windows.test_sampling_controller import test_sampling_controller_boot_curve
#
#     res = test_sampling_controller_boot_curve()
#
# File: test_sampling_controller.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тесты контроллера режимов опроса телеметрии."""

import time
import pytest
from apps.windows.telemetry.models import SamplingMode
from apps.windows.telemetry.sampling_controller import SamplingController


def test_sampling_controller_boot_curve():
    """Проверяет изменение интервалов в режиме BOOT_AGGRESSIVE в зависимости от аптайма."""
    now = time.time()

    # 1. Свежий старт (300 сек аптайма < 10 мин) -> 1.0 сек
    ctrl1 = SamplingController(initial_mode=SamplingMode.BOOT_AGGRESSIVE, boot_epoch=now - 300)
    assert ctrl1.get_current_interval() == 1.0

    # 2. 30 мин аптайма -> 5.0 сек
    ctrl2 = SamplingController(initial_mode=SamplingMode.BOOT_AGGRESSIVE, boot_epoch=now - 1800)
    assert ctrl2.get_current_interval() == 5.0

    # 3. 5 часов аптайма -> 30.0 сек
    ctrl3 = SamplingController(initial_mode=SamplingMode.BOOT_AGGRESSIVE, boot_epoch=now - 18000)
    assert ctrl3.get_current_interval() == 30.0


def test_sampling_controller_incident_mode():
    """Проверяет переключение в режим инцидента и возврат по истечении времени."""
    ctrl = SamplingController(initial_mode=SamplingMode.MONITORING)
    assert ctrl.get_current_interval() == 30.0

    # Включаем INCIDENT на короткое время
    ctrl.trigger_incident_mode(duration_seconds=0.1)
    assert ctrl.mode == SamplingMode.INCIDENT
    assert ctrl.get_current_interval() == 1.0

    time.sleep(0.15)
    # После сна режим должен автоматически сброситься на MONITORING
    assert ctrl.mode == SamplingMode.MONITORING
    assert ctrl.get_current_interval() == 30.0
