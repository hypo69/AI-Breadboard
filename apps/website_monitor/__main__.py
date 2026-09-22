# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Website Intelligence Monitor CLI Entry Point
# =============================================================================
# Description:
#   Command-line interface to launch the TUI live dashboard, query real-time
#   visitors, run AI health diagnostics, or start the standalone API server.
#
# Examples:
#   >>> python -m apps.website_monitor
#   >>> python -m apps.website_monitor --realtime
#   >>> python -m apps.website_monitor --diagnostic
#   >>> python -m apps.website_monitor --mode server --port 8107
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.website_monitor
# Class: N/A
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for Website Intelligence Monitor."""

from __future__ import annotations

import argparse
import json
import sys

from apps.website_monitor.src.anomaly_detector import AnomalyDetector
from apps.website_monitor.src.auth import WebsiteMonitorAuthManager
from apps.website_monitor.src.diagnostics import WebsiteDiagnosticsEngine
from apps.website_monitor.src.ga4_service import GA4Service
from apps.website_monitor.src.gsc_service import GSCService
from apps.website_monitor.src.normalizer import MetricsNormalizer
from apps.website_monitor.src.technical_service import TechnicalService
from logger import logger


def main() -> None:
    """Parse CLI arguments and dispatch commands."""
    parser = argparse.ArgumentParser(
        prog="apps.website_monitor",
        description="Website Intelligence Monitor: GA4, Search Console & Technical Observability Desk",
    )
    parser.add_argument(
        "--mode",
        choices=["tui", "server"],
        default="tui",
        help="Run interactive TUI dashboard or FastAPI server (default: tui)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8107,
        help="Server port when running in server mode (default: 8107)",
    )
    parser.add_argument("--status", action="store_true", help="Print authentication and property status")
    parser.add_argument("--realtime", action="store_true", help="Print current active visitors snapshot")
    parser.add_argument("--summary", action="store_true", help="Print 3-layer normalized report")
    parser.add_argument("--technical", action="store_true", help="Print server & HTTP technical telemetry")
    parser.add_argument("--diagnostic", action="store_true", help="Run AI root cause diagnosis & health scoring")
    parser.add_argument("--json", action="store_true", help="Format CLI output as JSON")

    args = parser.parse_args()

    auth_mgr = WebsiteMonitorAuthManager()
    ga4_svc = GA4Service(auth_mgr=auth_mgr)
    gsc_svc = GSCService(auth_mgr=auth_mgr)
    tech_svc = TechnicalService(auth_mgr=auth_mgr)
    norm = MetricsNormalizer(ga4_svc=ga4_svc, gsc_svc=gsc_svc, tech_svc=tech_svc)
    detector = AnomalyDetector()
    diag = WebsiteDiagnosticsEngine(normalizer=norm, anomaly_detector=detector)

    if args.status:
        st = auth_mgr.get_status()
        data = {
            "authenticated": st.authenticated,
            "auth_type": st.auth_type,
            "property_id": st.property_id,
            "site_url": st.site_url,
            "client_email": st.client_email,
            "is_mock": st.is_mock,
            "details": st.details,
        }
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"\n🌐 Website Monitor Status:")
            print(f"  • Site URL:     {st.site_url}")
            print(f"  • Property ID:  {st.property_id}")
            print(f"  • Auth Mode:    {st.auth_type.upper()}")
            print(f"  • Is Demo/Mock: {st.is_mock}")
            print(f"  • Details:      {st.details}\n")
        return

    if args.realtime:
        rt = ga4_svc.get_realtime_data()
        if args.json:
            print(json.dumps(rt.to_dict(), indent=2))
        else:
            print(f"\n⚡ Live Visitors (Last 30m):")
            print(f"  • Active Users Now: {rt.active_users}")
            print(f"  • Top Countries:    {', '.join(f'{c.country} ({c.active_users})' for c in rt.top_countries)}")
            print(f"  • Devices:          Desktop: {rt.device_breakdown.get('desktop', 0)}, Mobile: {rt.device_breakdown.get('mobile', 0)}\n")
        return

    if args.summary:
        report = norm.build_unified_report()
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"\n📈 Unified Site Summary:")
            print(f"  • Users (WoW):       {report.current_period.active_users:,} ({report.deltas['users'].change_percent:+.1f}%)")
            print(f"  • Sessions (WoW):    {report.current_period.sessions:,} ({report.deltas['sessions'].change_percent:+.1f}%)")
            print(f"  • Conversions (WoW): {report.current_period.conversions:,} ({report.deltas['conversions'].change_percent:+.1f}%)")
            print(f"  • Availability:      {report.technical.availability_percent:.2f}%\n")
        return

    if args.technical:
        tech = tech_svc.get_technical_summary()
        if args.json:
            print(json.dumps(tech.to_dict(), indent=2))
        else:
            print(f"\n🛠️ Technical Telemetry:")
            print(f"  • Availability:      {tech.availability_percent:.2f}%")
            print(f"  • Avg Latency:       {tech.avg_response_time_ms:.1f} ms")
            print(f"  • Status Codes:      200: {tech.status_200_count}, 404: {tech.status_404_count}, 5xx: {tech.status_5xx_count}")
            print(f"  • System Load:       CPU {tech.cpu_usage_percent:.0f}%, RAM {tech.memory_usage_percent:.0f}%\n")
        return

    if args.diagnostic:
        diag_res = diag.evaluate_site_health()
        if args.json:
            print(json.dumps(diag_res.to_dict(), indent=2))
        else:
            print(f"\n🤖 AI Root Cause Diagnosis (Score: {diag_res.health_score}/100 - {diag_res.overall_status}):")
            print(f"  • Summary:           {diag_res.executive_summary}")
            print(f"  • Business Impact:   {diag_res.business_impact}")
            print(f"  • Technical Verdict: {diag_res.technical_verdict}")
            print(f"  • Action Items:      {chr(10).join(f'    - {act}' for act in diag_res.action_items)}\n")
        return

    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.website_monitor.router import router

        app = FastAPI(title="Website Intelligence Monitor API", version="1.0.0")
        app.include_router(router)
        print(f"Starting Website Intelligence Monitor server on port {args.port}...")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
        return

    # Default: launch TUI
    from apps.website_monitor.tui import run_tui
    run_tui()


if __name__ == "__main__":
    main()
