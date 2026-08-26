## \file tests/test_launchers.py
# -*- coding: utf-8 -*-
"""
Тесты лончеров проекта (Run-*.ps1).

Проверяет что все лончеры:
- Находятся в корне проекта
- Следуют конвенции именования Run-<ServiceName>.ps1
- Содержат .SYNOPSIS (валидная PowerShell документация)
- Читают .env файл
- Не содержат жёстко заданных путей к другим проектам

Документация: .ai_instructions/knowledge/LAUNCHER_GUIDE.md
"""

import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Обязательный список лончеров согласно LAUNCHER_GUIDE.md
REQUIRED_LAUNCHERS = [
    "run.ps1",
    "Run-Unicorn.ps1",
    "Run-Foundry.ps1",
    "Run-LightServer.ps1",
    "Run-GeminiCli.ps1",
    "Run-Agy.ps1",
]

# Вспомогательные скрипты (не лончеры, но должны быть в корне)
REQUIRED_HELPER_SCRIPTS = [
    "install.ps1",
    "install_ssl_cert.ps1",
    "run_tests.ps1",
]

# Запрещённые пути из других проектов
FORBIDDEN_PATHS = [
    "C:\\~mediateka",
    "C:\\mediateka",   # старый путь без 'i'
    "c:\\~mediateka",
    "c:\\mediateka",
]


class TestLaunchersExistInRoot:
    """Проверяет что все обязательные лончеры находятся в корне."""

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_exists_in_root(self, launcher: str):
        """Каждый обязательный лончер должен существовать в корне проекта."""
        path = PROJECT_ROOT / launcher
        assert path.is_file(), \
            f"Лончер {launcher} не найден в корне проекта {PROJECT_ROOT}"

    @pytest.mark.parametrize("script", REQUIRED_HELPER_SCRIPTS)
    def test_helper_script_exists(self, script: str):
        """Вспомогательные скрипты должны существовать в корне."""
        path = PROJECT_ROOT / script
        assert path.is_file(), \
            f"Скрипт {script} не найден в корне проекта"


class TestLauncherNamingConvention:
    """Проверяет конвенцию именования лончеров."""

    def test_no_launchers_in_tools_dir(self):
        """В tools/ не должно быть Run-*.ps1 файлов."""
        tools_dir = PROJECT_ROOT / "tools"
        if not tools_dir.exists():
            pytest.skip("tools/ не существует")
        ps1_in_tools = list(tools_dir.rglob("Run-*.ps1"))
        assert len(ps1_in_tools) == 0, \
            f"Лончеры не должны быть в tools/: {ps1_in_tools}"

    def test_all_ps1_launchers_follow_naming(self):
        """Все Run-*.ps1 в корне должны следовать конвенции Run-PascalCase.ps1."""
        launchers = [f for f in PROJECT_ROOT.glob("Run-*.ps1")]
        for launcher in launchers:
            name = launcher.stem  # без .ps1
            assert name.startswith("Run-"), \
                f"{launcher.name} не следует конвенции Run-<ServiceName>.ps1"
            service = name[4:]  # убираем "Run-"
            assert service[0].isupper(), \
                f"Имя сервиса в {launcher.name} должно начинаться с заглавной буквы"


class TestLauncherContent:
    """Проверяет содержимое лончеров."""

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_has_synopsis(self, launcher: str):
        """Каждый лончер должен содержать .SYNOPSIS (PowerShell документация)."""
        path = PROJECT_ROOT / launcher
        if not path.is_file():
            pytest.skip(f"{launcher} не существует")
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".SYNOPSIS" in content or "SYNOPSIS" in content.upper(), \
            f"{launcher} не содержит .SYNOPSIS — добавь PowerShell документацию"

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_reads_env(self, launcher: str):
        """Лончер должен читать .env файл."""
        path = PROJECT_ROOT / launcher
        if not path.is_file():
            pytest.skip(f"{launcher} не существует")
        # run.ps1 вызывает другие лончеры, которые читают .env напрямую
        if launcher == "run.ps1":
            content = path.read_text(encoding="utf-8", errors="ignore")
            assert ".env" in content or "Run-Unicorn" in content, \
                f"{launcher} не ссылается на .env или дочерние лончеры"
            return
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".env" in content, \
            f"{launcher} не читает .env файл"

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_no_forbidden_paths(self, launcher: str):
        """Лончер не должен содержать пути к другим проектам."""
        path = PROJECT_ROOT / launcher
        if not path.is_file():
            pytest.skip(f"{launcher} не существует")
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_PATHS:
            assert forbidden.lower() not in content, \
                f"{launcher} содержит жёстко заданный путь к другому проекту: {forbidden}"

    def test_run_ps1_calls_unicorn(self):
        """run.ps1 должен вызывать Run-Unicorn.ps1."""
        path = PROJECT_ROOT / "run.ps1"
        if not path.is_file():
            pytest.skip("run.ps1 не существует")
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "Run-Unicorn" in content, \
            "run.ps1 не вызывает Run-Unicorn.ps1"



class TestLauncherAccessibility:
    """Проверяет доступность лончеров для агентов ИИ."""

    def test_launchers_not_in_subdirectories(self):
        """
        Лончеры Run-*.ps1 должны быть ТОЛЬКО в корне, не в поддиректориях.
        Это гарантирует что агент всегда знает где их искать.
        """
        root_launchers = set(f.name for f in PROJECT_ROOT.glob("Run-*.ps1"))
        all_launchers = set(f.name for f in PROJECT_ROOT.rglob("Run-*.ps1")
                            if ".venv" not in str(f) and "venv" not in str(f))
        nested = all_launchers - root_launchers
        assert len(nested) == 0, \
            f"Найдены лончеры вне корня проекта: {nested}"

    def test_launcher_guide_references_all_required(self):
        """LAUNCHER_GUIDE.md должен упоминать все обязательные лончеры."""
        guide_path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not guide_path.is_file():
            pytest.skip("LAUNCHER_GUIDE.md не существует")
        content = guide_path.read_text(encoding="utf-8")
        for launcher in REQUIRED_LAUNCHERS:
            assert launcher in content, \
                f"LAUNCHER_GUIDE.md не упоминает {launcher}"
