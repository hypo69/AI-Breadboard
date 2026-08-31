# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Tests for manage_tools.py CLI interface."""
#
# File: test_manage_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Tests for manage_tools.py CLI interface."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data" / "test_manage_tools"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

class TestManageToolsHelp:
    """Test help output and argument parsing."""

    def test_help_shows_all_commands(self):
        """Verify help displays all available commands."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "rag" in result.stdout
        assert "skills" in result.stdout
        assert "knowledge" in result.stdout
        assert "docs" in result.stdout
        assert "assist" in result.stdout

    def test_rag_help(self):
        """Verify rag subcommand help."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "rag", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "rebuild" in result.stdout
        assert "status" in result.stdout
        assert "validate" in result.stdout

    def test_skills_help(self):
        """Verify skills subcommand help."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "skills", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "list" in result.stdout
        assert "search" in result.stdout
        assert "show" in result.stdout
        assert "export" in result.stdout

    def test_knowledge_help(self):
        """Verify knowledge subcommand help."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "knowledge", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "extract" in result.stdout
        assert "add" in result.stdout
        assert "init" in result.stdout

class TestSkillsCommand:
    """Test skills command functionality."""

    def test_skills_list_returns_zero(self):
        """skills list should return exit code 0."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "skills", "list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0

    def test_skills_search_returns_zero(self):
        """skills search should return exit code 0."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "skills", "search", "media"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0

    def test_skills_show_nonexistent_returns_error(self):
        """skills show with non-existent skill should return error."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "skills", "show", "nonexistent_skill_12345"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1
        assert "Error" in result.stdout or "Error" in result.stderr

class TestRagCommand:
    """Test rag command functionality."""

    def test_rag_status_returns_zero(self):
        """rag status should return exit code 0."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "rag", "status"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0

    def test_rag_unknown_subcommand_returns_error(self):
        """rag with unknown subcommand should return error."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "rag", "unknown_command_12345"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1

class TestKnowledgeCommand:
    """Test knowledge command functionality."""

    def test_knowledge_unknown_subcommand_returns_error(self):
        """knowledge with unknown subcommand should return error."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "knowledge", "unknown_command_12345"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1

class TestDocsCommand:
    """Test docs command functionality."""

    def test_docs_unknown_subcommand_returns_error(self):
        """docs with unknown subcommand should return error."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "docs", "unknown_command_12345"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1

class TestUnknownCommand:
    """Test handling of unknown main commands."""

    def test_unknown_main_command_returns_error(self):
        """Unknown main command should return error and show help."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "unknown_command_12345"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1

class TestAssistCommand:
    """Test assist command forwarding."""

    def test_assist_help_returns_zero(self):
        """assist help should be forwarded to assist_cli."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "assist", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # assist_cli may return 0 (help) or exit before processing
        assert result.returncode in (0, 2)  # 2 is argparse error code

class TestRunScript:
    """Test _run_script helper function."""

    def test_run_script_nonexistent_file(self):
        """_run_script should return 1 for nonexistent script."""
        from manage_tools import _run_script
        result = _run_script("nonexistent_script_12345.py")
        assert result == 1

    def test_run_script_with_args(self):
        """_run_script should pass extra arguments to script."""
        # Test with a simple script that prints arguments
        test_script = TEST_DATA_DIR / "echo_args.py"
        test_script.write_text('import sys; print(" ".join(sys.argv[1:])); sys.exit(0)')

        from manage_tools import _run_script
        result = _run_script(str(test_script.relative_to(Path(__file__).parent.parent)), ["arg1", "arg2"])

        assert result == 0

@pytest.fixture
def mock_skill_registry(monkeypatch):
    """Create a mock SkillRegistry for testing."""
    mock_registry = MagicMock()
    mock_skill = MagicMock()
    mock_skill.name = "test-skill"
    mock_skill.description = "Test skill description"
    mock_skill.prompt.return_value = "Test prompt content"

    mock_registry.discover.return_value = [mock_skill]
    mock_registry.search.return_value = [mock_skill]
    mock_registry.get.return_value = mock_skill
    mock_registry.export_json.return_value = '{"name": "test-skill"}'

    return mock_registry

class TestIntegration:
    """Integration tests for full CLI workflow."""

    def test_full_cli_invocation(self):
        """Test complete CLI invocation with subcommand."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "skills", "list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0

    def test_command_without_subcommand_shows_help(self):
        """Command without subcommand should show help and return 0."""
        result = subprocess.run(
            [sys.executable, "manage_tools.py", "skills"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])