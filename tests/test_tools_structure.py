## \file tests/test_tools_structure.py
# -*- coding: utf-8 -*-
"""
Тесты структуры директорий проекта.

Проверяет наличие всех обязательных директорий, файлов и лончеров
согласно агентоориентированной стратегии проекта.

Документация: .ai_instructions/knowledge/LAUNCHER_GUIDE.md
"""

import pytest
from pathlib import Path


# Корень проекта определяется через header.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestToolsDirectoryStructure:
    """Проверяет структуру директории scripts/."""

    def test_scripts_directory_exists(self):
        """scripts/ обязан существовать."""
        assert (PROJECT_ROOT / "scripts").is_dir() or (PROJECT_ROOT / "tools").is_dir(), \
            "Директория со скриптами не найдена в корне проекта"

    def test_scripts_dev_directory_exists(self):
        """scripts/dev/ обязан существовать."""
        assert (PROJECT_ROOT / "scripts" / "dev").is_dir() or (PROJECT_ROOT / "tools" / "ai").is_dir()

    def test_scripts_readme_exists(self):
        """README.md скриптов обязан существовать."""
        assert (PROJECT_ROOT / "scripts" / "README.md").is_file() or (PROJECT_ROOT / "tools" / "README.md").is_file()


class TestAiToolsExist:
    """Проверяет наличие ключевых AI-инструментов и скриптов разработки."""

    def test_rebuild_dev_rag_exists(self):
        """rebuild_dev_rag.py обязан существовать."""
        assert (PROJECT_ROOT / "scripts" / "maintenance" / "rebuild_dev_rag.py").is_file() or (PROJECT_ROOT / "tools" / "ai" / "rebuild_dev_rag.py").is_file()

    def test_search_code_exists(self):
        """search_code.py обязан существовать."""
        assert (PROJECT_ROOT / "scripts" / "dev" / "search_code.py").is_file() or (PROJECT_ROOT / "tools" / "ai" / "search_code.py").is_file()

    def test_update_docs_exists(self):
        """update_docs.py обязан существовать."""
        assert (PROJECT_ROOT / "scripts" / "dev" / "update_docs.py").is_file() or (PROJECT_ROOT / "tools" / "ai" / "update_docs.py").is_file()


class TestReportsDirectory:
    """Проверяет директорию tmp/reports/."""

    def test_reports_directory_exists(self):
        """tmp/reports/ обязан существовать."""
        assert (PROJECT_ROOT / "tmp" / "reports").is_dir() or (PROJECT_ROOT / "tmp").is_dir(), \
            "Директория tmp не найдена"


class TestCoreRagDirectory:
    """Проверяет директорию core/rag/."""

    def test_core_rag_directory_exists(self):
        """core/rag/ обязан существовать."""
        assert (PROJECT_ROOT / "core" / "rag").is_dir(), \
            "Директория core/rag/ не найдена"

    def test_core_rag_models_exists(self):
        """core/rag/models.py обязан существовать."""
        assert (PROJECT_ROOT / "core" / "rag" / "models.py").is_file(), \
            "Файл core/rag/models.py не найден"


class TestAiInstructionsDocuments:
    """Проверяет ключевые AI-документы."""

    def test_launcher_guide_exists(self):
        """LAUNCHER_GUIDE.md обязан существовать."""
        path = PROJECT_ROOT / ".ai" / "instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not path.exists():
            path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        assert path.is_file(), "LAUNCHER_GUIDE.md не найден"

    def test_launcher_guide_not_empty(self):
        """LAUNCHER_GUIDE.md не должен быть пустым."""
        path = PROJECT_ROOT / ".ai" / "instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not path.exists():
            path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        assert path.stat().st_size > 200, \
            "LAUNCHER_GUIDE.md слишком мал — вероятно, не заполнен"

    def test_gemini_md_has_launcher_guide_ref(self):
        """GEMINI.md должен ссылаться на LAUNCHER_GUIDE.md."""
        path = PROJECT_ROOT / "GEMINI.md"
        content = path.read_text(encoding="utf-8")
        assert "LAUNCHER_GUIDE" in content, \
            "GEMINI.md не содержит ссылки на LAUNCHER_GUIDE.md"


class TestCoreProjectFiles:
    """Проверяет наличие ключевых файлов проекта в корне."""

    def test_main_py_exists(self):
        """main.py обязан существовать."""
        assert (PROJECT_ROOT / "main.py").is_file()

    def test_manage_tools_exists(self):
        """manage_tools.py обязан существовать."""
        assert (PROJECT_ROOT / "manage_tools.py").is_file()

    def test_header_py_exists(self):
        """header.py обязан существовать (используется main.py и manage_tools.py)."""
        assert (PROJECT_ROOT / "header.py").is_file(), \
            "header.py отсутствует — main.py и manage_tools.py не запустятся"

    def test_env_example_exists(self):
        """.env.example обязан существовать для документации переменных."""
        assert (PROJECT_ROOT / ".env.example").is_file()
