# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests Telemetry - Test Process Token Collector
# =============================================================================
# Description:
#   Тест проверяет, что collector возвращает список ProcessTokenInfo с ожидаемыми полями.
#
# Usage Examples:
#   Python API:
#     from tests.telemetry.test_process_token_collector import test_collect_returns_token_info
#
#     res = test_collect_returns_token_info()
#
# File: test_process_token_collector.py
# Project: ai-breadboard
# Package: tests.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Тест проверяет, что collector возвращает список ProcessTokenInfo с ожидаемыми полями."""

import pytest
from unittest import mock

# Импортируем нужные классы
from apps.windows.telemetry.process_token_collector import ProcessTokenCollector, ProcessTokenInfo


def test_collect_returns_token_info(monkeypatch):
    """Тест проверяет, что collector возвращает список ProcessTokenInfo с ожидаемыми полями.
    Мы мокируем внешние зависимости: psutil, ctypes и функции получения информации о токене.
    """
    # --- Мок psutil.process_iter -------------------------------------------------
    mock_proc = mock.Mock()
    mock_proc.info = {"pid": 1234, "name": "test.exe"}
    monkeypatch.setattr("psutil.process_iter", lambda attrs=None: [mock_proc])

    # --- Мок ctypes.windll ------------------------------------------------------
    class DummyHandle:
        def __init__(self):
            self.handle = 1
    dummy_ctypes = mock.Mock()
    dummy_ctypes.windll.kernel32.OpenProcess.return_value = 1
    dummy_ctypes.windll.kernel32.CloseHandle.return_value = None
    # Подменяем модуль ctypes внутри process_token_collector
    monkeypatch.setattr(
        "apps.windows.telemetry.process_token_collector.ctypes",
        dummy_ctypes,
    )

    # --- Мок функций получения токен‑информации -------------------------------
    monkeypatch.setattr(
        "apps.windows.telemetry.process_token_collector._get_token_elevation",
        lambda token: True,
    )
    monkeypatch.setattr(
        "apps.windows.telemetry.process_token_collector._get_integrity_level",
        lambda token: "Medium",
    )

    collector = ProcessTokenCollector()
    result = collector.collect()

    # Проверяем тип и содержимое результата
    assert isinstance(result, list)
    assert len(result) == 1
    token_info = result[0]
    assert isinstance(token_info, ProcessTokenInfo)
    assert token_info.pid == 1234
    assert token_info.name == "test.exe"
    assert token_info.elevation is True
    assert token_info.integrity_level == "Medium"
