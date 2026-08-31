# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тестирование получения первого доступного порта (б
# =============================================================================
# Description:
#   Исчерпывающее тестирование всех публичных функций модуля get_free_port.
#
# File: test_get_free_port.py
# Project: ai-breadboard
# Package: tests.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from core.utils.get_free_port import get_free_port

def test_get_free_port_first_available():
    """Тестирование получения первого доступного порта (без диапазона).
    
    Check: function должна вернуть integer, начиная с 1024.
    """
    # --- Подготовка (Arrange) ---
    # Хост localhost — стандарт для локальной проверки.
    host: str = 'localhost'
    
    # --- Выполнение (Act) ---
    # Поиск первого свободного порта без ограничений.
    port: int = get_free_port(host)
    
    # --- Check (Assert) ---
    # Check: порт должен быть >= 1024.
    assert port >= 1024, f"Порт должен быть >= 1024, получено: {port}"

def test_get_free_port_in_range():
    """Тестирование получения порта в заданном диапазоне."""
    # --- Подготовка (Arrange) ---
    host: str = 'localhost'
    port_range: str = '3000-5000'
    
    # --- Выполнение (Act) ---
    port: int = get_free_port(host, port_range)
    
    # --- Check (Assert) ---
    assert 3000 <= port <= 5000, f"Порт {port} вне диапазона {port_range}"

def test_get_free_port_invalid_range():
    """Тестирование ошибки при некорректном диапазоне."""
    # --- Подготовка (Arrange) ---
    host: str = 'localhost'
    port_range: str = 'invalid'
    
    # --- Выполнение (Act) & Check (Assert) ---
    with pytest.raises(ValueError):
        get_free_port(host, port_range)
