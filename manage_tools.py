# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Execution of an external Python script as a subpro
# =============================================================================
# Description:
#   Single entry point for all utility scripts and plugins:
#
# File: manage_tools.py
# Project: ai-breadboard
# Package: root
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

# =============================================================================
# UTF-8 Encoding Fix for Windows Console
# =============================================================================
# Windows console uses legacy encoding (CP1251) by default.
# Reconfigure stdout/stderr to use UTF-8 with replacement for invalid characters.
# This ensures Cyrillic characters in logs and messages are displayed correctly.

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# =============================================================================
# Environment Variables Loading
# =============================================================================
# Load environment variables from .env file located in project root.
# This allows secure storage of API keys and sensitive configuration.

load_dotenv(__root__ / '.env')

def _run_script(script_rel_path: str, extra_args: list[str] = []) -> int:
    """Execution of an external Python script as a subprocess.

    Invokes a Python interpreter with the target script and forwards any
    additional command-line arguments. The script runs in the project root
    directory, preserving the environment context.

    Args:
        script_rel_path (str): Path to the script file relative to project root.
                               Example: 'plugins/rag/tools/manage_knowledge.py'
        extra_args (list[str]): List of command-line arguments to pass to the script.
                               These are appended to the command after the script path.

    Returns:
        int: Exit code from the subprocess. 0 indicates success, non-zero indicates error.

    Examples:
        >>> _run_script('scripts/dev/update_docs.py', ['--force'])
        0
    """
    # Resolve the target script path from project root directory
    target_path = __root__ / script_rel_path

    # Validate that the script file exists before attempting execution
    if not target_path.exists():
        print(f"Error: script not found: {target_path}")
        return 1

    # Build command: python interpreter + script path + any extra arguments
    cmd = [sys.executable, str(target_path)]
    if extra_args:
        cmd.extend(extra_args)

    # Execute the script as a subprocess in the project root directory
    result = subprocess.run(cmd, cwd=str(__root__))
    return result.returncode

def run_knowledge_command(args: argparse.Namespace) -> int:
    """Delegation of knowledge base management commands to the dedicated tool.

    Routes knowledge management operations (extract, add, init) to the
    external knowledge management script located in plugins/rag/tools.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The specific knowledge operation to perform.
            - rest (list[str]): Additional arguments for the subcommand.

    Returns:
        int: Exit code from the delegated knowledge management script.

    Subcommands:
        extract: Extract knowledge from chat files
        add: Add new entries to the knowledge base
        init: Initialize the knowledge registry
    """
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub in ('extract', 'add', 'init'):
        cmd_args = [sub] + extra
        return _run_script('plugins/rag/tools/manage_knowledge.py', cmd_args)

    print(f"Unknown knowledge subcommand: {sub}")
    return 1

def run_rag_command(args: argparse.Namespace) -> int:
    """Management of Retrieval-Augmented Generation (RAG) index operations.

    Provides direct access to RAG index lifecycle operations including
    rebuilding, reindexing, validation, and status checking.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The specific RAG operation to perform.

    Returns:
        int: Exit code indicating operation success (0) or failure (1).

    Subcommands:
        rebuild: Full reconstruction of the RAG index from source documents
        reindex: Incremental update of existing index
        validate: Verification of index integrity and document consistency
        status: Check whether the RAG index exists and is ready for use
    """
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'rebuild':
        extra = getattr(args, 'rest', [])
        try:
            from core.rag import build_rules_index
            index_path, docs_path = build_rules_index(*extra)
            print(f"RAG index rebuilt successfully: {index_path}, {docs_path}")
            return 0
        except TypeError:
            # If build_rules_index doesn't accept arguments, call without args
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
    """Delegation of documentation management operations to external scripts.

    Handles project documentation updates and maintenance through
    dedicated development scripts.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The documentation operation to perform.
            - rest (list[str]): Additional arguments for the operation.

    Returns:
        int: Exit code from the delegated documentation script.

    Subcommands:
        update: Run documentation update pipeline and regeneration scripts
    """
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'update':
        return _run_script('scripts/dev/update_docs.py', extra)

    print(f"Unknown docs subcommand: {sub}")
    return 1

def run_skills_command(args: argparse.Namespace) -> int:
    """Unified skills catalog management for AI agents.

    Discovers, searches, and exports AI capabilities (skills) from
    the universal skills registry. Supports multiple discovery roots
    (.agents/skills, .gemini/skills).

    The SkillRegistry provides a portable interface for AI agents to
    understand available capabilities without hardcoding references.

    Args:
        args (argparse.Namespace): Parsed command arguments containing:
            - subcommand (str): The skills operation to perform.
            - query (str): Search terms for 'search' subcommand.
            - name (str): Skill name for 'show' and 'export' subcommands.
            - without_instructions (bool): Flag to exclude instructions when exporting.

    Returns:
        int: Exit code indicating operation success (0) or failure (1).

    Subcommands:
        list: Display all discovered skills with their descriptions
        search: Find skills matching query string by name or description
        show: Print full Markdown instructions for a specific skill
        export: Generate portable JSON contract for skill integration
    """
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
    """Primary entry point for the universal CLI management system.

    Initializes the argument parser with all available command groups and
    dispatches incoming commands to their respective handlers.

    Returns:
        int: Exit code indicating overall command execution status:
            0 - Success (command executed properly)
            1 - Error (unknown command, missing arguments, or handler failure)

    Command Structure:
        manage_tools.py <command> [<subcommand>] [<args>]

    Available Commands:
        knowledge - Knowledge base extraction and management
        rag       - RAG index operations (rebuild, status)
        docs      - Documentation updates and generation
        skills    - Skills registry operations (list, search, show, export)
        assist    - Assistant process management
    """
    # Initialize the argument parser with program metadata and formatting options
    parser = argparse.ArgumentParser(
        prog='manage_tools.py',
        description='Universal CLI for managing ai-breadboard project tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  py manage_tools.py rag rebuild                          # rebuild RAG index
  py manage_tools.py knowledge extract --file chat.md     # extract knowledge
  py manage_tools.py skills list                          # list all available skills
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # ==========================================================================
    # Knowledge Management Subparser
    # ==========================================================================
    # Commands for extracting, adding, and initializing knowledge base entries
    # from chat files and documentation sources.

    knowledge_parser = subparsers.add_parser('knowledge', help='Knowledge management')
    knowledge_subparsers = knowledge_parser.add_subparsers(dest='subcommand', help='Subcommands')
    knowledge_extract = knowledge_subparsers.add_parser('extract', help='Extract knowledge from chats')
    knowledge_extract.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments')
    knowledge_add = knowledge_subparsers.add_parser('add', help='Add new entry to knowledge')
    knowledge_add.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments')
    knowledge_subparsers.add_parser('init', help='Initialize knowledge registry')

    # ==========================================================================
    # RAG (Retrieval-Augmented Generation) Index Subparser
    # ==========================================================================
    # Commands for building, validating, and checking status of RAG indexes
    # used for semantic search and AI-powered knowledge retrieval.

    rag_parser = subparsers.add_parser('rag', help='RAG index management')
    rag_subparsers = rag_parser.add_subparsers(dest='subcommand', help='Subcommands')
    rag_rebuild = rag_subparsers.add_parser('rebuild', help='Full rebuild of RAG index')
    rag_rebuild.add_argument('rest', nargs=argparse.REMAINDER, help='Rebuild options')
    rag_subparsers.add_parser('reindex', help='Reindex knowledge base')
    rag_subparsers.add_parser('validate', help='Validate knowledge base files')
    rag_subparsers.add_parser('status', help='Check RAG index status')

    # ==========================================================================
    # Documentation Management Subparser
    # ==========================================================================
    # Commands for generating, updating, and maintaining project documentation
    # including auto-generated API docs and user guides.

    docs_parser = subparsers.add_parser('docs', help='Documentation management')
    docs_subparsers = docs_parser.add_subparsers(dest='subcommand', help='Subcommands')

    # ==========================================================================
    # Skills Registry Subparser
    # ==========================================================================
    # Universal skills catalog for AI agents. Discovers capabilities from
    # .agents/skills and .gemini/skills directories and provides
    # portable JSON contracts for agent integration.

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

    # ==========================================================================
    # Assistant CLI Subparser
    # ==========================================================================
    # Gateway to the main assistant CLI for process management including
    # start, stop, status queries, and provider configuration.

    assist_parser = subparsers.add_parser('assist', help='Assistant management (start, stop, status, providers, etc.)')
    assist_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments for assist CLI')

    # ==========================================================================
    # Command Dispatch
    # ==========================================================================
    # Parse arguments and route to the appropriate handler based on command type.

    args = parser.parse_args()

    # Display help when no command is provided
    if not args.command:
        parser.print_help()
        return 0

    # Special handling for 'assist' command - forwards to dedicated assist_cli
    if args.command == 'assist':
        from scripts.dev import assist_cli
        sys.argv = ['assist'] + getattr(args, 'rest', [])
        return assist_cli.main()

    # Display help when no subcommand is provided for commands that require one
    if not getattr(args, 'subcommand', ''):
        parser.print_help()
        return 0

    # Command-to-handler mapping for primary command groups
    dispatch = {
        'knowledge': run_knowledge_command,
        'rag': run_rag_command,
        'docs': run_docs_command,
        'skills': run_skills_command,
    }

    # Resolve and execute the appropriate command handler
    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)

if __name__ == '__main__':
    sys.exit(main())
