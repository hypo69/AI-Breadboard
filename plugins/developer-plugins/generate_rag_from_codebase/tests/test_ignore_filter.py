# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Codebase Ignore & Secret Filter
# =============================================================================
# Description:
#   Unit tests for IgnoreFilter checking glob exclusion, .ragignore parsing,
#   and secret detection/redaction.
#
# File: test_ignore_filter.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
import pytest

from plugins.generate_rag_from_codebase.ignore_filter import IgnoreFilter


def test_ignore_standard_directories(tmp_path: Path):
    filter_instance = IgnoreFilter(
        base_dir=tmp_path,
        ignore_patterns=[".git/**", ".venv/**", "logs/**", "site/**", "SANDBOX/**"]
    )

    git_file = tmp_path / ".git" / "config"
    venv_file = tmp_path / ".venv" / "lib" / "site-packages" / "foo.py"
    logs_file = tmp_path / "logs" / "app.log"
    src_file = tmp_path / "src" / "ai" / "agent.py"

    assert filter_instance.is_ignored(git_file) is True
    assert filter_instance.is_ignored(venv_file) is True
    assert filter_instance.is_ignored(logs_file) is True
    assert filter_instance.is_ignored(src_file) is False


def test_secret_detection_and_redaction():
    text_with_openai_key = 'openai_key = "sk-abcdef12345678901234567890abcdef"'
    text_with_google_key = 'key = "AIzaSyD-1234567890123456789012345678901"'
    clean_text = 'def test_func():\n    return "hello world"'

    assert IgnoreFilter.contains_secrets(text_with_openai_key) is True
    assert IgnoreFilter.contains_secrets(text_with_google_key) is True
    assert IgnoreFilter.contains_secrets(clean_text) is False

    redacted = IgnoreFilter.redact_secrets(text_with_openai_key)
    assert "sk-abcdef" not in redacted
    assert "[REDACTED_SECRET]" in redacted
