# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System & Hardware Inspector Rich TUI Dashboard
# =============================================================================
# Description:
#   Interactive Rich terminal dashboard for system telemetry, Wireshark-style
#   process streams, AIDA64-style hardware specs, and AI performance diagnosis.
#
# Examples:
#   >>> from apps.system_inspector.tui import run_system_inspector
#   >>> await run_system_inspector(interval=1.0, sort_by="cpu")
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Rich TUI dashboard renderer for System & Hardware Inspector."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Any, List, Optional

from src.logger import logger
from src.system import (
    AnomalyItem,
    HardwareNode,
    HardwareSensor,
    ProcessMetrics,
    SystemAIDiagnostician,
    SystemCollector,
    SystemDiagnosticReport,
    SystemSnapshot,
)

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


class SystemInspectorState:
    """Session state for interactive terminal system inspector."""

    def __init__(self, sort_by: str = "cpu", process_limit: int = 15) -> None:
        """Initialize session state."""
        self.collector: SystemCollector = SystemCollector()
        self.diagnostician: SystemAIDiagnostician = SystemAIDiagnostician()
        self.sort_by: str = sort_by
        self.process_limit: int = process_limit
        self.latest_snapshot: Optional[SystemSnapshot] = None
        self.latest_report: Optional[SystemDiagnosticReport] = None
        self.hardware_tree_nodes: List[HardwareNode] = []
        self.status_message: str = "Initializing telemetry stream..."

    def refresh(self) -> None:
        """Collect latest telemetry snapshot and evaluate heuristics."""
        self.latest_snapshot = self.collector.get_snapshot(process_limit=self.process_limit)
        if not self.hardware_tree_nodes:
            self.hardware_tree_nodes = self.collector.get_hardware_tree()

        score, anomalies, recommendations = self.diagnostician.evaluate_heuristics(self.latest_snapshot)
        self.latest_report = SystemDiagnosticReport(
            health_score=score,
            summary=f"System Health: {score}/100. Telemetry stream nominal.",
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used="Heuristic Monitor",
        )


def _render_process_table(snapshot: SystemSnapshot, sort_by: str) -> Table:
    """Build Wireshark-style live process table."""
    table = Table(
        title=f"Live Process Stream (Sorted by {sort_by.upper()})",
        expand=True,
        header_style="bold cyan",
        border_style="bright_black",
    )
    table.add_column("PID", style="cyan", width=8, justify="right")
    table.add_column("Process Name", style="bold white", min_width=18)
    table.add_column("Status", style="dim", width=10)
    table.add_column("CPU %", style="yellow", justify="right", width=8)
    table.add_column("RAM (MB)", style="green", justify="right", width=10)
    table.add_column("RAM %", style="dim green", justify="right", width=8)
    table.add_column("Threads", style="magenta", justify="right", width=8)
    table.add_column("User", style="dim", width=12)

    for proc in snapshot.top_processes:
        cpu_style = "bold red" if proc.cpu_percent > 50 else ("yellow" if proc.cpu_percent > 20 else "white")
        table.add_row(
            str(proc.pid),
            proc.name,
            proc.status,
            f"[{cpu_style}]{proc.cpu_percent:.1f}%[/{cpu_style}]",
            f"{proc.memory_mb:.1f}",
            f"{proc.memory_percent:.1f}%",
            str(proc.num_threads),
            proc.username or "SYSTEM",
        )
    return table


def _render_hardware_tree(nodes: List[HardwareNode], sensors: List[HardwareSensor]) -> Tree:
    """Build AIDA64-like hardware component tree."""
    tree = Tree("[bold cyan]🖥️ Host Hardware & Sensors[/bold cyan]")

    for node in nodes:
        branch = tree.add(f"[bold yellow]{node.category}[/bold yellow]: {node.name}")
        for k, v in node.properties.items():
            branch.add(f"[dim]{k}:[/dim] [white]{v}[/white]")

    if sensors:
        sensor_branch = tree.add("[bold red]🌡️ Active Hardware Sensors[/bold red]")
        for s in sensors:
            color = "red" if s.value >= 80 else ("yellow" if s.value >= 65 else "green")
            sensor_branch.add(f"{s.name}: [{color}]{s.value} {s.unit}[/{color}]")

    return tree


def render_ui(state: SystemInspectorState) -> Any:
    """Render full composite Rich TUI layout.

    Args:
        state: Active inspector session state.

    Returns:
        Any: Configured Rich layout instance.
    """
    if not RICH_AVAILABLE or not state.latest_snapshot:
        return None

    snap = state.latest_snapshot
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="processes", ratio=3),
        Layout(name="hardware_side", ratio=2),
    )

    layout["hardware_side"].split_column(
        Layout(name="hardware", ratio=3),
        Layout(name="ai_copilot", ratio=2),
    )

    # 1. Header with System Overview Gauges
    cpu_bar = f"CPU: {snap.cpu.total_percent}% ({snap.cpu.physical_cores}C/{snap.cpu.logical_cores}T)"
    ram_bar = f"RAM: {snap.memory.used_gb}/{snap.memory.total_gb} GB ({snap.memory.percent}%)"
    uptime_h = round(snap.uptime_seconds / 3600, 1)

    gpu_str = ", ".join([f"{g.name} ({g.memory_total_gb}GB)" for g in snap.gpus]) or "Integrated"
    header_text = Text.assemble(
        ("AI-BREADBOARD SYSTEM & HARDWARE INSPECTOR\n", "bold cyan"),
        (f"Host: {snap.hostname} | OS: {snap.os_name} | Uptime: {uptime_h}h | ", "dim"),
        (f"{cpu_bar} | {ram_bar} | GPU: {gpu_str}", "bold green"),
    )
    layout["header"].update(Panel(header_text, border_style="cyan"))

    # 2. Left Pane: Live Process Stream
    proc_table = _render_process_table(snap, state.sort_by)
    layout["processes"].update(Panel(proc_table, border_style="blue"))

    # 3. Right-Top Pane: AIDA64 Hardware Tree
    hw_tree = _render_hardware_tree(state.hardware_tree_nodes, snap.sensors)
    layout["hardware"].update(Panel(hw_tree, title="AIDA64 Hardware & Sensor Tree", border_style="yellow"))

    # 4. Right-Bottom Pane: AI Diagnostic Copilot
    rep = state.latest_report
    copilot_content = Text()
    if rep:
        health_color = "green" if rep.health_score >= 80 else ("yellow" if rep.health_score >= 60 else "red")
        copilot_content.append(f"System Health: {rep.health_score}/100\n", style=f"bold {health_color}")
        copilot_content.append(f"AI Engine: {rep.ai_model_used}\n\n", style="dim")
        if rep.anomalies:
            copilot_content.append("⚠️ Detected Anomalies:\n", style="bold yellow")
            for a in rep.anomalies:
                copilot_content.append(f" • [{a.severity.upper()}] {a.title}: {a.description}\n", style="white")
        else:
            copilot_content.append("✅ All hardware subsystems running optimal.\n", style="green")

        if rep.recommendations:
            copilot_content.append("\n💡 Recommendations:\n", style="bold cyan")
            for r in rep.recommendations:
                copilot_content.append(f" • {r}\n", style="dim")

    layout["ai_copilot"].update(Panel(copilot_content, title="🤖 AI Performance Copilot", border_style="magenta"))

    # 5. Footer
    footer_text = Text(" [Q] Quit  |  [S] Toggle CPU/RAM Sort  |  [D] Trigger AI Diagnostic  |  Polling: 1.0s", style="dim white")
    layout["footer"].update(Panel(footer_text, border_style="bright_black"))

    return layout


async def run_system_inspector(interval: float = 1.0, sort_by: str = "cpu", max_iterations: Optional[int] = None) -> None:
    """Run interactive live terminal dashboard.

    Args:
        interval: Polling frequency in seconds.
        sort_by: Initial process sort column ('cpu' or 'memory').
        max_iterations: Optional iterations limit (useful for dry runs / testing).
    """
    if not RICH_AVAILABLE:
        print("Rich library is required for interactive terminal UI.")
        return

    console = Console()
    state = SystemInspectorState(sort_by=sort_by)
    state.refresh()

    iterations = 0
    with Live(render_ui(state), console=console, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                state.refresh()
                live.update(render_ui(state))
                iterations += 1
                if max_iterations and iterations >= max_iterations:
                    break
                await asyncio.sleep(interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
