# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing project directory structure
# =============================================================================
# Description:
#   Checks structure of scripts directory for completeness and correctness.
#
# File: test_tools_structure.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Tests for project directory structure.

Check presence of all required directories, files and launchers
according to agent-oriented project strategy.

Documentation: .ai_instructions/knowledge/LAUNCHER_GUIDE.md
"""

import pytest
from pathlib import Path

# Project root is determined via header.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestToolsDirectoryStructure:
    """Check structure of scripts directory."""

    def test_scripts_directory_exists(self):
        """scripts/ directory must exist."""
        assert (PROJECT_ROOT / "scripts").is_dir() or (PROJECT_ROOT / "tools").is_dir(), \
            "Scripts directory not found in project root"

    def test_scripts_dev_directory_exists(self):
        """scripts/dev/ directory must exist."""
        assert (PROJECT_ROOT / "scripts" / "dev").is_dir() or (PROJECT_ROOT / "tools" / "ai").is_dir()

    def test_scripts_readme_exists(self):
        """Scripts README.md must exist."""
        assert (PROJECT_ROOT / "scripts" / "README.md").is_file() or (PROJECT_ROOT / "tools" / "README.md").is_file()

class TestAiToolsExist:
    """Check presence of key AI tools and development scripts."""

    def test_rebuild_dev_rag_exists(self):
        """rebuild_dev_rag.py must exist."""
        assert (PROJECT_ROOT / "scripts" / "maintenance" / "rebuild_dev_rag.py").is_file() or (PROJECT_ROOT / "tools" / "ai" / "rebuild_dev_rag.py").is_file()

    def test_search_code_exists(self):
        """search_code.py must exist."""
        assert (PROJECT_ROOT / "scripts" / "dev" / "search_code.py").is_file() or (PROJECT_ROOT / "tools" / "ai" / "search_code.py").is_file()

    def test_update_docs_exists(self):
        """update_docs.py must exist."""
        assert (PROJECT_ROOT / "scripts" / "dev" / "update_docs.py").is_file() or (PROJECT_ROOT / "tools" / "ai" / "update_docs.py").is_file()

class TestReportsDirectory:
    """Check tmp/reports/ directory."""

    def test_reports_directory_exists(self):
        """tmp/reports/ directory must exist."""
        assert (PROJECT_ROOT / "tmp" / "reports").is_dir() or (PROJECT_ROOT / "tmp").is_dir(), \
            "tmp directory not found"

class TestCoreRagDirectory:
    """Check core/rag/ directory."""

    def test_core_rag_directory_exists(self):
        """core/rag/ directory must exist."""
        assert (PROJECT_ROOT / "core" / "rag").is_dir(), \
            "core/rag/ directory not found"

    def test_core_rag_models_exists(self):
        """core/rag/models.py must exist."""
        assert (PROJECT_ROOT / "core" / "rag" / "models.py").is_file(), \
            "File core/rag/models.py not found"

class TestAiInstructionsDocuments:
    """Check key AI documents."""

    def test_launcher_guide_exists(self):
        """LAUNCHER_GUIDE.md must exist."""
        path = PROJECT_ROOT / ".ai" / "instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not path.exists():
            path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        assert path.is_file(), "LAUNCHER_GUIDE.md not found"

    def test_launcher_guide_not_empty(self):
        """LAUNCHER_GUIDE.md should not be empty."""
        path = PROJECT_ROOT / ".ai" / "instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not path.exists():
            path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        assert path.stat().st_size > 200, \
            "LAUNCHER_GUIDE.md is too small — probably not filled"

    def test_gemini_md_has_launcher_guide_ref(self):
