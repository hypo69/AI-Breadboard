# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK - Exceptions Hierarchy
# =============================================================================
# Description:
#   Иерархическая типизированная система исключений Windows SDK (Exceptions Hierarchy).
#   Обеспечивает строгое разделение системных сбоев Win32, нарушений SafeOps,
#   ошибок прав доступа UAC, сбоев драйверов и доменных модулей администрирования.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.exceptions import (
#         WindowsSDKError,
#         NativeCallError,
#         SafeOpsViolationError,
#         FeatureNotFoundError,
#         RegistryAccessError,
#     )
#
#     try:
#         windows_sdk.core.safe_executor.execute(action)
#     except SafeOpsViolationError as err:
#         logger.error("SafeOps заблокировал опасное действие: %s", err)
#     except WindowsSDKError as err:
#         logger.error("Общая ошибка SDK: %s", err)
#
# File: exceptions.py
# Project: ai-breadboard
# Package: apps.windows.sdk
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 07:16:00
# =============================================================================

from __future__ import annotations
"""Иерархия исключений для Windows SDK (Software Development Kit)."""

from typing import Any, Dict, Optional


class WindowsSDKError(Exception):
    """Базовое исключение для всех ошибок и сбоев Windows SDK.

    Attributes:
        message: Человекочитаемое описание ошибки.
        details: Дополнительные контекстные данные или параметры вызова.
        error_code: Числовой или строковый код ошибки (Win32, NTSTATUS, HTTP).
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование информации об исключении в сериализуемый словарь."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code!r})"


# =============================================================================
# 1. Слой Нативных вызовов (Native C-FFI Exceptions)
# =============================================================================

class NativeCallError(WindowsSDKError):
    """Ошибка низкоуровневого вызова к нативным Win32 / NTDLL библиотекам."""
    pass


class Win32NativeError(NativeCallError):
    """Ошибка Win32 API с системным кодом возврата (GetLastError / HRESULT)."""

    def __init__(
        self,
        message: str,
        win32_code: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        hex_code = f"0x{win32_code & 0xFFFFFFFF:08X}"
        super().__init__(
            message=f"{message} (Win32 Code: {win32_code} / {hex_code})",
            details=details,
            error_code=win32_code,
        )
        self.win32_code = win32_code
        self.hex_code = hex_code


class AccessDeniedSDKError(Win32NativeError):
    """Ошибка нарушения прав доступа (ERROR_ACCESS_DENIED, 0x00000005)."""

    def __init__(
        self,
        message: str = "Отказано в доступе. Требуются повышенные привилегии (Run as Administrator).",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, win32_code=5, details=details)


class PrivilegeElevationRequiredError(AccessDeniedSDKError):
    """Исключение, сигнализирующее о необходимости запуска от имени Администратора (UAC)."""
    pass


class InvalidHandleError(NativeCallError):
    """Исключение при попытке работы с недействительным системным дескриптором (HWND, HANDLE)."""
    pass


# =============================================================================
# 2. Слой Безопасности и SafeOps (Core & SafeOps Exceptions)
# =============================================================================

class SafeOpsViolationError(WindowsSDKError):
    """Попытка выполнения потенциально опасного действия без прохождения SafeOps-проверок."""
    pass


class DryRunExecutionError(SafeOpsViolationError):
    """Ошибка на этапе предварительного расчета и симуляции Dry-Run."""
    pass


class SystemRestorePointError(WindowsSDKError):
    """Ошибка создания или отката контрольной точки восстановления Windows System Restore."""
    pass


class DiagnosticEngineError(WindowsSDKError):
    """Ошибка в работе аналитических или корреляционных алгоритмов диагностики."""
    pass


class ParameterValidationError(WindowsSDKError):
    """Некорректные параметры настройки или нарушение схемы входных данных."""
    pass


# =============================================================================
# 3. Слой Драйверов и Оборудования (Drivers & Hardware Exceptions)
# =============================================================================

class DriverSubsystemError(WindowsSDKError):
    """Базовое исключение для ошибок работы с драйверами и оборудованием."""
    pass


class DriverNotFoundError(DriverSubsystemError):
    """Запрошенный драйвер или версия пакета не найдены в каталоге."""
    pass


class HardwareProbeError(DriverSubsystemError):
    """Ошибка опроса сенсоров или взаимодействия с LibreHardwareMonitor / GPU."""
    pass


class DriverDownloadError(DriverSubsystemError):
    """Ошибка скачивания или проверки целостности пакета драйвера."""
    pass


# =============================================================================
# 4. Слой Дополнительных компонентов (Windows Features Exceptions)
# =============================================================================

class WindowsFeatureError(WindowsSDKError):
    """Базовое исключение операций с Windows Optional Features."""
    pass


class FeatureNotFoundError(WindowsFeatureError):
    """Указанный компонент Windows не найден в системе."""
    pass


class FeatureInstallationError(WindowsFeatureError):
    """Сбой при включении или установке компонента Windows DISM."""
    pass


# =============================================================================
# 5. Слой Доменных подсистем (Modules Domain Exceptions)
# =============================================================================

class ModuleOperationError(WindowsSDKError):
    """Базовое исключение для операций в доменных модулях администрирования."""
    pass


class RegistryAccessError(ModuleOperationError):
    """Ошибка чтения или записи в системный реестр Windows."""
    pass


class ServiceControlError(ModuleOperationError):
    """Ошибка управления системной службой (SCM: запуск, остановка, тайм-аут)."""
    pass


class TaskSchedulerError(ModuleOperationError):
    """Ошибка взаимодействия с планировщиком заданий Windows Task Scheduler."""
    pass


class ProcessOperationError(ModuleOperationError):
    """Ошибка управления системным процессом (завершение, инспекция токена)."""
    pass


class ExplorerManagerError(ModuleOperationError):
    """Ошибка управления параметрами проводника Windows Explorer."""
    pass


class ShellNamespaceError(ModuleOperationError):
    """Ошибка разрешения Known Folders, Shell URI или виртуальных папок."""
    pass


class BackupOperationError(ModuleOperationError):
    """Ошибка создания резервной копии, VSS-снимка или поиска версий File History."""
    pass


class FirewallConfigurationError(ModuleOperationError):
    """Ошибка модификации правил или профилей брандмауэра Windows."""
    pass


class DefenderConfigurationError(ModuleOperationError):
    """Ошибка взаимодействия со службой или исключениями Windows Defender."""
    pass


__all__ = [
    # Базовое исключение
    "WindowsSDKError",
    # Нативный слой
    "NativeCallError",
    "Win32NativeError",
    "AccessDeniedSDKError",
    "PrivilegeElevationRequiredError",
    "InvalidHandleError",
    # SafeOps и ядро
    "SafeOpsViolationError",
    "DryRunExecutionError",
    "SystemRestorePointError",
    "DiagnosticEngineError",
    "ParameterValidationError",
    # Драйверы и оборудование
    "DriverSubsystemError",
    "DriverNotFoundError",
    "HardwareProbeError",
    "DriverDownloadError",
    # Windows Features
    "WindowsFeatureError",
    "FeatureNotFoundError",
    "FeatureInstallationError",
    # Доменные модули
    "ModuleOperationError",
    "RegistryAccessError",
    "ServiceControlError",
    "TaskSchedulerError",
    "ProcessOperationError",
    "ExplorerManagerError",
    "ShellNamespaceError",
    "BackupOperationError",
    "FirewallConfigurationError",
    "DefenderConfigurationError",
]
