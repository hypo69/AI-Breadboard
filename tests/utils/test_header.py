# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тестирование успешного нахождения корня проекта.
# =============================================================================
# Description:
#   Исчерпывающее тестирование всех публичных функций модуля header.
#
# File: test_header.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from pathlib import Path
from core.utils.header import set_project_root

def test_set_project_root_success():
    """Тестирование успешного нахождения корня проекта.
    
    Check: function должна найти директорию с маркером '__root__'.
    """
    # --- Подготовка (Arrange) ---
    expected_root = Path(__file__).resolve().parents[2]
    
    # --- Выполнение (Act) ---
    root = set_project_root()
    
    # --- Check (Assert) ---
    assert root == expected_root, f"Корень проекта не найден, ожидалось {expected_root}, получено {root}"

def test_set_project_root_nonexistent_marker():
    """Тестирование нахождения корня при отсутствии маркеров."""
    # --- Подготовка (Arrange) ---
    # Маркер, которого заведомо нет в дереве проекта.
    marker = ('nonexistent_file_12345',)
    
    # --- Выполнение (Act) ---
    root = set_project_root(marker_files=marker)
    
    # --- Check (Assert) ---
    # Поведение функции: если не найдено, Returns директорию скрипта.
    assert isinstance(root, Path), "Результат должен быть объектом Path"
