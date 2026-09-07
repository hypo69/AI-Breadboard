# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: PDF conversion utilities for HTML content and files
# =============================================================================
# Description:
#   Provides utilities for converting HTML content and files to PDF format using
#   multiple libraries including pdfkit, reportlab, weasyprint, and xhtml2pdf.
#   Includes text extraction and PDF generation from various sources.
#
# File: pdf.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import sys
import os
import json

from pathlib import Path
from typing import Union, Optional
from src.logger.logger import logger
from header import __root__


wkhtmltopdf_exe: Path = Path(r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

def extract_pdf_text(file_path: Union[str, Path]) -> Optional[str]:
    """
    Extract text content from a PDF file using pypdf -> pdfminer -> regex stream fallback.

    Args:
        file_path (Union[str, Path]): Path to the PDF file.

    Returns:
        Optional[str]: Extracted text or None if failed.
    """
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
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        text = pdfminer_extract_text(str(path))
        if text and text.strip():
            return text
    except Exception:
        pass

    # Fallback to pure regex stream extraction
    try:
        import re
        with open(path, 'rb') as f:
            content = f.read()
        text_matches = re.findall(rb'\(([\w\s.,!?;:/-]+)\)\s*Tj', content)
        if text_matches:
            decoded = ' '.join([m.decode('utf-8', errors='ignore') for m in text_matches])
            return decoded
    except Exception as ex:
        logger.error(f'Failed to extract text from PDF: {path}', ex)

    return None


class PDFUtils:

    """
    Utilities class for PDF file operations providing methods for saving HTML content to PDF using various libraries.
    """

    @staticmethod
    def save_pdf_pdfkit(data: str | Path, pdf_file: str | Path) -> bool:
        """Saving HTML content or file to PDF using pdfkit library."""
        try:
            import pdfkit
            configuration = pdfkit.configuration(wkhtmltopdf=str(wkhtmltopdf_exe))
            options = {"enable-local-file-access": ""}
            if isinstance(data, str):
                pdfkit.from_string(data, pdf_file, configuration=configuration, options=options)
            else:
                pdfkit.from_file(str(data), pdf_file, configuration=configuration, options=options)
            logger.info(f"PDF successfully saved: {pdf_file}")
            return True
        except Exception as ex:
            logger.error("Error during PDF generation with pdfkit: ", ex)
            return False

    @staticmethod
    def save_pdf_fpdf(data: str, pdf_file: str | Path) -> bool:
        """Save text to PDF using FPDF library."""
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            fonts_file_path = __root__ / 'assets' / 'fonts' / 'fonts.json'
            if fonts_file_path.exists():
                with open(fonts_file_path, 'r', encoding='utf-8') as json_file:
                    fonts = json.load(json_file)
                for font_name, font_info in fonts.items():
                    font_path = __root__ / 'assets' / 'fonts' / font_info['path']
                    if font_path.exists():
                        pdf.add_font(font_info['family'], font_info['style'], str(font_path), uni=font_info.get('uni', True))
                pdf.set_font('DejaVuSans', style='book', size=12)
            else:
                pdf.set_font('Helvetica', size=12)

            pdf.multi_cell(0, 10, data)
            pdf.output(str(pdf_file))
            logger.info(f'PDF report successfully saved: {pdf_file}')
            return True
        except Exception as ex:
            logger.error('Error saving PDF via FPDF: ', ex)
            return False

    @staticmethod
    def save_pdf_weasyprint(data: str | Path, pdf_file: str | Path) -> bool:
        """Save HTML content or file to PDF using WeasyPrint library."""
        try:
            from weasyprint import HTML
            if isinstance(data, str):
                HTML(string=data).write_pdf(pdf_file)
            else:
                HTML(filename=str(data)).write_pdf(pdf_file)
            logger.info(f"PDF successfully saved: {pdf_file}")
            return True
        except Exception as ex:
            logger.error("Error saving PDF via WeasyPrint: ", ex)
            return False

    @staticmethod
    def save_pdf_xhtml2pdf(data: str | Path, pdf_file: str | Path) -> bool:
        """Save HTML content or file to PDF using xhtml2pdf library."""
        try:
            from xhtml2pdf import pisa
            with open(pdf_file, "w+b") as result_file:
                if isinstance(data, str):
                    pisa.CreatePDF(data, dest=result_file)
                else:
                    with open(data, "r", encoding="utf-8") as source_file:
                        source_data = source_file.read()
                        pisa.CreatePDF(source_data, dest=result_file, encoding='UTF-8')
            logger.info(f"PDF successfully saved: {pdf_file}")
            return True
        except Exception as ex:
            logger.error("Error saving PDF via xhtml2pdf: ", ex)
            return False

    @staticmethod
    def html2pdf(html_str: str, pdf_file: str | Path) -> bool | None:
        """Converts HTML content to a PDF file using WeasyPrint."""
        try:
            from weasyprint import HTML
            HTML(string=html_str).write_pdf(pdf_file)
            return True
        except Exception as e:
            logger.error(f"Error during PDF generation: {e}")
            return None

    @staticmethod
    def pdf_to_html(pdf_file: str | Path, html_file: str | Path) -> bool:
        """Convert PDF file to HTML file."""
        try:
            text = extract_pdf_text(pdf_file) or ""
            with open(html_file, 'w', encoding='utf-8') as file:
                file.write(f"<html><body><pre>{text}</pre></body></html>")
            logger.info(f"HTML successfully saved: {html_file}")
            return True
        except Exception as ex:
            logger.error(f"Error converting PDF to HTML: {ex}")
            return False

    @staticmethod
    def dict2pdf(data: dict | Any, file_path: str | Path) -> bool:
        """Save dictionary data to a PDF file."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from types import SimpleNamespace

            if isinstance(data, SimpleNamespace):
                data = data.__dict__

            pdf = canvas.Canvas(str(file_path), pagesize=A4)
            width, height = A4
            x, y = 50, height - 50
            pdf.setFont("Helvetica", 12)

            for key, value in data.items():
                line = f"{key}: {value}"
                pdf.drawString(x, y, line)
                y -= 20
                if y < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 12)
                    y = height - 50

            pdf.save()
            return True
        except Exception as ex:
            logger.error(f"Error creating PDF from dict: {ex}")
            return False

