# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тестирование нормальных (ожидаемых) сценариев рабо
# =============================================================================
# Description:
#   Исчерпывающее тестирование всех публичных функций и классов модуля.
#
# File: test_save_file.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import os
from scripts.dev.save_file import save_file

class TestSaveFile_HappyPath:
    """Тестирование нормальных (ожидаемых) сценариев работы save_file."""

    def test_save_file_success(self, tmp_path):
        """Тестирование сохранения файла с корректными данными.
        
        Check: файл создается и содержимое записывается корректно.
        """
        # --- Подготовка (Arrange) ---
        # Временная директория для теста.
        test_dir = tmp_path / "subdir"
        # Путь к файлу в директории.
        test_file = test_dir / "test.txt"
        # Контент для записи.
        content = "Hello, world!"
        
        # --- Выполнение (Act) ---
        # Вызов функции сохранения.
        result = save_file(str(test_file), content)
        
        # --- Check (Assert) ---
        # Файл должен быть создан и возвращено True.
        assert result is True, "save_file должна вернуть True для корректного ввода"
        assert test_file.exists(), "Файл должен быть создан"
        assert test_file.read_text(encoding='utf-8') == content, "Содержимое файла не совпадает"

class TestSaveFile_EdgeCases:
    """Тестирование граничных значений и пустых данных."""

    def test_save_file_empty_content(self, tmp_path):
        """Тестирование сохранения пустого содержимого.
        
        Check: пустая string записывается в файл без ошибок.
        """
        # --- Подготовка (Arrange) ---
        # Путь к временному файлу.
        test_file = tmp_path / "empty.txt"
        # Пустая string как контент.
        content = ""
        
        # --- Выполнение (Act) ---
        # Вызов функции.
        result = save_file(str(test_file), content)
        
        # --- Check (Assert) ---
        # Function должна вернуть True и создать empty файл.
        assert result is True, "Должно быть возвращено True для пустого контента"
        assert test_file.exists(), "Файл должен быть создан"
        assert test_file.read_text(encoding='utf-8') == "", "Содержимое файла должно быть пустым"

class TestSaveFile_ErrorScenarios:
    """Тестирование обработки ошибочных сценариев."""

    def test_save_file_invalid_path(self):
        """Тестирование сохранения в недоступный путь.
        
        Check: при ошибке записи function должна вернуть False.
        """
        # --- Подготовка (Arrange) ---
        # Использование пути, который невозможно создать (на Windows).
        invalid_path = "Z:/invalid_directory/file.txt"
        
        # --- Выполнение (Act) ---
        # Вызов функции с неверным путем.
        result = save_file(invalid_path, "content")
        
        # --- Check (Assert) ---
        # Function должна корректно обработать exception и вернуть False.
        assert result is False, "save_file должна вернуть False при ошибке записи"
