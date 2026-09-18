# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Base Hardware Provider Interface
# =============================================================================
# Description:
#   Абстрактный базовый класс и структуры данных для аппаратных провайдеров
#   (Hardware Providers) в Windows System Diagnostic Engine.
#
# File: base.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Базовые абстракции и протоколы для аппаратных провайдеров."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from apps.windows.hardware.models import (
    CpuInventory,
    GpuInventory,
    MotherboardInventory,
    MemoryInventory,
    StorageInventory,
    SensorSnapshot,
    SystemHardwareInventory,
)


class ProviderStatus(str, Enum):
    """Статус доступности аппаратного провайдера."""
    AVAILABLE = "AVAILABLE"          # Готов к работе, утилита/API найдена
    RUNNING = "RUNNING"              # Утилита/сервис запущен в фоне (напр. LHM, HWiNFO)
    NOT_FOUND = "NOT_FOUND"          # Бинарный файл или сервис не обнаружен
    PERMISSION_DENIED = "DENIED"     # Требуются повышенные привилегии (Admin/UAC)
    ERROR = "ERROR"                  # Ошибка при инициализации или опросе


class ProviderTier(int, Enum):
    """Уровень приоритета провайдера в диагностической иерархии."""
    TIER_1_NATIVE = 1       # Нативные Windows API (WinAPI, WMI, SMBIOS, DXGI)
    TIER_2_PRIMARY = 2      # Основные диагностические комбайны (HWiNFO, AIDA64, LHM)
    TIER_3_SPECIALIZED = 3  # Специализированные утилиты (smartctl, CPU-Z, GPU-Z, NVML, CDI)
    TIER_4_AUXILIARY = 4    # Дополнительные/вспомогательные источники (Speccy, OHM, CoreTemp)


class ProviderCapability(str, Enum):
    """Возможности аппаратного провайдера."""
    CPU_INVENTORY = "CPU_INVENTORY"
    MOTHERBOARD_INVENTORY = "MOTHERBOARD_INVENTORY"
    RAM_INVENTORY = "RAM_INVENTORY"
    GPU_INVENTORY = "GPU_INVENTORY"
    STORAGE_INVENTORY = "STORAGE_INVENTORY"
    SMART_DIAGNOSTICS = "SMART_DIAGNOSTICS"
    LIVE_SENSORS = "LIVE_SENSORS"
    SHARED_MEMORY = "SHARED_MEMORY"
    OFFLINE_REPORT = "OFFLINE_REPORT"


class BaseHardwareProvider(ABC):
    """Абстрактный базовый класс для аппаратного провайдера."""

    def __init__(self, name: str, tier: ProviderTier, binary_path: Optional[str] = None) -> None:
        """Инициализация провайдера.

        Args:
            name: Человекочитаемое имя провайдера.
            tier: Уровень иерархии провайдера.
            binary_path: Путь к исполняемому файлу (если применимо).
        """
        self.name = name
        self.tier = tier
        self.binary_path = binary_path
        self._status = ProviderStatus.NOT_FOUND

    @property
    def status(self) -> ProviderStatus:
        """Текущий статус провайдера."""
        return self._status

    @abstractmethod
    def is_available(self) -> bool:
        """Проверить доступность утилиты или интерфейса в системе."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[ProviderCapability]:
        """Получить список поддерживаемых возможностей."""
        pass

    @abstractmethod
    def probe_inventory(self) -> Optional[SystemHardwareInventory]:
        """Собрать детальный инвентарь оборудования."""
        pass

    @abstractmethod
    def probe_sensors(self) -> Optional[SensorSnapshot]:
        """Собрать оперативные показания датчиков (сенсоров) в реальном времени."""
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """Получить метаданные о провайдере для API и CLI."""
        return {
            "name": self.name,
            "tier": self.tier.value,
            "tier_label": self.tier.name,
            "status": self.status.value,
            "binary_path": self.binary_path,
            "capabilities": [c.value for c in self.get_capabilities()],
        }
