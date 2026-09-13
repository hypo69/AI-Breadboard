# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Assistant Terminal UI Dashboard
# =============================================================================
# Description:
#   Rich terminal interface for displaying daily agenda, unread emails, upcoming
#   calendar appointments, and recent user documents.
#
# File: tui.py
# Package: apps.user_assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

from apps.user_assistant.engine import UserAssistantEngine


def render_dashboard(user_id: int = 1) -> None:
    """Render the User Assistant daily agenda in terminal."""
    console = Console()
    engine = UserAssistantEngine(user_id=user_id)
    agenda = engine.get_daily_agenda()

    # Create Mail Table
    mail_table = Table(title="✉️ Unread Emails", expand=True)
    mail_table.add_column("From", style="cyan")
    mail_table.add_column("Subject", style="white")
    mail_table.add_column("Date", style="dim")

    for msg in agenda.get("emails", []):
        mail_table.add_row(msg.get("from", "Unknown"), msg.get("subject", "No Subject"), msg.get("date", ""))
    if not agenda.get("emails"):
        mail_table.add_row("No unread messages", "-", "-")

    # Create Calendar Table
    cal_table = Table(title="📅 Upcoming Events", expand=True)
    cal_table.add_column("Event", style="green")
    cal_table.add_column("Start Time", style="yellow")
    cal_table.add_column("Location", style="dim")

    for ev in agenda.get("events", []):
        cal_table.add_row(ev.get("summary", ""), str(ev.get("start", "")), ev.get("location", ""))
    if not agenda.get("events"):
        cal_table.add_row("No events scheduled", "-", "-")

    # Create Files Table
    files_table = Table(title="📁 Recent Documents", expand=True)
    files_table.add_column("Name", style="blue")
    files_table.add_column("Size (Bytes)", style="dim")

    for f in agenda.get("files", []):
        files_table.add_row(f.get("name", ""), str(f.get("size_bytes", "")))
    if not agenda.get("files"):
        files_table.add_row("No recent documents", "-")

    console.print(Panel(f"[bold cyan]User Personal Assistant Desk[/bold cyan] (User #{user_id})", border_style="cyan"))
    console.print(cal_table)
    console.print(mail_table)
    console.print(files_table)


if __name__ == "__main__":
    render_dashboard()
