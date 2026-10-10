# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Hardware -   Init  
# =============================================================================
# Description:
#   Пакет аппаратного мониторинга, диагностики и провайдеров внешних утилит.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Пакет аппаратного мониторинга, диагностики и провайдеров внешних утилит."""

from apps.windows.hardware.base import BaseHardwareProvider, ProviderCapability, ProviderStatus, ProviderTier
from apps.windows.hardware.cross_validator import CrossValidator, ValidationReport
from apps.windows.hardware.discovery import UtilityDiscovery
from apps.windows.hardware.models import CpuInventory, GpuInventory, MemoryInventory, MotherboardInventory, SensorReading, SensorSnapshot, StorageDeviceInventory, StorageInventory, SystemHardwareInventory
from apps.windows.hardware.registry import HardwareProviderRegistry
__all__ = ['BaseHardwareProvider', 'ProviderCapability', 'ProviderStatus', 'ProviderTier', 'HardwareProviderRegistry', 'UtilityDiscovery', 'CrossValidator', 'ValidationReport', 'CpuInventory', 'GpuInventory', 'MemoryInventory', 'MotherboardInventory', 'StorageInventory', 'StorageDeviceInventory', 'SensorReading', 'SensorSnapshot', 'SystemHardwareInventory']