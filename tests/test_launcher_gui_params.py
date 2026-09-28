"""Тесты графического лончера (launcher.ps1 и launchers.ps1) и извлечения параметров."""

from pathlib import Path
import pytest
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestLauncherGuiParams:
    """Тесты проверки структуры и логики параметров в launcher.ps1."""

    def test_launcher_ps1_exists(self):
        """Проверка наличия главного лончера launcher.ps1 в корне проекта."""
        launcher_path = PROJECT_ROOT / 'launcher.ps1'
        assert launcher_path.is_file(), 'Файл launcher.ps1 не найден в корне проекта'

    def test_launchers_ps1_alias_exists(self):
        """Проверка наличия алиаса launchers.ps1 в корне проекта."""
        alias_path = PROJECT_ROOT / 'launchers.ps1'
        assert alias_path.is_file(), 'Файл launchers.ps1 не найден в корне проекта'

    def test_launcher_ps1_contains_parameter_parsing(self):
        """Проверка присутствия функции извлечения параметров и поддержка ValidateSet / ComboBox."""
        launcher_path = PROJECT_ROOT / 'launcher.ps1'
        content = launcher_path.read_text(encoding='utf-8', errors='ignore')
        
        assert 'Get-ScriptParameters' in content, 'launcher.ps1 должен содержать функцию Get-ScriptParameters'
        assert 'ValidateSet' in content, 'launcher.ps1 должен извлекать и обрабатывать ValidateSet'
        assert 'ComboBox' in content, 'launcher.ps1 должен использовать ComboBox для выбора значений'
        assert 'DropDownList' in content, 'ComboBox должен иметь стиль DropDownList'

    def test_launchers_ps1_references_main_launcher(self):
        """Проверка, что launchers.ps1 ссылается на launcher.ps1."""
        alias_path = PROJECT_ROOT / 'launchers.ps1'
        content = alias_path.read_text(encoding='utf-8', errors='ignore')
        assert 'launcher.ps1' in content, 'launchers.ps1 должен ссылаться на launcher.ps1'

    def test_ps1_launchers_have_valid_param_blocks(self):
        """Проверка, что все сервисные лончеры в launchers/ имеют параметры с документацией."""
        launchers_dir = PROJECT_ROOT / 'launchers'
        assert launchers_dir.is_dir()
        
        ps1_files = list(launchers_dir.glob('Run-*.ps1'))
        assert len(ps1_files) > 0, 'Директория launchers/ должна содержать Run-*.ps1 скрипты'
        
        for ps1 in ps1_files:
            content = ps1.read_text(encoding='utf-8', errors='ignore')
            assert 'param (' in content or 'param(' in content, f'Скрипт {ps1.name} должен содержать блок param()'
