# -*- coding: utf-8 -*-
# ====================================================================
# Process Name: Unit tests for PDF export utilities
# ===================================================================
# Description:
#   Tests PDF generation functions including build_docs_pdf and build_code_pdf.
##
# File: test_pdf_export.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# ===================================================================

import pytest
from pathlib import Path
from src.utils.pdf import PDFUtils
from src.utils.file import save_text_file

def test_build_docs_pdf(tmp_path: Path):
    """Test generating docs.pdf from markdown files."""
    doc_dir = tmp_path / 'docs'
    doc_dir.mkdir()
    
    save_text_file('# Document 1\n\nThis is a test doc.', doc_dir / 'doc1.md')
    save_text_file('# Document 2\n\n```python\nprint(\'hello\')\n```', doc_dir / 'doc2.md')
    
    out_pdf = tmp_path / 'output' / 'docs.pdf'
    
    success = PDFUtils.build_docs_pdf(
        root_dir=tmp_path,
        output_file=out_pdf,
        doc_patterns=['*.md']
    )
    
    assert success is True
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0

def test_build_docs_pdf_silent_overwrite(tmp_path: Path):
    """Test that build_docs_pdf silently overwrites existing files."""
    doc_dir = tmp_path / 'docs'
    doc_dir.mkdir(exist_ok=True)
    save_text_file('# Original Doc', doc_dir / 'doc.md')

    out_pdf = tmp_path / 'output' / 'docs.pdf'
    out_pdf.parent.mkdir(exist_ok=True)
    out_pdf.write_text('temp old content')
    assert out_pdf.exists()

    success = PDFUtils.build_docs_pdf(
        root_dir=tmp_path,
        output_file=out_pdf,
        doc_patterns=['*.md']
    )

    assert success is True
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 10

    
def test_build_code_pdf(tmp_path: Path):
    """Test generating code.pdf from source files."""
    src_dir = tmp_path / 'src'
    src_dir.mkdir()
    
    save_text_file('def hello():\n    return \'world\'\n', src_dir / 'main.py')
    save_text_file('{"status": "ok"}', src_dir / 'config.json')
    
    out_pdf = tmp_path / 'output' / 'code.pdf'
    
    success = PDFUtils.build_code_pdf(
        root_dir=tmp_path,
        output_file=out_pdf,
        code_patterns=['*.py', '*.json']
    )
    
    assert success is True
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0

def test_build_code_pdf_silent_overwrite(tmp_path: Path):
    """Test that build_code_pdf silently overwrites existing files."""
    src_dir = tmp_path / 'src'
    src_dir.mkdir(exist_ok=True)
    save_text_file('print(1)', src_dir / 'a.py')

    out_pdf = tmp_path / 'output' / 'code.pdf'
    out_pdf.parent.mkdir(exist_ok=True)
    out_pdf.write_text('temp old code')

    success = PDFUtils.build_code_pdf(
        root_dir=tmp_path,
        output_file=out_pdf,
        code_patterns=['*.py']
    )

    assert success is True
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 10

def test_build_docs_pdf_empty_dir_test(tmp_path: Path):
    """Test handling of directory with no documents."""
    empty_dir = tmp_path / 'empty'
    empty_dir.mkdir()
    out_pdf = tmp_path / 'output' / 'empty_docs.pdf'
    
    success = PDFUtils.build_docs_pdf(
        root_dir=empty_dir,
        output_file=out_pdf,
        doc_patterns=['+.md']
    )
    
    assert success is False
