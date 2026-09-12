# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Terminal Rich TUI Dashboard
# =============================================================================
# Description:
#   Rich terminal user interface renderer for the trading desk. Renders
#   market overview, portfolio positions, L2 depth, and execution event logs.
#
# Examples:
#   >>> await run_dashboard(symbol="BTC/USDT", interval=0.5)
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.trading_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Rich TUI dashboard renderer and event loop for trading desk."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Optional

from .engine import TradingDeskEngine

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    Console = Any  # type: ignore
    Layout = Any  # type: ignore
    Live = Any  # type: ignore
    Panel = Any  # type: ignore
    Table = Any  # type: ignore
    Text = Any  # type: ignore
    RICH_AVAILABLE = False


def render_ui(engine: TradingDeskEngine, console: Optional[Console] = None) -> Any:
    """Render terminal dashboard layout using rich panels and tables.

    Args:
        engine (TradingDeskEngine): Current state engine of the trading desk.
        console (Optional[Console]): Rich console instance.

    Returns:
        Any: Configured rich terminal layout or None.
    """
    if not RICH_AVAILABLE:
        return None
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1),
    )

    layout["left"].split_column(
        Layout(name="market", ratio=1),
        Layout(name="position", ratio=1),
    )

    layout["right"].split_column(
        Layout(name="orderbook", ratio=1),
        Layout(name="logs", ratio=1),
    )

    # Header
    header_text = Text(
        f" AI Breadboard — Exchange Control Desk | Symbol: {engine.symbol} | Status: ONLINE ",
        style="bold white on blue",
        justify="center",
    )
    layout["header"].update(Panel(header_text, style="blue"))

    # Market Panel
    pnl_color = "green" if engine.unrealized_pnl >= 0 else "red"
    market_table = Table(show_header=False, expand=True)
    market_table.add_column("Key", style="cyan")
    market_table.add_column("Val", style="bold white")
    market_table.add_row("Current Price", f"${engine.current_price:,.2f}")
    market_table.add_row("Account Balance", f"${engine.balance:,.2f}")
    market_table.add_row("Realized PnL", f"${engine.realized_pnl:+,.2f}")
    market_table.add_row("Unrealized PnL", f"[{pnl_color}]${engine.unrealized_pnl:+,.2f}[/{pnl_color}]")
    layout["market"].update(Panel(market_table, title="[bold yellow]Market Overview[/bold yellow]", border_style="cyan"))

    # Position Panel
    base_asset = engine.symbol.split("/")[0]
    pos_table = Table(show_header=False, expand=True)
    pos_table.add_column("Key", style="cyan")
    pos_table.add_column("Val", style="bold white")
    pos_table.add_row("Holding Size", f"{engine.position_size:.4f} {base_asset}")
    pos_table.add_row("Entry Price", f"${engine.entry_price:,.2f}" if engine.position_size > 0 else "N/A")
    pos_table.add_row(
        "Position Value",
        f"${(engine.position_size * engine.current_price):,.2f}",
    )
    total_eq = engine.balance + (engine.position_size * engine.current_price)
    pos_table.add_row("Total Equity", f"${total_eq:,.2f}")
    layout["position"].update(Panel(pos_table, title="[bold yellow]Portfolio & Position[/bold yellow]", border_style="cyan"))

    # Orderbook Simulation
    ob = engine.get_orderbook(depth=3)
    ob_table = Table(title="Live Depth (L2)", expand=True, show_edge=False)
    ob_table.add_column("Side", justify="center", style="bold")
    ob_table.add_column("Price", justify="right")
    ob_table.add_column("Size", justify="right")

    for ask_p, ask_s in ob["asks"]:
        ob_table.add_row("ASK", f"${ask_p:,.2f}", f"{ask_s:.3f}", style="red")
    for bid_p, bid_s in ob["bids"]:
        ob_table.add_row("BID", f"${bid_p:,.2f}", f"{bid_s:.3f}", style="green")

    layout["orderbook"].update(Panel(ob_table, title="[bold yellow]Order Book Depth[/bold yellow]", border_style="magenta"))

    # Logs Panel
    log_content = "\n".join(engine.logs[-6:])
    layout["logs"].update(Panel(Text(log_content, style="dim white"), title="[bold yellow]Execution Logs[/bold yellow]", border_style="green"))

    # Footer
    footer_text = Text(
        " Shortcuts: [B] Buy 0.05 | [S] Sell 0.05 | [K] Kill-Switch Close All | [Ctrl+C] Exit ",
        style="bold black on white",
        justify="center",
    )
    layout["footer"].update(Panel(footer_text))

    return layout


async def run_dashboard(
    symbol: str = "BTC/USDT",
    interval: float = 0.5,
    engine: Optional[TradingDeskEngine] = None,
) -> None:
    """Run interactive async trading dashboard.

    Args:
        symbol (str): Trading pair symbol.
        interval (float): Refresh interval in seconds.
        engine (Optional[TradingDeskEngine]): Optional pre-initialized engine instance.
    """
    if engine is None:
        engine = TradingDeskEngine(symbol=symbol)

    if not RICH_AVAILABLE:
        print(f"[Trading Desk] Running simplified mode for {symbol} (rich library not installed)")
        while True:
            engine.update_market()
            print(f"Price: ${engine.current_price:,.2f} | Balance: ${engine.balance:,.2f} | Pos: {engine.position_size}")
            time.sleep(2.0)

    console = Console()
    with Live(render_ui(engine, console), refresh_per_second=4, screen=True) as live:
        try:
            counter = 0
            while True:
                engine.update_market()
                counter += 1

                # Random simulated fills in demo mode
                if counter % 15 == 0 and random.random() > 0.6:
                    side = "BUY" if random.random() > 0.5 else "SELL"
                    engine.place_order(side, 0.02)

                live.update(render_ui(engine, console))
                await asyncio.sleep(interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
