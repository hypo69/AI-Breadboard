# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Python AST Parser
# =============================================================================
# Description:
#   Unit tests verifying AST parsing into module, class, and method chunks
#   with accurate docstring, signature, and sibling relationship extraction.
#
# File: test_ast_parser.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
import pytest

from plugins.generate_rag_from_codebase.ast_parser import PythonAstParser


SAMPLE_PYTHON_CODE = '''"""Sample module docstring."""

import os
from typing import Dict, Any

class MediaSearchAgent:
    """Agent for searching media items."""
    
    def __init__(self, name: str) -> None:
        """Initialize agent."""
        self.name = name

    def _get_llm(self) -> str:
        """Get LLM instance."""
        return "gemini"

    async def search(self, query: str) -> Dict[str, Any]:
        """Perform media search."""
        return {"query": query}


def standalone_helper(x: int, y: int) -> int:
    """Helper function."""
    return x + y
'''


def test_ast_parser_extracts_chunks(tmp_path: Path):
    sample_file = tmp_path / "src" / "ai" / "sample_agent.py"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text(SAMPLE_PYTHON_CODE, encoding="utf-8")

    parser = PythonAstParser(base_dir=tmp_path)
    chunks = parser.parse_file(sample_file)

    chunk_types = [c["type"] for c in chunks]
    assert "python_module" in chunk_types
    assert "python_class" in chunk_types
    assert "python_method" in chunk_types
    assert "python_function" in chunk_types

    # Verify method chunk properties
    search_chunk = next(c for c in chunks if c["symbol"] == "MediaSearchAgent.search")
    assert search_chunk["is_async"] is True
    assert search_chunk["class_name"] == "MediaSearchAgent"
    assert search_chunk["docstring"] == "Perform media search."
    assert "os" in search_chunk["imports"]
    assert "_get_llm" in search_chunk["related_symbols"]
    assert "__init__" in search_chunk["related_symbols"]
    assert "async def search(self, query)" in search_chunk["signature"]
