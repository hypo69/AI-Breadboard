# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Focus Executor
# =============================================================================
# Description:
#   Точка входа для Windows Task Scheduler: запуск/остановка фокус-сессии профиля.
#
# Usage Examples:
#   python -m apps.windows.core.focus_executor --action start --profile-id prof-work-default
#
# File: focus_executor.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""CLI-исполнитель задач TC_Focus_Start_* / TC_Focus_Stop_*."""

import argparse
from typing import List, Optional

from logger import logger
from apps.windows.modules.focus_policy.controller import WindowsFocusController


def run(action: str, profile_id: str, controller: Optional[WindowsFocusController] = None) -> None:
    """Выполняет действие ``start`` или ``stop`` (источник: TASK_SCHEDULER)."""
    ctrl = controller or WindowsFocusController()
    if action == 'start':
        ctrl.start_session(profile_id, 'TASK_SCHEDULER')
    elif action == 'stop':
        ctrl.stop_session('TASK_SCHEDULER')
    else:
        raise ValueError(f'Неизвестное действие: {action}')


def main(argv: Optional[List[str]] = None) -> int:
    """Разбор аргументов и запуск; возвращает код процесса."""
    parser = argparse.ArgumentParser(description='Focus Policy executor')
    parser.add_argument('--action', required=True, choices=['start', 'stop'])
    parser.add_argument('--profile-id', required=True)
    args = parser.parse_args(argv)
    try:
        run(args.action, args.profile_id)
    except (KeyError, RuntimeError) as exc:
        logger.warning(f'[FocusExecutor] {exc}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
