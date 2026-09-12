# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Log Analyzer Skill
# =============================================================================
# Description:
#   Validates log parsing, error clustering, signature normalization,
#   and report formatting in the log-analyzer skill package.
#
# File: test_skill_log_analyzer.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for log-analyzer skill."""

import sys
from pathlib import Path
import pytest

# Ensure skill directory is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = PROJECT_ROOT / ".agents" / "skills" / "log-analyzer" / "scripts"

if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from analyze import LogParser, LogAnalyzer, LogEntry, format_markdown_report


def test_parse_text_logs():
    """Verify parsing standard plaintext logs into LogEntry structures."""
    sample_text = (
        "2026-09-08 12:00:00 [INFO] [server] Application startup complete\n"
        "2026-09-08 12:00:05 [WARNING] [db] Connection pool low\n"
        "2026-09-08 12:00:10 [ERROR] [api] Failed to connect to 192.168.1.1:8080\n"
        "Traceback (most recent call last):\n"
        "  File 'main.py', line 42, in run\n"
        "ConnectionRefusedError: Connection refused\n"
    )

    parser = LogParser()
    entries = parser.parse_text(sample_text)

    assert len(entries) == 3
    assert entries[0].level == "INFO"
    assert entries[0].message == "Application startup complete"

    assert entries[1].level == "WARNING"
    assert entries[1].source == "db"

    assert entries[2].level == "ERROR"
    assert "ConnectionRefusedError" in entries[2].traceback


def test_parse_json_lines_logs():
    """Verify parsing JSON Lines log streams."""
    sample_json = (
        '{"timestamp": "2026-09-08T12:00:00Z", "level": "INFO", "message": "Ready"}\n'
        '{"timestamp": "2026-09-08T12:00:01Z", "level": "ERROR", "message": "Failed auth at 0x7fff", "exc_info": "AuthError"}\n'
    )

    parser = LogParser()
    entries = parser.parse_json_lines(sample_json)

    assert len(entries) == 2
    assert entries[0].level == "INFO"
    assert entries[1].level == "ERROR"
    assert entries[1].traceback == "AuthError"


def test_log_analyzer_clustering():
    """Verify error clustering and signature normalization."""
    parser = LogParser()
    analyzer = LogAnalyzer(parser)

    entries = [
        LogEntry(level="INFO", message="Normal operation"),
        LogEntry(level="ERROR", message="Failed socket to 0x7ffe1234 on port 8080"),
        LogEntry(level="ERROR", message="Failed socket to 0x8ffa5678 on port 9090"),
        LogEntry(level="WARNING", message="Slow response 500ms"),
    ]

    result = analyzer.analyze_entries(entries)

    assert result.total_events == 4
    assert result.level_counts.get("ERROR") == 2
    assert result.level_counts.get("INFO") == 1
    assert result.level_counts.get("WARNING") == 1

    # Both errors should cluster into 1 normalized signature: "Failed socket to 0x... on port <N>"
    assert len(result.top_errors) == 1
    assert result.top_errors[0]["count"] == 2


def test_markdown_report_generation():
    """Verify formatting of markdown report."""
    parser = LogParser()
    analyzer = LogAnalyzer(parser)

    entries = [
        LogEntry(timestamp="2026-09-08 10:00:00", level="INFO", message="Boot"),
        LogEntry(timestamp="2026-09-08 10:05:00", level="ERROR", message="Crash"),
    ]

    result = analyzer.analyze_entries(entries)
    report = format_markdown_report(result, target_name="TestLog")

    assert "# 📊 Log Analysis Report: `TestLog`" in report
    assert "Total Events:** 2" in report
    assert "🔴 **ERROR:** 1" in report
