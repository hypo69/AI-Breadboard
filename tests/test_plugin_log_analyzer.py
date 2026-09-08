# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Log Analyzer Admin Plugin
# =============================================================================
# Description:
#   Validates plugin initialization, manifest structure, configuration schema,
#   action execution (analyze_all, analyze_errors, rotate_and_clean),
#   and tool definitions for the log_analyzer plugin.
#
# File: test_plugin_log_analyzer.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for plugins.log_analyzer."""

import pytest
from plugins.log_analyzer import plugin, LogAnalyzerPlugin


@pytest.mark.asyncio
async def test_log_analyzer_plugin_init():
    """Verify plugin initialization and metadata."""
    instance = plugin()
    assert isinstance(instance, LogAnalyzerPlugin)
    assert instance.name == "log_analyzer"
    assert instance.icon == "📊"
    assert instance.category == "tools"
    assert instance.is_system is True
    assert instance.scope == "system"


def test_log_analyzer_manifest():
    """Verify manifest schema and exposed fields/actions."""
    instance = plugin()
    manifest = instance.get_manifest()

    assert manifest["name"] == "log_analyzer"
    assert manifest["enabled"] is True
    assert "actions" in manifest
    assert "fields" in manifest

    action_ids = [a["id"] for a in manifest["actions"]]
    assert "analyze_all" in action_ids
    assert "analyze_errors" in action_ids
    assert "ai_diagnose" in action_ids
    assert "rotate_and_clean" in action_ids

    field_ids = [f["id"] for f in manifest["fields"]]
    assert "log_level" in field_ids
    assert "tail_lines" in field_ids
    assert "enable_ai_synthesis" in field_ids


@pytest.mark.asyncio
async def test_log_analyzer_actions_execution():
    """Verify action execution handles gracefully."""
    instance = plugin()

    # Test analyze_all
    res_all = await instance.execute_action("analyze_all", {"tail_lines": 50})
    assert res_all["success"] is True
    assert "result" in res_all
    assert "total_events" in res_all["result"]

    # Test analyze_errors
    res_err = await instance.execute_action("analyze_errors", {"tail_lines": 50})
    assert res_err["success"] is True
    assert "error_events" in res_err["result"]

    # Test rotate_and_clean
    res_clean = await instance.execute_action("rotate_and_clean")
    assert res_clean["success"] is True
    assert "rotated_files" in res_clean["result"]

    # Test unknown action
    res_unk = await instance.execute_action("unknown_action")
    assert res_unk["success"] is False
    assert "error" in res_unk


@pytest.mark.asyncio
async def test_log_analyzer_handle_stream():
    """Verify handle async generator outputs diagnostics."""
    instance = plugin()
    events = []
    async for chunk in instance.handle("Check system status"):
        events.append(chunk)

    assert len(events) >= 2
    assert events[0]["status"] == "started"
    assert events[-1]["status"] == "complete"


def test_log_analyzer_tools_definition():
    """Verify LLM function calling schema."""
    instance = plugin()
    tools = instance.get_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "analyze_system_logs"
    assert "parameters" in tools[0]
