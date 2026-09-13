# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud Monitor Interactive TUI Dashboard
# =============================================================================
# Description:
#   Rich terminal user interface (TUI) for real-time live telemetry,
#   monitoring logs, metrics, audit events, and AI health assessments.
#
# Examples:
#   >>> from apps.gcloud_monitor.tui import run_tui
#   >>> run_tui()
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor
# Class: N/A
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Interactive Rich-based terminal dashboard for Google Cloud Monitor."""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apps.gcloud_monitor.src.alert_engine import GCloudAlertEngine
from apps.gcloud_monitor.src.audit_service import GCloudAuditService
from apps.gcloud_monitor.src.auth import GCloudAuthManager
from apps.gcloud_monitor.src.diagnostics import GCloudDiagnosticsEngine
from apps.gcloud_monitor.src.error_reporting import GCloudErrorReporter
from apps.gcloud_monitor.src.logging_service import GCloudLoggingService
from apps.gcloud_monitor.src.metrics_service import GCloudMetricsService


def create_header(auth_mgr: GCloudAuthManager) -> Panel:
    """Render header panel with project info and auth status."""
    status = auth_mgr.get_status()
    auth_label = f'[green]AUTHENTICATED ({status.auth_type.upper()})[/green]' if status.authenticated else '[yellow]DEMO / MOCK MODE[/yellow]'
    
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='right', ratio=1)
    grid.add_row(
        f'[bold cyan]☁️ GOOGLE CLOUD OBSERVABILITY CONSOLE[/bold cyan] | Project: [bold white]{status.project_id}[/bold white]',
        f'Auth: {auth_label} | Account: [cyan]{status.client_email or "local-dev"}[/cyan]'
    )
    return Panel(grid, style='blue')


def create_metrics_panel(metrics_svc: GCloudMetricsService) -> Panel:
    """Render metrics summary table."""
    summary = metrics_svc.get_metrics_summary()
    table = Table(title='📊 Cloud Monitoring Telemetry', expand=True, box=None)
    table.add_column('Metric', style='cyan')
    table.add_column('Value', style='bold white', justify='right')
    table.add_column('Status', justify='center')

    err_color = 'green' if summary.error_rate_percent < 2.0 else 'red'
    table.add_row('Throughput', f'{summary.total_requests_per_min:.0f} req/min', '🟢 OK')
    table.add_row('Error Rate', f'[{err_color}]{summary.error_rate_percent:.2f}%[/{err_color}]', '🟢 OK' if summary.error_rate_percent < 2.0 else '🔴 HIGH')
    table.add_row('P95 Latency', f'{summary.p95_latency_ms:.0f} ms', '🟢 OK' if summary.p95_latency_ms < 500 else '🟡 SLOW')
    table.add_row('CPU Utilization', f'{summary.cpu_utilization_percent:.1f}%', '🟢 OK' if summary.cpu_utilization_percent < 80 else '🔴 HIGH')
    table.add_row('Memory Usage', f'{summary.memory_utilization_percent:.1f}%', '🟢 OK')
    table.add_row('Active Instances', str(summary.active_instances), '🟢 UP')

    return Panel(table, title='[bold]Metrics[/bold]', border_style='green')


def create_logs_panel(logging_svc: GCloudLoggingService) -> Panel:
    """Render recent logs table."""
    logs = logging_svc.query_logs(max_entries=8)
    table = Table(title='📜 Cloud Logging Stream', expand=True, box=None)
    table.add_column('Time', style='dim', width=12)
    table.add_column('Sev', width=6)
    table.add_column('Service', style='cyan', width=18)
    table.add_column('Message', ratio=1)

    for entry in logs:
        sev_color = 'green' if entry.severity == 'INFO' else ('yellow' if entry.severity == 'WARNING' else 'red')
        ts_short = entry.timestamp[-13:-5] if len(entry.timestamp) > 13 else entry.timestamp
        svc_name = entry.resource_labels.get('service_name', entry.resource_type)
        table.add_row(
            ts_short,
            f'[{sev_color}]{entry.severity[:4]}[/{sev_color}]',
            svc_name[:18],
            entry.text_payload[:60]
        )
    return Panel(table, title='[bold]Live Logs[/bold]', border_style='cyan')


def create_audit_panel(audit_svc: GCloudAuditService) -> Panel:
    """Render security audit table."""
    audits = audit_svc.get_recent_audit_events(limit=5)
    table = Table(title='🛡️ Cloud Audit & IAM Events', expand=True, box=None)
    table.add_column('Principal', style='yellow', width=22)
    table.add_column('Method', style='magenta', width=25)
    table.add_column('Status', width=6)

    for ev in audits:
        stat_color = 'green' if ev.status_code == 'OK' else 'red'
        method_short = ev.method_name.split('.')[-1]
        table.add_row(
            ev.principal_email[:22],
            method_short[:25],
            f'[{stat_color}]{ev.status_code}[/{stat_color}]'
        )
    return Panel(table, title='[bold]Audit & Security[/bold]', border_style='magenta')


def create_diagnostics_panel(diag_engine: GCloudDiagnosticsEngine) -> Panel:
    """Render AI health and diagnostics assessment."""
    report = diag_engine.evaluate_health()
    status_color = 'green' if report.status == 'HEALTHY' else ('yellow' if report.status == 'DEGRADED' else 'red')
    
    text = Text()
    text.append(f'Health Score: {report.score}/100  |  Status: ', style='bold')
    text.append(f'{report.status}\n', style=f'bold {status_color}')
    text.append(f'RCA: {report.root_cause_analysis}\n', style='dim')
    if report.recommendations:
        text.append(f'Recommended Action: {report.recommendations[0]}', style='cyan')

    return Panel(text, title='[bold]🤖 AI Observability Diagnostics[/bold]', border_style='yellow')


def run_tui() -> None:
    """Run live TUI dashboard loop."""
    console = Console()
    auth_mgr = GCloudAuthManager()
    logging_svc = GCloudLoggingService(auth_mgr=auth_mgr)
    metrics_svc = GCloudMetricsService(auth_mgr=auth_mgr)
    audit_svc = GCloudAuditService(auth_mgr=auth_mgr, logging_svc=logging_svc)
    error_reporter = GCloudErrorReporter(auth_mgr=auth_mgr, logging_svc=logging_svc)
    alert_engine = GCloudAlertEngine(auth_mgr=auth_mgr, metrics_svc=metrics_svc, logging_svc=logging_svc)
    diag_engine = GCloudDiagnosticsEngine(
        auth_mgr=auth_mgr,
        metrics_svc=metrics_svc,
        error_reporter=error_reporter,
        audit_svc=audit_svc,
        alert_engine=alert_engine,
    )

    layout = Layout()
    layout.split_column(
        Layout(name='header', size=3),
        Layout(name='upper', ratio=2),
        Layout(name='lower', ratio=2),
        Layout(name='footer', size=5),
    )
    layout['upper'].split_row(
        Layout(name='metrics', ratio=1),
        Layout(name='logs', ratio=2),
    )
    layout['lower'].split_row(
        Layout(name='audit', ratio=1),
        Layout(name='diagnostics', ratio=1),
    )

    try:
        with Live(layout, console=console, refresh_per_second=1, screen=True):
            while True:
                layout['header'].update(create_header(auth_mgr))
                layout['upper']['metrics'].update(create_metrics_panel(metrics_svc))
                layout['upper']['logs'].update(create_logs_panel(logging_svc))
                layout['lower']['audit'].update(create_audit_panel(audit_svc))
                layout['lower']['diagnostics'].update(create_diagnostics_panel(diag_engine))
                layout['footer'].update(Panel('[bold dim]Press Ctrl+C to exit dashboard[/bold dim]', style='grey50'))
                time.sleep(2.0)
    except KeyboardInterrupt:
        console.print('\n[bold green]Exited Google Cloud Monitor TUI.[/bold green]')
