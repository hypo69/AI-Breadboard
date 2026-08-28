# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/logger
# =============================================================================
# Описание:
#   Модуль содержит тесты для модуля логгера core/logger. Проверяет форматирование
#   логов в JSON-формате, поведение singleton-паттерна и основные методы логгера.
#   Обеспечивает покрытие ключевых функций логирования для стабильности системы.
#
# File: tests/test_logger.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты модуля core/logger
"""

import pytest
import json
from unittest.mock import Mock
from pathlib import Path


class TestJsonFormatter:
    """Тесты JsonFormatter."""

    def test_format(self):
        """Тест форматирования лога."""
        from core.logger.logger import JsonFormatter
        
        formatter = JsonFormatter()
        
        record = Mock()
        record.levelname = "INFO"
        record.getMessage = Mock(return_value="Test message")
        record.pathname = "/test/path.py"
        record.lineno = 123
        record.funcName = "test_func"
        record.created = 1722687000.0 # float
        record.msecs = 123.0 # float для форматирования мс
        record.exc_info = None # Добавлено: чтобы форматтер не падал


        
        result = formatter.format(record)
        
        assert isinstance(result, str)
        log_data = json.loads(result)
        assert log_data['levelname'] == 'INFO'
        assert log_data['message'] == 'Test message'


class TestLogger:
    """Тесты Logger."""

    def test_logger_singleton(self):
        """Тест синглтона логера."""
        from core.logger.logger import Logger
        
        logger1 = Logger()
        logger2 = Logger()
        
        assert logger1 is logger2

    def test_logger_methods(self):
        """Тест методов логера."""
        from core.logger.logger import Logger
        
        logger = Logger()
        
        # Проверка что методы существуют
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')

    def test_logger_log(self):
        """Тест логирования."""
        from core.logger.logger import logger
        
        # Проверка что глобальный logger доступен
        assert logger is not None
        assert hasattr(logger, 'info')


class TestLogAnalyzer:
    """Тесты log_analyzer.py."""

    def test_get_max_size_bytes(self):
        """Тест получения максимального размера лога."""
        from core.logger.log_analyzer import get_max_size_bytes
        
        result = get_max_size_bytes()
        
        assert result > 0
