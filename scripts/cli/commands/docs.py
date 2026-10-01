# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Docs
# =============================================================================
# Description:
#   Команды управления документацией (docs).
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.docs import register_docs_parser
#
#     res = register_docs_parser()
#
# File: docs.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

from __future__ import annotations
"""Команды управления документацией (docs)."""

import argparse
from .common import run_script


def register_docs_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды docs."""
    docs_parser = subparsers.add_parser('docs', help='Documentation management')
    docs_subparsers = docs_parser.add_subparsers(dest='subcommand', help='Subcommands')
    docs_generate = docs_subparsers.add_parser('generate', help='Generate and synchronize API and scripts documentation')
    docs_generate.add_argument('rest', nargs=argparse.REMAINDER, help='Additional generator options')
    docs_update = docs_subparsers.add_parser('update', help='Validate documentation validity of modified files')
    docs_update.add_argument('rest', nargs=argparse.REMAINDER, help='Additional validator options')
    docs_pdf = docs_subparsers.add_parser('pdf', help='Export project code and documentation into code.pdf and docs.pdf')
    docs_pdf.add_argument('rest', nargs=argparse.REMAINDER, help='PDF exporter options (--target all|docs|code, --output-dir, etc.)')


def run_docs_command(args: argparse.Namespace) -> int:
    """Делегирование операций документирования внешним скриптам."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])
    if sub == 'generate':
        api_code = run_script('scripts/docs/generate_api.py', extra)
        if api_code != 0:
            return api_code
        scripts_code = run_script('scripts/dev/update_scripts_documentation.py', extra)
        return scripts_code
    if sub == 'update':
        return run_script('scripts/dev/update_docs.py', extra)
    if sub == 'pdf':
        return run_script('scripts/dev/export_pdf.py', extra)
    print(f'Unknown docs subcommand: {sub}')
    return 1
