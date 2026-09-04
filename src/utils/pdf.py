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
import pdfkit
from reportlab.pdfgen import canvas
from fpdf import FPDF
from weasyprint import HTML
from xhtml2pdf import pisa
from pdfminer.high_level import extract_text
from src.logger.logger import logger
from src.utils.printer import pprint

def set_project_root(marker_files=('__root__','.git')) -> Path:
    """
    Finding the root directory of the project starting from the current file's directory.

    Args:
        marker_files (tuple): Filenames or directory names to identify the project root.
    
    Returns:
        Path: Path to the root directory if found, otherwise the directory where the script is located.
    """
    __root__:Path
    current_path:Path = Path(__file__).resolve().parent
    __root__ = current_path
    for parent in [current_path] + list(current_path.parents):
        if any((parent / marker).exists() for marker in marker_files):
            __root__ = parent
            break
    if __root__ not in sys.path:
        sys.path.insert(0, str(__root__))
    return __root__

# Get the root directory of the project
__root__: Path = set_project_root()
"""__root__ (Path): Path to the root directory of the project"""

wkhtmltopdf_exe = __root__ / 'bin' / 'wkhtmltopdf' / 'files' / 'bin' /  'wkhtmltopdf.exe'

if not wkhtmltopdf_exe.exists():
    logger.error("wkhtmltopdf.exe not found at specified path.")
    raise FileNotFoundError("wkhtmltopdf.exe is missing")

class PDFUtils:
    """
    Utilities class for PDF file operations providing methods for saving HTML content to PDF using various libraries.
    """

    @staticmethod
    def save_pdf_pdfkit(data: str | Path, pdf_file: str | Path) -> bool:
        """
        Saving HTML content or file to PDF using pdfkit library.

        Args:
            data (str | Path): HTML content or path to HTML file.
            pdf_file (str | Path): Path to saved PDF file.

        Returns:
            bool: True if PDF successfully saved, otherwise False.

        Exceptions:
            pdfkit.PDFKitError: Error during PDF generation via pdfkit.
            OSError: Error accessing file.
        """

        try:
            configuration = pdfkit.configuration(
                            wkhtmltopdf=str(wkhtmltopdf_exe)
                            )

            options = {"enable-local-file-access": ""}
            if isinstance(data, str):
                # Conversion of HTML content to PDF
                pdfkit.from_string(data, pdf_file, configuration=configuration, options=options)
            else:
                # Conversion of HTML file to PDF
                pdfkit.from_file(str(data), pdf_file, configuration=configuration, options=options)
            logger.info(f"PDF successfully saved: {pdf_file}")
            return True
        # except (pdfkit.PDFKitError, OSError) as ex:
        #     logger.error("Error during PDF generation: ", ex)
        #     return False
        except Exception as ex:
            logger.error("Unexpected error: ", ex)
            ...
            return False

    @staticmethod
    def save_pdf_fpdf(data: str, pdf_file: str | Path) -> bool:
        """
        Save text to PDF using FPDF library.

        Args:
            data (str): Text to save in PDF.
            pdf_file (str | Path): Path to saved PDF file.

        Returns:
            bool: `True` if PDF successfully saved, otherwise `False`.
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto = True, margin = 15)

            # Path to fonts.json file
            fonts_file_path = __root__ / 'assets' / 'fonts' / 'fonts.json'
            if not fonts_file_path.exists():
                logger.error(
                    f'Font settings JSON file not found: {fonts_file_path}\n'
                    'Format of `fonts.json` file:\n'
                    '{\n'
                    '    "dejavu-sans.book": {\n'
                    '        "family": "DejaVuSans",\n'
                    '        "path": "dejavu-sans.book.ttf",\n'
                    '        "style": "book",\n'
                    '        "uni": true\n'
                    '    }\n'
                    '}'
                )
                raise FileNotFoundError(f'Font file not found: {fonts_file_path}')
                ...

            with open(fonts_file_path, 'r', encoding = 'utf-8') as json_file:
                fonts = json.load(json_file)

            # Add fonts
            for font_name, font_info in fonts.items():
                font_path = __root__ / 'assets' / 'fonts' / font_info['path']
                if not font_path.exists():
                    logger.error(f'Font file not found: {font_path}')
                    raise FileNotFoundError(f'Font file not found: {font_path}')
                    ...

                pdf.add_font(font_info['family'], font_info['style'], str(font_path), uni = font_info['uni'])

            # Set default font
            pdf.set_font('DejaVuSans', style = 'book', size = 12)
            pdf.multi_cell(0, 10, data)
            pdf.output(str(pdf_file))
            logger.info(f'PDF report successfully saved: {pdf_file}')
            return True
        except Exception as ex:
            logger.error('Error saving PDF via FPDF: ', ex)
            ...
            return False

    @staticmethod
    def save_pdf_weasyprint(data: str | Path, pdf_file: str | Path) -> bool:
        """
        Save HTML content or file to PDF using WeasyPrint library.

        Args:
            data (str | Path): HTML content or path to HTML file.
            pdf_file (str | Path): Path to saved PDF file.

        Returns:
            bool: `True` if PDF successfully saved, otherwise `False`.
        """
        try:
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
        """
        Save HTML content or file to PDF using xhtml2pdf library.

        Args:
            data (str | Path): HTML content or path to HTML file.
            pdf_file (str | Path): Path to saved PDF file.

        Returns:
            bool: `True` if PDF successfully saved, otherwise `False`.
        """
        try:
            with open(pdf_file, "w+b") as result_file:
                if isinstance(data, str):
                    # Ensure string has UTF-8 encoding
                    data_utf8 = data.encode('utf-8').decode('utf-8')  # Convert string back to UTF-8 if needed
                    try:
                        pisa.CreatePDF(data, dest=result_file)
                    except Exception as ex:
                        logger.error("Error compiling PDF: ", ex)
                        ...
                else:
                    with open(data, "r", encoding="utf-8") as source_file:
                        try:
                            # Read file in UTF-8 encoding
                            source_data = source_file.read()
                            pisa.CreatePDF(source_data, dest=result_file, encoding='UTF-8')
                        except Exception as ex:
                            logger.error("Error compiling PDF: ", ex)
                            ...
            logger.info(f"PDF successfully saved: {pdf_file}")
            ...
            return True
        except Exception as ex:
            logger.error("Error saving PDF via xhtml2pdf: ", ex)
            ...
            return False

    @staticmethod
    def html2pdf(html_str: str, pdf_file: str | Path) -> bool | None:
        """Converts HTML content to a PDF file using WeasyPrint."""
        try:
            HTML(string=html_str).write_pdf(pdf_file)
            return True
        except Exception as e:
            print(f"Error during PDF generation: {e}")
            return

        
    @staticmethod
    def pdf_to_html(pdf_file: str | Path, html_file: str | Path) -> bool:
        """
        Convert PDF file to HTML file.

        Args:
            pdf_file (str | Path): Path to source PDF file.
            html_file (str | Path): Path to saved HTML file.

        Returns:
            bool: `True` if conversion successful, otherwise `False`.
        """
        try:
            # Extract text from PDF
            text = extract_text(str(pdf_file))

            # Create HTML file
            with open(html_file, 'w', encoding='utf-8') as file:
                file.write(f"<html><body>{text}</body></html>")

            print(f"HTML successfully saved: {html_file}")
            return True
        except Exception as ex:
            print(f"Error converting PDF to HTML: {ex}")
            return False

    # Function to convert dictionary to PDF
    @staticmethod
    def dict2pdf(data: dict | 'SimpleNamespace', file_path: str | Path) -> None:
        """
        Save dictionary data to a PDF file.

        Args:
            data (dict | SimpleNamespace): The dictionary to convert to PDF.
            file_path (str | Path): Path to the output PDF file.
        """
        if isinstance(data, 'SimpleNamespace'):
            data = data.__dict__

        pdf = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4
        x, y = 50, height - 50

        pdf.setFont("Helvetica", 12)

        for key, value in data.items():
            line = f"{key}: {value}"
            pdf.drawString(x, y, line)
            y -= 20

            if y < 50:  # Create new page if not enough space
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = height - 50

        pdf.save()
