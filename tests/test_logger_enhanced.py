# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Logger Enhanced
# =============================================================================
# Description:
#   Enhanced logger module tests.
#
# Usage Examples:
#   Python API:
#     from tests.test_logger_enhanced import temp_logger
#
#     res = temp_logger()
#
# File: test_logger_enhanced.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Enhanced logger module tests.

Tests for core logger module with temporary file handling and verification."""

import pytest
import os
import json
import logging
from pathlib import Path
from logger import Logger

@pytest.fixture
def temp_logger(tmp_path):
    """Fixture for creating logger with temporary paths.
    
    Creates a logger instance configured with temporary directories
    for log file storage to ensure test isolation.
    """
    log_dir = tmp_path / 'test_logs'
    log_dir.mkdir()
    logger = Logger(info_log_path='info.log', debug_log_path='debug.log', errors_log_path='errors.log', json_log_path='log.json')
    logger.log_files_path = log_dir
    logger.info_log_path = log_dir / 'info.log'
    logger.debug_log_path = log_dir / 'debug.log'
    logger.errors_log_path = log_dir / 'errors.log'
    logger.json_log_path = log_dir / 'log.json'
    for logger_obj in [logger.logger_file_info, logger.logger_file_debug, logger.logger_file_errors, logger.logger_file_json]:
        for handler in logger_obj.handlers[:]:
            logger_obj.removeHandler(handler)
    info_handler = logging.FileHandler(logger.info_log_path, encoding='utf-8')
    info_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.logger_file_info.addHandler(info_handler)
    debug_handler = logging.FileHandler(logger.debug_log_path, encoding='utf-8')
    debug_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.logger_file_debug.addHandler(debug_handler)
    errors_handler = logging.FileHandler(logger.errors_log_path, encoding='utf-8')
    errors_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.logger_file_errors.addHandler(errors_handler)
    from logger import JsonFormatter
    json_handler = logging.FileHandler(logger.json_log_path, encoding='utf-8')
    json_handler.setFormatter(JsonFormatter())
    logger.logger_file_json.addHandler(json_handler)
    return logger

def test_logger_file_writing(temp_logger):
    """Test writing logs to files.
    
    Verifies that log messages are correctly written to the info log file.
    """
    message: str = 'Test info message'
    temp_logger.info(message)
    assert temp_logger.info_log_path.exists(), 'info.log file was not created'
    with open(temp_logger.info_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert message in content, f"Message '{message}' not found in info.log, got: {content}"

def test_logger_json_writing(temp_logger):
    """Test writing logs to JSON file.
    
    Verifies that log entries are correctly serialized in JSON format.
    """
    message: str = 'Test JSON message'
    temp_logger.info(message)
    assert temp_logger.json_log_path.exists(), 'log.json file was not created'
    with open(temp_logger.json_log_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        log_data = json.loads(line)
        assert log_data['message'] == message, f"JSON message mismatch: {log_data['message']}"

def test_logger_debug_filter(temp_logger):
    """Test DEBUG level filtering in PROD mode (is_debug_mode=False).
    
    Verifies that debug messages are not logged when debug mode is disabled.
    """
    temp_logger.is_debug_mode = False
    message: str = 'Debug message'
    temp_logger.debug(message)
    with open(temp_logger.debug_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert message not in content, 'DEBUG message was logged in PROD mode'