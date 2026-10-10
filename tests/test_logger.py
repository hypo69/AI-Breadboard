# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Logger
# =============================================================================
# Description:
#   Модульные тесты для пакета централизованного логирования logger.
#   Проверяет Singleton, JsonFormatter, методы логирования, получение
#   подсистемных логгеров и маршрутизацию по изолированным файлам.
#
# File: test_logger.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:17:00
# =============================================================================

"""Тесты для модуля централизованного логирования."""

import json
from pathlib import Path
from unittest.mock import Mock
import pytest


class TestJsonFormatter:
    """Тесты для JsonFormatter."""

    def test_format(self):
        """Проверка корректности сериализации записи в JSON."""
        from logger import JsonFormatter
        formatter = JsonFormatter()
        record = Mock()
        record.levelname = 'INFO'
        record.getMessage = Mock(return_value='Test message')
        record.pathname = '/test/path.py'
        record.lineno = 123
        record.funcName = 'test_func'
        record.created = 1722687000.0
        record.msecs = 123.0
        record.exc_info = None
        result = formatter.format(record)
        assert isinstance(result, str)
        log_data = json.loads(result)
        assert log_data['levelname'] == 'INFO'
        assert log_data['message'] == 'Test message'


class TestLogger:
    """Тесты для класса Logger."""

    def test_logger_singleton(self):
        """Проверка паттерна Singleton."""
        from logger import Logger
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2

    def test_logger_methods(self):
        """Проверка наличия всех стандартных методов логирования."""
        from logger import Logger
        logger = Logger()
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')
        assert hasattr(logger, 'success')
        assert hasattr(logger, 'get_subsystem_logger')

    def test_logger_log(self):
        """Проверка доступности глобального экземпляра logger."""
        from logger import logger
        assert logger is not None
        assert hasattr(logger, 'info')

    def test_get_subsystem_loggers(self):
        """Проверка получения специализированных логгеров подсистем."""
        from logger import logger, get_subsystem_logger
        for name in [
            'windows', 'telemetry', 'wikillm', 'rag', 'ai', 'trading', 'fastapi', 'skills',
            'gemini', 'gemini_cli', 'agy', 'agy_cli', 'ollama', 'openai', 'foundry', 'windows_ai', 'huggingface', 'onnx', 'voice'
        ]:
            sub_log = get_subsystem_logger(name)
            assert sub_log is not None
            assert hasattr(sub_log, 'info')
            assert hasattr(sub_log, 'error')

    def test_subsystem_logging_writes_file(self, tmp_path):
        """Проверка записи подсистемного лога в отдельный файл."""
        from logger import Logger
        test_logger = Logger()
        sub_log = test_logger.get_subsystem_logger('windows')
        test_msg = 'WINDOWS_SUBSYSTEM_TEST_EVENT_12345'
        sub_log.info(test_msg)

        win_file = test_logger.log_files_path / 'windows.log'
        assert win_file.exists()
        # Сброс буфера для проверки содержимого
        for h in sub_log.handlers:
            h.flush()
        with open(win_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            assert test_msg in content

    def test_ai_providers_write_discrete_files(self):
        """Проверка записи сообщений в изолированные файлы логов провайдеров ИИ."""
        from logger import get_subsystem_logger, logger
        providers = {
            'gemini': 'gemini.log',
            'gemini_cli': 'gemini_cli.log',
            'agy': 'agy.log',
            'agy_cli': 'agy_cli.log',
            'ollama': 'ollama.log',
            'openai': 'openai.log',
        }
        for alias, filename in providers.items():
            sub = get_subsystem_logger(alias)
            marker = f'TEST_MARKER_{alias.upper()}_LOG'
            sub.info(marker)
            for h in sub.handlers:
                h.flush()
            target_path = logger.log_files_path / filename
            assert target_path.exists(), f'Файл {filename} не был создан'
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                data = f.read()
                assert marker in data, f'Маркер {marker} не найден в {filename}'

    def test_uvicorn_log_config_and_access_logging(self, tmp_path):
        """Проверка конфигурации логирования uvicorn и отсутствия KeyError для client_addr."""
        import logging
        import logging.config
        from logger.logger import get_uvicorn_log_config

        log_file = 'test_uvicorn_access.log'
        cfg = get_uvicorn_log_config(log_file)
        assert 'formatters' in cfg
        assert 'file_access' in cfg['formatters']
        assert cfg['formatters']['file_access'].get('()') == 'uvicorn.logging.AccessFormatter'

        logging.config.dictConfig(cfg)
        access_logger = logging.getLogger('uvicorn.access')
        
        # Эмуляция вызова uvicorn access логгера
        access_logger.info(
            '%s - "%s %s HTTP/%s" %d',
            '127.0.0.1:51573', 'GET', '/api/v1/system/file-audit/telemetry', '1.1', 200
        )
        for h in access_logger.handlers:
            h.flush()


class TestLogAnalyzer:
    """Тесты для модуля анализатора логов."""

    def test_get_max_size_bytes(self):
        """Проверка вычисления максимального размера лог-файла."""
        from logger.log_analyzer import get_max_size_bytes
        result = get_max_size_bytes()
        assert result > 0