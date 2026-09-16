# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostic Center TUI
# =============================================================================
# Description:
#   Интерактивный терминальный интерфейс (TUI) на библиотеке Rich для
#   просмотра статуса здоровья Windows, результатов аудита и действий SafeOps.
#
# Examples:
#   >>> from apps.windows.tui import run_tui
#   >>> run_tui()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Интерактивный TUI интерфейс для Windows AI Diagnostic Center."""

from __future__ import annotations

import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    Console = None  # type: ignore

from apps.windows.core.models import FullAuditReport, RiskLevel
from apps.windows.core.root_cause_engine import RootCauseEngine


def render_dashboard(report: FullAuditReport, console: Console) -> None:
    """Отрисовка главного дашборда здоровья системы."""
    console.clear()
    
    score = report.health_score.score
    color = "green" if score >= 85 else "yellow" if score >= 60 else "red"

    # Заголовок
    header_text = Text(" AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER ", style="bold white on blue")
    console.print(Panel(header_text, style="blue", expand=True))

    # Сводка индекса здоровья
    health_panel = Panel(
        f"[bold {color}]Индекс здоровья: {score}/100 ({report.health_score.status_label})[/]\n"
        f"Критические проблемы: [red]{report.health_score.critical_count}[/] | "
        f"Предупреждения: [yellow]{report.health_score.medium_count}[/] | "
        f"Безопасные действия: [green]{report.health_score.low_count}[/]",
        title="[bold]System Health Score[/bold]",
        border_style=color,
    )
    console.print(health_panel)

    # Таблица доменов
    table = Table(title="Результаты аудита 15 системных доменов", expand=True)
    table.add_column("Домен", style="cyan", ratio=2)
    table.add_column("Статус", justify="center", ratio=1)
    table.add_column("Находки / Рекомендации", ratio=5)

    for d_name, d_res in report.domains.items():
        status_style = "green" if d_res.status == "ok" else "red" if d_res.status == "critical" else "yellow"
        findings_text = ""
        if d_res.findings:
            findings_text = ", ".join([f.title for f in d_res.findings[:2]])
            if len(d_res.findings) > 2:
                findings_text += f" (ещё {len(d_res.findings) - 2}...)"
        else:
            findings_text = "[dim]Аномалий не обнаружено[/dim]"

        table.add_row(
            d_res.title_ru,
            f"[{status_style}]{d_res.status.upper()}[/{status_style}]",
            findings_text,
        )

    console.print(table)

    # Футер управления
    footer = Panel(
        "[bold cyan]Горячие клавиши:[/] [R] Обновить | [F] Полный аудит | [S] Безопасность | [P] Производительность | [Q] Выход",
        style="dim",
    )
    console.print(footer)


def run_tui() -> None:
    """Запуск интерактивного TUI цикла."""
    if Console is None:
        print("Библиотека rich не установлена. Запустите: pip install rich")
        sys.exit(1)

    console = Console()
    engine = RootCauseEngine()
    current_mode = "quick"

    report = engine.run_full_audit(mode=current_mode)
    render_dashboard(report, console)


if __name__ == "__main__":
    run_tui()
