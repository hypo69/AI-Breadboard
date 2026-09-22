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
from logger.logger import logger
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

    @staticmethod
    def _is_ignored(rel_path: str, excludes: list[str]) -> bool:
        """
        Check if relative path matches default or user exclusions.
        
        Preserves important dot-directories like `.ai`, `.agents`, `.gemini`,
        while ignoring tool/cache directories like `.git`, `.vscode`, `.idea`, `__pycache__`.
        """
        import fnmatch
        default_excludes = [
            ".git", ".vs", ".vscode", ".idea",
            "__pycache__", ".pytest_cache", ".coverage", "coverage", "htmlcov",
            ".hypothesis", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
            ".venv", "venv", "node_modules",
            "dist", "build", "pdf_exports", ".system_generated", "brain"
        ]
        all_excludes = default_excludes + excludes
        normalized_path = rel_path.replace('\\', '/')
        path_parts = Path(normalized_path).parts

        for part in path_parts:
            for excl in all_excludes:
                if part == excl or fnmatch.fnmatch(part, excl):
                    return True

        for excl in all_excludes:
            if fnmatch.fnmatch(normalized_path, excl) or fnmatch.fnmatch(f"*/{normalized_path}", f"*/{excl}"):
                return True

        return False

    @classmethod
    def build_docs_pdf(
        cls,
        root_dir: str | Path,
        output_file: str | Path,
        doc_patterns: list[str] = ["*.md", "*.rst", "*.txt"],
        excludes: list[str] = []
    ) -> bool:
        """
        Collect and compile project documentation into a single PDF document.

        Args:
            root_dir (str | Path): Root directory to scan for documentation files.
            output_file (str | Path): Target PDF output file path.
            doc_patterns (list[str], optional): File patterns to consider as docs.
            excludes (list[str], optional): Additional folder or file patterns to ignore.

        Returns:
            bool: True if PDF generation succeeded, False otherwise.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
            from reportlab.lib import colors
            from src.utils.file import read_text_file, recursively_get_file_path
            from src.utils.convertors.md import md2html
            import html as html_lib

            root_path = Path(root_dir).resolve()
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass

            found_files: list[Path] = []
            for pattern in doc_patterns:
                found_files.extend(recursively_get_file_path(root_path, pattern))

            # Filter unique & non-ignored files
            unique_files: list[Path] = []
            seen = set()
            for fp in found_files:
                if not fp.is_file() or fp in seen:
                    continue
                seen.add(fp)
                rel = fp.relative_to(root_path).as_posix()
                if not cls._is_ignored(rel, excludes):
                    unique_files.append(fp)

            unique_files.sort(key=lambda p: p.relative_to(root_path).as_posix())

            if not unique_files:
                logger.warning(f"No documentation files found in {root_path}")
                return False

            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                leftMargin=40,
                rightMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor('#1E3A8A'),
                spaceAfter=15
            )
            file_header_style = ParagraphStyle(
                'FileHeader',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#0F766E'),
                spaceBefore=10,
                spaceAfter=8
            )
            body_style = ParagraphStyle(
                'DocBody',
                parent=styles['Normal'],
                fontSize=9,
                leading=12,
                spaceAfter=6
            )
            code_style = ParagraphStyle(
                'DocCode',
                parent=styles['Code'],
                fontName='Courier',
                fontSize=8,
                leading=10,
                backColor=colors.HexColor('#F3F4F6'),
                borderPadding=4,
                spaceAfter=6
            )

            story = []
            story.append(Paragraph("Project Documentation", title_style))
            story.append(Paragraph(f"Generated from: {root_path.name} | Total documents: {len(unique_files)}", body_style))
            story.append(Spacer(1, 15))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=20))

            for idx, file_p in enumerate(unique_files):
                rel_str = file_p.relative_to(root_path).as_posix()
                content = read_text_file(file_p) or ""
                
                story.append(Paragraph(f"📄 {html_lib.escape(rel_str)}", file_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=10))

                for block in content.split('\n\n'):
                    block = block.strip()
                    if not block:
                        continue
                    if block.startswith('```') or block.startswith('    '):
                        safe_block = html_lib.escape(block).replace('\n', '<br/>')
                        story.append(Paragraph(safe_block, code_style))
                    elif block.startswith('#'):
                        safe_block = html_lib.escape(block)
                        story.append(Paragraph(f"<b>{safe_block}</b>", body_style))
                    else:
                        safe_block = html_lib.escape(block).replace('\n', ' ')
                        story.append(Paragraph(safe_block, body_style))

                if idx < len(unique_files) - 1:
                    story.append(PageBreak())

            doc.build(story)
            logger.info(f"Docs PDF successfully generated: {output_path}")
            return True

        except Exception as ex:
            logger.error(f"Error generating docs PDF: {ex}", exc_info=True)
            return False

    @classmethod
    def build_code_pdf(
        cls,
        root_dir: str | Path,
        output_file: str | Path,
        code_patterns: list[str] = ["*.py", "*.ps1", "*.sh", "*.json", "*.yaml", "*.yml", "*.sql", "*.js", "*.ts", "*.html", "*.css"],
        excludes: list[str] = []
    ) -> bool:
        """
        Collect and compile project source code into a single PDF document with syntax highlighting.

        Args:
            root_dir (str | Path): Root directory to scan for source code files.
            output_file (str | Path): Target PDF output file path.
            code_patterns (list[str], optional): File patterns to consider as code.
            excludes (list[str], optional): Additional folder or file patterns to ignore.

        Returns:
            bool: True if PDF generation succeeded, False otherwise.
        """
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Preformatted
            from reportlab.lib import colors
            from src.utils.file import read_text_file, recursively_get_file_path
            import html as html_lib

            root_path = Path(root_dir).resolve()
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass

            found_files: list[Path] = []
            for pattern in code_patterns:
                found_files.extend(recursively_get_file_path(root_path, pattern))

            unique_files: list[Path] = []
            seen = set()
            for fp in found_files:
                if not fp.is_file() or fp in seen:
                    continue
                seen.add(fp)
                rel = fp.relative_to(root_path).as_posix()
                if not cls._is_ignored(rel, excludes):
                    unique_files.append(fp)

            unique_files.sort(key=lambda p: p.relative_to(root_path).as_posix())

            if not unique_files:
                logger.warning(f"No source code files found in {root_path}")
                return False

            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=landscape(A4),
                leftMargin=30,
                rightMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CodeDocTitle',
                parent=styles['Heading1'],
                fontSize=18,
                leading=22,
                textColor=colors.HexColor('#1E293B'),
                spaceAfter=10
            )
            file_header_style = ParagraphStyle(
                'CodeFileHeader',
                parent=styles['Heading2'],
                fontSize=11,
                leading=14,
                textColor=colors.HexColor('#1E40AF'),
                spaceBefore=6,
                spaceAfter=6
            )
            meta_style = ParagraphStyle(
                'CodeMeta',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                textColor=colors.HexColor('#64748B'),
                spaceAfter=8
            )
            code_style = ParagraphStyle(
                'CodeBlock',
                parent=styles['Code'],
                fontName='Courier',
                fontSize=7,
                leading=8.5,
                textColor=colors.HexColor('#0F172A')
            )

            story = []
            story.append(Paragraph("Project Source Code Compilation", title_style))
            story.append(Paragraph(f"Root: {root_path.name} | Total files: {len(unique_files)}", meta_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

            for idx, file_p in enumerate(unique_files):
                rel_str = file_p.relative_to(root_path).as_posix()
                lines = read_text_file(file_p, as_list=True) or []
                
                story.append(Paragraph(f"📁 {html_lib.escape(rel_str)}", file_header_style))
                story.append(Paragraph(f"Lines: {len(lines)} | Extension: {file_p.suffix}", meta_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#93C5FD'), spaceAfter=8))

                # Numbered code lines
                numbered_lines = []
                for line_no, line in enumerate(lines, 1):
                    clean_line = line.rstrip('\r\n')
                    numbered_lines.append(f"{line_no:4d} | {clean_line}")

                code_text = "\n".join(numbered_lines) if numbered_lines else "(empty file)"
                story.append(Preformatted(code_text, code_style))

                if idx < len(unique_files) - 1:
                    story.append(PageBreak())

            doc.build(story)
            logger.info(f"Code PDF successfully generated: {output_path}")
            return True

        except Exception as ex:
            logger.error(f"Error generating code PDF: {ex}", exc_info=True)
            return False


