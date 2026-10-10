# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Manage Tools
# =============================================================================
# Description:
#   Tests for manage_tools.py CLI interface with unified agent and skill commands.
#
# Usage Examples:
#   CLI:
#     python -m tests.test_manage_tools
#   Python API:
#     from tests.test_manage_tools import TestManageToolsHelp
#
#     service = TestManageToolsHelp()
#
# File: test_manage_tools.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 08:35:00
# =============================================================================

from __future__ import annotations
"""Тесты для CLI-интерфейса manage_tools.py."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

TEST_DATA_DIR = Path(__file__).parent / 'data' / 'test_manage_tools'
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPO_ROOT = Path(__file__).parent.parent


def _exec_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Вспомогательная функция для надежного вызова manage_tools.py с кодировкой UTF-8."""
    return subprocess.run(
        [sys.executable, 'manage_tools.py', *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=REPO_ROOT
    )


class TestManageToolsHelp:
    """Проверка вывода справки и парсинга аргументов."""

    def test_help_shows_all_commands(self):
        """Проверка наличия базовых команд в общей справке."""
        result = _exec_cli('--help')
        assert result.returncode == 0
        assert 'rag' in result.stdout
        assert 'skills' in result.stdout
        assert 'agents' in result.stdout
        assert 'docs' in result.stdout
        assert 'db' in result.stdout
        assert 'assist' in result.stdout

    def test_rag_help(self):
        """Проверка справки подкоманды rag."""
        result = _exec_cli('rag', '--help')
        assert result.returncode == 0
        assert 'rebuild' in result.stdout
        assert 'status' in result.stdout
        assert 'validate' in result.stdout

    def test_skills_help(self):
        """Проверка справки подкоманды skills."""
        result = _exec_cli('skills', '--help')
        assert result.returncode == 0
        assert 'list' in result.stdout
        assert 'search' in result.stdout
        assert 'show' in result.stdout
        assert 'export' in result.stdout


class TestSkillsCommand:
    """Тестирование функционала команд skills."""

    def test_skills_list_returns_zero(self):
        """Команда skills list возвращает код 0."""
        result = _exec_cli('skills', 'list')
        assert result.returncode == 0

    def test_skills_search_returns_zero(self):
        """Команда skills search возвращает код 0."""
        result = _exec_cli('skills', 'search', 'media')
        assert result.returncode == 0

    def test_skills_show_nonexistent_returns_error(self):
        """Запрос несуществующего скилла возвращает ошибку."""
        result = _exec_cli('skills', 'show', 'nonexistent_skill_12345')
        assert result.returncode == 1
        assert 'Error' in result.stdout or 'Error' in result.stderr or 'не найден' in result.stdout or 'не найден' in result.stderr


class TestRagCommand:
    """Тестирование функционала команд rag."""

    def test_rag_status_returns_zero(self):
        """Команда rag status возвращает код 0."""
        result = _exec_cli('rag', 'status')
        assert result.returncode == 0

    def test_rag_unknown_subcommand_returns_error(self):
        """Неизвестная подкоманда rag возвращает ошибку."""
        result = _exec_cli('rag', 'unknown_command_12345')
        assert result.returncode in (1, 2)


class TestDocsCommand:
    """Тестирование функционала команд docs."""

    def test_docs_unknown_subcommand_returns_error(self):
        """Неизвестная подкоманда docs возвращает ошибку."""
        result = _exec_cli('docs', 'unknown_command_12345')
        assert result.returncode in (1, 2)


class TestUnknownCommand:
    """Тестирование обработки неизвестных команд верхнего уровня."""

    def test_unknown_main_command_returns_error(self):
        """Неизвестная команда возвращает ошибку и показывает справку."""
        result = _exec_cli('unknown_command_12345')
        assert result.returncode in (1, 2)


class TestPluginsCommand:
    """Тестирование функционала команд plugins."""

    def test_plugins_help(self):
        """Команда plugins --help возвращает код 0."""
        result = _exec_cli('plugins', '--help')
        assert result.returncode == 0
        assert 'list' in result.stdout
        assert 'create' in result.stdout


class TestDbCommand:
    """Тестирование функционала команд db."""

    def test_db_help(self):
        """Команда db --help возвращает код 0."""
        result = _exec_cli('db', '--help')
        assert result.returncode == 0
        assert 'status' in result.stdout
        assert 'migrate' in result.stdout
        assert 'create' in result.stdout

    def test_db_status_returns_zero(self):
        """Команда db status возвращает код 0."""
        result = _exec_cli('db', 'status')
        assert result.returncode == 0
        assert 'DATABASE MIGRATION STATUS' in result.stdout


class TestNetworkCommand:
    """Тестирование функционала команд network."""

    def test_network_help(self):
        """Команда network --help возвращает код 0."""
        result = _exec_cli('network', '--help')
        assert result.returncode == 0
        assert 'status' in result.stdout
        assert 'interfaces' in result.stdout
        assert 'analyze' in result.stdout


class TestAgentsCommand:
    """Тестирование функционала команд agents."""

    def test_agents_help(self):
        """Команда agents --help возвращает код 0."""
        result = _exec_cli('agents', '--help')
        assert result.returncode == 0
        assert 'list' in result.stdout
        assert 'run' in result.stdout

    def test_agents_list(self):
        """Команда agents list выводит список зарегистрированных агентов и манифестов."""
        result = _exec_cli('agents', 'list')
        assert result.returncode == 0
        assert 'windows_controller_agent' in result.stdout or 'AGENT_REGISTRY' in result.stdout


class TestSysParamCommand:
    """Тестирование функционала команд sys-param."""

    def test_sys_param_help(self):
        """Команда sys-param --help возвращает код 0."""
        result = _exec_cli('sys-param', '--help')
        assert result.returncode == 0
        assert 'list' in result.stdout
        assert 'preview' in result.stdout


class TestTelemetryCommand:
    """Тестирование функционала команд telemetry."""

    def test_telemetry_help(self):
        """Команда telemetry --help возвращает код 0."""
        result = _exec_cli('telemetry', '--help')
        assert result.returncode == 0
        assert 'start' in result.stdout
        assert 'audit' in result.stdout


class TestAssistCommand:
    """Тестирование перенаправления команд assist."""

    def test_assist_help_returns_zero(self):
        """Команда assist --help корректно перенаправляется."""
        result = _exec_cli('assist', '--help')
        assert result.returncode in (0, 2)


class TestRunScript:
    """Тестирование вспомогательной функции _run_script."""

    def test_run_script_nonexistent_file(self):
        """_run_script возвращает код 1 для несуществующего скрипта."""
        from manage_tools import _run_script
        result = _run_script('nonexistent_script_12345.py')
        assert result == 1

    def test_run_script_with_args(self):
        """_run_script передает дополнительные аргументы в скрипт."""
        test_script = TEST_DATA_DIR / 'echo_args.py'
        test_script.write_text('import sys; print(" ".join(sys.argv[1:])); sys.exit(0)', encoding='utf-8')
        from manage_tools import _run_script
        result = _run_script(str(test_script.relative_to(REPO_ROOT)), ['arg1', 'arg2'])
        assert result == 0


@pytest.fixture
def mock_skill_registry(monkeypatch):
    """Фикстура мока SkillRegistry."""
    mock_registry = MagicMock()
    mock_skill = MagicMock()
    mock_skill.name = 'test-skill'
    mock_skill.description = 'Test skill description'
    mock_skill.prompt.return_value = 'Test prompt content'
    mock_registry.discover.return_value = [mock_skill]
    mock_registry.search.return_value = [mock_skill]
    mock_registry.get.return_value = mock_skill
    mock_registry.export_json.return_value = '{"name": "test-skill"}'
    return mock_registry


class TestIntegration:
    """Интеграционные тесты общего сценария CLI."""

    def test_full_cli_invocation(self):
        """Интеграционный тест вызова подкоманды."""
        result = _exec_cli('skills', 'list')
        assert result.returncode == 0

    def test_command_without_subcommand_shows_help(self):
        """Вызов команды без аргументов возвращает справку."""
        result = _exec_cli('skills')
        assert result.returncode == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])