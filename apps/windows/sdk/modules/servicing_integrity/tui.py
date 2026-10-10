# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Servicing_Integrity - Tui
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.servicing_integrity.tui import ServicingIntegrityTUI
#
#     service = ServicingIntegrityTUI()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.servicing_integrity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from apps.windows.sdk.modules.servicing_integrity.core.manager import ServicingIntegrityManager


class ServicingIntegrityTUI:
    """Консольный интерфейс отображения статуса целостности Windows."""

    def __init__(self, manager: ServicingIntegrityManager | None = None) -> None:
        self.manager = manager or ServicingIntegrityManager()
        self.console = Console()

    def render_dashboard(self) -> None:
        """Отображение сводного дашборда целостности."""
        report = self.manager.generate_report()

        sfc_color = 'green' if 'clean' in report.sfc_status.lower() else 'red'
        dism_color = 'green' if 'healthy' in report.dism_component_store_status.lower() else 'yellow'

        panel = Panel(
            f"[bold white]WRP / SFC Status:[/bold white] [{sfc_color}]{report.sfc_status}[/{sfc_color}]\n"
            f"[bold white]DISM Component Store:[/bold white] [{dism_color}]{report.dism_component_store_status}[/{dism_color}]\n"
            f"[bold white]Corrupted Files:[/bold white] {report.corrupted_files_count}\n"
            f"[bold white]Cleanup Recommended:[/bold white] {'Да' if report.dism_cleanup_recommended else 'Нет'}",
            title='Целостность Системных Компонентов (Servicing Integrity)',
            style='cyan'
        )

        table = Table(title='Ключевые компоненты Windows Features', header_style='bold magenta')
        table.add_column('Имя компонента')
        table.add_column('Статус', justify='center')

        for f in report.features:
            st_color = 'green' if f.state.lower() == 'enabled' else 'dim'
            table.add_row(f.name, f"[{st_color}]{f.state}[/{st_color}]")

        self.console.print(Panel('[bold white]AI-Breadboard: Windows Servicing & Component Integrity[/bold white]', style='blue'))
        self.console.print(panel)
        self.console.print(table)


__all__ = ['ServicingIntegrityTUI']
