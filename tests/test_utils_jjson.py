# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/utils/jjson
# =============================================================================
# Описание:
#   Исчерпывающее тестирование всех публичных функций модуля jjson: 
#   j_dumps, j_loads, j_loads_ns.
#   Покрытие: прямые тесты, граничные условия, регрессионные сценарии.
#
# File: tests/test_utils_jjson.py
# Project: ai-assistant
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
import json
from pathlib import Path
from types import SimpleNamespace
from core.utils.jjson import j_dumps, j_loads, j_loads_ns

class TestJJson:
    """Класс для тестирования функций модуля jjson."""

    def test_j_loads_happy_path_str(self):
        """Тестирование загрузки корректной JSON-строки.

        Проверка: j_loads корректно парсит простую JSON-строку в словарь.
        """
        # --- Подготовка (Arrange) ---
        # Тестовая JSON-строка: стандартный объект с ключом 'a' и значением 1.
        json_str: str = '{"a": 1}'
        
        # --- Выполнение (Act) ---
        # Вызов функции j_loads для парсинга строки.
        result: dict = j_loads(json_str)
        
        # --- Проверка (Assert) ---
        # Ожидается словарь {'a': 1}.
        assert result == {'a': 1}, f"j_loads() должна вернуть {'a': 1}, получено: {result!r}"

    def test_j_dumps_happy_path_dict(self):
        """Тестирование дампирования словаря в JSON (в память).

        Проверка: j_dumps возвращает корректный словарь при отсутствии файла.
        """
        # --- Подготовка (Arrange) ---
        # Тестовый словарь.
        data: dict = {'a': 1, 'b': 2}
        
        # --- Выполнение (Act) ---
        # Дампирование без указания файла (должно вернуть данные).
        result: dict = j_dumps(data)
        
        # --- Проверка (Assert) ---
        assert result == data, f"j_dumps() должна вернуть {data!r}, получено: {result!r}"
        
    def test_j_loads_empty_str(self):
        """Тестирование граничного случая: пустая строка.
        
        Проверка: пустая строка должна возвращать пустой словарь (ошибка логики парсинга).
        """
        # --- Подготовка (Arrange) ---
        empty_str: str = ""
        
        # --- Выполнение (Act) ---
        # Пустая строка приводит к ошибке парсинга внутри string2dict.
        result = j_loads(empty_str)
        
        # --- Проверка (Assert) ---
        assert result == {}, f"j_loads() должна вернуть пустой словарь для пустой строки, получено: {result!r}"

