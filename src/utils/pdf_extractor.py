# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: PDF Text Extraction Utilities
# =============================================================================
# Description:
#   PDF text extraction using pypdf/pdfminer if available, with robust fallback.
#
# File: pdf_extractor.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Union
from src.logger.logger import logger

def extract_pdf_text(file_path: Union[str, Path]) -> Optional[str]:
    path = Path(file_path)
    if not path.is_file():
        logger.error(f'PDF file not found: {path}')
        return None

    # Try pypdf first
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append(f'## Page {i + 1}\n\n' + text)
        if pages:
            return '\n\n'.join(pages)
    except Exception:
        pass

    # Try pdfminer
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(str(path))
        if text and text.strip():
            return text
    except Exception:
        pass

    # Fallback to pure regex stream extraction
    try:
        with open(path, 'rb') as f:
            content = f.read()
        # Find raw text in BT / ET blocks or (text) Tj
        text_matches = re.findall(b'\(([\w\s.,!?;:/-]+)\)\s*Tj', content)
        if text_matches:
            decoded = ' '.join([m.decode('utf-8', errors='ignore') for m in text_matches])
            return decoded
    except Exception as ex:
        logger.error(f'Failed to extract text from PDF: {path}', ex)

    return None
