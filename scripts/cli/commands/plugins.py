# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Plugins
# =============================================================================
# Description:
#   Команды управления плагинами (plugins).
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.plugins import register_plugins_parser
#
#     res = register_plugins_parser()
#
# File: plugins.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

from __future__ import annotations
"""Команды управления плагинами (plugins)."""

import argparse


def register_plugins_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды plugins."""
    plugins_parser = subparsers.add_parser('plugins', help='System and user plugins management and scaffolding')
    plugins_subparsers = plugins_parser.add_subparsers(dest='subcommand', help='Subcommands')
    plugins_list = plugins_subparsers.add_parser('list', help='List installed plugins')
    plugins_list.add_argument('--lang', '-l', help='Language code for localized title and description')
    plugins_create = plugins_subparsers.add_parser('create', help='Scaffold a new plugin')
    plugins_create.add_argument('name', help='Plugin name (e.g. audit_logger)')
    plugins_create.add_argument('--title', '-t', default='', help='English display title')
    plugins_create.add_argument('--title-ru', '-tru', default='', help='Russian display title')
    plugins_create.add_argument('--description', '-d', default='', help='English description')
    plugins_create.add_argument('--description-ru', '-ru', default='', help='Russian description')
    plugins_create.add_argument('--category', '-c', default='general', help='Plugin category')
    plugins_create.add_argument('--icon', '-i', default='🧩', help='Emoji icon')
    plugins_create.add_argument('--scope', '-s', default='system', choices=['system', 'user'], help='Plugin scope')


def run_plugins_command(args: argparse.Namespace) -> int:
    """Управление и скаффолдинг плагинов."""
    sub = args.subcommand
    if sub == 'list':
        from plugins import load_plugins
        loaded = load_plugins()
        lang = getattr(args, 'lang', None)
        print('\n--- INSTALLED PLUGINS ---')
        for name, p in sorted(loaded.items()):
            t = p.get_title(lang) if lang else p.title
            d = p.get_description(lang) if lang else p.description
            status = 'enabled' if p.enabled else 'disabled'
            print(f'[{p.icon}] {name} ({t}) - {status}\n    {d}')
        print('-------------------------\n')
        return 0
    if sub == 'create':
        from scripts.dev.init_plugin import create_plugin
        create_plugin(
            name=args.name,
            title=getattr(args, 'title', '') or '',
            title_ru=getattr(args, 'title_ru', '') or '',
            description=getattr(args, 'description', '') or '',
            description_ru=getattr(args, 'description_ru', '') or '',
            category=getattr(args, 'category', 'general') or 'general',
            icon=getattr(args, 'icon', '🧩') or '🧩',
            scope=getattr(args, 'scope', 'system') or 'system',
        )
        return 0
    print(f'Unknown plugins subcommand: {sub}')
    return 1
