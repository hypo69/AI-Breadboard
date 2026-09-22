# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network traffic analysis and statistics aggregation
# =============================================================================
# Description:
#   Computes traffic flow metrics, protocol breakdown, talker summaries,
#   and heuristic rule checks across network packets.
#
# Examples:
#   >>> from src.network.analyzer import TrafficAnalyzer
#   >>> analyzer = TrafficAnalyzer()
#   >>> stats = analyzer.compute_stats(packets)
#
# File: analyzer.py
# Project: ai-breadboard
# Package: src.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Network traffic analyzer and statistical aggregator."""

from collections import Counter
from typing import List, Dict, Any

from .models import PacketSummary, TrafficStats


class TrafficAnalyzer:
    """Traffic metrics and flow pattern analysis engine."""

    def compute_stats(self, packets: List[PacketSummary]) -> TrafficStats:
        """Compute aggregated statistics across a list of packets.

        Args:
            packets (List[PacketSummary]): List of decoded packet summaries.

        Returns:
            TrafficStats: Aggregated metrics object.
        """
        if not packets:
            return TrafficStats()

        total_bytes = sum(pkt.length for pkt in packets)
        proto_counter: Counter[str] = Counter()
        src_counter: Counter[str] = Counter()
        dst_counter: Counter[str] = Counter()
        port_counter: Counter[int] = Counter()

        for pkt in packets:
            proto_counter[pkt.protocol] += 1
            if pkt.source_ip:
                src_counter[pkt.source_ip] += 1
            if pkt.destination_ip:
                dst_counter[pkt.destination_ip] += 1

            # Extract ports if available in TCP/UDP layers
            tcp_layer = pkt.raw_layers.get("tcp", {})
            udp_layer = pkt.raw_layers.get("udp", {})
            
            src_port = tcp_layer.get("tcp.srcport") or udp_layer.get("udp.srcport")
            dst_port = tcp_layer.get("tcp.dstport") or udp_layer.get("udp.dstport")
            
            if src_port:
                try:
                    port_counter[int(src_port)] += 1
                except (ValueError, TypeError):
                    pass
            if dst_port:
                try:
                    port_counter[int(dst_port)] += 1
                except (ValueError, TypeError):
                    pass

        return TrafficStats(
            total_packets=len(packets),
            total_bytes=total_bytes,
            protocol_distribution=dict(proto_counter.most_common(10)),
            top_sources=dict(src_counter.most_common(10)),
            top_destinations=dict(dst_counter.most_common(10)),
            top_ports={str(k): v for k, v in port_counter.most_common(10)},
        )

    def detect_heuristics(self, packets: List[PacketSummary]) -> List[str]:
        """Perform heuristic inspection to identify potential network issues or port scans.

        Args:
            packets (List[PacketSummary]): List of packets to inspect.

        Returns:
            List[str]: List of identified warnings and heuristics findings.
        """
        findings: List[str] = []
        if not packets:
            return findings

        # Check for port scan behavior (one source connecting to many distinct ports)
        src_to_ports: Dict[str, set] = {}
        for pkt in packets:
            tcp = pkt.raw_layers.get("tcp", {})
            dst_port = tcp.get("tcp.dstport")
            if pkt.source_ip and dst_port:
                if pkt.source_ip not in src_to_ports:
                    src_to_ports[pkt.source_ip] = set()
                src_to_ports[pkt.source_ip].add(dst_port)

        for src, ports in src_to_ports.items():
            if len(ports) >= 20:
                findings.append(f"Potential port scan detected from source {src}: contacted {len(ports)} distinct ports.")

        # Check for high DNS request volume / potential DNS tunneling
        dns_packets = [p for p in packets if "DNS" in p.protocol.upper()]
        if len(dns_packets) > 100:
            findings.append(f"High volume of DNS queries detected ({len(dns_packets)} packets). Check for DNS tunneling or amplification.")

        return findings
