# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy - Scheduler
# =============================================================================
# Description:
#   Регистрация задач старта/остановки фокус-сессий в Windows Task Scheduler (schtasks).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.focus_policy.scheduler import FocusTaskRegistrar
#
#     FocusTaskRegistrar().register(profile)
#
# File: scheduler.py
# Project: ai-breadboard
# Package: apps.windows.modules.focus_policy
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""Интеграция Focus Policy Engine с Windows Task Scheduler."""

import subprocess
import sys
from typing import Callable, List, Optional

from logger import logger
from apps.windows.modules.focus_policy.models import FocusProfile

TASK_FOLDER = '\\TestComputer\\FocusTimers\\'


def _default_runner(cmd: List[str]) -> int:
    """Запускает schtasks и возвращает код возврата."""
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        logger.debug(f'[FocusScheduler] {cmd[1]} -> {res.returncode}: {res.stderr.strip()}')
    return res.returncode


class FocusTaskRegistrar:
    """Создает и удаляет задачи ``TC_Focus_Start_<id>`` / ``TC_Focus_Stop_<id>``."""

    def __init__(self, runner: Optional[Callable[[List[str]], int]] = None, python: Optional[str] = None) -> None:
        """Args:
            runner: Исполнитель команд (внедряется в тестах).
            python: Путь к интерпретатору для команды задачи.
        """
        self.runner = runner or _default_runner
        self.python = python or sys.executable

    def _names(self, profile_id: str) -> List[tuple]:
        return [('Start', f'TC_Focus_Start_{profile_id}'), ('Stop', f'TC_Focus_Stop_{profile_id}')]

    def register(self, profile: FocusProfile) -> None:
        """Регистрирует задачи профиля; при ``auto_start=False`` удаляет их."""
        if not profile.schedule.auto_start:
            self.unregister(profile.profile_id)
            return
        days = ','.join(d.upper() for d in profile.schedule.days)
        times = {'Start': profile.schedule.start_time, 'Stop': profile.schedule.end_time}
        for action, name in self._names(profile.profile_id):
            command = f'"{self.python}" -m apps.windows.core.focus_executor --action {action.lower()} --profile-id {profile.profile_id}'
            cmd = ['schtasks.exe', '/Create', '/F', '/TN', f'{TASK_FOLDER}{name}', '/TR', command,
                   '/SC', 'WEEKLY', '/D', days, '/ST', times[action]]
            self.runner(cmd)

    def unregister(self, profile_id: str) -> None:
        """Удаляет задачи профиля (отсутствие задачи не является ошибкой)."""
        for _, name in self._names(profile_id):
            self.runner(['schtasks.exe', '/Delete', '/F', '/TN', f'{TASK_FOLDER}{name}'])
