# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Terminal CLI Main Entry Point
# =============================================================================
# Description:
#   Executable module entry point for running the interactive trading desk TUI.
#
# Examples:
#   $ python -m apps.trading_terminal --symbol BTC/USDT --interval 0.5
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.trading_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for the trading terminal dashboard."""

import argparse
import asyncio
import sys

from .tui import run_dashboard


def main() -> None:
    """Parse CLI arguments and launch interactive trading dashboard."""
    parser = argparse.ArgumentParser(description="AI Breadboard Exchange Trading Terminal")
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/USDT",
        help="Trading pair symbol (e.g. BTC/USDT, ETH/USDT, SOL/USDT)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Dashboard refresh interval in seconds",
    )
    parser.add_argument(
        "--balance",
        type=float,
        default=10000.0,
        help="Initial simulated starting account balance in USD",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_dashboard(symbol=args.symbol, interval=args.interval))
    except KeyboardInterrupt:
        print("\n[Trading Terminal] Closed gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
