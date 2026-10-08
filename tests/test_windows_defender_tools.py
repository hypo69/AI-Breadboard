# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Defender Tools
# =============================================================================
# Description:
#   Тестовый набор для проверки набора инструментов Microsoft Defender & AI Security (defender.py)
#   и их интеграции в WindowsControllerAgent.
#
# Usage Examples:
#   CLI:
#     py -m pytest tests/test_windows_defender_tools.py -v
#
# File: test_windows_defender_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:17:00
# =============================================================================

"""Тестовый набор для проверки набора инструментов Microsoft Defender."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from src.ai.agents.windows_controller_agent import WindowsControllerAgent
from src.ai.agents.windows_tools import (
    windows_defender_status_scan,
    windows_defender_audit_security,
    windows_defender_ai_diagnostics,
    WINDOWS_DEFENDER_TOOLS,
)


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
async def test_windows_defender_status_scan():
    """Тест получения статуса Defender."""
    with patch("apps.windows.modules.defender.core.defender_service.DefenderService.get_defender_status") as mock_func:
        mock_func.return_value = {"real_time_protection": True, "antivirus_enabled": True}
        res_str = await call_tool(windows_defender_status_scan, action="status")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "defender_status" in res
        assert res["defender_status"]["real_time_protection"] is True


@pytest.mark.asyncio
async def test_windows_defender_audit_security():
    """Тест выполнения аудита ASR, исключений и угроз."""
    with patch("apps.windows.modules.defender.core.asr_manager.ASRManager.get_asr_rules") as mock_asr, \
         patch("apps.windows.modules.defender.core.exclusions_auditor.ExclusionsAuditor.audit_exclusions") as mock_ex, \
         patch("apps.windows.modules.defender.core.threat_manager.ThreatManager.get_threats_history") as mock_threats:

        mock_asr.return_value = [{"rule_name": "Block LSASS"}]
        mock_ex.return_value = {"total_exclusions": 0}
        mock_threats.return_value = []

        res_str = await call_tool(windows_defender_audit_security, mode="all")
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "asr_rules" in res
        assert "exclusions_audit" in res
        assert "recent_threats" in res


@pytest.mark.asyncio
async def test_windows_defender_ai_diagnostics():
    """Тест формирования отчета Security Score."""
    with patch("apps.windows.modules.defender.core.ai_diagnostician.AIDiagnostician.generate_diagnostic_report") as mock_func:
        mock_func.return_value = {"security_score": 95, "critical_findings": []}
        res_str = await call_tool(windows_defender_ai_diagnostics)
        res = json.loads(res_str)
        assert res["status"] == "ok"
        assert "security_report" in res
        assert res["security_report"]["security_score"] == 95


def test_windows_controller_agent_has_defender_tools():
    """Проверка наличия новых инструментов Defender в WindowsControllerAgent."""
    agent = WindowsControllerAgent()
    tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.native_tools]
    assert "windows_defender_status_scan" in tool_names
    assert "windows_defender_audit_security" in tool_names
    assert "windows_defender_ai_diagnostics" in tool_names
