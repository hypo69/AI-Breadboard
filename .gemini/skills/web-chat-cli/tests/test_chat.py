# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Тестирование парсинга аргументов по умолчанию."""
#
# File: test_chat.py
# Project: ai-breadboard
# Package: .gemini.skills.web-chat-cli.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
import os

# Импортируем напрямую из файла
# C:\ai-assistant\.gemini\skills\web-chat-cli\src\chat.py
import importlib.util

spec = importlib.util.spec_from_file_location("chat", r"C:\ai-assistant\.gemini\skills\web-chat-cli\src\chat.py")
chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat)

parse_arguments = chat.parse_arguments

import pytest
from unittest.mock import MagicMock, patch

def test_parse_arguments_default():
    """Тестирование парсинга аргументов по умолчанию."""
    test_args = ['chat.py']
    with patch('sys.argv', test_args):
        args = parse_arguments()
    assert args.model == 'gemini-1.5-flash', "Модель по умолчанию должна быть gemini-1.5-flash"

def test_parse_arguments_custom():
    """Тестирование парсинга пользовательских аргументов."""
    test_args = ['chat.py', '--model', 'gemini-1.5-pro', '--debug']
    with patch('sys.argv', test_args):
        args = parse_arguments()
    assert args.model == 'gemini-1.5-pro', "Модель должна быть изменена"
    assert args.debug is True, "Режим отладки должен быть включен"
