# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Inspector CLI Entry Point
# =============================================================================
# Description:
#   Executable module entry point for launching the interactive System & Hardware
#   Inspector TUI, one-shot hardware audits, or JSON telemetry snapshots.
#
# Examples:
#   $ python -m apps.system_inspector --sort memory --interval 2.0
#   $ python -m apps.system_inspector --diagnose
#   $ python -m apps.system_inspector --hardware
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the System & Hardware Inspector application."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from src.system import SystemAIDiagnostician, SystemCollector
from .tui import run_system_inspector


def main() -> None:
    """Parse command line arguments and execute requested action."""
    parser = argparse.ArgumentParser(
        description="AI Breadboard System & Hardware Inspector (AIDA64 + Wireshark Dual Monitor)"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=1.0,
        help="Polling interval in seconds for live monitor (default: 1.0)",
    )
    parser.add_argument(
        "--sort",
        "-s",
        type=str,
        choices=["cpu", "memory"],
        default="cpu",
        help="Sort active process stream by 'cpu' or 'memory' (default: cpu)",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=20,
        help="Number of active processes to display (default: 20)",
    )
    parser.add_argument(
        "--diagnose",
        "-d",
        action="store_true",
        help="Perform one-shot AI system performance diagnosis and exit",
    )
    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Print AIDA64-style hardware specification tree and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw telemetry snapshot as JSON and exit",
    )

    args = parser.parse_args()
    collector = SystemCollector()

    if args.json:
        snapshot = collector.get_snapshot(process_limit=args.limit)
        print(snapshot.model_dump_json(indent=2))
        return

    if args.hardware:
        tree = collector.get_hardware_tree()
        print("\n=== AIDA64 Hardware Specification Tree ===")
        for node in tree:
            print(f"\n[{node.category}] {node.name}")
            for k, v in node.properties.items():
                print(f"  • {k}: {v}")
        return

    if args.diagnose:
        snapshot = collector.get_snapshot(process_limit=args.limit)
        diagnostician = SystemAIDiagnostician()
        report = asyncio.run(diagnostician.diagnose(snapshot))
        print("\n=== AI System Performance & Health Audit ===")
        print(f"Health Score: {report.health_score}/100")
        print(f"Summary: {report.summary}")
        if report.anomalies:
            print("\nAnomalies Detected:")
            for a in report.anomalies:
                print(f" - [{a.severity.upper()}] {a.title}: {a.description}")
        print("\nRecommendations:")
        for r in report.recommendations:
            print(f" - {r}")
        return

    # Default: launch interactive live TUI dashboard
    try:
        asyncio.run(run_system_inspector(interval=args.interval, sort_by=args.sort))
    except KeyboardInterrupt:
        print("\nSystem Inspector closed.")


if __name__ == "__main__":
    main()
