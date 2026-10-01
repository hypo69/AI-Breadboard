# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm Tests - Test Code Indexer
# =============================================================================
# Description:
#   Тесты для AST индексатора структуры Python кода (Code Knowledge).
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.tests.test_code_indexer import test_index_python_file
#
#     res = test_index_python_file()
#
# File: test_code_indexer.py
# Project: ai-breadboard
# Package: apps.windows.wikillm.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Тесты для AST индексатора структуры Python кода (Code Knowledge)."""

import tempfile
from pathlib import Path
import pytest
from apps.windows.wikillm.code_indexer import CodeKnowledgeIndexer
from apps.windows.wikillm.storage import WikiStorage


def test_index_python_file() -> None:
    """Проверка извлечения классов, функций и docstrings через AST."""
    storage = WikiStorage(":memory:")
    indexer = CodeKnowledgeIndexer(storage)

    code_snippet = '''"""Тестовый модуль для проверки индексатора."""
import os
from typing import Optional

class SampleDiagnosticTool:
    """Класс для системной диагностики."""

    def run_check(self, target: str) -> bool:
        """Выполняет проверку целевого компонента."""
        return True

def standalone_helper(param1: int) -> str:
    """Вспомогательная функция."""
    return str(param1)
'''
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "sample_mod.py"
        tmp_file.write_text(code_snippet, encoding="utf-8")

        entities = indexer.index_file(tmp_file, base_dir=tmp_dir)
        assert len(entities) == 3

        keys = [e.canonical_key for e in entities]
        assert any("SampleDiagnosticTool" in k for k in keys)
        assert any("run_check" in k for k in keys)
        assert any("standalone_helper" in k for k in keys)

        # Проверяем, что сущности сохранены в хранилище и доступны по FTS
        search_res = storage.search_fts("системной диагностики")
        assert len(search_res) >= 1
