# -*- coding: utf-8 -*-
"""Тесты для модуля src.utils.printer.

Требования:
- Использовать pytest.
- Докстринги и комментарии на русском языке (hypo79 docblock).
- Проверять основные функции pformat и pprint.
"""

import json
import pytest
from pathlib import Path

from src.utils.printer import pformat, pprint


def test_pformat_dict_default():
    """Проверка форматирования словаря без цветовых параметров.

    Ожидается, что результат будет отформатированным JSON со стандартным
    отступом (6 пробелов) и без ANSI‑цветов.
    """
    data = {"name": "Alice", "age": 30, "items": [1, 2, 3]}
    result = pformat(data)
    parsed = json.loads(result)
    assert parsed == data
    lines = result.split('\n')
    for line in lines[1:-1]:
        if line.strip():
            assert line.startswith('      ')


def test_pformat_embedded_json_in_string():
    """Проверка форматирования JSON, встроенного в обычную строку.

    Функция должна найти JSON‑блок, отформатировать его и вернуть строку
    с отформатированным JSON.
    """
    raw = "User data: {\"id\":1,\"active\":true} end"
    result = pformat(raw)
    assert "{\n" in result
    assert "\"id\": 1" in result
    assert result.startswith("User data: ")
    assert result.strip().endswith("end")


def test_pformat_file_path_csv(tmp_path):
    """Проверка обработки пути к файлу .csv.

    При передаче существующего пути к CSV‑файлу функция должна вернуть
    строку вида "File: <path> (supported: .csv, .xls)".
    """
    file_path = tmp_path / "sample.csv"
    file_path.write_text("a,b\n1,2\n")
    result = pformat(str(file_path))
    expected_prefix = f"File: {file_path} (supported: .csv, .xls)"
    assert result == expected_prefix


def test_pformat_none_returns_none_string():
    """Проверка, что pformat(None) возвращает строку "None" без цвета."""
    assert pformat(None) == "None"


def test_pprint_outputs_formatted_string(capsys):
    """Проверка функции pprint: вывод в stdout и работа параметров.

    Функция должна объединить несколько аргументов, отформатировать каждый
    через pformat и записать в поток вывода.
    """
    data1 = {"x": 1}
    data2 = "plain text"
    pprint(data1, data2, text_color="green", sep=" | ", end="!\n")
    captured = capsys.readouterr()
    assert captured.out.endswith("!\n")
    assert " | " in captured.out
    assert "{\n" in captured.out
    assert "plain text" in captured.out