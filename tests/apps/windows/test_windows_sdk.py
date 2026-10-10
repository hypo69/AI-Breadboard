# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Windows SDK Test Suite
# =============================================================================
# Description:
#   Комплексные модульные тесты для единого Windows SDK (Software Development Kit).
#   Проверяют инициализацию фасада WindowsSDK, доступ к нативному C-FFI уровню,
#   ядру SafeOps, драйверному слою, Windows Features и доменным подсистемам.
#
# Usage Examples:
#   pytest tests/apps/windows/test_windows_sdk.py -v
#
# File: test_windows_sdk.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:45:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для единого Windows SDK."""

import pytest
from apps.windows.sdk import WindowsSDK, windows_sdk
from apps.windows.sdk.drivers import VendorType, DriverBranch, DriverRelease
from apps.windows.sdk.native import Kernel32, Advapi32, WindowsErrorDecoder


class TestWindowsSDK:
    """Тестовый набор для проверки функционала единого Windows SDK."""

    def test_sdk_singleton_initialization(self) -> None:
        """Проверка успешной инициализации глобального экземпляра SDK."""
        assert windows_sdk is not None
        assert isinstance(windows_sdk, WindowsSDK)
        assert windows_sdk.native is not None
        assert windows_sdk.drivers is not None
        assert windows_sdk.features is not None
        assert windows_sdk.core is not None
        assert windows_sdk.modules is not None

    def test_native_subsystem_access(self) -> None:
        """Проверка доступа к низкоуровневым нативным C-FFI биндингам."""
        assert windows_sdk.native.kernel32 is not None
        assert windows_sdk.native.advapi32 is not None
        assert windows_sdk.native.psapi is not None
        assert windows_sdk.native.pdh is not None
        assert windows_sdk.native.wevtapi is not None

        # Проверка декодера ошибок
        msg = WindowsErrorDecoder().format_system_error(0)
        assert isinstance(msg, str)

    def test_drivers_subsystem(self) -> None:
        """Проверка функционала каталогов драйверов и детектора GPU."""
        detector = windows_sdk.drivers.detector
        assert detector is not None

        # Проверка нормализации версии драйвера NVIDIA
        raw_nv = "32.0.15.6094"
        formatted_nv = detector.format_driver_version(raw_nv, VendorType.NVIDIA)
        assert formatted_nv == "560.94"

        # Проверка каталога релизов NVIDIA
        releases = windows_sdk.drivers.nvidia_catalog.get_releases()
        assert len(releases) > 0
        assert isinstance(releases[0], DriverRelease)

    def test_features_subsystem(self) -> None:
        """Проверка методов управления Windows Optional Features."""
        features_sub = windows_sdk.features
        assert hasattr(features_sub, "get_features")
        assert hasattr(features_sub, "enable_feature")
        assert hasattr(features_sub, "disable_feature")

    def test_core_subsystem_and_safeops(self) -> None:
        """Проверка ядра SafeOps, WinAPI и системной диагностики."""
        core = windows_sdk.core
        assert core.winapi is not None
        assert core.safe_executor is not None
        assert core.diagnostics is not None
        assert core.correlation is not None
        assert core.system32_catalog is not None

    def test_modules_subsystem_lazy_properties(self) -> None:
        """Проверка доступа к доменным модулям администрирования через свойства."""
        modules = windows_sdk.modules
        assert modules.hardware is not None
        assert modules.network is not None
        assert modules.storage is not None
        assert modules.defender is not None
        assert modules.firewall is not None
        assert modules.services is not None
        assert modules.task_scheduler is not None
        assert modules.registry is not None
        assert modules.process_manager is not None
        assert modules.taskbar is not None
        assert modules.window_control_plane is not None

    def test_get_health_summary(self) -> None:
        """Проверка вызова метода получения сводки здоровья системы."""
        summary = windows_sdk.get_health_summary()
        assert isinstance(summary, dict)
