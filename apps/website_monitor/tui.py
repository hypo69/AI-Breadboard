# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Website Intelligence Monitor TUI Dashboard
# =============================================================================
# Description:
#   Rich terminal user interface (TUI) for real-time website intelligence:
#   live visitors, GA4 traffic channels, top pages, period deltas, technical
#   telemetry, active anomaly alerts, and AI diagnostics.
#
# Examples:
#   >>> from apps.website_monitor.tui import run_tui
#   >>> run_tui()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.website_monitor
# Class: N/A
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Interactive Rich-based terminal dashboard for Website Intelligence Monitor."""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apps.website_monitor.src.anomaly_detector import AnomalyDetector
from apps.website_monitor.src.auth import WebsiteMonitorAuthManager
from apps.website_monitor.src.diagnostics import WebsiteDiagnosticsEngine
from apps.website_monitor.src.ga4_service import GA4Service
from apps.website_monitor.src.gsc_service import GSCService
from apps.website_monitor.src.normalizer import MetricsNormalizer
from apps.website_monitor.src.technical_service import TechnicalService


def create_header(auth_mgr: WebsiteMonitorAuthManager) -> Panel:
    """Render header panel with site and property info."""
    status = auth_mgr.get_status()
    auth_label = f"[green]AUTHENTICATED ({status.auth_type.upper()})[/green]" if status.authenticated else "[yellow]DEMO / MOCK MODE[/yellow]"

    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right", ratio=1)
    grid.add_row(
        f"[bold cyan]🌐 WEBSITE INTELLIGENCE MONITOR[/bold cyan] | Site: [bold white]{status.site_url}[/bold white]",
        f"Property: [cyan]{status.property_id}[/cyan] | Auth: {auth_label}"
    )
    return Panel(grid, style="blue")


def create_realtime_panel(ga4_svc: GA4Service) -> Panel:
    """Render live visitors panel."""
    rt = ga4_svc.get_realtime_data()
    table = Table(expand=True, box=None)
    table.add_column("Live Metric", style="cyan")
    table.add_column("Value", style="bold white", justify="right")

    table.add_row("👥 Active Users Now", f"[bold green]{rt.active_users}[/bold green]")
    for c in rt.top_countries[:3]:
        table.add_row(f"📍 {c.country}", str(c.active_users))

    desktop_cnt = rt.device_breakdown.get("desktop", 0)
    mobile_cnt = rt.device_breakdown.get("mobile", 0)
    table.add_row("📱 Desktop / Mobile", f"{desktop_cnt} / {mobile_cnt}")

    return Panel(table, title="[bold]⚡ Realtime (Last 30m)[/bold]", border_style="green")


def create_overview_panel(normalizer: MetricsNormalizer) -> Panel:
    """Render period comparison table (This Week vs Previous Week)."""
    report = normalizer.build_unified_report()
    cur = report.current_period
    prev = report.previous_period

    table = Table(title="📈 Period Comparison (WoW)", expand=True, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("This Week", justify="right", style="bold white")
    table.add_column("Last Week", justify="right", style="dim")
    table.add_column("Delta", justify="right")

    def fmt_delta(delta_key: str) -> str:
        d = report.deltas.get(delta_key)
        if not d:
            return "0%"
        color = "green" if d.change_percent >= 0 else "red"
        return f"[{color}]{d.change_percent:+.1f}%[/{color}]"

    table.add_row("Active Users", f"{cur.active_users:,}", f"{prev.active_users:,}", fmt_delta("users"))
    table.add_row("Sessions", f"{cur.sessions:,}", f"{prev.sessions:,}", fmt_delta("sessions"))
    table.add_row("Page Views", f"{cur.page_views:,}", f"{prev.page_views:,}", fmt_delta("page_views"))
    table.add_row("Conversions", f"{cur.conversions:,}", f"{prev.conversions:,}", fmt_delta("conversions"))
    table.add_row("Engagement Rate", f"{cur.engagement_rate:.1f}%", f"{prev.engagement_rate:.1f}%", fmt_delta("engagement_rate"))

    return Panel(table, title="[bold]Business Layer (GA4)[/bold]", border_style="blue")


def create_traffic_panel(ga4_svc: GA4Service) -> Panel:
    """Render traffic acquisition channels."""
    channels = ga4_svc.get_channel_breakdown()
    table = Table(expand=True, box=None)
    table.add_column("Channel", style="cyan")
    table.add_column("Share", justify="right")
    table.add_column("Conversions", justify="right", style="bold white")

    for ch in channels:
        bars = "█" * int(ch.percentage / 5)
        table.add_row(ch.channel_group, f"{bars} {ch.percentage:.0f}%", str(ch.conversions))

    return Panel(table, title="[bold]Acquisition Channels[/bold]", border_style="magenta")


def create_technical_panel(tech_svc: TechnicalService) -> Panel:
    """Render technical telemetry and server health."""
    summary = tech_svc.get_technical_summary()
    table = Table(expand=True, box=None)
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="right", style="bold white")

    table.add_row("Availability", f"[green]{summary.availability_percent:.2f}%[/green]")
    table.add_row("Avg Response", f"{summary.avg_response_time_ms:.0f} ms")
    err_color = "green" if summary.status_5xx_count == 0 else "red"
    table.add_row("5xx Errors", f"[{err_color}]{summary.status_5xx_count}[/{err_color}]")
    table.add_row("404 Errors", f"{summary.status_404_count}")
    table.add_row("CPU / Memory", f"{summary.cpu_usage_percent:.0f}% / {summary.memory_usage_percent:.0f}%")

    return Panel(table, title="[bold]Technical & Server[/bold]", border_style="cyan")


def create_alerts_panel(diag_engine: WebsiteDiagnosticsEngine) -> Panel:
    """Render AI diagnosis and active alerts."""
    assessment = diag_engine.evaluate_site_health()
    table = Table(expand=True, box=None)
    table.add_column("Alert / Verdict", style="yellow")
    table.add_column("Impact", justify="right", style="bold red")

    for alert in assessment.active_alerts:
        table.add_row(f"⚠️ {alert.title}", alert.change_value)

    if not assessment.active_alerts:
        table.add_row("🟢 All systems and business metrics nominal", "OK")

    summary_text = Text(assessment.executive_summary, style="italic dim")
    grid = Table.grid(expand=True)
    grid.add_row(table)
    grid.add_row(Panel(summary_text, title="[bold green]🤖 AI Root Cause Diagnosis[/bold green]", border_style="green"))

    return Panel(grid, title=f"[bold]Alerts & Diagnostics (Score: {assessment.health_score}/100)[/bold]", border_style="yellow")


def make_layout() -> Layout:
    """Create dashboard layout structure."""
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=9),
    )
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1),
    )
    layout["left"].split(
        Layout(name="realtime", ratio=1),
        Layout(name="traffic", ratio=1),
    )
    layout["right"].split(
        Layout(name="overview", ratio=1),
        Layout(name="technical", ratio=1),
    )
    layout["footer"].update(Layout(name="alerts"))
    return layout


def run_tui() -> None:
    """Start interactive TUI monitoring loop."""
    console = Console()
    auth_mgr = WebsiteMonitorAuthManager()
    ga4_svc = GA4Service(auth_mgr=auth_mgr)
    tech_svc = TechnicalService(auth_mgr=auth_mgr)
    gsc_svc = GSCService(auth_mgr=auth_mgr)
    normalizer = MetricsNormalizer(ga4_svc=ga4_svc, gsc_svc=gsc_svc, tech_svc=tech_svc)
    anomaly_detector = AnomalyDetector()
    diag_engine = WebsiteDiagnosticsEngine(normalizer=normalizer, anomaly_detector=anomaly_detector)

    layout = make_layout()

    try:
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                layout["header"].update(create_header(auth_mgr))
                layout["left"]["realtime"].update(create_realtime_panel(ga4_svc))
                layout["left"]["traffic"].update(create_traffic_panel(ga4_svc))
                layout["right"]["overview"].update(create_overview_panel(normalizer))
                layout["right"]["technical"].update(create_technical_panel(tech_svc))
                layout["footer"].update(create_alerts_panel(diag_engine))
                time.sleep(2)
    except KeyboardInterrupt:
        console.print("[yellow]Website Intelligence Monitor exited.[/yellow]")


if __name__ == "__main__":
    run_tui()
