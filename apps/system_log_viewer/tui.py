# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Log Center Terminal Dashboard
# =============================================================================
# Description:
#   Интерактивный терминальный интерфейс для мониторинга системных журналов
#   Windows и анализа событий в реальном времени.
#
# File: tui.py
# Project: AI-Breadboard
# Package: apps.system_log_viewer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Терминальный интерфейс (TUI) для System Log Center."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from src.logger import logger
from apps.windows.core.modules.eventlog_collector import EventLogCollector

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    Console = Any  # type: ignore
    Live = Any  # type: ignore
    Panel = Any  # type: ignore
    Table = Any  # type: ignore
    RICH_AVAILABLE = False


async def run_log_dashboard(interval: float = 2.0) -> None:
    """Запуск интерактивного дашборда системных журналов в терминале."""
    collector = EventLogCollector()
    
    if not RICH_AVAILABLE:
        print("[System Log Center] Rich not available. Running basic monitoring loop...")
        while True:
            events = collector.collect()
            print(f"[{events.timestamp}] Scanned channels. Total events: {len(events.recent_critical_events)}")
            await asyncio.sleep(interval)

    console = Console()
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            events = collector.collect()
            table = Table(title="📜 Windows System Log Center — Live Events")
            table.add_column("Channel", style="cyan")
            table.add_column("Level", style="magenta")
            table.add_column("Event ID", style="green")
            table.add_column("Message", style="white")

            for ev in events.recent_critical_events[:10]:
                table.add_row(
                    str(getattr(ev, "channel", "System")),
                    str(getattr(ev, "level", "Warning")),
                    str(getattr(ev, "event_id", "0")),
                    str(getattr(ev, "message", "-"))[:60],
                )

            live.update(Panel(table, title="System Logs Monitor", border_style="blue"))
            await asyncio.sleep(interval)
