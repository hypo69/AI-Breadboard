# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Performance_Tracing - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.performance_tracing.tui import PerformanceTracingTUI
#
#     service = PerformanceTracingTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.modules.performance_tracing
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.modules.performance_tracing.core.manager import PerformanceTracingManager


class PerformanceTracingTUI:
    """Консольный интерфейс отображения производительности."""

    def __init__(self, manager: PerformanceTracingManager | None = None) -> None:
        self.manager = manager or PerformanceTracingManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда производительности."""
        report = self.manager.generate_report()

        panel = Panel(
            f"[bold white]CPU Usage:[/bold white] {report.cpu_usage_percent:.1f}% | "
            f"[bold white]RAM Usage:[/bold white] {report.ram_usage_percent:.1f}% | "
            f"[bold white]Disk Queue:[/bold white] {report.disk_queue_length} | "
            f"[bold cyan]Network:[/bold cyan] {report.network_utilization_kbps:.1f} KB/s",
            title='Системная производительность и счетчики (typeperf)',
            style='blue'
        )

        table = Table(title='Сборщики данных ETW (Data Collector Sets)', header_style='bold cyan')
        table.add_column('Имя сборщика')
        table.add_column('Тип')
        table.add_column('Статус', justify='center')

        for c in report.collectors:
            st_color = 'green' if c.status.lower() == 'running' else 'dim'
            table.add_row(c.name, c.collector_type, f"[{st_color}]{c.status}[/{st_color}]")

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Performance & ETW Tracing[/bold white]', style='blue'))
        self.console.print(panel)
        self.console.print(table)


__all__ = ['PerformanceTracingTUI']
