# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Тесты метода interval."""
#
# File: test_utils_date_time.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Тесты модуля core/utils/date_time.py
"""

import pytest
from datetime import time
from unittest.mock import patch, Mock
from core.utils.date_time import TimeoutCheck

class TestTimeoutCheckInterval:
    """Тесты метода interval."""

    def test_interval_same_day_morning(self):
        """Тест интервала в пределах одного дня (утро)."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 30)
            
            checker.interval(start=time(8, 0), end=time(17, 0))
            
            assert checker.result is True

    def test_interval_same_day_outside(self):
        """Тест интервала вне времени (тот же день)."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(3, 0)
            
            checker.interval(start=time(8, 0), end=time(17, 0))
            
            assert checker.result is False

    def test_interval_crosses_midnight(self):
        """Тест интервала, переходящего через полночь."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(1, 0)
            
            checker.interval(start=time(23, 0), end=time(6, 0))
            
            assert checker.result is True

    def test_interval_crosses_midnight_outside(self):
        """Тест интервала вне времени (через полночь)."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(12, 0)
            
            checker.interval(start=time(23, 0), end=time(6, 0))
            
            assert checker.result is False

    def test_interval_exact_start(self):
        """Тест точного времени начала."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(23, 0)
            
            checker.interval(start=time(23, 0), end=time(6, 0))
            
            assert checker.result is True

    def test_interval_exact_end(self):
        """Тест точного времени окончания."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(6, 0)
            
            checker.interval(start=time(23, 0), end=time(6, 0))
            
            assert checker.result is True

class TestTimeoutCheckIntervalWithTimeout:
    """Тесты метода interval_with_timeout."""

    def test_interval_with_timeout_success(self):
        """Тест успешного интервала с таймаутом."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 0)
            
            result = checker.interval_with_timeout(timeout=5, start=time(8, 0), end=time(17, 0))
            
            assert result is True

    def test_interval_with_timeout_thread_completes(self):
        """Тест что поток завершается при вызове interval_with_timeout."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 0)
            
            result = checker.interval_with_timeout(timeout=5)
            
            # Проверяем что результат определен
            assert result is True or result is False

    def test_interval_with_timeout_default_parameters(self):
        """Тест с параметрами по умолчанию."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(1, 0)
            
            result = checker.interval_with_timeout()
            
            assert result is True  # 1:00 входит в 23:00-6:00

class TestTimeoutCheckInput:
    """Тесты методов ввода."""

    def test_get_input_sets_attribute(self):
        """Тест что get_input sets атрибут."""
        checker = TimeoutCheck()
        
        with patch('builtins.input', return_value='test input'):
            checker.get_input()
            
            assert hasattr(checker, 'user_input')
            assert checker.user_input == 'test input'

    def test_input_with_timeout_success(self):
        """Тест успешного ввода с таймаутом."""
        checker = TimeoutCheck()
        
        with patch('builtins.input', return_value='hello'):
            result = checker.input_with_timeout(timeout=5)
            
            assert result == 'hello'

    def test_input_with_timeout_empty_input(self):
        """Тест пустого ввода."""
        checker = TimeoutCheck()
        
        with patch('builtins.input', return_value=''):
            result = checker.input_with_timeout(timeout=5)
            
            assert result == ''

class TestTimeoutCheckEdgeCases:
    """Тесты граничных случаев."""

    def test_interval_empty_start_end(self):
        """Тест с граничными значениями времени."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(0, 0)
            
            # Интервал от полночи до полуночи - весь день
            checker.interval(start=time(0, 0), end=time(0, 0))
            
            assert checker.result is True

    def test_interval_one_minute(self):
        """Тест интервала в одну минуту."""
        checker = TimeoutCheck()
        
        with patch('core.utils.date_time.datetime') as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 0)
            
            checker.interval(start=time(10, 0), end=time(10, 1))
            
            assert checker.result is True

    def test_result_initially_none(self):
        """Тест что result инициализируется как None."""
        checker = TimeoutCheck()
        
        assert checker.result is None