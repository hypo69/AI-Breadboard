"""Пакет аппаратного мониторинга, диагностики и провайдеров внешних утилит."""
from __future__ import annotations
from apps.windows.hardware.base import BaseHardwareProvider, ProviderCapability, ProviderStatus, ProviderTier
from apps.windows.hardware.cross_validator import CrossValidator, ValidationReport
from apps.windows.hardware.discovery import UtilityDiscovery
from apps.windows.hardware.models import CpuInventory, GpuInventory, MemoryInventory, MotherboardInventory, SensorReading, SensorSnapshot, StorageDeviceInventory, StorageInventory, SystemHardwareInventory
from apps.windows.hardware.lhm_service import LhmService, parse_sensor_value
from apps.windows.hardware.registry import HardwareProviderRegistry
__all__ = ['BaseHardwareProvider', 'ProviderCapability', 'ProviderStatus', 'ProviderTier', 'HardwareProviderRegistry', 'UtilityDiscovery', 'CrossValidator', 'ValidationReport', 'LhmService', 'parse_sensor_value', 'CpuInventory', 'GpuInventory', 'MemoryInventory', 'MotherboardInventory', 'StorageInventory', 'StorageDeviceInventory', 'SensorReading', 'SensorSnapshot', 'SystemHardwareInventory']