# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing web-chat-cli argument parsing
# =============================================================================
# Description:
#   Unit tests for web-chat-cli argument parsing and configuration defaults.
#
# File: test_chat.py
# Project: ai-breadboard
# Package: .agents.skills.web-chat-cli.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Import chat dynamically relative to this test file
chat_file = Path(__file__).resolve().parents[1] / "src" / "chat.py"
spec = importlib.util.spec_from_file_location("chat", str(chat_file))
if spec and spec.loader:
    chat = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chat)
    parse_arguments = getattr(chat, "parse_arguments", None)
else:
    parse_arguments = None


def test_parse_arguments_default():
    """Test argument parsing with default parameters."""
    if parse_arguments is None:
        return
    test_args = ["chat.py"]
    with patch("sys.argv", test_args):
        args = parse_arguments()
    assert args.model == "gemini-1.5-flash", "Default model should be gemini-1.5-flash"


def test_parse_arguments_custom():
    """Test argument parsing with custom parameters."""
    if parse_arguments is None:
        return
    test_args = ["chat.py", "--model", "gemini-1.5-pro", "--debug"]
    with patch("sys.argv", test_args):
        args = parse_arguments()
    assert args.model == "gemini-1.5-pro", "Model should be updated to gemini-1.5-pro"
    assert args.debug is True, "Debug mode should be enabled"
