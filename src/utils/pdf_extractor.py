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

from src.utils.pdf import extract_pdf_text
from src.utils.image import get_image_bytes
import asyncio
from pathlib import Path
from typing import Optional, Union
from logger.logger import logger


def extract_text_from_image_sync(image_input: Union[str, Path, bytes]) -> str:
    """Synchronously extract textual content from an image.

    Args:
        image_input (Union[str, Path, bytes]): Path to image or raw image bytes.

    Returns:
        str: Extracted textual content.
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        if isinstance(image_input, (str, Path)):
            img = Image.open(str(image_input))
        else:
            img = Image.open(io.BytesIO(image_input))
        text = pytesseract.image_to_string(img, lang="rus+eng")
        return text.strip() if text else ""
    except Exception as ex:
        logger.debug(f"Direct tesseract extraction failed: {ex}")

    return ""


async def extract_text_from_image(image_input: Union[str, Path, bytes]) -> str:
    """Extract textual content from an image using cascading OCR and vision models.

    Args:
        image_input (Union[str, Path, bytes]): Path to image or raw bytes.

    Returns:
        str: Extracted text or empty string on failure.
    """
    # 1. Try pytesseract if available
    tess_text = extract_text_from_image_sync(image_input)
    if tess_text and len(tess_text) > 10:
        return tess_text

    # 2. Try Gemini Multimodal Vision
    try:
        from src.ai.gemini.api import GoogleGenerativeAI
        ai = GoogleGenerativeAI()
        img_path = Path(image_input) if isinstance(image_input, (str, Path)) else None
        img_bytes = image_input if isinstance(image_input, bytes) else (img_path.read_bytes() if img_path else None)

        if img_bytes:
            prompt = (
                "Extract all text, numbers, dates, company names, line items, and totals "
                "from this document image. Preserve key numbers and table layout."
            )
            res = await ai.describe_image(img_bytes, prompt=prompt)
            if res and isinstance(res, str):
                return res.strip()
    except Exception as ex:
        logger.debug(f"Gemini vision OCR fallback error: {ex}")

    return tess_text or ""


async def extract_document_text(file_path: Union[str, Path]) -> str:
    """Extract textual content from a PDF or image document.

    Args:
        file_path (Union[str, Path]): Path to PDF or image file.

    Returns:
        str: Extracted document text.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Document file not found: {path}")
        return ""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf_text(path)
        if text and len(text.strip()) > 20:
            return text.strip()
        # If PDF has no extractable text layer (scanned PDF), attempt vision on pages
        try:
            import fitz  # PyMuPDF if available
            doc = fitz.open(str(path))
            pages_text = []
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                page_ocr = await extract_text_from_image(img_bytes)
                if page_ocr:
                    pages_text.append(f"## Page {i + 1}\n{page_ocr}")
            if pages_text:
                return "\n\n".join(pages_text)
        except Exception:
            pass
        return text or ""

    if suffix in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"):
        return await extract_text_from_image(path)

    return ""


__all__ = ["extract_pdf_text", "extract_text_from_image", "extract_document_text"]


