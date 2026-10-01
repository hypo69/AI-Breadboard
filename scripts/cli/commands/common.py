# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Common
# =============================================================================
# Description:
#   Утилита запуска внешних скриптов как подпроцессов.
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.common import run_script
#
#     res = run_script()
#
# File: common.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

from __future__ import annotations
"""Утилита запуска внешних скриптов как подпроцессов."""

import subprocess
import sys
from pathlib import Path
from header import __root__


def run_script(script_rel_path: str, extra_args: list[str] = []) -> int:
    """Выполнение внешнего Python-скрипта как подпроцесса.

    Args:
        script_rel_path (str): Относительный путь к скрипту от корня проекта.
        extra_args (list[str]): Дополнительные аргументы командной строки.

    Returns:
        int: Код завершения процесса (0 - успех, не 0 - ошибка).
    """
    target_path = __root__ / script_rel_path
    if not target_path.exists():
        print(f'Error: script not found: {target_path}')
        return 1
    cmd = [sys.executable, str(target_path)]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, cwd=str(__root__))
    return result.returncode
