# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor Terminal UI
# =============================================================================
# Description:
#   Интерактивный терминальный интерфейс (TUI) на базе библиотеки Rich
#   для отображения точек автозагрузки, предупреждений безопасности,
#   метрик производительности и детального отчета аудита.
#
# Examples:
#   >>> from apps.windows.startup.tui import StartupAuditorTUI
#   >>> tui = StartupAuditorTUI()
#   >>> tui.render_dashboard()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.startup
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Терминальный интерфейс (Rich TUI) для Startup Auditor."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apps.windows.startup.core.auditor import StartupAuditor
from apps.windows.startup.core.models import AuditReport, RiskLevel, StartupEntry


class StartupAuditorTUI:
    """Консольный рендерер аудита автозапуска."""

    def __init__(self, auditor: Optional[StartupAuditor] = None) -> None:
        """Инициализация TUI."""
        self.console = Console()
        self.auditor = auditor or StartupAuditor()

    def render_dashboard(self) -> None:
        """Рендеринг основного дашборда аудита в консоль."""
        report = self.auditor.run_audit()

        # 1. Заголовочная панель с Health Score
        score = report.summary.health_score
        score_color = "green" if score >= 80 else ("yellow" if score >= 60 else "red")

        header_text = Text()
        header_text.append("🚀 Windows Startup & Persistence Auditor\n", style="bold cyan")
        header_text.append(f"Хост: {report.hostname} | ОС: {report.os_name} | Время скана: {report.scan_duration_ms} мс\n", style="dim")
        header_text.append(f"Индекс чистоты и безопасности: ", style="bold")
        header_text.append(f"{score}/100\n", style=f"bold {score_color}")

        # Сводные счетчики
        header_text.append(f"Всего: {report.summary.total_entries} | ", style="white")
        header_text.append(f"Активно: {report.summary.active_entries} | ", style="green")
        header_text.append(f"Отключено: {report.summary.disabled_entries} | ", style="dim")
        header_text.append(f"Битых записей: {report.summary.broken_entries} | ", style="yellow")
        header_text.append(f"Угроз: {report.summary.critical_count + report.summary.suspicious_count}", style="bold red")

        self.console.print(Panel(header_text, border_style="cyan", title="[bold]AI Breadboard[/bold]", subtitle=report.timestamp[:19]))

        # 2. Таблица записей автозагрузки
        table = Table(title="📋 Обнаруженные элементы автозапуска", expand=True, border_style="blue")
        table.add_column("Статус", justify="center", width=8)
        table.add_column("Имя / Элемент", style="bold white", width=24)
        table.add_column("Локация", style="dim cyan", width=22)
        table.add_column("Категория", style="italic", width=20)
        table.add_column("Риск", justify="center", width=12)
        table.add_column("Исполняемый путь / Команда", style="dim", overflow="fold")
        table.add_column("Влияние", justify="center", width=10)

        for e in report.entries:
            # Статус включен/отключен
            status_badge = "[green]✓ Вкл[/green]" if e.is_enabled else "[dim]✗ Откл[/dim]"

            # Цвет риска
            risk_badge = self._format_risk(e.risk_level)

            # Категория
            cat_str = e.category.value if hasattr(e.category, "value") else str(e.category)

            # Путь
            display_path = e.executable_path or e.command
            if not e.file_exists and e.executable_path:
                display_path = f"[red][ФАЙЛ ОТСУТСТВУЕТ][/red] {display_path}"

            table.add_row(
                status_badge,
                e.name[:24],
                e.location_type.value if hasattr(e.location_type, "value") else str(e.location_type),
                cat_str,
                risk_badge,
                display_path,
                e.boot_impact,
            )

        self.console.print(table)

        # 3. Панель предупреждений и рекомендаций
        if report.recommendations:
            rec_text = Text()
            for rec in report.recommendations:
                rec_text.append(f"• {rec}\n")
            self.console.print(Panel(rec_text, title="[bold yellow]💡 Рекомендации по оптимизации[/bold yellow]", border_style="yellow"))

    def _format_risk(self, risk: RiskLevel) -> str:
        """Форматирование бейджа уровня риска."""
        if risk == RiskLevel.CRITICAL:
            return "[bold red]CRITICAL[/bold red]"
        elif risk == RiskLevel.SUSPICIOUS:
            return "[magenta]SUSPICIOUS[/magenta]"
        elif risk == RiskLevel.WARNING:
            return "[yellow]WARNING[/yellow]"
        elif risk == RiskLevel.NOTICE:
            return "[blue]NOTICE[/blue]"
        return "[green]CLEAN[/green]"


__all__ = ["StartupAuditorTUI"]
