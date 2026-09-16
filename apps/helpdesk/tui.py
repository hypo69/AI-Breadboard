# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Helpdesk Interactive Terminal UI (TUI)
# =============================================================================
# Description:
#   Rich-based interactive console dashboard for operators and sysadmins to
#   view active tickets, inspect ticket message history, and filter by priority.
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.helpdesk
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Interactive Rich-based Terminal User Interface for Helpdesk."""

from __future__ import annotations

import sys
import time
from typing import List, Dict, Any, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.live import Live
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from src.api.helpdesk.database import init_db, get_db


class HelpdeskTUI:
    """Rich TUI interface for Helpdesk operator desk."""

    def __init__(self) -> None:
        """Initialize TUI environment and database."""
        init_db()
        self.console = Console() if HAS_RICH else None

    def get_tickets(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieve recent support tickets from database.

        Args:
            limit (int): Maximum number of tickets to retrieve.

        Returns:
            List[Dict[str, Any]]: List of ticket records.
        """
        with get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM helpdesk_tickets
                ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END,
                         updated_at DESC
                LIMIT ?;
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> Dict[str, int]:
        """Retrieve quick aggregate KPI statistics.

        Returns:
            Dict[str, int]: Statistics counters.
        """
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets;").fetchone()["c"]
            open_cnt = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'open';").fetchone()["c"]
            in_prog = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'in_progress';").fetchone()["c"]
            resolved = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'resolved';").fetchone()["c"]
            urgent = conn.execute("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE priority = 'urgent' AND status NOT IN ('resolved', 'closed');").fetchone()["c"]
            return {
                "total": total,
                "open": open_cnt,
                "in_progress": in_prog,
                "resolved": resolved,
                "urgent": urgent,
            }

    def render_plain(self) -> None:
        """Render simple ASCII dashboard when Rich is unavailable."""
        stats = self.get_stats()
        print("\n=======================================================")
        print("           HELPDESK SUPPORT DESK (TUI)                ")
        print("=======================================================")
        print(f" Открыто: {stats['open']} | В работе: {stats['in_progress']} | Решено: {stats['resolved']} | СРОЧНО: {stats['urgent']}")
        print("-------------------------------------------------------")
        tickets = self.get_tickets()
        if not tickets:
            print(" Нет активных обращений.")
        else:
            for t in tickets:
                print(f" [#{t.get('ticket_number')}] [{t.get('priority', '').upper()}] [{t.get('status', '').upper()}] {t.get('subject')} - {t.get('user_name')}")
        print("=======================================================\n")

    def render_rich(self) -> None:
        """Render Rich formatted dashboard table and KPI cards."""
        if not self.console:
            self.render_plain()
            return

        stats = self.get_stats()

        kpi_text = Text()
        kpi_text.append(f" 🛟 Всего: {stats['total']}  ", style="bold white")
        kpi_text.append(f" 🔴 Открыто: {stats['open']}  ", style="bold red")
        kpi_text.append(f" 🟡 В работе: {stats['in_progress']}  ", style="bold yellow")
        kpi_text.append(f" 🟢 Решено: {stats['resolved']}  ", style="bold green")
        kpi_text.append(f" ⚡ СРОЧНО: {stats['urgent']} ", style="bold red reverse")

        kpi_panel = Panel(kpi_text, title="📊 Helpdesk KPI & Статус", border_style="cyan")
        self.console.print(kpi_panel)

        table = Table(title="📋 Активные обращения в службу поддержки", border_style="blue", expand=True)
        table.add_column("№", style="cyan", width=6)
        table.add_column("Приоритет", style="bold", width=12)
        table.add_column("Статус", width=14)
        table.add_column("Тема обращения", style="white", ratio=3)
        table.add_column("Пользователь", style="magenta", ratio=2)
        table.add_column("Обновлено", style="dim", width=20)

        priority_colors = {
            "urgent": "bold red",
            "high": "bold yellow",
            "normal": "white",
            "low": "dim white",
        }

        status_badges = {
            "open": "[red]● Открыт[/red]",
            "in_progress": "[yellow]⚙ В работе[/yellow]",
            "resolved": "[green]✓ Решен[/green]",
            "closed": "[dim]✖ Закрыт[/dim]",
        }

        tickets = self.get_tickets()
        for t in tickets:
            p = t.get("priority", "normal")
            p_style = priority_colors.get(p, "white")
            st = t.get("status", "open")
            st_text = status_badges.get(st, st)

            table.add_row(
                f"#{t.get('ticket_number', '')}",
                f"[{p_style}]{p.upper()}[/{p_style}]",
                st_text,
                t.get("subject", ""),
                f"{t.get('user_name', '')} ({t.get('user_email', '')})",
                t.get("updated_at", "")[:19].replace("T", " "),
            )

        self.console.print(table)


def run_tui() -> None:
    """Entry point for running interactive TUI."""
    tui = HelpdeskTUI()
    if HAS_RICH:
        tui.render_rich()
    else:
        tui.render_plain()


if __name__ == "__main__":
    run_tui()
