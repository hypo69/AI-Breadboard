# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Codebase RAG Plugin
# =============================================================================
# Description:
#   Integration tests for GenerateRagCodebasePlugin testing manifest, actions,
#   tools, custom project directories, named indexes, and user isolation.
#
# File: test_plugin.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from pathlib import Path
import pytest

from plugins.generate_rag_from_codebase.plugin import GenerateRagCodebasePlugin


@pytest.mark.asyncio
async def test_plugin_manifest_and_tools():
    plugin = GenerateRagCodebasePlugin()
    manifest = plugin.get_manifest()

    assert manifest["name"] == "generate_rag_from_codebase"
    assert manifest["category"] == "tools"
    assert len(manifest["tools"]) == 2
    tool_names = [t["function"]["name"] for t in manifest["tools"]]
    assert "search_codebase_rag" in tool_names
    assert "lookup_symbol" in tool_names

    actions = plugin.get_actions()
    action_ids = [a["id"] for a in actions]
    assert "rebuild_index" in action_ids
    assert "search_code" in action_ids
    assert "search_symbols" in action_ids
    assert "list_indexes" in action_ids
    assert "get_stats" in action_ids


@pytest.mark.asyncio
async def test_plugin_custom_project_root_and_user_isolation(tmp_path: Path):
    # Setup custom external project workspace
    external_proj = tmp_path / "my_custom_project"
    src_dir = external_proj / "core"
    src_dir.mkdir(parents=True, exist_ok=True)
    sample_py = src_dir / "calculator.py"
    sample_py.write_text(
        'class SuperCalculator:\n    """Advanced math engine."""\n    def compute(self, x: int) -> int:\n        """Compute square."""\n        return x * x\n',
        encoding="utf-8"
    )

    plugin = GenerateRagCodebasePlugin()

    # Rebuild custom named index for user_id=42
    res_rebuild = await plugin.execute_action("rebuild_index", {
        "project_root": str(external_proj),
        "index_name": "custom_math_v1",
        "user_id": 42,
        "include_dirs": ["core"],
    })
    assert res_rebuild["success"] is True
    assert res_rebuild["data"]["index_name"] == "custom_math_v1"
    assert res_rebuild["data"]["user_id"] == 42
    assert res_rebuild["data"]["total_chunks"] > 0

    # Search symbol in custom index
    res_sym = await plugin.execute_action("search_symbols", {
        "query": "SuperCalculator",
        "index_name": "custom_math_v1",
        "user_id": 42
    })
    assert res_sym["success"] is True
    assert res_sym["count"] >= 1
    assert res_sym["results"][0]["symbol"] == "SuperCalculator"

    # Search code in custom index
    res_code = await plugin.execute_action("search_code", {
        "query": "Compute square",
        "index_name": "custom_math_v1",
        "user_id": 42
    })
    assert res_code["success"] is True
    assert res_code["count"] >= 1

    # List indexes
    res_list = await plugin.execute_action("list_indexes", {"user_id": 42})
    assert res_list["success"] is True
    assert any(i["name"] == "custom_math_v1" for i in res_list["indexes"])

    # Streaming handle test
    events = []
    async for event in plugin.handle("SuperCalculator", index_name="custom_math_v1", user_id=42):
        events.append(event)
    assert len(events) >= 2
    assert events[-1]["status"] == "complete"
    assert len(events[-1]["data"]["symbols"]) >= 1
