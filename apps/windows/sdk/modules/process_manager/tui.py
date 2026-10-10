# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.process_manager.tui import ProcessManagerTUI
#
#     service = ProcessManagerTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.process_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.process_manager.core.manager import ProcessManager


class ProcessManagerTUI:
    """Консольный интерфейс отображения процессов Windows."""

    def __init__(self, manager: ProcessManager | None = None) -> None:
        self.manager = manager or ProcessManager()
        self.console = Console()

    def render_dashboard(self, limit: int = 25) -> None:
        """Отображение сводного дашборда процессов."""
        report = self.manager.generate_report()

        panel = Panel(
            f"[bold white]Всего процессов:[/bold white] {report.total_processes} | "
            f"[bold white]Всего потоков:[/bold white] {report.total_threads} | "
            f"[bold cyan]Занято памяти процессами:[/bold cyan] {report.total_memory_used_mb:.1f} MB",
            title='Windows Process Intelligence Dashboard',
            style='blue'
        )

        table = Table(title=f'Активные процессы (топ {limit})', header_style='bold cyan')
        table.add_column('PID', justify='center')
        table.add_column('Имя процесса')
        table.add_column('CPU %', justify='right')
        table.add_column('RAM (MB)', justify='right')
        table.add_column('Потоки', justify='center')
        table.add_column('Пользователь')

        for p in sorted(report.processes, key=lambda x: x.memory_mb, reverse=True)[:limit]:
            cpu_color = 'green' if p.cpu_percent < 10 else ('yellow' if p.cpu_percent < 50 else 'bold red')
            table.add_row(
                str(p.pid),
                p.name,
                f"[{cpu_color}]{p.cpu_percent:.1f}%[/{cpu_color}]",
                f"{p.memory_mb:.1f}",
                str(p.num_threads),
                str(p.username or '-')
            )

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Process & Memory Manager[/bold white]', style='blue'))
        self.console.print(panel)
        self.console.print(table)


__all__ = ['ProcessManagerTUI']
