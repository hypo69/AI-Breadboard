# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Boot_Recovery - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.boot_recovery.tui import BootRecoveryTUI
#
#     service = BootRecoveryTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.boot_recovery
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.boot_recovery.core.manager import BootRecoveryManager


class BootRecoveryTUI:
    """Консольный интерфейс отображения параметров BCD и WinRE."""

    def __init__(self, manager: BootRecoveryManager | None = None) -> None:
        self.manager = manager or BootRecoveryManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда конфигурации загрузчика."""
        report = self.manager.generate_report()

        table = Table(title='Загрузочные записи BCD (Boot Configuration Data)', header_style='bold cyan')
        table.add_column('Идентификатор', justify='center')
        table.add_column('Описание')
        table.add_column('Устройство (Device)')
        table.add_column('Загрузчик (Path)')
        table.add_column('Default', justify='center')

        for e in report.entries:
            def_badge = '[bold green]ДА[/bold green]' if e.is_default else '[dim]НЕТ[/dim]'
            table.add_row(
                e.identifier,
                e.description,
                e.device,
                e.path,
                def_badge
            )

        winre_color = 'green' if report.winre.enabled else 'red'
        summary_panel = Panel(
            f"[bold white]Default OS:[/bold white] {report.default_os}\n"
            f"[bold white]Boot Timeout:[/bold white] {report.timeout_seconds} сек\n"
            f"[bold white]WinRE Status:[/bold white] [{winre_color}]{'Включен (Enabled)' if report.winre.enabled else 'Отключен'}[/{winre_color}]\n"
            f"[bold white]WinRE Location:[/bold white] {report.winre.location}\n"
            f"[bold white]Secure Boot:[/bold white] {'Включен' if report.secure_boot_enabled else 'Отключен'}",
            title='Сводка Boot & Recovery Environment',
            style='cyan'
        )

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Boot & Recovery Center[/bold white]', style='blue'))
        self.console.print(summary_panel)
        self.console.print(table)


__all__ = ['BootRecoveryTUI']
