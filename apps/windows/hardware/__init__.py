# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware Module Init
# =============================================================================
# Description:
#   Инициализация пакета аппаратного обеспечения (apps/windows/hardware).
#   Экспортирует основные провайдеры, модели, валидатор и реестр.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет аппаратного мониторинга, диагностики и провайдеров внешних утилит."""

from __future__ import annotations

from apps.windows.hardware.base import (
    BaseHardwareProvider,
    ProviderCapability,
    ProviderStatus,
    ProviderTier,
)
from apps.windows.hardware.cross_validator import CrossValidator, ValidationReport
from apps.windows.hardware.discovery import UtilityDiscovery
from apps.windows.hardware.models import (
    CpuInventory,
    GpuInventory,
    MemoryInventory,
    MotherboardInventory,
    SensorReading,
    SensorSnapshot,
    StorageDeviceInventory,
    StorageInventory,
    SystemHardwareInventory,
)
from apps.windows.hardware.registry import HardwareProviderRegistry

__all__ = [
    "BaseHardwareProvider",
    "ProviderCapability",
    "ProviderStatus",
    "ProviderTier",
    "HardwareProviderRegistry",
    "UtilityDiscovery",
    "CrossValidator",
    "ValidationReport",
    "CpuInventory",
    "GpuInventory",
    "MemoryInventory",
    "MotherboardInventory",
    "StorageInventory",
    "StorageDeviceInventory",
    "SensorReading",
    "SensorSnapshot",
    "SystemHardwareInventory",
]
