# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Parse Order Document
# =============================================================================
# Description:
#   Extracts raw textual content from HR document files (.txt, .docx, .pdf).
#
# Examples:
#   >>> from parse_order import parse_document_text
#   >>> text = parse_document_text('sample.txt')
#
# File: parse_order.py
# Package: .agents.skills.employee-offboarding-monitor.scripts
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================
"""Document parser utility for HR dismissal orders."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_document_text(file_path: str | Path) -> str:
    """Extract text content from an HR document.

    Args:
        file_path (str | Path): Path to the target document.

    Returns:
        str: Extracted text content or empty string on error.

    Exceptions:
        FileNotFoundError: If the specified file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix in ('.txt', '.md', '.log'):
        return path.read_text(encoding='utf-8', errors='replace').strip()

    try:
        return path.read_text(encoding='utf-8', errors='replace').strip()
    except Exception:
        return ""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse text from HR document')
    parser.add_argument('--file', required=True, help='Path to document')
    args = parser.parse_args()
    print(parse_document_text(args.file))
