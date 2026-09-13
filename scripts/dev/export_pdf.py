# -*- coding: utf-8 -*-
# ====================================================================
# Process Name: Project Code and Docs PDF Exporter CLI
# ===================================================================
# Description:
#   Exports all relevant code and documentation into two PDF documents:
#   docs.pdf and code.pdf.
#
# File: export_pdf.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# ====================================================================

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import header
from header import __root__
from src.logger.logger import logger
from src.utils.pdf import PDFUtils


def main(args_list: list[str] | None = None) -> int:
    """Export codebase and documentation to PDF."""
    parser = argparse.ArgumentParser(
        prog='manage_tools.py docs pdf',
        description='Compile project code and documentation into docs.pdf and code.pdf'
    )
    parser.add_argument(
        '--target',
        choices=['all', 'docs', 'code'],
        default='all',
        help='Which PDF(s) to generate (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        default='pdf_exports',
        help='Directory to save generated PDF, relative to project root'
    )
    parser.add_argument(
        '--root-dir',
        default='.',
        help='Root directory to scan (default: project root)'
    )

    raw_args = args_list if args_list is not None else sys.argv[1:]
    args = parser.parse_args(raw_args)

    root_dir = (__root__ / args.root_dir).resolve()
    output_dir = (__root__ / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    success = True

    if args.target in ('all', 'docs'):
        docs_pdf = output_dir / 'docs.pdf'
        logger.info(f"Generating documentation PDF: {docs_pdf}...")
        ok_docs = PDFUtils.build_docs_pdf(root_dir=root_dir, output_file=docs_pdf)
        if ok_docs:
            print(f"✅ Saved documentation PDF: {docs_pdf}")
        else:
            print(f"❌ Failed to generate documentation PDF")
            success = False

    if args.target in ('all', 'code'):
        code_pdf = output_dir / 'code.pdf'
        logger.info(f"Generating source code PDF: {code_pdf}...")
        ok_code = PDFUtils.build_code_pdf(root_dir=root_dir, output_file=code_pdf)
        if ok_code:
            print(f"✅ Saved source code PDF: {code_pdf}")
        else:
            print(f"❌ Failed to generate source code PDF")
            success = False

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
