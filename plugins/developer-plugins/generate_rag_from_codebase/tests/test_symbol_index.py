# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Code Symbol Index
# =============================================================================
# Description:
#   Unit tests verifying symbol table indexing, exact/fuzzy search, and persistence.
#
# File: test_symbol_index.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
import pytest

from plugins.generate_rag_from_codebase.symbol_index import CodeSymbolIndex


def test_symbol_index_crud_and_search(tmp_path: Path):
    index = CodeSymbolIndex()

    sample_chunk = {
        "id": "src/ai/agent.py::MediaSearchAgent.search",
        "symbol": "MediaSearchAgent.search",
        "type": "python_method",
        "path": "src/ai/agent.py",
        "module": "src.ai.agent",
        "class_name": "MediaSearchAgent",
        "function_name": "search",
        "signature": "async def search(query: str)",
        "docstring": "Search media.",
        "related_symbols": ["_get_llm"]
    }

    index.add_symbol_from_chunk(sample_chunk)

    # Search by simple method name
    results_simple = index.search("search")
    assert len(results_simple) >= 1
    assert results_simple[0]["symbol"] == "MediaSearchAgent.search"

    # Search by full symbol
    results_full = index.search("mediasearchagent.search", exact=True)
    assert len(results_full) == 1

    # Persistence
    save_file = tmp_path / "symbols.json"
    index.save(save_file)
    assert save_file.exists()

    new_index = CodeSymbolIndex()
    assert new_index.load(save_file) is True
    assert new_index.count() == index.count()
