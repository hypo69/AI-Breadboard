# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Cloudflared Monitor State & Core Logic
# =============================================================================
# Description:
#   Unit tests for CloudflaredState, process inspection, log parsing, endpoint
#   probing, and AI diagnostic heuristics in apps/cloudflared_monitor/src/state.py.
#
# File: test_cloudflared_monitor.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for Cloudflared Monitor state engine and diagnostics."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from apps.cloudflared_monitor.src.state import (
    CloudflaredAnomaly,
    CloudflaredDiagnosticReport,
    CloudflaredLogEntry,
    CloudflaredProcessInfo,
    CloudflaredState,
    EndpointHealth,
)


class TestCloudflaredState(unittest.TestCase):
    """Test suite for CloudflaredState engine."""

    def setUp(self):
        """Set up test sandbox and mock paths."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.log_file = self.project_root / "logs" / "cloudflared.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.state = CloudflaredState(
            project_root=self.project_root,
            public_url="https://test.example.com",
            log_file_rel="logs/cloudflared.log",
        )

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_initial_state(self):
        """Test default values of freshly instantiated CloudflaredState."""
        self.assertFalse(self.state.process.is_running)
        self.assertEqual(self.state.public_url, "https://test.example.com")
        self.assertEqual(len(self.state.logs), 0)
        self.assertEqual(self.state.total_errors_in_log, 0)

    def test_parse_log_line_standard_iso(self):
        """Test log parsing with ISO timestamps and level indicators."""
        line = "2026-09-13T03:40:00Z ERR Connection lost with edge server connIndex=0"
        entry = self.state.parse_log_line(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.level, "ERROR")
        self.assertEqual(entry.connection_id, "0")
        self.assertIn("Connection lost", entry.message)

    def test_parse_log_line_info(self):
        """Test parsing info log line."""
        line = "2026-09-13T03:40:05Z INF Registered tunnel connection connIndex=1 location=FRA"
        entry = self.state.parse_log_line(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.level, "INFO")
        self.assertEqual(entry.connection_id, "1")

    def test_parse_log_line_empty(self):
        """Test that empty or whitespace lines return None."""
        self.assertIsNone(self.state.parse_log_line(""))
        self.assertIsNone(self.state.parse_log_line("   \n"))

    def test_tail_logs(self):
        """Test tailing and error count calculation from log file."""
        log_content = (
            "2026-09-13T03:40:00Z INF Starting tunnel\n"
            "2026-09-13T03:40:01Z INF Registered tunnel connection connIndex=0\n"
            "2026-09-13T03:40:02Z WRN High latency to origin\n"
            "2026-09-13T03:40:03Z ERR Failed to proxy request connIndex=0\n"
        )
        self.log_file.write_text(log_content, encoding="utf-8")

        entries = self.state.tail_logs(limit=10)
        self.assertEqual(len(entries), 4)
        self.assertEqual(self.state.total_errors_in_log, 1)
        self.assertEqual(self.state.total_warnings_in_log, 1)
        self.assertGreaterEqual(self.state.active_connections_count, 1)

    def test_check_token_missing(self):
        """Test token checking when .env has no token."""
        has_token = self.state.check_token()
        self.assertFalse(has_token)
        self.assertEqual(self.state.token_preview, "Missing")

    def test_check_token_present(self):
        """Test token checking with valid token in .env."""
        env_path = self.project_root / ".env"
        env_path.write_text("CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiMTIzNDU2Nzg5MCJ9\n", encoding="utf-8")

        has_token = self.state.check_token()
        self.assertTrue(has_token)
        self.assertTrue(self.state.token_preview.startswith("eyJ"))

    def test_evaluate_diagnostics_healthy(self):
        """Test diagnostic evaluation for a healthy tunnel state."""
        self.state.exe_path = "C:/mock/cloudflared.exe"
        self.state.has_token = True
        self.state.process = CloudflaredProcessInfo(
            is_running=True, pid=1234, cpu_percent=2.5, memory_mb=45.0
        )
        self.state.endpoint = EndpointHealth(
            url="https://test.example.com",
            is_reachable=True,
            status_code=200,
            response_time_ms=85.0,
        )
        self.state.total_errors_in_log = 0

        report = self.state.evaluate_diagnostics()
        self.assertEqual(report.status, "HEALTHY")
        self.assertGreaterEqual(report.health_score, 90)
        self.assertEqual(len(report.anomalies), 0)

    def test_evaluate_diagnostics_unhealthy(self):
        """Test diagnostic evaluation when process is dead and token missing."""
        self.state.exe_path = None
        self.state.has_token = False
        self.state.process = CloudflaredProcessInfo(is_running=False)
        self.state.endpoint = EndpointHealth(is_reachable=False)

        report = self.state.evaluate_diagnostics()
        self.assertIn(report.status, ("CRITICAL", "OFFLINE"))
        self.assertLess(report.health_score, 50)
        self.assertGreater(len(report.anomalies), 0)
        self.assertGreater(len(report.recommendations), 0)


if __name__ == "__main__":
    unittest.main()
