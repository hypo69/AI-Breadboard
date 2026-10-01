# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Skills
# =============================================================================
# Description:
#   Команды управления каталогом навыков (skills).
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.skills import register_skills_parser
#
#     res = register_skills_parser()
#
# File: skills.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

from __future__ import annotations
"""Команды управления каталогом навыков (skills)."""

import argparse
from src.skills import SkillRegistry
from .common import run_script


def register_skills_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды skills."""
    skills_parser = subparsers.add_parser('skills', help='Universal skills registry')
    skills_subparsers = skills_parser.add_subparsers(dest='subcommand', help='Subcommands')
    skills_list = skills_subparsers.add_parser('list', help='List discovered skills')
    skills_list.add_argument('--lang', '-l', help='Language code (e.g. en, ru, es)')
    skills_search = skills_subparsers.add_parser('search', help='Search skills by name or description')
    skills_search.add_argument('query', help='Search terms')
    skills_search.add_argument('--lang', '-l', help='Language code for output (e.g. en, ru, es)')
    skills_create = skills_subparsers.add_parser('create', help='Create a new skill')
    skills_create.add_argument('--name', required=True, help='Skill name')
    skills_create.add_argument('--description', required=True, help='English description')
    skills_create.add_argument('--description-ru', required=True, help='Russian description')
    skills_show = skills_subparsers.add_parser('show', help='Print Markdown instructions')
    skills_show.add_argument('name', help='Skill name')
    skills_export = skills_subparsers.add_parser('export', help='Export a portable JSON skill contract')
    skills_export.add_argument('name', help='Skill name')
    skills_export.add_argument('--without-instructions', action='store_true', help='Exclude Markdown instructions')
    skills_export.add_argument('--lang', '-l', help='Language code for exported description')


def run_skills_command(args: argparse.Namespace) -> int:
    """Управление реестром AI-навыков."""
    registry = SkillRegistry()
    sub = args.subcommand
    lang = getattr(args, 'lang', None)
    if sub == 'list':
        for skill in registry.discover(lang=lang):
            print(f'{skill.name}\t{(skill.get_description(lang) if lang else skill.description)}')
        return 0
    if sub == 'search':
        for skill in registry.search(args.query, lang=lang):
            print(f'{skill.name}\t{(skill.get_description(lang) if lang else skill.description)}')
        return 0
    if sub == 'create':
        return run_script('scripts/dev/init_skill.py', ['--name', args.name, '--description', args.description, '--description-ru', args.description_ru])
    if sub in ('show', 'export'):
        try:
            if sub == 'show':
                skill = registry.get(args.name)
                print(skill.prompt())
            else:
                print(registry.export_json(args.name, include_instructions=not args.without_instructions, lang=lang))
            return 0
        except KeyError as error:
            print(f'Error: {error}')
            return 1
    print(f'Unknown skills subcommand: {sub}')
    return 1
