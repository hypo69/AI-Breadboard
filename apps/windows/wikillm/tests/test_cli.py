# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Cli
# =============================================================================
# Description:
#   Тесты для CLI интерфейса и конфигуратора WikiLLM.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_cli import test_config_defaults
#
#     res = test_config_defaults()
#
# File: test_cli.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для CLI интерфейса и конфигуратора WikiLLM."""

import argparse
from unittest.mock import AsyncMock, patch
import pytest
from apps.windows.wikillm.cli import _async_cli_main
from apps.windows.wikillm.config import WikiLLMConfig, load_config


def test_config_defaults() -> None:
    """Проверка загрузки конфигурации по умолчанию."""
    cfg = load_config(None)
    assert cfg.database_path == "data/windows_wikillm/knowledge.db"
    assert cfg.min_confidence_threshold == 0.70
    assert cfg.enable_semantic_search is True


@pytest.mark.asyncio
async def test_cli_search_and_stats(capsys: pytest.CaptureFixture) -> None:
    """Проверка команд search и stats в CLI."""
    args_stats = argparse.Namespace(command="stats")
    await _async_cli_main(args_stats)
    captured = capsys.readouterr()
    assert "lookup_stats" in captured.out

    args_search = argparse.Namespace(command="search", query="test", limit=5)
    await _async_cli_main(args_search)
    captured = capsys.readouterr()
    assert "Найдено результатов" in captured.out


@pytest.mark.asyncio
async def test_cli_index_code(capsys: pytest.CaptureFixture) -> None:
    """Проверка команды index-code в CLI."""
    args = argparse.Namespace(command="index-code", path="apps/windows/wikillm")
    await _async_cli_main(args)
    captured = capsys.readouterr()
    assert "Успешно проиндексировано" in captured.out
