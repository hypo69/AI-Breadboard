# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit testing for Network traffic and TShark wrapper module
# =============================================================================
# Description:
#   Comprehensive unit tests for TSharkWrapper, TrafficAnalyzer, and AIDetector
#   covering packet normalization, statistics computation, heuristics detection,
#   and fallback behavior.
#
# Examples:
#   pytest tests/test_network.py
#
# File: test_network.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for src.network module."""

import unittest
from unittest.mock import MagicMock, patch
from src.network.models import NetworkInterface, PacketSummary, CaptureFilter, TrafficStats, AnomalyReport
from src.network.tshark_wrapper import TSharkWrapper
from src.network.analyzer import TrafficAnalyzer
from src.network.ai_detector import AIDetector


class TestNetworkModule(unittest.IsolatedAsyncioTestCase):
    """Scenario-based test suite for Network analysis module."""

    def setUp(self) -> None:
        """Arrange common test fixture data."""
        self.wrapper = TSharkWrapper(tshark_path="")
        self.analyzer = TrafficAnalyzer()
        self.ai_detector = AIDetector()

        # Sample mock TShark JSON packet
        self.sample_raw_pkt = {
            "_source": {
                "layers": {
                    "frame": {
                        "frame.number": "1",
                        "frame.time": "Sep 12, 2026 21:00:00.000",
                        "frame.len": "128",
                    },
                    "eth": {
                        "eth.src": "00:11:22:33:44:55",
                        "eth.dst": "66:77:88:99:aa:bb",
                    },
                    "ip": {
                        "ip.src": "192.168.1.50",
                        "ip.dst": "1.1.1.1",
                    },
                    "tcp": {
                        "tcp.srcport": "54321",
                        "tcp.dstport": "443",
                    },
                }
            }
        }

    def test_parse_json_packet_happy_path(self) -> None:
        """Test parsing valid TShark JSON packet structure."""
        # Act
        parsed = self.wrapper.parse_json_packet(self.sample_raw_pkt)

        # Assert
        self.assertEqual(parsed.number, 1, "Packet frame number mismatch")
        self.assertEqual(parsed.source_ip, "192.168.1.50", "Source IP mismatch")
        self.assertEqual(parsed.destination_ip, "1.1.1.1", "Destination IP mismatch")
        self.assertEqual(parsed.protocol, "TCP", "Protocol extraction mismatch")
        self.assertEqual(parsed.length, 128, "Frame length mismatch")

    def test_parse_json_packet_empty_layers(self) -> None:
        """Test edge case with empty layers dictionary."""
        # Act
        parsed = self.wrapper.parse_json_packet({})

        # Assert
        self.assertEqual(parsed.number, 0)
        self.assertEqual(parsed.protocol, "UNKNOWN")
        self.assertEqual(parsed.source_ip, "unknown")

    def test_compute_stats_happy_path(self) -> None:
        """Test traffic statistics calculation across packet list."""
        # Arrange
        p1 = self.wrapper.parse_json_packet(self.sample_raw_pkt)
        p2 = PacketSummary(
            number=2,
            timestamp="",
            source_ip="192.168.1.50",
            destination_ip="8.8.8.8",
            protocol="DNS",
            length=64,
            info="DNS query",
            raw_layers={"udp": {"udp.srcport": "12345", "udp.dstport": "53"}},
        )

        # Act
        stats = self.analyzer.compute_stats([p1, p2])

        # Assert
        self.assertEqual(stats.total_packets, 2, "Expected 2 total packets")
        self.assertEqual(stats.total_bytes, 192, "Expected 192 total bytes")
        self.assertEqual(stats.protocol_distribution.get("TCP"), 1)
        self.assertEqual(stats.protocol_distribution.get("DNS"), 1)
        self.assertEqual(stats.top_sources.get("192.168.1.50"), 2)

    def test_compute_stats_empty_list(self) -> None:
        """Test stats computation with empty packet list."""
        stats = self.analyzer.compute_stats([])
        self.assertEqual(stats.total_packets, 0)
        self.assertEqual(stats.total_bytes, 0)

    def test_detect_heuristics_port_scan(self) -> None:
        """Test detection of port scan pattern when source touches multiple ports."""
        # Arrange: create 25 packets from one source to 25 different destination ports
        packets = []
        for port in range(1, 26):
            pkt = PacketSummary(
                number=port,
                source_ip="10.0.0.99",
                destination_ip="10.0.0.1",
                protocol="TCP",
                length=60,
                raw_layers={"tcp": {"tcp.dstport": str(port)}},
            )
            packets.append(pkt)

        # Act
        findings = self.analyzer.detect_heuristics(packets)

        # Assert
        self.assertTrue(any("port scan" in f.lower() for f in findings), "Expected port scan finding")

    async def test_ai_detector_fallback(self) -> None:
        """Test AI detector fallback to heuristics when AI router is unmocked or unavailable."""
        stats = TrafficStats(total_packets=10, total_bytes=1000)
        report = await self.ai_detector.diagnose_traffic([], stats, ["Suspicious payload detected"])

        self.assertEqual(report.threat_level, "medium")
        self.assertIn("Suspicious payload detected", report.findings)


if __name__ == "__main__":
    unittest.main()
