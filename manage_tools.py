# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Root - Manage Tools
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`manage_tools`).
#
# Usage Examples:
#   CLI:
#     python manage_tools.py
#   Python API:
#     from manage_tools import main
#
#     res = main()
#
# File: manage_tools.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

from __future__ import annotations
"""Скрипт/модуль системы AI-Breadboard (`manage_tools`)."""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

import header
from header import __root__
from scripts.cli.commands import (
    COMMAND_HANDLERS,
    register_all_parsers,
    run_skills_command,
    run_rag_command,
    run_agents_command,
    run_db_command,
    run_docs_command,
    run_plugins_command,
    run_sys_param_command,
    run_telemetry_command,
    run_network_command,
)
from scripts.cli.commands.common import run_script as _run_script

# =============================================================================
# UTF-8 Encoding Fix for Windows Console
# =============================================================================
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# =============================================================================
# Environment Variables Loading
# =============================================================================
load_dotenv(__root__ / '.env')


def main() -> int:
    """Primary entry point for the universal CLI management system.

    Initializes the argument parser with all available command groups and
    dispatches incoming commands to their respective modular handlers.

    Returns:
        int: Exit code indicating overall command execution status:
            0 - Success (command executed properly)
            1 - Error (unknown command, missing arguments, or handler failure)
    """
    parser = argparse.ArgumentParser(
        prog='manage_tools.py',
        description='Universal CLI for managing ai-breadboard project tools and agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  py manage_tools.py skills list                          # list all available skills
  py manage_tools.py rag rebuild                          # rebuild RAG index
  py manage_tools.py agents list                          # list AI agents
  py manage_tools.py db status                            # check SQLite migrations
  py manage_tools.py docs generate                        # generate documentation
  py manage_tools.py telemetry status                     # view telemetry status
'''
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Register modular subcommands
    register_all_parsers(subparsers)

    # Parse arguments
    args, unknown = parser.parse_known_args()

    # Calculate exact unconsumed trailing CLI arguments for sub-command delegation
    if args.command in ('rag', 'docs', 'plugins', 'db', 'sys-param', 'telemetry') and getattr(args, 'subcommand', None):
        argv_list = list(sys.argv[1:])
        if args.subcommand in argv_list:
            sub_idx = argv_list.index(args.subcommand)
            args.rest = argv_list[sub_idx + 1:]
        else:
            args.rest = unknown
    elif unknown:
        if hasattr(args, 'rest') and isinstance(args.rest, list):
            args.rest = args.rest + unknown
        else:
            args.rest = unknown

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

    handler = COMMAND_HANDLERS.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == '__main__':
    sys.exit(main())