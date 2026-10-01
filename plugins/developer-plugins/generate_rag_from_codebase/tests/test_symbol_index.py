# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins Developer-Plugins Generate_Rag_From_Codebase Tests - Test Symbol Index
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_symbol_index`).
#
# Usage Examples:
#   Python API:
#     from plugins.developer-plugins.generate_rag_from_codebase.tests.test_symbol_index import test_symbol_index_crud_and_search
#
#     res = test_symbol_index_crud_and_search()
#
# File: test_symbol_index.py
# Project: ai-breadboard
# Package: plugins.developer-plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_symbol_index`)."""

from pathlib import Path
import pytest
from plugins.generate_rag_from_codebase.symbol_index import CodeSymbolIndex

def test_symbol_index_crud_and_search(tmp_path: Path):
    index = CodeSymbolIndex()
    sample_chunk = {'id': 'src/ai/agent.py::MediaSearchAgent.search', 'symbol': 'MediaSearchAgent.search', 'type': 'python_method', 'path': 'src/ai/agent.py', 'module': 'src.ai.agent', 'class_name': 'MediaSearchAgent', 'function_name': 'search', 'signature': 'async def search(query: str)', 'docstring': 'Search media.', 'related_symbols': ['_get_llm']}
    index.add_symbol_from_chunk(sample_chunk)
    results_simple = index.search('search')
    assert len(results_simple) >= 1
    assert results_simple[0]['symbol'] == 'MediaSearchAgent.search'
    results_full = index.search('mediasearchagent.search', exact=True)
    assert len(results_full) == 1
    save_file = tmp_path / 'symbols.json'
    index.save(save_file)
    assert save_file.exists()
    new_index = CodeSymbolIndex()
    assert new_index.load(save_file) is True
    assert new_index.count() == index.count()