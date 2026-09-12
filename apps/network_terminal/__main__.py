# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal CLI Main Entry Point
# =============================================================================
# Description:
#   Executable module entry point for running the interactive network terminal TUI.
#
# Examples:
#   $ python -m apps.network_terminal --interface 1 --filter "tcp port 80"
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.network_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the Network Analyzer Terminal dashboard."""

import argparse
import asyncio
import sys

from .tui import run_network_dashboard
from src.network import TSharkWrapper


def main() -> None:
    """Parse CLI arguments and launch interactive network terminal dashboard."""
    parser = argparse.ArgumentParser(description="AI Breadboard Network Analyzer Terminal")
    parser.add_argument(
        "--interface",
        "-i",
        type=str,
        default="1",
        help="Capture interface index or name (default: 1)",
    )
    parser.add_argument(
        "--filter",
        "-f",
        type=str,
        default="",
        help="Wireshark display filter string (e.g. 'tcp or udp', 'http', 'tls')",
    )
    parser.add_argument(
        "--simulate",
        "-s",
        action="store_true",
        help="Force simulation mode with synthetic network packet generation",
    )
    parser.add_argument(
        "--list-interfaces",
        "-l",
        action="store_true",
        help="List available network capture interfaces on host and exit",
    )
    args = parser.parse_args()

    if args.list_interfaces:
        wrapper = TSharkWrapper()
        if not wrapper.is_available():
            print("[Error] TShark executable not found on host. Please install Wireshark / TShark.")
            sys.exit(1)
        interfaces = wrapper.list_interfaces()
        print(f"Available capture interfaces ({len(interfaces)} found):")
        for iface in interfaces:
            print(f"  [{iface.index}] {iface.name} - {iface.description or 'No description'}")
        sys.exit(0)

    try:
        asyncio.run(
            run_network_dashboard(
                interface=args.interface,
                display_filter=args.filter,
                simulate=args.simulate,
            )
        )
    except KeyboardInterrupt:
        print("\n[Network Terminal] Closed gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
