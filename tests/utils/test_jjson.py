# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/utils/jjson.py
# =============================================================================
# Описание:
#   Тестирование функций загрузки и сохранения JSON данных.
#
# File: tests/utils/test_jjson.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import json
from pathlib import Path
from core.utils.jjson import j_loads, j_dumps
from types import SimpleNamespace

# --- Тесты для j_dumps ---

def test_j_dumps_happy_path(tmp_path):
    """Тестирование сохранения JSON в файл (успешный сценарий)."""
    # Arrange: тестовые данные
    data = {"key": "value"}
    file_path = tmp_path / "test.json"
    
    # Act: сохранение
    result = j_dumps(data, file_path=file_path)
    
    # Assert
    assert result == data, "j_dumps должна вернуть исходные данные"
    assert file_path.exists(), "Файл должен быть создан"
    assert json.loads(file_path.read_text(encoding="utf-8")) == data, "Содержимое файла не совпадает"

# --- Тесты для j_loads ---

def test_j_loads_str_happy_path():
    """Тестирование загрузки JSON из строки (успешный сценарий)."""
    # Arrange
    json_str = '{"key": "value"}'
    
    # Act
    result = j_loads(json_str)
    
    # Assert
    assert result == {"key": "value"}, "Загруженные данные не совпадают"

def test_j_loads_file_happy_path(tmp_path):
    """Тестирование загрузки JSON из файла (успешный сценарий)."""
    # Arrange
    file_path = tmp_path / "data.json"
    data = {"key": "value"}
    file_path.write_text(json.dumps(data), encoding="utf-8")
    
    # Act
    result = j_loads(file_path)
    
    # Assert
    assert result == data, "Загруженные данные из файла не совпадают"
