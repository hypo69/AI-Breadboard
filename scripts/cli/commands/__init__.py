# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands -   Init  
# =============================================================================
# Description:
#   Модули команд для CLI и диспетчера manage_tools.
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.__init__ import register_all_parsers
#
#     res = register_all_parsers()
#
# File: __init__.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:00:00
# =============================================================================

from __future__ import annotations
"""Модули команд для CLI и диспетчера manage_tools."""

import argparse
from typing import Callable, Dict

from .skills import register_skills_parser, run_skills_command
from .rag import register_rag_parser, run_rag_command
from .agents import register_agents_parser, run_agents_command
from .db import register_db_parser, run_db_command
from .docs import register_docs_parser, run_docs_command
from .plugins import register_plugins_parser, run_plugins_command
from .sys_param import register_sys_param_parser, run_sys_param_command
from .telemetry import register_telemetry_parser, run_telemetry_command
from .network import register_network_parser, run_network_command
from .ui import register_ui_parser, run_ui_command

# Utility for launching external commands
from ..utils import run_command

def register_headers_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрирует парсер для команды `headers`.
    Подкоманда `update` запускает скрипт `tools/update_file_headers.py`.
    """
    headers_parser = subparsers.add_parser('headers', help='Управление заголовками файлов')
    headers_sub = headers_parser.add_subparsers(dest='subcommand', help='Подкоманды headers')
    headers_sub.add_parser('update', help='Обновить заголовки во всех поддерживаемых файлах')

def run_headers_command(args: argparse.Namespace) -> int:
    """Обработчик команды `headers`.
    Поддерживаемая подкоманда: `update`.
    """
    if getattr(args, 'subcommand', None) == 'update':
        return run_command(
            ['python', 'tools/update_file_headers.py'],
            cwd=__root__,
            WaitMsBeforeAsync=5000,
            toolAction='Обновление заголовков файлов',
            toolSummary='Запуск скрипта update_file_headers'
        )
    return 1

COMMAND_HANDLERS: Dict[str, Callable[[argparse.Namespace], int]] = {
    'skills': run_skills_command,
    'rag': run_rag_command,
    'agents': run_agents_command,
    'db': run_db_command,
    'docs': run_docs_command,
    'plugins': run_plugins_command,
    'sys-param': run_sys_param_command,
    'telemetry': run_telemetry_command,
    'network': run_network_command,
    'ui': run_ui_command,
}


def register_all_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Регистрирует активные подпарсеры команд CLI."""
    register_skills_parser(subparsers)
    register_rag_parser(subparsers)
    register_agents_parser(subparsers)
    register_db_parser(subparsers)
    register_docs_parser(subparsers)
    register_plugins_parser(subparsers)
    register_sys_param_parser(subparsers)
    register_telemetry_parser(subparsers)
    register_network_parser(subparsers)
    register_ui_parser(subparsers)
    register_headers_parser(subparsers)  # регистрация новой команды

    # Assist CLI Gateway
    assist_parser = subparsers.add_parser('assist', help='Assistant management (start, stop, status, providers, etc.)')
    assist_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Arguments for assist CLI')


__all__ = [
    'COMMAND_HANDLERS',
    'register_all_parsers',
    'run_skills_command',
    'run_rag_command',
    'run_agents_command',
    'run_db_command',
    'run_docs_command',
    'run_plugins_command',
    'run_sys_param_command',
    'run_telemetry_command',
    'run_network_command',
    'run_ui_command',
]
