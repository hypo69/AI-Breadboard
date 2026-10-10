# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Software_Manager - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.software_manager.tui import SoftwareManagerTUI
#
#     service = SoftwareManagerTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.software_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.software_manager.core.manager import SoftwarePackagesManager


class SoftwareManagerTUI:
    """Консольный интерфейс отображения установленного ПО."""

    def __init__(self, manager: SoftwarePackagesManager | None = None) -> None:
        self.manager = manager or SoftwarePackagesManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда установленных программ."""
        report = self.manager.generate_report()

        panel = Panel(
            f"[bold white]Всего программ:[/bold white] {report.total_packages} | "
            f"[bold yellow]Доступно обновлений:[/bold yellow] {report.updates_available_count} | "
            f"[bold cyan]WinGet CLI:[/bold cyan] {'Доступен' if report.winget_available else 'Не обнаружен'}",
            title='Windows Software & Packages Manager',
            style='blue'
        )

        table = Table(title='Установленные пакеты ПО', header_style='bold cyan')
        table.add_column('Имя программы')
        table.add_column('Идентификатор (ID)')
        table.add_column('Установленная версия', justify='center')
        table.add_column('Новая версия', justify='center')
        table.add_column('Источник', justify='center')

        for p in report.packages:
            upd_text = f"[bold green]{p.available_version}[/bold green]" if p.available_version else '-'
            table.add_row(
                p.name,
                p.package_id,
                p.version,
                upd_text,
                p.source
            )

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Software & Package Manager[/bold white]', style='blue'))
        self.console.print(panel)
        self.console.print(table)


__all__ = ['SoftwareManagerTUI']
