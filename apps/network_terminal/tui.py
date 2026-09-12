# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Analyzer Terminal Rich TUI Dashboard
# =============================================================================
# Description:
#   Interactive Rich TUI dashboard for deep packet inspection, live traffic
#   statistics, protocol distribution, and AI security anomaly detection.
#
# Examples:
#   >>> await run_network_dashboard(interface="1", display_filter="tcp or udp")
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.network_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Rich TUI dashboard renderer and live capture loop for Network Terminal."""

from __future__ import annotations

import asyncio
import sys
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, List, Optional

from src.logger import logger
from src.network import (
    AIDetector,
    AnomalyReport,
    CaptureFilter,
    NetworkInterface,
    PacketSummary,
    TSharkWrapper,
    TrafficAnalyzer,
    TrafficStats,
)

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


class NetworkTerminalState:
    """State management for live network terminal dashboard."""

    def __init__(
        self,
        interface: str = "1",
        display_filter: str = "",
        max_buffer_packets: int = 50,
    ) -> None:
        """Initialize network terminal session state.

        Args:
            interface (str): Capture interface name or index.
            display_filter (str): Wireshark display filter string.
            max_buffer_packets (int): Maximum retained packets in sliding window.
        """
        self.interface: str = interface
        self.display_filter: str = display_filter
        self.wrapper: TSharkWrapper = TSharkWrapper()
        self.analyzer: TrafficAnalyzer = TrafficAnalyzer()
        self.ai_detector: AIDetector = AIDetector()

        self.packet_buffer: Deque[PacketSummary] = deque(maxlen=max_buffer_packets)
        self.total_packets_captured: int = 0
        self.total_bytes_captured: int = 0
        self.protocol_counts: dict[str, int] = {}
        self.latest_heuristics: List[str] = []
        self.latest_ai_report: Optional[AnomalyReport] = None
        self.status_msg: str = "Ready"
        self.start_time: float = time.time()

    def add_packet(self, packet: PacketSummary) -> None:
        """Process incoming live packet and update running stats.

        Args:
            packet (PacketSummary): Captured packet.
        """
        self.packet_buffer.append(packet)
        self.total_packets_captured += 1
        self.total_bytes_captured += packet.length
        proto = packet.protocol.upper()
        self.protocol_counts[proto] = self.protocol_counts.get(proto, 0) + 1

    def compute_stats(self) -> TrafficStats:
        """Compute rolling traffic statistics from current packet buffer."""
        return self.analyzer.compute_stats(list(self.packet_buffer))

    def evaluate_security(self) -> None:
        """Run heuristics evaluation over current sliding window."""
        self.latest_heuristics = self.analyzer.detect_heuristics(list(self.packet_buffer))


def render_ui(state: NetworkTerminalState) -> Any:
    """Render Rich dashboard layout for network monitoring.

    Args:
        state (NetworkTerminalState): Active terminal session state.

    Returns:
        Any: Rich terminal layout or None if Rich is unavailable.
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
        Layout(name="left", ratio=3),
        Layout(name="right", ratio=2),
    )

    layout["right"].split_column(
        Layout(name="stats", ratio=1),
        Layout(name="alerts", ratio=1),
    )

    # Header
    status_icon = "🟢" if state.wrapper.is_available() else "🔴"
    filter_str = f"Filter: '{state.display_filter}'" if state.display_filter else "Filter: ALL"
    header_text = Text(
        f" AI Breadboard — Network Terminal | Interface: {state.interface} | {filter_str} | Status: {status_icon} {state.status_msg} ",
        style="bold white on blue",
        justify="center",
    )
    layout["header"].update(Panel(header_text, style="blue"))

    # Live Packet Stream Table (Left)
    pkt_table = Table(title="Live Captured Packets (Sliding Window)", expand=True, show_edge=False)
    pkt_table.add_column("No", justify="right", style="cyan", width=5)
    pkt_table.add_column("Time", style="dim white", width=12)
    pkt_table.add_column("Source", style="green", width=18)
    pkt_table.add_column("Destination", style="yellow", width=18)
    pkt_table.add_column("Proto", style="bold magenta", width=8)
    pkt_table.add_column("Length", justify="right", style="cyan", width=8)
    pkt_table.add_column("Info", style="white")

    for pkt in list(state.packet_buffer)[-15:]:
        pkt_table.add_row(
            str(pkt.packet_number),
            pkt.timestamp.split("T")[-1].replace("Z", "")[:10] if "T" in pkt.timestamp else pkt.timestamp[:10],
            f"{pkt.source}:{pkt.source_port}" if pkt.source_port else pkt.source,
            f"{pkt.destination}:{pkt.destination_port}" if pkt.destination_port else pkt.destination,
            pkt.protocol,
            f"{pkt.length} B",
            (pkt.info or "")[:40],
        )

    layout["left"].update(Panel(pkt_table, title="[bold yellow]Deep Packet Inspection[/bold yellow]", border_style="cyan"))

    # Statistics & Protocol Distribution (Right Top)
    elapsed = max(1.0, time.time() - state.start_time)
    kb_rate = (state.total_bytes_captured / 1024.0) / elapsed
    pps_rate = state.total_packets_captured / elapsed

    stats_table = Table(show_header=False, expand=True)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="bold white")
    stats_table.add_row("Total Packets", f"{state.total_packets_captured:,}")
    stats_table.add_row("Total Bytes", f"{state.total_bytes_captured / 1024.0:,.1f} KB")
    stats_table.add_row("Capture Rate", f"{pps_rate:,.1f} pkt/s ({kb_rate:,.1f} KB/s)")

    # Top 3 Protocols
    sorted_protos = sorted(state.protocol_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    proto_summary = ", ".join(f"{k}: {v}" for k, v in sorted_protos) if sorted_protos else "None"
    stats_table.add_row("Top Protocols", proto_summary)

    layout["stats"].update(Panel(stats_table, title="[bold yellow]Bandwidth & Protocols[/bold yellow]", border_style="magenta"))

    # Security & Anomaly Alerts (Right Bottom)
    alert_lines: List[str] = []
    if state.latest_heuristics:
        for h in state.latest_heuristics[-3:]:
            alert_lines.append(f"[bold red]⚠️ {h}[/bold red]")
    else:
        alert_lines.append("[green]✓ No immediate heuristic security threats detected[/green]")

    if state.latest_ai_report:
        risk_color = "red" if state.latest_ai_report.threat_level == "CRITICAL" else ("yellow" if state.latest_ai_report.threat_level == "SUSPICIOUS" else "green")
        alert_lines.append(f"[{risk_color}]AI Threat Assessment: {state.latest_ai_report.threat_level}[/{risk_color}]")
        alert_lines.append(f"[dim]{state.latest_ai_report.summary[:80]}...[/dim]")

    alerts_panel = Panel(Text.from_markup("\n".join(alert_lines)), title="[bold yellow]AI & Security Diagnostics[/bold yellow]", border_style="red" if state.latest_heuristics else "green")
    layout["alerts"].update(alerts_panel)

    # Footer
    footer_text = Text(
        " Controls: [Ctrl+C] Stop & Exit | [API] Mounts at /api/v1/network/ws/live ",
        style="bold black on white",
        justify="center",
    )
    layout["footer"].update(Panel(footer_text))

    return layout


async def run_network_dashboard(
    interface: str = "1",
    display_filter: str = "",
    simulate: bool = False,
) -> None:
    """Run interactive async Network Terminal dashboard.

    Args:
        interface (str): Network capture interface index or name.
        display_filter (str): Capture display filter expression.
        simulate (bool): When True, generates simulated traffic if TShark is absent.
    """
    state = NetworkTerminalState(interface=interface, display_filter=display_filter)

    if not RICH_AVAILABLE:
        print(f"[Network Terminal] Running simplified console mode (rich not installed)")
        print(f"Interface: {interface} | Filter: {display_filter}")
        return

    console = Console()

    # Verify TShark availability
    if not state.wrapper.is_available() and not simulate:
        console.print("[bold yellow][Network Terminal][/bold yellow] TShark executable not found. Running in demo/simulation mode.")
        simulate = True

    with Live(render_ui(state), refresh_per_second=4, screen=True) as live:
        try:
            if simulate:
                # Simulated packet generator loop
                counter = 0
                protocols = ["TCP", "UDP", "TLS", "HTTP", "DNS", "ICMP"]
                ips = ["192.168.1.15", "142.250.180.206", "10.0.0.1", "1.1.1.1", "8.8.8.8"]
                while True:
                    counter += 1
                    proto = protocols[counter % len(protocols)]
                    pkt = PacketSummary(
                        packet_number=counter,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        source=ips[counter % len(ips)],
                        destination=ips[(counter + 1) % len(ips)],
                        protocol=proto,
                        length=128 + (counter % 512),
                        source_port=443 if proto in ("TLS", "HTTP") else (53 if proto == "DNS" else 1024 + counter),
                        destination_port=52000,
                        info=f"Simulated {proto} transmission flow payload #{counter}",
                    )
                    state.add_packet(pkt)
                    if counter % 10 == 0:
                        state.evaluate_security()

                    state.status_msg = f"Streaming (Simulated, #{counter})"
                    live.update(render_ui(state))
                    await asyncio.sleep(0.2)

            else:
                # Real live capture stream from TShark
                cap_filter = CaptureFilter(interface=interface, display_filter=display_filter)
                state.status_msg = "Capturing (Live TShark)"

                async for pkt in state.wrapper.live_capture_stream(cap_filter):
                    state.add_packet(pkt)
                    if state.total_packets_captured % 10 == 0:
                        state.evaluate_security()
                    live.update(render_ui(state))

        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
