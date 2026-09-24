# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Administrator TUI Dashboard
# =============================================================================
# Description:
#   Rich-based interactive terminal UI for Windows system administration,
#   real-time monitoring of user sessions, process controls, group policy
#   status, security events, and Active Directory operations.
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Interactive TUI dashboard for Windows System Administrator."""

from __future__ import annotations

import asyncio
from typing import List

from .src.state import SecurityEvent, SystemAdminState, UserSession

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


def _render_system_info(state: SystemAdminState) -> Panel:
    """Render system information panel."""
    info_text = Text()
    info_text.append(f"Hostname: ", style="bold cyan")
    info_text.append(f"{state.hostname}\n")
    info_text.append(f"Domain: ", style="bold cyan")
    info_text.append(f"{state.domain}\n")
    info_text.append(f"AD Status: ", style="bold cyan")
    
    ad_style = "green" if state.ad_connected else "red"
    info_text.append(f"{state.ad_status}\n", style=ad_style)
    
    info_text.append(f"Uptime: ", style="bold cyan")
    hours = state.uptime_seconds // 3600
    info_text.append(f"{hours}h\n")

    return Panel(info_text, title="[bold]System Information[/bold]", border_style="blue")


def _render_users_table(users: List[UserSession]) -> Table:
    """Render active user sessions table."""
    table = Table(title="Active User Sessions", show_header=True, header_style="bold magenta")
    table.add_column("Username", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Session ID", style="yellow")
    table.add_column("Login Time", style="white")
    table.add_column("IP Address", style="blue")
    table.add_column("Processes", style="red")

    for user in users:
        table.add_row(
            user.username,
            user.status,
            str(user.session_id),
            user.login_time[:19],  # Format datetime
            user.ip_address,
            str(user.process_count),
        )

    return table


def _render_events_table(events: List[SecurityEvent]) -> Table:
    """Render security events table."""
    table = Table(title="Recent Security Events", show_header=True, header_style="bold magenta")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Event ID", style="yellow")
    table.add_column("Level", style="red")
    table.add_column("Source", style="blue")
    table.add_column("Description", style="white")

    for event in events[:10]:  # Last 10 events
        level_style = {
            "Critical": "bold red",
            "Warning": "bold yellow",
            "Information": "green"
        }.get(event.level, "white")
        
        table.add_row(
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            str(event.event_id),
            event.level,
            event.source,
            event.description,
            style=level_style,
        )

    return table


def _render_ad_tree(state: SystemAdminState) -> Tree:
    """Render Active Directory structure tree."""
    tree = Tree("📂 Active Directory Structure", guide_style="bold bright_blue")
    
    domain_branch = tree.add(f"🏢 {state.domain}")
    domain_branch.add("👥 Users")
    domain_branch.add("👨‍💼 Groups")
    domain_branch.add("🖥️ Computers")
    domain_branch.add("📋 Group Policies")
    domain_branch.add("🔐 Security")

    return tree


async def run_sysadmin_dashboard(interval: float = 2.0) -> None:
    """Run the interactive Windows System Administrator dashboard."""
    console = Console()
    state = SystemAdminState()
    state.refresh()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )

    layout["header"].update(
        Panel(
            Text("🪟 Windows System Administrator Dashboard", style="bold white", justify="center"),
            style="bold blue",
        )
    )

    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["footer"].update(
        Panel(
            Text(
                "Q: Quit  |  U: Users  |  E: Events  |  A: AD Info  |  R: Refresh",
                style="white",
                justify="center",
            ),
            style="bold yellow",
        )
    )

    try:
        with Live(layout, refresh_per_second=4, console=console) as live:
            start_time = datetime.now()
            
            while True:
                state.refresh()
                state.uptime_seconds = int((datetime.now() - start_time).total_seconds())

                # Left panel: System info + Users
                left_layout = Layout()
                left_layout.split_column(
                    Layout(_render_system_info(state), name="info", size=6),
                    Layout(_render_users_table(state.users), name="users"),
                )
                layout["left"].update(left_layout)

                # Right panel: Events + AD Tree
                right_layout = Layout()
                right_layout.split_column(
                    Layout(_render_events_table(state.events), name="events"),
                    Layout(_render_ad_tree(state), name="ad", size=8),
                )
                layout["right"].update(right_layout)

                # Simulate time passage
                await asyncio.sleep(interval)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise


__all__ = [
    "run_sysadmin_dashboard",
    "SystemAdminState",
    "UserSession",
    "SecurityEvent",
]
