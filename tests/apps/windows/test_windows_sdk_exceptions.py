# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Windows SDK Exceptions Hierarchy Suite
# =============================================================================
# Description:
#   Модульные тесты для проверки типизированной иерархии исключений Windows SDK.
#   Проверяют базовый класс WindowsSDKError, сериализацию в to_dict,
#   коды ошибок Win32NativeError, наследование SafeOps и доменных сбоев.
#
# Usage Examples:
#   pytest tests/apps/windows/test_windows_sdk_exceptions.py -v
#
# File: test_windows_sdk_exceptions.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 07:16:00
# =============================================================================

from __future__ import annotations
"""Модульные тесты для иерархии исключений Windows SDK."""

import pytest
from apps.windows.sdk.exceptions import (
    WindowsSDKError,
    NativeCallError,
    Win32NativeError,
    AccessDeniedSDKError,
    PrivilegeElevationRequiredError,
    InvalidHandleError,
    SafeOpsViolationError,
    DryRunExecutionError,
    SystemRestorePointError,
    DiagnosticEngineError,
    DriverSubsystemError,
    DriverNotFoundError,
    WindowsFeatureError,
    FeatureNotFoundError,
    ModuleOperationError,
    RegistryAccessError,
    ServiceControlError,
    TaskSchedulerError,
    ProcessOperationError,
    ExplorerManagerError,
    ShellNamespaceError,
    BackupOperationError,
)


class TestWindowsSDKExceptions:
    """Тестовый набор для проверки иерархии исключений Windows SDK."""

    def test_base_sdk_error_and_serialization(self) -> None:
        """Проверка базового класса WindowsSDKError и метода to_dict."""
        err = WindowsSDKError(
            message="Тестовая ошибка SDK",
            details={"param": "value", "step": 1},
            error_code=500,
        )
        assert isinstance(err, Exception)
        assert err.message == "Тестовая ошибка SDK"
        assert err.error_code == 500
        assert err.details["step"] == 1

        d = err.to_dict()
        assert d["error_type"] == "WindowsSDKError"
        assert d["message"] == "Тестовая ошибка SDK"
        assert d["error_code"] == 500
        assert d["details"]["param"] == "value"

    def test_native_win32_exceptions_hierarchy(self) -> None:
        """Проверка нативных Win32 исключений и кодов ошибок."""
        win_err = Win32NativeError("Сбой открытия дескриптора", win32_code=2)
        assert isinstance(win_err, NativeCallError)
        assert isinstance(win_err, WindowsSDKError)
        assert win_err.win32_code == 2
        assert "0x00000002" in win_err.hex_code

        # Access Denied
        access_err = AccessDeniedSDKError()
        assert isinstance(access_err, Win32NativeError)
        assert isinstance(access_err, NativeCallError)
        assert access_err.win32_code == 5

        # Privilege Elevation Required
        uac_err = PrivilegeElevationRequiredError("Требуется запуск от администратора")
        assert isinstance(uac_err, AccessDeniedSDKError)
        assert isinstance(uac_err, WindowsSDKError)

        # Invalid Handle
        handle_err = InvalidHandleError("Недействительный HWND")
        assert isinstance(handle_err, NativeCallError)

    def test_safeops_exceptions_hierarchy(self) -> None:
        """Проверка исключений ядра SafeOps и симуляции."""
        safe_err = SafeOpsViolationError("Действие запрещено политикой")
        assert isinstance(safe_err, WindowsSDKError)

        dry_err = DryRunExecutionError("Ошибка симуляции Dry-Run")
        assert isinstance(dry_err, SafeOpsViolationError)
        assert isinstance(dry_err, WindowsSDKError)

        restore_err = SystemRestorePointError("Не удалось создать точку отката")
        assert isinstance(restore_err, WindowsSDKError)

    def test_drivers_and_features_exceptions(self) -> None:
        """Проверка исключений драйверов и компонентов Features."""
        drv_err = DriverNotFoundError("Драйвер NVIDIA 599.99 не найден")
        assert isinstance(drv_err, DriverSubsystemError)
        assert isinstance(drv_err, WindowsSDKError)

        feat_err = FeatureNotFoundError("Компонент IIS-WebServer не найден")
        assert isinstance(feat_err, WindowsFeatureError)
        assert isinstance(feat_err, WindowsSDKError)

    def test_module_domain_exceptions_hierarchy(self) -> None:
        """Проверка исключений доменных модулей администрирования."""
        reg_err = RegistryAccessError("Ключ реестра заблокирован")
        assert isinstance(reg_err, ModuleOperationError)
        assert isinstance(reg_err, WindowsSDKError)

        srv_err = ServiceControlError("Таймаут остановки службы Spooler")
        assert isinstance(srv_err, ModuleOperationError)

        task_err = TaskSchedulerError("Задача планировщика не найдена")
        assert isinstance(task_err, ModuleOperationError)

        proc_err = ProcessOperationError("Невозможно завершить системный процесс")
        assert isinstance(proc_err, ModuleOperationError)

        exp_err = ExplorerManagerError("Сбой установки параметра LaunchTo")
        assert isinstance(exp_err, ModuleOperationError)

        shell_err = ShellNamespaceError("Не удалось разрешить KnownFolder GUID")
        assert isinstance(shell_err, ModuleOperationError)

        backup_err = BackupOperationError("Сбой создания снимка VSS")
        assert isinstance(backup_err, ModuleOperationError)
