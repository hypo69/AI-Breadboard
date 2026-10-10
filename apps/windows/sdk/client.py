# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows SDK - Main Client Facade
# =============================================================================
# Description:
#   Единый программный интерфейс (SDK Facade) для доступа ко всем подсистемам
#   Windows: нативный C-FFI слой, ядро SafeOps/диагностики, драйверы,
#   компоненты Windows Optional Features и доменные модули администрирования.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk import WindowsSDK, windows_sdk
#
#     # Быстрая сводка здоровья системы:
#     health = windows_sdk.get_health_summary()
#
#     # Доступ к нативному C-FFI уровню:
#     kernel = windows_sdk.native.kernel32
#
#     # Управление компонентами ОС:
#     features = windows_sdk.features.get_features()
#
# File: client.py
# Project: ai-breadboard
# Package: apps.windows.sdk
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:45:00
# =============================================================================

from __future__ import annotations
"""Единый фасад Windows SDK (Software Development Kit) для AI-Breadboard."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from logger import logger

# Подсистемы SDK
from apps.windows.sdk import native
from apps.windows.sdk import core
from apps.windows.sdk import drivers
from apps.windows.sdk import features
from apps.windows.sdk import modules


class NativeSubsystem:
    """Слой 1: Нативные C-FFI биндинги к системным DLL Windows."""

    def __init__(self) -> None:
        self.advapi32 = native.Advapi32
        self.kernel32 = native.Kernel32
        self.psapi = native.Psapi
        self.pdh = native.PDHManager
        self.scm = native.ServiceManagerFFI
        self.setupapi = native.SetupAPI
        self.ntdll = native.NativeNT
        self.wevtapi = native.WindowsEventLogAPI
        self.tasksched = native.TaskSchedulerFFI
        self.error_decoder = native.WindowsErrorDecoder
        self.win32_error = native.Win32Error
        self.win32_error_check = native.win32_error_check


class DriversSubsystem:
    """Слой 2: Управление и аудит драйверов и аппаратных каталогов."""

    def __init__(self) -> None:
        self.detector = drivers.GpuHardwareDetector()
        self.nvidia_catalog = drivers.NvidiaCatalogManager()
        self.amd_catalog = drivers.AmdCatalogManager()
        self.downloader = drivers.DriverDownloader()
        self.VendorType = drivers.VendorType
        self.DriverBranch = drivers.DriverBranch
        self.DriverRelease = drivers.DriverRelease


class FeaturesSubsystem:
    """Слой 3: Управление дополнительными компонентами Windows (Optional Features)."""

    def get_features(self) -> List[Dict[str, str]]:
        """Получение списка всех компонентов Windows и их статусов."""
        return features.get_windows_features()

    def enable_feature(self, name: str, all_dependencies: bool = True) -> Dict[str, str]:
        """Включение компонента Windows с автоматической установкой зависимостей."""
        return features.enable_windows_feature(name, all=all_dependencies)

    def disable_feature(self, name: str) -> Dict[str, str]:
        """Отключение компонента Windows."""
        return features.disable_windows_feature(name)


class CoreSubsystem:
    """Слой 4: Ядро SafeOps, системная диагностика, аудит и безопасность."""

    def __init__(self) -> None:
        self.winapi = core.WinAPI()
        self.safe_executor = core.SafeExecutor()
        self.diagnostics = core.DiagnosticsEngine()
        self.correlation = core.CorrelationEngine()
        self.restore_manager = core.WindowsSystemRestoreManager()
        self.param_manager = core.SafeSystemParamManager()
        self.process_audit = core.ProcessAuditManager()
        self.system32_catalog = core.System32Catalog()
        self.etw_pipeline = core.EtwTelemetryPipeline()


class ModulesSubsystem:
    """Слой 5: Доменные модули администрирования и мониторинга."""

    @property
    def hardware(self) -> Any:
        """Модуль мониторинга и диагностики оборудования."""
        from apps.windows.sdk.modules.hardware.hardware_monitor import HardwareMonitor
        return HardwareMonitor()

    @property
    def network(self) -> Any:
        """Модуль сетевого аудита и сокетов."""
        from apps.windows.sdk.modules.network.network_usage import WindowsNetworkUsageCollector
        return WindowsNetworkUsageCollector()

    @property
    def storage(self) -> Any:
        """Модуль дисковых накопителей и S.M.A.R.T."""
        from apps.windows.sdk.modules.storage_manager.core.manager import StorageManager
        return StorageManager()

    @property
    def defender(self) -> Any:
        """Модуль Windows Defender и безопасности."""
        from apps.windows.sdk.modules.defender.core.defender_service import DefenderService
        return DefenderService()

    @property
    def firewall(self) -> Any:
        """Модуль брандмауэра Windows."""
        from apps.windows.sdk.modules.firewall_manager.core.manager import FirewallManager
        return FirewallManager()

    @property
    def services(self) -> Any:
        """Модуль управления системными службами."""
        from apps.windows.sdk.modules.services_manager.core.manager import ServicesManager
        return ServicesManager()

    @property
    def task_scheduler(self) -> Any:
        """Модуль планировщика заданий."""
        from apps.windows.sdk.modules.task_scheduler.core.manager import TaskSchedulerManager
        return TaskSchedulerManager()

    @property
    def registry(self) -> Any:
        """Модуль безопасного доступа к реестру."""
        from apps.windows.sdk.modules.registry.viewer import RegistryViewer
        return RegistryViewer()

    @property
    def process_manager(self) -> Any:
        """Модуль расширенного управления процессами."""
        from apps.windows.sdk.modules.process_manager.core.manager import ProcessManager
        return ProcessManager()

    @property
    def taskbar(self) -> Any:
        """Модуль управления панелью задач."""
        from apps.windows.sdk.modules.taskbar.core.manager import TaskbarController
        return TaskbarController()

    @property
    def window_control_plane(self) -> Any:
        """Модуль управления окнами Windows."""
        from apps.windows.sdk.modules.window_control_plane.manager import WindowManagementControlPlane
        return WindowManagementControlPlane()


class WindowsSDK:
    """Единый комплексный SDK для операционной системы Windows.

    Объединяет 5 функциональных уровней:
    1. `native`: C-FFI низкоуровневые вызовы
    2. `drivers`: Драйверный слой и каталоги
    3. `features`: Windows Optional Features
    4. `core`: SafeOps, аудит, корреляция и аналитика
    5. `modules`: 27 специализированных модулей управления
    """

    def __init__(self) -> None:
        """Инициализация подсистем Windows SDK."""
        self.native = NativeSubsystem()
        self.drivers = DriversSubsystem()
        self.features = FeaturesSubsystem()
        self.core = CoreSubsystem()
        self.modules = ModulesSubsystem()
        logger.debug("[WindowsSDK] Инициализирован единый Windows SDK")

    def get_health_summary(self) -> Dict[str, Any]:
        """Получение быстрой сводки здоровья системы.

        Returns:
            Словарь с общими показателями здоровья и активными предупреждениями.
        """
        try:
            return self.core.diagnostics.quick_check()
        except Exception as e:
            logger.warning(f"[WindowsSDK] Ошибка сбора сводки здоровья: {e}")
            return {"status": "error", "error": str(e)}

    def get_system_snapshot(self) -> core.SystemState:
        """Сбор моментального системного снимка (процессы, память, службы).

        Returns:
            Объект SystemState с полным состоянием системы.
        """
        return self.core.winapi.get_system_state()


# Глобальный синглтон экземпляр SDK для быстрого импорта
windows_sdk = WindowsSDK()

__all__ = [
    "WindowsSDK",
    "windows_sdk",
    "NativeSubsystem",
    "DriversSubsystem",
    "FeaturesSubsystem",
    "CoreSubsystem",
    "ModulesSubsystem",
]
