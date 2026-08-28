# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/utils/file
# =============================================================================
# Описание:
#   Исчерпывающее тестирование функций работы с файлами модуля file.py:
#   save_text_file, read_text_file, get_filenames, remove_bom.
#
# File: tests/test_utils_file.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import os
from pathlib import Path
from core.utils.file import save_text_file, read_text_file, get_filenames, remove_bom

class TestFileUtils:
    """Класс для тестирования функций модуля file.py."""

    def test_save_and_read_text_file_happy_path(self, tmp_path):
        """Тестирование нормального сценария записи и чтения текста.
        
        Проверка: данные записанные в файл корректно считываются.
        """
        # --- Подготовка (Arrange) ---
        # Временная папка tmp_path (фикс pytest).
        test_file: Path = tmp_path / "test.txt"
        content: str = "Тестовая строка"
        
        # --- Выполнение (Act) ---
        # Запись текста.
        save_result: bool = save_text_file(content, test_file)
        # Чтение текста.
        read_result: str | None = read_text_file(test_file)
        
        # --- Проверка (Assert) ---
        assert save_result is True, "save_text_file() должна вернуть True"
        assert read_result == content, f"Ожидалось {content!r}, получено {read_result!r}"

    def test_save_and_read_dict_happy_path(self, tmp_path):
        """Тестирование записи и чтения словаря в формате JSON."""
        # --- Подготовка (Arrange) ---
        test_file: Path = tmp_path / "test.json"
        data: dict = {"key": "value"}
        
        # --- Выполнение (Act) ---
        save_result: bool = save_text_file(data, test_file)
        # При чтении файла JSON через read_text_file мы получим строку JSON.
        read_result_str: str | None = read_text_file(test_file)
        
        # --- Проверка (Assert) ---
        assert save_result is True
        # Проверяем, что в файле есть корректная структура JSON.
        import json
        assert json.loads(read_result_str) == data
        
    def test_remove_bom(self, tmp_path):
        """Тестирование функции очистки BOM."""
        # --- Подготовка (Arrange) ---
        test_file: Path = tmp_path / "bom.txt"
        # Создаем файл с BOM (UTF-8 signature).
        content_with_bom: str = "\ufeffТекст с BOM"
        test_file.write_text(content_with_bom, encoding="utf-8")
        
        # --- Выполнение (Act) ---
        remove_bom(test_file)
        
        # --- Проверка (Assert) ---
        content_without_bom = test_file.read_text(encoding="utf-8")
        assert "\ufeff" not in content_without_bom
        assert content_without_bom == "Текст с BOM"

