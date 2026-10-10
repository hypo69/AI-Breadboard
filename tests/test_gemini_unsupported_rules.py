# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Gemini Unsupported Rules
# =============================================================================
# Description:
#   Тестирование механизма правил и условий исключения неподдерживаемых моделей Gemini
#   (проверка версий <2, подстрок -image, явных списков и масок).
#
# Usage Examples:
#   Python API:
#     pytest tests/test_gemini_unsupported_rules.py
#
# File: test_gemini_unsupported_rules.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 10:47:00
# =============================================================================

"""Тестирование механизма правил и условий исключения неподдерживаемых моделей Gemini."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
from src.ai.gemini.rules import (
    matches_rule,
    is_gemini_model_unsupported,
    filter_unsupported_gemini_models,
    load_unsupported_rules_and_models,
    add_unsupported_gemini_model,
)


class TestGeminiUnsupportedRules:
    """Набор тестов для проверки движка правил исключения моделей Gemini."""

    def test_version_rules_less_than(self):
        """Проверка условия версии '<2'."""
        assert matches_rule("gemini-1.0-pro", "<2") is True
        assert matches_rule("gemini-1.5-flash", "<2") is True
        assert matches_rule("gemini-1.5-pro", "<2") is True
        assert matches_rule("models/gemini-1.5-flash", "<2") is True
        assert matches_rule("gemini:gemini-1.0-ultra", "<2") is True

        assert matches_rule("gemini-2.0-flash", "<2") is False
        assert matches_rule("gemini-2.5-flash", "<2") is False
        assert matches_rule("gemini-3.1-flash-lite", "<2") is False
        assert matches_rule("gemini-3.5-flash-lite", "<2") is False

    def test_version_rules_less_or_equal(self):
        """Проверка условия версии '<=2.0' и '<=2.5'."""
        assert matches_rule("gemini-2.0-flash", "<=2.0") is True
        assert matches_rule("gemini-2.5-flash", "<=2.0") is False
        assert matches_rule("gemini-2.5-flash", "<=2.5") is True
        assert matches_rule("gemini-3.1-flash-lite", "<=2.5") is False

    def test_substring_negation_rules(self):
        """Проверка правил с префиксом '-' (например, '-image', '-tts')."""
        assert matches_rule("imagen-3.0-generate-002", "-image") is True
        assert matches_rule("gemini-2.0-flash-image-gen", "-image") is True
        assert matches_rule("gemini-3.1-flash-lite", "-image") is False

        assert matches_rule("gemini-2.5-flash-preview-tts", "-tts") is True
        assert matches_rule("gemini-2.5-flash-preview-tts", "-preview-tts") is True
        assert matches_rule("gemini-3.1-flash-lite", "-tts") is False

    def test_wildcard_rules(self):
        """Проверка шаблонов с подстановочными знаками '*'."""
        assert matches_rule("gemini-1.0-pro", "gemini-1.*") is True
        assert matches_rule("gemini-1.5-flash", "gemini-1.*") is True
        assert matches_rule("gemini-2.0-flash", "gemini-1.*") is False
        assert matches_rule("imagen-3.0-generate-002", "*imagen*") is True

    def test_exact_model_match(self):
        """Проверка точного совпадения имени модели."""
        assert matches_rule("gemini-old", "gemini-old") is True
        assert matches_rule("models/gemini-old", "gemini-old") is True
        assert matches_rule("gemini-3.1-flash-lite", "gemini-old") is False

    def test_load_from_dict_json(self, tmp_path: Path):
        """Проверка загрузки структуры JSON со словарем (rules + unsupported_models)."""
        custom_file = tmp_path / "unsopported_gemini_models.json"
        data = {
            "rules": ["<2", "-image"],
            "unsupported_models": ["gemini-custom-old", "gemini-legacy"],
        }
        custom_file.write_text(json.dumps(data), encoding="utf-8")

        with patch("src.ai.gemini.rules.get_unsupported_config_path", return_value=custom_file):
            rules, explicit = load_unsupported_rules_and_models()
            assert "<2" in rules
            assert "-image" in rules
            assert "gemini-custom-old" in explicit
            assert "gemini-legacy" in explicit

            assert is_gemini_model_unsupported("gemini-1.5-flash") is True
            assert is_gemini_model_unsupported("imagen-3.0-fast") is True
            assert is_gemini_model_unsupported("gemini-custom-old") is True
            assert is_gemini_model_unsupported("gemini-3.1-flash-lite") is False

    def test_load_from_array_json(self, tmp_path: Path):
        """Проверка загрузки структуры JSON в виде плоского списка строк."""
        custom_file = tmp_path / "unsopported_gemini_models.json"
        data = ["<2", "-image", "gemini-flat-old"]
        custom_file.write_text(json.dumps(data), encoding="utf-8")

        with patch("src.ai.gemini.rules.get_unsupported_config_path", return_value=custom_file):
            rules, explicit = load_unsupported_rules_and_models()
            assert "<2" in rules
            assert "-image" in rules
            assert "gemini-flat-old" in explicit

            assert is_gemini_model_unsupported("gemini-1.0-ultra") is True
            assert is_gemini_model_unsupported("gemini-flat-old") is True
            assert is_gemini_model_unsupported("gemini-3.7-flash") is False

    def test_filter_unsupported_gemini_models(self, tmp_path: Path):
        """Проверка пакетной фильтрации списка моделей."""
        custom_file = tmp_path / "unsopported_gemini_models.json"
        data = {
            "rules": ["<2", "-tts"],
            "unsupported_models": ["gemini-old"],
        }
        custom_file.write_text(json.dumps(data), encoding="utf-8")

        models = [
            "gemini-1.0-pro",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-flash-preview-tts",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-old",
        ]

        with patch("src.ai.gemini.rules.get_unsupported_config_path", return_value=custom_file):
            supported = filter_unsupported_gemini_models(models)
            assert supported == [
                "gemini-2.0-flash",
                "gemini-3.1-flash-lite",
                "gemini-3.5-flash-lite",
            ]

    def test_add_unsupported_gemini_model(self, tmp_path: Path):
        """Проверка динамического добавления неподдерживаемой модели в JSON."""
        custom_file = tmp_path / "unsopported_gemini_models.json"
        data = {"rules": ["<2"], "unsupported_models": []}
        custom_file.write_text(json.dumps(data), encoding="utf-8")

        with patch("src.ai.gemini.rules.get_unsupported_config_path", return_value=custom_file):
            added = add_unsupported_gemini_model("gemini-failed-model", reason="404 Not Found")
            assert added is True

            updated = json.loads(custom_file.read_text(encoding="utf-8"))
            assert "gemini-failed-model" in updated["unsupported_models"]
            assert is_gemini_model_unsupported("gemini-failed-model") is True
