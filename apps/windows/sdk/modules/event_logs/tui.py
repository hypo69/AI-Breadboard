# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Event_Logs - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.event_logs.tui import EventLogsTUI
#
#     service = EventLogsTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.event_logs
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.event_logs.core.manager import EventLogsManager


class EventLogsTUI:
    """Консольный интерфейс отображения журналов событий."""

    def __init__(self, manager: EventLogsManager | None = None) -> None:
        self.manager = manager or EventLogsManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда журналов событий."""
        report = self.manager.generate_report()

        panel = Panel(
            f"[bold white]Всего каналов:[/bold white] {report.total_channels} | "
            f"[bold red]Ошибок за 24ч:[/bold red] {report.error_events_24h} | "
            f"[bold yellow]Предупреждений:[/bold yellow] {report.warning_events_24h}",
            title='Windows Event Log Diagnostics',
            style='blue'
        )

        table = Table(title='Ключевые каналы журналов событий', header_style='bold cyan')
        table.add_column('Имя канала')
        table.add_column('Записей', justify='right')
        table.add_column('Размер (MB)', justify='right')
        table.add_column('Статус', justify='center')

        for c in report.channels:
            size_mb = c.size_bytes / (1024 ** 2)
            st_color = 'green' if c.enabled else 'dim'
            table.add_row(
                c.name,
                str(c.record_count),
                f"{size_mb:.1f}",
                f"[{st_color}]{'Активен' if c.enabled else 'Отключен'}[/{st_color}]"
            )

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Event Log Center[/bold white]', style='blue'))
        self.console.print(panel)
        self.console.print(table)


__all__ = ['EventLogsTUI']
