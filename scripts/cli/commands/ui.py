# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - UI Capture
# =============================================================================
# Description:
#   Команды управления и захвата веб-интерфейсов (ui).
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.ui import register_ui_parser, run_ui_command
#
# File: scripts/cli/commands/ui.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 12:00:00
# =============================================================================

from __future__ import annotations
"""Команды захвата веб-интерфейсов (ui)."""

import argparse
from .common import run_script


def register_ui_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды ui.

    :параметр subparsers: Менеджер подпарсеров argparse.
    """
    ui_parser = subparsers.add_parser('ui', help='Инструменты захвата и аудита веб-интерфейса (UI Capture)')
    ui_subparsers = ui_parser.add_subparsers(dest='subcommand', help='Подкоманды UI')

    capture_parser = ui_subparsers.add_parser('capture', help='Автоматический обход интерфейса и сохранение скриншотов в PNG')
    capture_parser.add_argument('url', help='URL веб-интерфейса для захвата')
    capture_parser.add_argument('-o', '--output', default='assets/webgui', help='Каталог для результатов')
    capture_parser.add_argument('--wait', type=int, default=800, help='Ожидание после навигации в миллисекундах')
    capture_parser.add_argument('--full-page', action='store_true', help='Сохранять всю страницу целиком')
    capture_parser.add_argument('--debug', action='store_true', help='Включить видимый браузер и отладку')


def run_ui_command(args: argparse.Namespace) -> int:
    """Делегирование операций захвата UI утилите tools/capture_ui.py.

    :параметр args: Аргументы командной строки namespace.
    :возвращает: Код завершения процесса.
    """
    sub = getattr(args, 'subcommand', None)
    if sub == 'capture':
        extra = []
        if getattr(args, 'url', None):
            extra.append(args.url)
        if getattr(args, 'output', None):
            extra.extend(['--output', str(args.output)])
        if getattr(args, 'wait', None) is not None:
            extra.extend(['--wait', str(args.wait)])
        if getattr(args, 'full_page', False):
            extra.append('--full-page')
        if getattr(args, 'debug', False):
            extra.append('--debug')

        return run_script(
            'tools/capture_ui.py',
            extra,
        )

    print(f'Неизвестная подкоманда ui: {sub}')
    return 1
