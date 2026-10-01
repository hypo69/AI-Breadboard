# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Plugins Developer-Plugins Generate_Rag_From_Codebase Tests - Test Md Parser
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_md_parser`).
#
# Usage Examples:
#   Python API:
#     from plugins.developer-plugins.generate_rag_from_codebase.tests.test_md_parser import test_md_parser_headings
#
#     res = test_md_parser_headings()
#
# File: test_md_parser.py
# Project: ai-breadboard
# Package: plugins.developer-plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:23:11
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_md_parser`)."""

from pathlib import Path
import pytest
from plugins.generate_rag_from_codebase.md_parser import MarkdownParser
SAMPLE_MARKDOWN = '# RAG Architecture\n\nOverview of RAG components.\n\n## Ingestion Pipeline\n\nDescribes the document parsing process.\n\n### AST Parser\n\nExtracts semantic code nodes.\n\n### Heading Parser\n\nDecomposes Markdown headers.\n'

def test_md_parser_headings(tmp_path: Path):
    doc_file = tmp_path / 'docs' / 'rag_guide.md'
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    doc_file.write_text(SAMPLE_MARKDOWN, encoding='utf-8')
    parser = MarkdownParser(base_dir=tmp_path)
    chunks = parser.parse_file(doc_file)
    assert len(chunks) == 4
    headings = [c['heading'] for c in chunks]
    assert 'RAG Architecture' in headings
    assert 'Ingestion Pipeline' in headings
    assert 'AST Parser' in headings
    assert 'Heading Parser' in headings
    ast_chunk = next((c for c in chunks if c['heading'] == 'AST Parser'))
    assert ast_chunk['parent_heading'] == 'Ingestion Pipeline'
    assert ast_chunk['breadcrumb'] == 'RAG Architecture > Ingestion Pipeline > AST Parser'
    assert 'Extracts semantic code nodes.' in ast_chunk['text']