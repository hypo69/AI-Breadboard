# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Hardware Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Windows Hardware Diagnostics (hardware.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_hardware_tools.py -v
#
# File: test_windows_hardware_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:48:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Windows Hardware Diagnostics."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_hardware_monitor,
    windows_hardware_inventory,
    windows_hardware_benchmark,
    WINDOWS_HARDWARE_TOOLS,
)
from apps.windows.sdk.modules.hardware.hardware_monitor import CpuMetrics, MemoryMetrics
from apps.windows.sdk.modules.hardware.stress_benchmark import StressTestResult, AIBenchmarkResult


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
async def test_windows_hardware_monitor_summary():
    """Тест получения краткой сводки здоровья оборудования."""
    with patch("apps.windows.sdk.modules.hardware.hardware_monitor.HardwareMonitor.get_summary") as mock_func:
        mock_func.return_value = {"status": "HEALTHY", "cpu_pct": 15.4, "memory_pct": 45.2, "warnings": []}
        res_str = await call_tool(windows_hardware_monitor, action="summary")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "summary" in res
        assert res["summary"]["status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_windows_hardware_monitor_component_cpu():
    """Тест получения метрик процессора."""
    with patch("apps.windows.sdk.modules.hardware.hardware_monitor.HardwareMonitor.get_cpu_metrics") as mock_func:
        mock_func.return_value = CpuMetrics(
            model_name="Intel Core i9-14900K",
            physical_cores=24,
            logical_cores=32,
            utilization_pct=12.5,
        )
        res_str = await call_tool(windows_hardware_monitor, action="component", component="cpu")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["component"] == "cpu"
        assert res["metrics"]["model_name"] == "Intel Core i9-14900K"


@pytest.mark.asyncio
async def test_windows_hardware_inventory_summary():
    """Тест выполнения инвентаризации оборудования."""
    with patch("apps.windows.sdk.modules.hardware.hardware_monitor.HardwareMonitor.get_snapshot") as mock_func:
        mock_func.return_value = {"system": "AI Breadboard Workstation"}
        res_str = await call_tool(windows_hardware_inventory, action="summary")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "inventory" in res


@pytest.mark.asyncio
async def test_windows_hardware_benchmark_ai():
    """Тест выполнения бенчмарка ИИ-инференса."""
    with patch("apps.windows.sdk.modules.hardware.stress_benchmark.StressBenchmarkEngine.run_ai_inference_benchmark") as mock_func:
        mock_func.return_value = AIBenchmarkResult(
            provider="gemini",
            model_name="gemini-3.1-flash",
            success=True,
            ttft_ms=120.0,
            total_time_ms=450.0,
            prompt_tokens=10,
            completion_tokens=25,
            tokens_per_second=55.5,
            generated_text="Тестовый ответ инференса",
        )
        res_str = await call_tool(
            windows_hardware_benchmark,
            action="ai_inference",
            provider="gemini",
            model_name="gemini-3.1-flash",
        )
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert res["ai_benchmark"]["tokens_per_second"] == 55.5


def test_windows_controller_agent_has_hardware_tools():
    """Проверка наличия новых инструментов в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_hardware_monitor" in tool_names
    assert "windows_hardware_inventory" in tool_names
    assert "windows_hardware_benchmark" in tool_names
