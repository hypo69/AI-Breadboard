# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware Providers Unit Tests
# =============================================================================
# Description:
#   Модульные тесты для аппаратных провайдеров, авто-поиска утилит в /bin,
#   нормализованных моделей данных и движка кросс-валидации.
#
# File: test_hardware_providers.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для аппаратных провайдеров и движка валидации."""

from __future__ import annotations

import pytest
from pathlib import Path

from apps.windows.hardware.base import ProviderStatus, ProviderTier
from apps.windows.hardware.discovery import UtilityDiscovery
from apps.windows.hardware.models import (
    CpuInventory,
    GpuInventory,
    SensorReading,
    SensorSnapshot,
    SystemHardwareInventory,
)
from apps.windows.hardware.providers.aida64_provider import Aida64Provider
from apps.windows.hardware.providers.cpuz_provider import CpuzProvider
from apps.windows.hardware.providers.hwinfo_provider import HwinfoProvider
from apps.windows.hardware.providers.lhm_provider import LhmProvider
from apps.windows.hardware.providers.native_win_provider import NativeWinProvider
from apps.windows.hardware.providers.smartmontools_provider import SmartmontoolsProvider
from apps.windows.hardware.registry import HardwareProviderRegistry
from apps.windows.hardware.cross_validator import CrossValidator


def test_native_win_provider():
    """Проверка сбора данных через нативный провайдер Windows."""
    provider = NativeWinProvider()
    assert provider.is_available() is True
    assert provider.tier == ProviderTier.TIER_1_NATIVE
    assert provider.status == ProviderStatus.AVAILABLE

    inv = provider.probe_inventory()
    assert inv is not None
    assert inv.cpu is not None
    assert inv.memory is not None
    assert "Native Windows API" in inv.sources_used

    sensors = provider.probe_sensors()
    assert sensors is not None
    assert len(sensors.sensors) > 0


def test_discovery_and_registry(tmp_path: Path):
    """Проверка авто-поиска утилит в /bin и регистрации."""
    # Создаем фейковый бинарник cpuz.exe во временной папке bin
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    fake_cpuz = fake_bin_dir / "cpuz.exe"
    fake_cpuz.write_text("fake binary")

    discovery = UtilityDiscovery(project_root=tmp_path)
    found_cpuz = discovery.find_utility("cpuz")
    assert found_cpuz is not None
    assert "cpuz.exe" in found_cpuz

    reg = HardwareProviderRegistry(discovery=discovery)
    cpuz_prov = reg.get_provider("cpuz")
    assert cpuz_prov is not None
    assert cpuz_prov.is_available() is True


def test_aida64_xml_sensor_parsing():
    """Тестирование разбора данных сенсоров AIDA64."""
    provider = Aida64Provider()
    # Эмулируем ответ Shared Memory
    xml_data = "<root><temp><id>TCPU</id><label>CPU</label><value>42.5</value></temp><fan><id>FCPU</id><label>CPU Fan</label><value>1450</value></fan></root>"
    provider._read_shared_memory = lambda: xml_data

    sensors = provider.probe_sensors()
    assert sensors is not None
    assert len(sensors.sensors) == 2
    assert sensors.sensors[0].value == 42.5
    assert sensors.sensors[0].sensor_type == "Temperature"
    assert sensors.sensors[1].value == 1450.0
    assert sensors.sensors[1].unit == "RPM"


def test_cross_validator():
    """Проверка выявления расхождений движком CrossValidator."""
    validator = CrossValidator()
    report = validator.run_cross_check()

    assert report is not None
    assert report.consensus_score_pct >= 0.0
    assert report.normalized_inventory is not None
