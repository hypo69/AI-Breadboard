# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Control_Center - Tui
# =============================================================================
# Description:
#   Терминальный интерфейс (TUI) для System Control Center.
#
# Usage Examples:
#   Python API:
#     import apps.windows.sdk.modules.system_control_center.tui as tui
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_control_center
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Терминальный интерфейс (TUI) для System Control Center."""

import asyncio
import platform
import sys
import psutil
from typing import Any
from logger import logger
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    Console = Any
    Live = Any
    Panel = Any
    Table = Any
    RICH_AVAILABLE = False

async def run_control_dashboard(interval: float=2.0) -> None:
    """Запуск интерактивного дашборда центра управления в терминале."""
    if not RICH_AVAILABLE:
        print('[System Control Center] Running console loop...')
        while True:
            mem = psutil.virtual_memory()
            print(f'[{platform.node()}] CPU: {psutil.cpu_percent()}% | RAM: {mem.percent}%')
            await asyncio.sleep(interval)
    console = Console()
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            mem = psutil.virtual_memory()
            table = Table(title='🛠️ Windows System Control Center')
            table.add_column('Parameter', style='cyan')
            table.add_column('Value', style='green')
            table.add_row('Hostname', platform.node())
            table.add_row('OS', f'{platform.system()} {platform.release()} ({platform.version()})')
            table.add_row('CPU Load', f'{psutil.cpu_percent()}%')
            table.add_row('RAM Usage', f'{mem.percent}% ({round(mem.used / 1024 ** 3, 1)} / {round(mem.total / 1024 ** 3, 1)} GB)')
            live.update(Panel(table, title='System Control & Health', border_style='green'))
            await asyncio.sleep(interval)