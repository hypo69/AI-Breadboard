# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля core/utils/get_free_port
# =============================================================================
# Описание:
#   Исчерпывающее тестирование всех публичных функций модуля get_free_port.
#   Покрытие: прямые тесты, граничные условия, регрессионные сценарии.
#
# File: tests/utils/test_get_free_port.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from core.utils.get_free_port import get_free_port

def test_get_free_port_first_available():
    """Тестирование получения первого доступного порта (без диапазона).
    
    Проверка: функция должна вернуть целое число, начиная с 1024.
    """
    # --- Подготовка (Arrange) ---
    # Хост localhost — стандарт для локальной проверки.
    host: str = 'localhost'
    
    # --- Выполнение (Act) ---
    # Поиск первого свободного порта без ограничений.
    port: int = get_free_port(host)
    
    # --- Проверка (Assert) ---
    # Проверка: порт должен быть >= 1024.
    assert port >= 1024, f"Порт должен быть >= 1024, получено: {port}"

def test_get_free_port_in_range():
    """Тестирование получения порта в заданном диапазоне."""
    # --- Подготовка (Arrange) ---
    host: str = 'localhost'
    port_range: str = '3000-5000'
    
    # --- Выполнение (Act) ---
    port: int = get_free_port(host, port_range)
    
    # --- Проверка (Assert) ---
    assert 3000 <= port <= 5000, f"Порт {port} вне диапазона {port_range}"

def test_get_free_port_invalid_range():
    """Тестирование ошибки при некорректном диапазоне."""
    # --- Подготовка (Arrange) ---
    host: str = 'localhost'
    port_range: str = 'invalid'
    
    # --- Выполнение (Act) & Проверка (Assert) ---
    with pytest.raises(ValueError):
        get_free_port(host, port_range)
