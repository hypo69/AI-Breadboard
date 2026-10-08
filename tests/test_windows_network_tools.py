# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Network Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Network Terminal (network.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_network_tools.py -v
#
# File: test_windows_network_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:52:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Network Terminal."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_network_scan_lan,
    windows_network_usage_stats,
    windows_network_speedtest,
    WINDOWS_NETWORK_TOOLS,
)
from apps.windows.modules.network.lan_scanner import LanDevice


async def call_tool(tool_obj, **kwargs):
    """Вспомогательный вызов инструмента LangChain или базовой функции."""
    if hasattr(tool_obj, "ainvoke"):
        return await tool_obj.ainvoke(kwargs)
    elif hasattr(tool_obj, "invoke"):
        return tool_obj.invoke(kwargs)
    elif hasattr(tool_obj, "func") and tool_obj.func:
        func = tool_obj.func
        return await func(**kwargs) if asyncio.iscoroutinefunction(func) else func(**kwargs)
    else:
        return await tool_obj(**kwargs)


@pytest.mark.asyncio
async def test_windows_network_scan_lan_devices():
    """Тест сканирования и инспекции устройств LAN."""
    with patch("apps.windows.modules.network.lan_scanner.WindowsLanScanner.discover_devices") as mock_func:
        mock_func.return_value = [
            LanDevice(ip="192.168.1.1", mac="00:11:22:33:44:55", hostname="router.local", state="Online", is_gateway=True)
        ]
        res_str = await call_tool(windows_network_scan_lan, action="devices")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["total"] == 1
        assert res["devices"][0]["ip"] == "192.168.1.1"


@pytest.mark.asyncio
async def test_windows_network_usage_stats_adapters():
    """Тест получения накопительной статистики сетевых адаптеров."""
    with patch("apps.windows.modules.network.network_usage.WindowsNetworkUsageCollector.get_adapter_statistics") as mock_func:
        mock_func.return_value = [{"name": "Ethernet", "received_bytes": 1024000, "sent_bytes": 512000}]
        res_str = await call_tool(windows_network_usage_stats, action="adapters")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "adapters" in res
        assert len(res["adapters"]) == 1


@pytest.mark.asyncio
async def test_windows_network_speedtest():
    """Тест выполнения замера скорости и качества соединения."""
    with patch("apps.windows.modules.network.speedtest.NetworkSpeedTester.run_full_speedtest") as mock_func:
        mock_func.return_value = {
            "download_mbps": 250.5,
            "upload_mbps": 100.2,
            "latency_unloaded_ms": 12.0,
            "grade": "Отличное (Ultra Fast)",
        }
        res_str = await call_tool(windows_network_speedtest, duration_seconds=1)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["speedtest"]["download_mbps"] == 250.5


def test_windows_controller_agent_has_network_tools():
    """Проверка наличия новых сетевых инструментов в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_network_scan_lan" in tool_names
    assert "windows_network_usage_stats" in tool_names
    assert "windows_network_speedtest" in tool_names
