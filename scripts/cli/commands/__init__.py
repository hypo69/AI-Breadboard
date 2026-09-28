# -*- coding: utf-8 -*-
"""Модули команд для CLI и диспетчера manage_tools."""
from __future__ import annotations

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
]
