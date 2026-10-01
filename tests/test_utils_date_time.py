# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils Date Time
# =============================================================================
# Description:
#   Tests for core/utils/date_time.py module
#
# Usage Examples:
#   Python API:
#     from tests.test_utils_date_time import TestTimeoutCheckInterval
#
#     service = TestTimeoutCheckInterval()
#
# File: test_utils_date_time.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Tests for core/utils/date_time.py module"""

import pytest
from datetime import time
from unittest.mock import patch, Mock
from src.utils.date_time import TimeoutCheck

class TestTimeoutCheckInterval:
    """Tests for interval method."""

    def test_interval_same_day_morning(self):
        """Test interval within one day (morning)."""
        checker = TimeoutCheck()
        with patch('src.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 30)
            checker.interval(start=time(8, 0), end=time(17, 0))
            assert checker.result is True

    def test_interval_same_day_outside(self):
        """Test interval outside time window (same day)."""
        checker = TimeoutCheck()
        with patch('src.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(3, 0)
            checker.interval(start=time(8, 0), end=time(17, 0))
            assert checker.result is False

    def test_interval_crosses_midnight(self):
        """Test interval crossing midnight."""
        checker = TimeoutCheck()
        with patch('src.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(1, 0)
            checker.interval(start=time(23, 0), end=time(6, 0))
            assert checker.result is True

    def test_interval_crosses_midnight_outside(self):
        """Test interval outside time window (crossing midnight)."""
        checker = TimeoutCheck()
        with patch('src.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(12, 0)
            checker.interval(start=time(23, 0), end=time(6, 0))
            assert checker.result is False

    def test_interval_exact_start(self):
        """Test exact start time."""
        checker = TimeoutCheck()
        with patch('src.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(23, 0)
            checker.interval(start=time(23, 0), end=time(6, 0))
            assert checker.result is True