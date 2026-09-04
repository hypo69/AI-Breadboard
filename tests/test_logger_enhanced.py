# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Fixture for creating logger with temporary paths
# =============================================================================
# Description:
#   Comprehensive testing of all public functions and classes of core/logger module.
#
# File: test_logger_enhanced.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Enhanced logger module tests.

Tests for core logger module with temporary file handling and verification."""

import pytest
import os
import json
import logging
from pathlib import Path
from src.logger.logger import Logger

@pytest.fixture
def temp_logger(tmp_path):
    """Fixture for creating logger with temporary paths.
    
    Creates a logger instance configured with temporary directories
    for log file storage to ensure test isolation.
    """
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    # Initialize logger with temporary directory paths
    logger = Logger(
        info_log_path="info.log",
        debug_log_path="debug.log",
        errors_log_path="errors.log",
        json_log_path="log.json"
    )
    
    # Override logger paths with temporary paths for test isolation
    logger.log_files_path = log_dir
    logger.info_log_path = log_dir / "info.log"
    logger.debug_log_path = log_dir / "debug.log"
    logger.errors_log_path = log_dir / "errors.log"
    logger.json_log_path = log_dir / "log.json"
    
    # Recreate handlers for new paths
    for logger_obj in [logger.logger_file_info, logger.logger_file_debug, logger.logger_file_errors, logger.logger_file_json]:
        for handler in logger_obj.handlers[:]:
            logger_obj.removeHandler(handler)
            
    # Add new handlers with temporary paths
    info_handler = logging.FileHandler(logger.info_log_path, encoding='utf-8')
    info_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.logger_file_info.addHandler(info_handler)
    
    debug_handler = logging.FileHandler(logger.debug_log_path, encoding='utf-8')
    debug_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.logger_file_debug.addHandler(debug_handler)
    
    errors_handler = logging.FileHandler(logger.errors_log_path, encoding='utf-8')
    errors_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.logger_file_errors.addHandler(errors_handler)
    
    from src.logger.logger import JsonFormatter
    json_handler = logging.FileHandler(logger.json_log_path, encoding='utf-8')
    json_handler.setFormatter(JsonFormatter())
    logger.logger_file_json.addHandler(json_handler)

    return logger

def test_logger_file_writing(temp_logger):
    """Test writing logs to files.
    
    Verifies that log messages are correctly written to the info log file.
    """
    # --- Arrange ---
    message: str = "Test info message"
    
    # --- Act ---
    temp_logger.info(message)
    
    # --- Assert ---
    # Check that info.log file was created and contains the message
    assert temp_logger.info_log_path.exists(), "info.log file was not created"
    with open(temp_logger.info_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert message in content, f"Message '{message}' not found in info.log, got: {content}"

def test_logger_json_writing(temp_logger):
    """Test writing logs to JSON file.
    
    Verifies that log entries are correctly serialized in JSON format.
    """
    # --- Arrange ---
    message: str = "Test JSON message"
    
    # --- Act ---
    temp_logger.info(message)
    
    # --- Assert ---
    assert temp_logger.json_log_path.exists(), "log.json file was not created"
    with open(temp_logger.json_log_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        log_data = json.loads(line)
        assert log_data['message'] == message, f"JSON message mismatch: {log_data['message']}"

def test_logger_debug_filter(temp_logger):
    """Test DEBUG level filtering in PROD mode (is_debug_mode=False).
    
    Verifies that debug messages are not logged when debug mode is disabled.
    """
    # --- Arrange ---
    temp_logger.is_debug_mode = False
    message: str = "Debug message"
    
    # --- Act ---
    temp_logger.debug(message)
    
    # --- Assert ---
    # Check that message was not added to debug.log
    with open(temp_logger.debug_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert message not in content, "DEBUG message was logged in PROD mode"
