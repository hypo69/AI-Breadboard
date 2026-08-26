#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Universal CLI for Project Tools Management
# =============================================================================
# Description:
#   Single entry point for all utility scripts and plugins:
#   - Knowledge and RAG management (knowledge, rag) -> plugins.rag.tools
#   - Documentation and development (docs, dev) -> scripts.dev
#
# File: manage_tools.py
# Project: ai-assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

import header
from header import __root__
from core.skills import SkillRegistry

# Fix Windows console utf-8 output encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv(__root__ / '.env')


def _run_script(script_rel_path: str, extra_args: list[str] = []) -> int:
    """Runs a Python script by relative path from the project root.

    Args:
        script_rel_path (str): Relative path to the script from the project root.
        extra_args (list[str]): Additional command line arguments.

    Returns:
        int: Process return code (0 - success, >0 - error).
    """
    target_path = __root__ / script_rel_path
    if not target_path.exists():
        print(f"Error: script not found: {target_path}")
        return 1

    cmd = [sys.executable, str(target_path)]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, cwd=str(__root__))
    return result.returncode


def run_knowledge_command(args: argparse.Namespace) -> int:
    """Commands for managing the project knowledge base."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub in ('extract', 'add', 'init'):
        cmd_args = [sub] + extra
        return _run_script('plugins/rag/tools/manage_knowledge.py', cmd_args)

    print(f"Unknown knowledge subcommand: {sub}")
    return 1


def run_rag_command(args: argparse.Namespace) -> int:
    """Commands for managing RAG indexes."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'rebuild':
        try:
            from core.rag import build_rules_index
            index_path, docs_path = build_rules_index()
            print(f"RAG index rebuilt successfully: {index_path}, {docs_path}")
            return 0
        except Exception as e:
            print(f"Error rebuilding RAG: {e}")
            return 1
    if sub == 'status':
        try:
            from header import __root__
            idx_file = __root__ / 'tmp' / 'rag' / 'rules.index'
            print(f"Core RAG status: {'Ready' if idx_file.exists() else 'Not built'}")
            return 0
        except Exception as e:
            print(f"Error checking RAG status: {e}")
            return 1

    print(f"Unknown rag subcommand: {sub}")
    return 1


def run_docs_command(args: argparse.Namespace) -> int:
    """Commands for managing documentation."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'update':
        return _run_script('scripts/dev/update_docs.py', extra)

    print(f"Unknown docs subcommand: {sub}")
    return 1


def run_skills_command(args: argparse.Namespace) -> int:
    """Выводит единый каталог навыков для любого AI-агента."""
    registry = SkillRegistry()
    sub = args.subcommand

    if sub == 'list':
        for skill in registry.discover():
            print(f"{skill.name}\t{skill.description}")
        return 0

    if sub == 'search':
        for skill in registry.search(args.query):
            print(f"{skill.name}\t{skill.description}")
        return 0

    if sub in ('show', 'export'):
        try:
            if sub == 'show':
                skill = registry.get(args.name)
                print(skill.prompt())
            else:
                print(registry.export_json(args.name, include_instructions=not args.without_instructions))
            return 0
        except KeyError as error:
            print(f"Error: {error}")
            return 1

    print(f"Unknown skills subcommand: {sub}")
    return 1


def main() -> int:
    """Main entry point for the universal CLI."""
    parser = argparse.ArgumentParser(
        prog='manage_tools.py',
        description='Universal CLI for managing ai-assistant project tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  py manage_tools.py rag rebuild                          # rebuild RAG index
  py manage_tools.py knowledge extract --file chat.md     # extract knowledge
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # --- Knowledge commands ---
    knowledge_parser = subparsers.add_parser('knowledge', help='Knowledge management')
    knowledge_subparsers = knowledge_parser.add_subparsers(dest='subcommand', help='Subcommands')
    knowledge_extract = knowledge_subparsers.add_parser('extract', help='Extract knowledge from chats')
    knowledge_extract.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments')
    knowledge_add = knowledge_subparsers.add_parser('add', help='Add new entry to knowledge')
    knowledge_add.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments')
    knowledge_subparsers.add_parser('init', help='Initialize knowledge registry')

    # --- RAG commands ---
    rag_parser = subparsers.add_parser('rag', help='RAG index management')
    rag_subparsers = rag_parser.add_subparsers(dest='subcommand', help='Subcommands')
    rag_subparsers.add_parser('rebuild', help='Full rebuild of RAG index')
    rag_subparsers.add_parser('reindex', help='Reindex knowledge base')
    rag_subparsers.add_parser('validate', help='Validate knowledge base files')
    rag_subparsers.add_parser('status', help='Check RAG index status')

    # --- Docs commands ---
    docs_parser = subparsers.add_parser('docs', help='Documentation management')
    docs_subparsers = docs_parser.add_subparsers(dest='subcommand', help='Subcommands')
    # --- Skills commands ---
    skills_parser = subparsers.add_parser('skills', help='Universal skills registry')
    skills_subparsers = skills_parser.add_subparsers(dest='subcommand', help='Subcommands')
    skills_subparsers.add_parser('list', help='List discovered skills')
    skills_search = skills_subparsers.add_parser('search', help='Search skills by name or description')
    skills_search.add_argument('query', help='Search terms')
    skills_show = skills_subparsers.add_parser('show', help='Print Markdown instructions')
    skills_show.add_argument('name', help='Skill name')
    skills_export = skills_subparsers.add_parser('export', help='Export a portable JSON skill contract')
    skills_export.add_argument('name', help='Skill name')
    skills_export.add_argument('--without-instructions', action='store_true', help='Exclude Markdown instructions')
    # --- Assist CLI commands ---
    assist_parser = subparsers.add_parser('assist', help='Assistant management (start, stop, status, providers, etc.)')
    assist_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments for assist CLI')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == 'assist':
        from scripts.dev import assist_cli
        sys.argv = ['assist'] + getattr(args, 'rest', [])
        return assist_cli.main()

    if not getattr(args, 'subcommand', ''):
        parser.print_help()
        return 0

    dispatch = {
        'knowledge': run_knowledge_command,
        'rag': run_rag_command,
        'docs': run_docs_command,
        'skills': run_skills_command,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == '__main__':
    sys.exit(main())
