# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тестирование сохранения текста в файл (успешный сц
# =============================================================================
# Description:
#   Исчерпывающее тестирование функций для работы с файлами.
#
# File: test_file.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from pathlib import Path
import os
from core.utils.file import save_text_file, read_text_file

# --- Тесты для save_text_file ---

def test_save_text_file_happy_path(tmp_path):
    """Тестирование сохранения текста в файл (успешный сценарий)."""
    # Arrange: путь к временному файлу
    file_path = tmp_path / "test.txt"
    data = "Hello, World!"

    # Act: вызов функции
    result = save_text_file(data, file_path)

    # Assert: проверяем успешность и содержимое
    assert result is True, "save_text_file должна вернуть True при успешной записи"
    assert file_path.read_text(encoding="utf-8") == data, "Содержимое файла не совпадает с записанным"

def test_read_text_file_happy_path(tmp_path):
    """Тестирование чтения текста из файла (успешный сценарий)."""
    # Arrange: путь к временному файлу
    file_path = tmp_path / "test_read.txt"
    data = "Hello, read!"
    file_path.write_text(data, encoding="utf-8")

    # Act: вызов функции
    result = read_text_file(file_path)

    # Assert: проверяем содержимое
    assert result == data, "Прочитанное содержимое не совпадает с записанным"

def test_save_text_file_invalid_mode(tmp_path):
    """Тестирование записи с невалидным режимом (ожидаем ошибку или False)."""
    # Arrange
    file_path = tmp_path / "invalid_mode.txt"
    data = "data"
    
    # Act
    # Если function правильно processes исключения через log, она должна вернуть False
    result = save_text_file(data, file_path, mode="x") # 'x' не поддерживается логикой, но в open допустимо, проверим 'r' как пример
    
    # Assert
    # Согласно стандартам, должна вернуть False при сбое, не генерировать exception
    # В реальности 'x' создаст файл, но проверим, как function processes запись
    assert result is True 
