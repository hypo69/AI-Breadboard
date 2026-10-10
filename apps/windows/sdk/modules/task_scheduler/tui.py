# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Task_Scheduler - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.task_scheduler.tui import TaskSchedulerTUI
#
#     service = TaskSchedulerTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.task_scheduler
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.task_scheduler.core.manager import TaskSchedulerManager


class TaskSchedulerTUI:
    """Консольный интерфейс отображения заданий Task Scheduler."""

    def __init__(self, manager: TaskSchedulerManager | None = None) -> None:
        self.manager = manager or TaskSchedulerManager()
        self.console = Console()

    def render_dashboard(self, limit: int = 25) -> None:
        """Отображение сводного дашборда планировщика."""
        report = self.manager.generate_report()

        panel = Panel(
            f"[bold white]Всего заданий:[/bold white] {report.total_tasks} | "
            f"[bold green]Готовы (Ready):[/bold green] {report.ready_tasks} | "
            f"[bold cyan]Выполняются (Running):[/bold cyan] {report.running_tasks} | "
            f"[bold dim]Отключены (Disabled):[/bold dim] {report.disabled_tasks}",
            title='Windows Task Scheduler Dashboard',
            style='blue'
        )

        table = Table(title=f'Запланированные задания (первые {limit})', header_style='bold cyan')
        table.add_column('Имя задания')
        table.add_column('Состояние', justify='center')
        table.add_column('Следующий запуск')
        table.add_column('Автор')

        for t in report.tasks[:limit]:
            st_color = 'green' if t.state.lower() == 'ready' else ('cyan' if t.state.lower() == 'running' else 'dim')
            table.add_row(
                t.task_name,
                f"[{st_color}]{t.state}[/{st_color}]",
                t.next_run_time or '-',
                t.author[:30]
            )

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Task Scheduler Center[/bold white]', style='blue'))
        self.console.print(panel)
        self.console.print(table)


__all__ = ['TaskSchedulerTUI']
