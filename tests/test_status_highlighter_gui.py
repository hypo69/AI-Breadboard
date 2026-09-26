"""
tests/test_status_highlighter_gui.py — Тестирование системы программной подсветки статусов

Данный модуль проверяет корректность файлов CSS и JS модуля status-highlighter.js,
отвечающих за программное выделение включенных/активных состояний зеленым цветом,
а выключенных/неактивных — красным.
"""

import os
import pytest


def test_status_highlighter_js_exists():
    """Проверка наличия созданного глобального модуля status-highlighter.js"""
    js_path = os.path.join(
        "src", "api", "webgui", "js", "status-highlighter.js"
    )
    assert os.path.exists(js_path), f"Файл {js_path} не найден."

    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "StatusHighlighterEngine" in content
    assert "POSITIVE_KEYWORDS" in content
    assert "NEGATIVE_KEYWORDS" in content
    assert "isPositive" in content
    assert "isNegative" in content


def test_components_css_contains_status_selectors():
    """Проверка наличия правил подсветки в components.css для data-status и data-state"""
    css_path = os.path.join(
        "src", "api", "webgui", "css", "components.css"
    )
    assert os.path.exists(css_path), f"Файл {css_path} не найден."

    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert '[data-status="active"]' in content
    assert '[data-status="enabled"]' in content
    assert '[data-status="inactive"]' in content
    assert '[data-status="disabled"]' in content
    assert "--status-success-bg" in content
    assert "--status-danger-bg" in content
    assert ".status-dot" in content


def test_index_html_includes_status_highlighter():
    """Проверка подключения модуля status-highlighter.js в index.html"""
    html_path = os.path.join("src", "api", "webgui", "index.html")
    assert os.path.exists(html_path), f"Файл {html_path} не найден."

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "status-highlighter.js" in content
