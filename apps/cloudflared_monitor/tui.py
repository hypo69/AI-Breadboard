# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cloudflared Monitor Rich TUI Dashboard
# =============================================================================
# Description:
#   Interactive terminal dashboard for Cloudflare Tunnel monitoring, real-time
#   log streaming, process telemetry, endpoint latency, and AI diagnostics.
#
# Examples:
#   >>> from apps.cloudflared_monitor.tui import run_cloudflared_dashboard
#   >>> await run_cloudflared_dashboard(interval=2.0)
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.cloudflared_monitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Rich TUI dashboard renderer for Cloudflared Tunnel Monitor."""

from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from src.logger import logger
from .src.state import CloudflaredLogEntry, CloudflaredState

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    Console = Any  # type: ignore
    Layout = Any  # type: ignore
    Live = Any  # type: ignore
    Panel = Any  # type: ignore
    Table = Any  # type: ignore
    Text = Any  # type: ignore
    Tree = Any  # type: ignore
    RICH_AVAILABLE = False


def _render_tunnel_info_table(state: CloudflaredState) -> Table:
    """Render tunnel connection and process details table.

    Args:
        state: Active CloudflaredState instance.

    Returns:
        Table: Populated Rich Table.
    """
    table = Table(
        expand=True,
        show_header=False,
        box=None,
        padding=(0, 1),
    )
    table.add_column("Property", style="bold cyan", width=20)
    table.add_column("Value", style="white")

    proc = state.process
    status_style = "bold green" if proc.is_running else "bold red"
    status_str = f"[{status_style}]{'ACTIVE / RUNNING' if proc.is_running else 'INACTIVE / STOPPED'}[/{status_style}]"

    table.add_row("Daemon Status", status_str)
    table.add_row("Process ID (PID)", str(proc.pid) if proc.pid else "[dim]N/A[/dim]")
    table.add_row("CPU Usage", f"{proc.cpu_percent:.1f}%")
    table.add_row("Memory RSS", f"{proc.memory_mb:.1f} MB ({proc.memory_percent:.1f}%)")
    table.add_row("Threads", str(proc.num_threads))
    uptime_h = round(proc.uptime_seconds / 3600, 2)
    table.add_row("Uptime", f"{uptime_h} hours ({int(proc.uptime_seconds)}s)")
    table.add_row("Started At", proc.start_time or "[dim]N/A[/dim]")

    table.add_row("─" * 18, "─" * 30)

    token_color = "green" if state.has_token else "red"
    table.add_row("Tunnel Token", f"[{token_color}]{state.token_preview}[/{token_color}]")
    table.add_row("Binary Path", state.exe_path or "[red]Not found in PATH[/red]")
    table.add_row("Public Ingress", f"[bold underline cyan]{state.public_url}[/bold underline cyan]")

    ep = state.endpoint
    if ep.is_reachable:
        code_color = "green" if (ep.status_code and ep.status_code < 400) else "yellow"
        ep_status = f"[{code_color}]HTTP {ep.status_code}[/{code_color}] ({ep.response_time_ms} ms)"
    else:
        ep_status = f"[red]Unreachable[/red] ({ep.error_message or 'Connection failed'})"

    table.add_row("Public Health", ep_status)
    table.add_row("Active Connectors", f"[bold green]{state.active_connections_count}[/bold green]")
    table.add_row("Log Errors/Warns", f"[red]{state.total_errors_in_log}[/red] / [yellow]{state.total_warnings_in_log}[/yellow]")

    return table


def _render_log_table(logs: List[CloudflaredLogEntry]) -> Table:
    """Render recent log stream table with syntax styling.

    Args:
        logs: List of parsed log records.

    Returns:
        Table: Populated Rich Table.
    """
    table = Table(
        title="Live Log Stream (Tail: logs/cloudflared.log)",
        expand=True,
        header_style="bold cyan",
        border_style="bright_black",
    )
    table.add_column("Time", style="dim", width=19)
    table.add_column("Level", width=7, justify="center")
    table.add_column("Conn", style="dim magenta", width=6)
    table.add_column("Message", style="white", min_width=30)

    if not logs:
        table.add_row("-", "[dim]INFO[/dim]", "-", "[dim]No log events recorded yet.[/dim]")
        return table

    for entry in logs[:18]:
        lvl = entry.level.upper()
        if lvl in ("ERR", "ERROR"):
            lvl_fmt = "[bold red]ERR[/bold red]"
            msg_fmt = f"[red]{entry.message}[/red]"
        elif lvl in ("WRN", "WARN", "WARNING"):
            lvl_fmt = "[bold yellow]WRN[/bold yellow]"
            msg_fmt = f"[yellow]{entry.message}[/yellow]"
        elif lvl in ("DBG", "DEBUG"):
            lvl_fmt = "[dim]DBG[/dim]"
            msg_fmt = f"[dim]{entry.message}[/dim]"
        else:
            lvl_fmt = "[green]INF[/green]"
            msg_fmt = entry.message

        table.add_row(
            entry.timestamp[-19:] if len(entry.timestamp) >= 19 else entry.timestamp,
            lvl_fmt,
            entry.connection_id or "-",
            msg_fmt,
        )

    return table


def render_ui(state: CloudflaredState) -> Any:
    """Build composite Rich TUI layout for Cloudflared Monitor.

    Args:
        state: Active CloudflaredState instance.

    Returns:
        Any: Configured Layout instance.
    """
    if not RICH_AVAILABLE:
        return None

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="left_panel", ratio=2),
        Layout(name="right_panel", ratio=3),
    )

    layout["right_panel"].split_column(
        Layout(name="logs", ratio=3),
        Layout(name="diagnostics", ratio=2),
    )

    # 1. Header Banner
    proc = state.process
    status_label = "ONLINE" if proc.is_running else "OFFLINE"
    status_style = "bold green" if proc.is_running else "bold red"
    rep = state.report
    score_val = rep.health_score if rep else 0
    score_color = "green" if score_val >= 80 else ("yellow" if score_val >= 50 else "red")

    header_text = Text.assemble(
        ("CLOUDFLARE TUNNEL MONITOR & SUPERVISOR\n", "bold cyan"),
        (f"Target: {state.public_url} | Daemon: ", "dim"),
        (f"[{status_label}] ", status_style),
        (f"| Health Score: [{score_val}/100] | ", f"bold {score_color}"),
        (f"Errors in log: {state.total_errors_in_log}", "yellow" if state.total_errors_in_log else "dim"),
    )
    layout["header"].update(Panel(header_text, border_style="cyan"))

    # 2. Left Panel: Status & Configuration Tree
    info_table = _render_tunnel_info_table(state)
    layout["left_panel"].update(Panel(info_table, title="⚙️ Tunnel Telemetry & Process Info", border_style="blue"))

    # 3. Right-Top Panel: Live Log Table
    log_table = _render_log_table(state.logs)
    layout["logs"].update(Panel(log_table, border_style="bright_black"))

    # 4. Right-Bottom Panel: AI & Heuristic Diagnostics
    diag_content = Text()
    if rep:
        diag_color = "green" if rep.health_score >= 80 else ("yellow" if rep.health_score >= 50 else "red")
        diag_content.append(f"Diagnostic Assessment: {rep.status} ({rep.health_score}/100)\n", style=f"bold {diag_color}")
        diag_content.append(f"{rep.summary}\n\n", style="white")

        if rep.anomalies:
            diag_content.append("⚠️ Identified Issues:\n", style="bold yellow")
            for a in rep.anomalies:
                diag_content.append(f" • [{a.severity.upper()}] {a.title}: {a.description}\n", style="white")
        else:
            diag_content.append("✅ No operational anomalies detected.\n", style="green")

        if rep.recommendations:
            diag_content.append("\n💡 Recommendations:\n", style="bold cyan")
            for r in rep.recommendations:
                diag_content.append(f" • {r}\n", style="dim")
    else:
        diag_content.append("Diagnostics pending initial cycle...", style="dim")

    layout["diagnostics"].update(Panel(diag_content, title="🤖 AI & Heuristic Health Diagnostician", border_style="magenta"))

    # 5. Footer
    footer_text = Text(
        " [Q] Quit  |  [R] Force Refresh  |  [P] Probe Public Endpoint  |  Polling: 2.0s",
        style="dim white",
    )
    layout["footer"].update(Panel(footer_text, border_style="bright_black"))

    return layout


async def run_cloudflared_dashboard(
    interval: float = 2.0,
    public_url: str = "https://kino.davidka.net",
    max_iterations: Optional[int] = None,
) -> None:
    """Run the live interactive Rich terminal dashboard.

    Args:
        interval: Refresh frequency in seconds.
        public_url: Public hostname to monitor.
        max_iterations: Limit iterations for testing / dry runs.
    """
    if not RICH_AVAILABLE:
        print("Rich library is required for interactive terminal UI.")
        return

    console = Console()
    state = CloudflaredState(public_url=public_url)
    state.refresh(probe_network=True)

    iterations = 0
    with Live(render_ui(state), console=console, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                # Probe network every 5th cycle to avoid spamming public endpoint
                probe_net = (iterations % 5 == 0)
                state.refresh(probe_network=probe_net)
                live.update(render_ui(state))
                iterations += 1
                if max_iterations and iterations >= max_iterations:
                    break
                await asyncio.sleep(interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
