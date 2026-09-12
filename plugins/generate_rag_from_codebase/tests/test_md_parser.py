# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Markdown Hierarchy Parser
# =============================================================================
# Description:
#   Unit tests verifying heading-based section chunking and breadcrumb hierarchy.
#
# File: test_md_parser.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
import pytest

from plugins.generate_rag_from_codebase.md_parser import MarkdownParser


SAMPLE_MARKDOWN = '''# RAG Architecture

Overview of RAG components.

## Ingestion Pipeline

Describes the document parsing process.

### AST Parser

Extracts semantic code nodes.

### Heading Parser

Decomposes Markdown headers.
'''


def test_md_parser_headings(tmp_path: Path):
    doc_file = tmp_path / "docs" / "rag_guide.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    doc_file.write_text(SAMPLE_MARKDOWN, encoding="utf-8")

    parser = MarkdownParser(base_dir=tmp_path)
    chunks = parser.parse_file(doc_file)

    assert len(chunks) == 4
    headings = [c["heading"] for c in chunks]
    assert "RAG Architecture" in headings
    assert "Ingestion Pipeline" in headings
    assert "AST Parser" in headings
    assert "Heading Parser" in headings

    ast_chunk = next(c for c in chunks if c["heading"] == "AST Parser")
    assert ast_chunk["parent_heading"] == "Ingestion Pipeline"
    assert ast_chunk["breadcrumb"] == "RAG Architecture > Ingestion Pipeline > AST Parser"
    assert "Extracts semantic code nodes." in ast_chunk["text"]
