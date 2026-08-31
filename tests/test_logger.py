# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for core/logger module
# =============================================================================
# Description:
#   Module contains tests for core/logger module. Checks formatting and logging functionality.
#
# File: test_logger.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Tests for core/logger module.

Comprehensive testing of JSON formatter and logger functionality."""

import pytest
import json
from unittest.mock import Mock
from pathlib import Path

class TestJsonFormatter:
    """Tests for JsonFormatter."""

    def test_format(self):
        """Test log message formatting.
        
        Verifies that JsonFormatter correctly formats log records as JSON.
        """
        from core.logger.logger import JsonFormatter
        
        formatter = JsonFormatter()
        
        record = Mock()
        record.levelname = "INFO"
        record.getMessage = Mock(return_value="Test message")
        record.pathname = "/test/path.py"
        record.lineno = 123
        record.funcName = "test_func"
        record.created = 1722687000.0  # float timestamp
        record.msecs = 123.0  # float for millisecond formatting
        record.exc_info = None  # Added: to prevent formatter failure

        
        result = formatter.format(record)
        
        assert isinstance(result, str)
        log_data = json.loads(result)
        assert log_data['levelname'] == 'INFO'
        assert log_data['message'] == 'Test message'

class TestLogger:
    """Tests for Logger class."""

    def test_logger_singleton(self):
        """Test logger singleton pattern.
        
        Verifies that logger instances are singletons.
        """
        from core.logger.logger import Logger
        
        logger1 = Logger()
        logger2 = Logger()
        
        assert logger1 is logger2

    def test_logger_methods(self):
        """Test logger methods exist.
        
        Verifies that all standard logging methods are available.
        """
        from core.logger.logger import Logger
        
        logger = Logger()
        
        # Check that methods exist
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')

    def test_logger_log(self):
        """Test logger functionality.
        
        Verifies that global logger instance is accessible.
        """
        from core.logger.logger import logger
        
        # Check that global logger is available
        assert logger is not None
        assert hasattr(logger, 'info')

class TestLogAnalyzer:
    """Tests for log_analyzer module."""

    def test_get_max_size_bytes(self):
        """Test retrieval of maximum log size.
        
        Verifies that max log size bytes calculation returns positive value.
        """
        from core.logger.log_analyzer import get_max_size_bytes
        
        result = get_max_size_bytes()
        
        assert result > 0
