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
# Package: apps.windows_sysadmin
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Interactive TUI dashboard for Windows System Administrator."""

from __future__ import annotations

import asyncio
import platform
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


@dataclass
class UserSession:
    """Represents an active Windows user session."""
    username: str
    session_id: int
    status: str = "Active"
    login_time: str = ""
    ip_address: str = ""
    process_count: int = 0


@dataclass
class SecurityEvent:
    """Represents a Windows security event."""
    timestamp: datetime
    event_id: int
    level: str  # Critical, Warning, Information
    source: str
    description: str


@dataclass
class SystemAdminState:
    """Current state of Windows System Administrator dashboard."""
    hostname: str = "WORKSTATION"
    domain: str = "WORKGROUP"
    users: List[UserSession] = field(default_factory=list)
    events: List[SecurityEvent] = field(default_factory=list)
    uptime_seconds: int = 0
    ad_connected: bool = False
    ad_status: str = "Disconnected"

    def refresh(self) -> None:
        """Refresh system state from Windows APIs."""
        hostname = platform.node()
        self.hostname = hostname
        
        # Placeholder user sessions
        if not self.users:
            self.users = [
                UserSession(
                    username="Administrator",
                    session_id=1,
                    status="Active",
                    login_time=datetime.now().isoformat(),
                    ip_address="127.0.0.1",
                    process_count=23
                ),
                UserSession(
                    username="Guest",
                    session_id=2,
                    status="Idle",
                    login_time=(datetime.now() - timedelta(hours=2)).isoformat(),
                    ip_address="127.0.0.1",
                    process_count=1
                ),
            ]

        # Placeholder security events
        if not self.events:
            self.events = [
                SecurityEvent(
                    timestamp=datetime.now(),
                    event_id=4624,
                    level="Information",
                    source="Security",
                    description="An account was successfully logged on."
                ),
                SecurityEvent(
                    timestamp=datetime.now() - timedelta(minutes=5),
                    event_id=4688,
                    level="Information",
                    source="Security",
                    description="A new process has been created."
                ),
                SecurityEvent(
                    timestamp=datetime.now() - timedelta(minutes=10),
                    event_id=4720,
                    level="Warning",
                    source="Security",
                    description="A user account was created."
                ),
            ]


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
