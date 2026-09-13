# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud Monitor CLI Entry Point
# =============================================================================
# Description:
#   Command-line interface (CLI) for executing Google Cloud Console &
#   Observability inspections, launching TUI dashboard, or running server.
#
# Examples:
#   $ python -m apps.gcloud_monitor --status
#   $ python -m apps.gcloud_monitor --logs --limit 20
#   $ python -m apps.gcloud_monitor --mode server --port 8105
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor
# Class: N/A
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for Google Cloud Console & Observability Monitor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from apps.gcloud_monitor.router import router
from apps.gcloud_monitor.src.alert_engine import GCloudAlertEngine
from apps.gcloud_monitor.src.audit_service import GCloudAuditService
from apps.gcloud_monitor.src.auth import GCloudAuthManager
from apps.gcloud_monitor.src.diagnostics import GCloudDiagnosticsEngine
from apps.gcloud_monitor.src.error_reporting import GCloudErrorReporter
from apps.gcloud_monitor.src.logging_service import GCloudLoggingService
from apps.gcloud_monitor.src.metrics_service import GCloudMetricsService
from apps.gcloud_monitor.tui import run_tui
from src.logger import logger


def main() -> None:
    """Main CLI execution dispatcher."""
    parser = argparse.ArgumentParser(
        description='Google Cloud Console & Observability Monitor (ai-breadboard)'
    )
    parser.add_argument(
        '--mode',
        choices=['tui', 'server'],
        default='tui',
        help='Run mode: interactive TUI dashboard or standalone FastAPI server',
    )
    parser.add_argument('--port', type=int, default=8105, help='Port for FastAPI server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host for server')
    parser.add_argument('--status', action='store_true', help='Print GCP connectivity and auth status')
    parser.add_argument('--logs', action='store_true', help='Query and print recent logs')
    parser.add_argument('--filter', type=str, default='', help='GCP Logging filter expression')
    parser.add_argument('--metrics', action='store_true', help='Print metrics summary')
    parser.add_argument('--audit', action='store_true', help='Print recent audit security events')
    parser.add_argument('--errors', action='store_true', help='Print clustered error groups')
    parser.add_argument('--diagnostic', action='store_true', help='Run AI health diagnostic')
    parser.add_argument('--limit', type=int, default=20, help='Max records to return')
    parser.add_argument('--json', action='store_true', help='Output in raw JSON format')

    args = parser.parse_args()

    auth_mgr = GCloudAuthManager()
    logging_svc = GCloudLoggingService(auth_mgr=auth_mgr)
    metrics_svc = GCloudMetricsService(auth_mgr=auth_mgr)
    audit_svc = GCloudAuditService(auth_mgr=auth_mgr, logging_svc=logging_svc)
    error_reporter = GCloudErrorReporter(auth_mgr=auth_mgr, logging_svc=logging_svc)
    alert_engine = GCloudAlertEngine(
        auth_mgr=auth_mgr, metrics_svc=metrics_svc, logging_svc=logging_svc
    )
    diag_engine = GCloudDiagnosticsEngine(
        auth_mgr=auth_mgr,
        metrics_svc=metrics_svc,
        error_reporter=error_reporter,
        audit_svc=audit_svc,
        alert_engine=alert_engine,
    )

    if args.status:
        st = auth_mgr.get_status()
        res = {
            'authenticated': st.authenticated,
            'auth_type': st.auth_type,
            'project_id': st.project_id,
            'client_email': st.client_email,
            'details': st.details,
        }
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"GCP Project: {st.project_id} (Auth: {st.auth_type}, Authenticated: {st.authenticated})")
        return

    if args.logs:
        logs = logging_svc.query_logs(filter_expr=args.filter, max_entries=args.limit)
        res_list = [l.to_dict() for l in logs]
        if args.json:
            print(json.dumps(res_list, indent=2))
        else:
            for l in logs:
                print(f"[{l.timestamp}] [{l.severity}] ({l.resource_type}) {l.text_payload}")
        return

    if args.metrics:
        m = metrics_svc.get_metrics_summary()
        if args.json:
            print(json.dumps(m.to_dict(), indent=2))
        else:
            print(f"Requests/min: {m.total_requests_per_min:.0f} | Error Rate: {m.error_rate_percent:.2f}% | P95: {m.p95_latency_ms:.0f}ms | CPU: {m.cpu_utilization_percent:.1f}%")
        return

    if args.audit:
        auds = audit_svc.get_recent_audit_events(limit=args.limit)
        res_list = [a.to_dict() for a in auds]
        if args.json:
            print(json.dumps(res_list, indent=2))
        else:
            for a in auds:
                print(f"[{a.timestamp}] [{a.status_code}] {a.principal_email} -> {a.method_name}")
        return

    if args.errors:
        errs = error_reporter.get_error_groups(limit=args.limit)
        res_list = [e.to_dict() for e in errs]
        if args.json:
            print(json.dumps(res_list, indent=2))
        else:
            for e in errs:
                print(f"[{e.occurrences_count}x] {e.error_type} in {e.service}: {e.message}")
        return

    if args.diagnostic:
        diag = diag_engine.evaluate_health()
        if args.json:
            print(json.dumps(diag.to_dict(), indent=2))
        else:
            print(f"Status: {diag.status} (Score: {diag.score}/100)")
            print(f"RCA: {diag.root_cause_analysis}")
        return

    if args.mode == 'server':
        app = FastAPI(title='Google Cloud Monitor Microservice')
        app.include_router(router)
        print(f"Starting Google Cloud Monitor API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    # Default: Run TUI Dashboard
    run_tui()


if __name__ == '__main__':
    main()
