# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Фикстура для создания логгера с временными путями.
# =============================================================================
# Description:
#   Исчерпывающее тестирование всех публичных функций и классов модуля core/logger.
#
# File: test_logger_enhanced.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import os
import json
import logging
from pathlib import Path
from core.logger.logger import Logger

@pytest.fixture
def temp_logger(tmp_path):
    """Фикстура для создания логгера с временными путями."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    # Инициализируем логгер с путями во временной директории
    logger = Logger(
        info_log_path="info.log",
        debug_log_path="debug.log",
        errors_log_path="errors.log",
        json_log_path="log.json"
    )
    
    # Переопределяем пути логгера на временные для изоляции тестов
    logger.log_files_path = log_dir
    logger.info_log_path = log_dir / "info.log"
    logger.debug_log_path = log_dir / "debug.log"
    logger.errors_log_path = log_dir / "errors.log"
    logger.json_log_path = log_dir / "log.json"
    
    # Пересоздаем обработчики для новых путей
    for logger_obj in [logger.logger_file_info, logger.logger_file_debug, logger.logger_file_errors, logger.logger_file_json]:
        for handler in logger_obj.handlers[:]:
            logger_obj.removeHandler(handler)
            
    # Добавляем новые обработчики
    info_handler = logging.FileHandler(logger.info_log_path, encoding='utf-8')
    info_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.logger_file_info.addHandler(info_handler)
    
    debug_handler = logging.FileHandler(logger.debug_log_path, encoding='utf-8')
    debug_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.logger_file_debug.addHandler(debug_handler)
    
    errors_handler = logging.FileHandler(logger.errors_log_path, encoding='utf-8')
    errors_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.logger_file_errors.addHandler(errors_handler)
    
    from core.logger.logger import JsonFormatter
    json_handler = logging.FileHandler(logger.json_log_path, encoding='utf-8')
    json_handler.setFormatter(JsonFormatter())
    logger.logger_file_json.addHandler(json_handler)

    return logger

def test_logger_file_writing(temp_logger):
    """Тестирование записи логов в файлы."""
    # --- Arrange ---
    message: str = "Test info message"
    
    # --- Act ---
    temp_logger.info(message)
    
    # --- Assert ---
    # Check, что файл info.log существует и содержит сообщение
    assert temp_logger.info_log_path.exists(), "Файл info.log не создан"
    with open(temp_logger.info_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert message in content, f"Сообщение '{message}' не найдено в info.log, получено: {content}"

def test_logger_json_writing(temp_logger):
    """Тестирование записи логов в JSON файл."""
    # --- Arrange ---
    message: str = "Test JSON message"
    
    # --- Act ---
    temp_logger.info(message)
    
    # --- Assert ---
    assert temp_logger.json_log_path.exists(), "Файл log.json не создан"
    with open(temp_logger.json_log_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        log_data = json.loads(line)
        assert log_data['message'] == message, f"Сообщение в JSON не совпадает: {log_data['message']}"

def test_logger_debug_filter(temp_logger):
    """Тестирование фильтрации DEBUG в режиме PROD (is_debug_mode=False)."""
    # --- Arrange ---
    temp_logger.is_debug_mode = False
    message: str = "Debug message"
    
    # --- Act ---
    temp_logger.debug(message)
    
    # --- Assert ---
    # Check, что сообщение не попало в debug.log
    with open(temp_logger.debug_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert message not in content, "DEBUG сообщение записано в PROD режиме"
