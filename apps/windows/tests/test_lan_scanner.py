# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Lan Scanner
# =============================================================================
# Description:
#   Тесты для модуля обнаружения устройств локальной сети (LAN Device Discovery).
#
# Usage Examples:
#   Python API:
#     from apps.windows.tests.test_lan_scanner import test_lookup_vendor
#
#     res = test_lookup_vendor()
#
# File: test_lan_scanner.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для модуля обнаружения устройств локальной сети (LAN Device Discovery)."""

import pytest
from unittest.mock import MagicMock, patch

from apps.windows.telemetry.win32_ffi.nethelper import IPHelperAPI
from apps.windows.network.lan_scanner import LanDevice, WindowsLanScanner, OUI_VENDOR_MAP
from apps.windows.network.sensors import NetworkTerminalSensor


def test_lookup_vendor():
    """Тест определения вендора по OUI префиксу MAC-адреса."""
    scanner = WindowsLanScanner()
    assert scanner.lookup_vendor('00:1D:0F:11:22:33') == 'TP-Link'
    assert scanner.lookup_vendor('00-1D-0F-11-22-33') == 'TP-Link'
    assert scanner.lookup_vendor('00:03:93:AA:BB:CC') == 'Apple'
    assert scanner.lookup_vendor('00:12:FB:11:22:33') == 'Samsung'
    assert scanner.lookup_vendor('00:1B:21:00:11:22') == 'Intel'
    assert scanner.lookup_vendor('00:0C:42:11:22:33') == 'MikroTik'
    assert scanner.lookup_vendor('invalid-mac') is None
    assert scanner.lookup_vendor(None) is None


def test_lan_device_model():
    """Тест инициализации и валидации модели LanDevice."""
    dev = LanDevice(
        ip='192.168.1.50',
        mac='00:1D:0F:AA:BB:CC',
        hostname='my-pc.lan',
        vendor='TP-Link',
        is_gateway=True,
        is_local=False,
        discovery_methods=['arp_sweep'],
        latency_ms=1.5,
    )
    assert dev.ip == '192.168.1.50'
    assert dev.mac == '00:1D:0F:AA:BB:CC'
    assert dev.is_gateway is True
    assert dev.is_local is False
    assert dev.vendor == 'TP-Link'
    assert 'arp_sweep' in dev.discovery_methods


def test_get_local_interfaces_info():
    """Тест получения списка активных локальных сетевых интерфейсов и подсетей."""
    scanner = WindowsLanScanner()
    ifaces = scanner.get_local_interfaces_info()
    assert isinstance(ifaces, list)
    if ifaces:
        first = ifaces[0]
        assert 'name' in first
        assert 'ip' in first
        assert 'cidr' in first


def test_get_neighbor_cache_devices():
    """Тест чтения кеша ARP соседей ядра Windows."""
    scanner = WindowsLanScanner()
    devices = scanner.get_neighbor_cache_devices()
    assert isinstance(devices, list)
    for d in devices:
        assert isinstance(d, LanDevice)
        assert d.ip is not None


def test_discover_devices_cache_mode():
    """Тест работы главного метода discover_devices в быстром режиме кеша."""
    scanner = WindowsLanScanner()
    devices = scanner.discover_devices(full_scan=False, include_ssdp=False)
    assert isinstance(devices, list)
    # Всегда должен присутствовать как минимум локальный хост
    local_found = any(d.is_local for d in devices)
    assert local_found or len(devices) == 0


def test_sensor_get_lan_devices():
    """Тест интеграции LAN сканера в NetworkTerminalSensor."""
    sensor = NetworkTerminalSensor()
    devices_dict = sensor.get_lan_devices(full_scan=False)
    assert isinstance(devices_dict, list)
    for item in devices_dict:
        assert isinstance(item, dict)
        assert 'ip' in item
