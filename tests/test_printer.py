# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit tests for printer utility module
# =============================================================================
# Description:
#   Validates pretty printing, formatting, ANSI styling, and auto-detection
#   of JSON and arbitrary embedded JSON structures for console and logger output.
#
# File: test_printer.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for the printer and pretty formatting module.

Tests format detection for dicts, lists, JSON strings, arbitrary embedded JSON
blocks (<text> <JSON> <text>), and verifies integration with logger methods.
"""

import json
import pytest
from src.utils.printer import pformat, pprint, _color_text, TEXT_COLORS
from src.logger.logger import logger


class TestPrinterFormatting:
    """Tests for pformat function and JSON parsing."""

    def test_pformat_dict(self):
        """Test formatting of python dict."""
        data = {"hello": "world", "num": 42}
        result = pformat(data)
        assert '"hello": "world"' in result
        assert '"num": 42' in result

    def test_pformat_list(self):
        """Test formatting of python list."""
        data = ["apple", "banana", 123]
        result = pformat(data)
        assert '"apple"' in result
        assert "123" in result

    def test_pformat_json_string(self):
        """Test formatting of string containing raw JSON."""
        raw_json = '{"name":"Antigravity","status":"active"}'
        result = pformat(raw_json)
        assert '"name": "Antigravity"' in result
        assert '"status": "active"' in result
        assert "      " in result  # 6 spaces indentation from config.json

    def test_pformat_prefixed_json_string(self):
        """Test formatting of log string containing prefix followed by JSON."""
        msg = 'RAW WS MSG: {"stepUpdate":{"state":"STATE_RUNNING","stepIndex":1}}'
        result = pformat(msg)
        assert "RAW WS MSG:" in result
        assert '"stepUpdate": {' in result
        assert '"state": "STATE_RUNNING"' in result

    def test_pformat_embedded_json_sandwich(self):
        """Test formatting of <text> <JSON> <text> string."""
        msg = 'Starting task {"task_id": "abc123", "progress": 0.5} and continuing execution'
        result = pformat(msg)
        assert "Starting task" in result
        assert '"task_id": "abc123"' in result
        assert '"progress": 0.5' in result
        assert "and continuing execution" in result

    def test_pformat_multiple_embedded_json(self):
        """Test formatting with multiple JSON blocks in one string."""
        msg = 'Config: {"env": "prod"} with servers: ["srv-1", "srv-2"] ready.'
        result = pformat(msg)
        assert "Config:" in result
        assert '"env": "prod"' in result
        assert '"srv-1"' in result
        assert '"srv-2"' in result
        assert "ready." in result

    def test_pformat_none(self):
        """Test formatting of None."""
        result = pformat(None)
        assert "None" in result

    def test_pformat_colored(self):
        """Test applying ANSI colors to formatted text."""
        data = {"key": "value"}
        result = pformat(data, text_color="green")
        assert TEXT_COLORS["green"] in result

    def test_pprint_output(self, capsys):
        """Test pprint prints to stdout."""
        pprint({"test": 123}, text_color="white")
        captured = capsys.readouterr()
        assert '"test": 123' in captured.out


class TestLoggerPrinterIntegration:
    """Tests logger integration with automatic pretty printing."""

    def test_logger_info_with_json_string(self, capsys):
        """Test logging a JSON string auto-formats nicely."""
        json_msg = '{"event":"start","agent":"Antigravity"}'
        logger.info(json_msg)
        result = pformat(json_msg)
        assert '"event": "start"' in result
        assert '"agent": "Antigravity"' in result

    def test_logger_info_with_dict(self):
        """Test logging a dict object directly."""
        dict_msg = {"event": "login", "user_id": 999}
        logger.info(dict_msg)
        result = pformat(dict_msg)
        assert '"event": "login"' in result

    def test_logger_info_with_embedded_json(self):
        """Test logging an embedded JSON block in arbitrary text."""
        embedded_msg = 'User payload {"user": "alice", "action": "ping"} received from socket'
        logger.info(embedded_msg)
        result = pformat(embedded_msg)
        assert "User payload" in result
        assert '"user": "alice"' in result
        assert "received from socket" in result
