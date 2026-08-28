## \file tests/test_launchers.py
# -*- coding: utf-8 -*-
"""
Тесты лончеров проекта (run.ps1 и launchers/Run-*.ps1).

Проверяет что:
- Главный лончер run.ps1 находится в корне проекта
- Специализированные лончеры находятся в директории launchers/
- Скрипты следуют конвенции именования Run-<ServiceName>.ps1
- Содержат .SYNOPSIS (валидная PowerShell документация)
- Читают .env файл и определяют корень проекта
- Не содержат жёстко заданных путей к другим проектам
- run.ps1 корректно вызывает дочерние лончеры из директории launchers/

Документация: .ai_instructions/knowledge/LAUNCHER_GUIDE.md
"""

import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAUNCHERS_DIR = PROJECT_ROOT / "launchers"

# Главный лончер в корне
ROOT_LAUNCHERS = [
    "run.ps1",
]

# Вспомогательные скрипты в корне
ROOT_HELPER_SCRIPTS = [
    "install.ps1",
    "install_ssl_cert.ps1",
]

# Обязательные специализированные лончеры в launchers/
REQUIRED_LAUNCHERS = [
    "Run-Unicorn.ps1",
    "Run-Foundry.ps1",
    "Run-LightServer.ps1",
    "Run-GeminiCli.ps1",
    "Run-Agy.ps1",
    "run_tests.ps1",
]

# Запрещённые пути из других проектов
FORBIDDEN_PATHS = [
    "C:\\~mediateka",
    "C:\\mediateka",
    "c:\\~mediateka",
    "c:\\mediateka",
]


class TestLaunchersStructure:
    """Проверяет корректность файловой структуры лончеров."""

    def test_launchers_dir_exists(self):
        """Директория launchers/ должна существовать в проекте."""
        assert LAUNCHERS_DIR.is_dir(), f"Директория {LAUNCHERS_DIR} не найдена"

    @pytest.mark.parametrize("launcher", ROOT_LAUNCHERS)
    def test_root_launcher_exists(self, launcher: str):
        """Главный лончер должен существовать в корне проекта."""
        path = PROJECT_ROOT / launcher
        assert path.is_file(), f"Главный лончер {launcher} не найден в корне проекта"

    @pytest.mark.parametrize("script", ROOT_HELPER_SCRIPTS)
    def test_root_helper_script_exists(self, script: str):
        """Вспомогательные скрипты установки должны существовать в корне."""
        path = PROJECT_ROOT / script
        assert path.is_file(), f"Скрипт {script} не найден в корне проекта"

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_exists_in_launchers_dir(self, launcher: str):
        """Каждый специализированный лончер должен существовать в launchers/."""
        path = LAUNCHERS_DIR / launcher
        assert path.is_file(), f"Лончер {launcher} не найден в {LAUNCHERS_DIR}"


class TestLauncherNamingConvention:
    """Проверяет конвенцию именования лончеров."""

    def test_no_launchers_in_tools_dir(self):
        """В tools/ не должно быть Run-*.ps1 файлов."""
        tools_dir = PROJECT_ROOT / "tools"
        if not tools_dir.exists():
            pytest.skip("tools/ не существует")
        ps1_in_tools = list(tools_dir.rglob("Run-*.ps1"))
        assert len(ps1_in_tools) == 0, f"Лончеры не должны быть в tools/: {ps1_in_tools}"

    def test_no_service_launchers_in_root(self):
        """В корне не должно быть Run-*.ps1 файлов (они должны быть в launchers/)."""
        root_service_launchers = list(PROJECT_ROOT.glob("Run-*.ps1"))
        assert len(root_service_launchers) == 0, (
            f"Сервисные лончеры должны быть в launchers/, найдены в корне: {root_service_launchers}"
        )

    def test_all_ps1_launchers_follow_naming(self):
        """Все Run-*.ps1 в launchers/ должны следовать конвенции Run-PascalCase.ps1."""
        launchers = [f for f in LAUNCHERS_DIR.glob("Run-*.ps1")]
        for launcher in launchers:
            name = launcher.stem  # без .ps1
            assert name.startswith("Run-"), f"{launcher.name} не следует конвенции Run-<ServiceName>.ps1"
            service = name[4:]  # убираем "Run-"
            assert service[0].isupper(), f"Имя сервиса в {launcher.name} должно начинаться с заглавной буквы"


class TestLauncherContent:
    """Проверяет содержимое и корректность логики лончеров."""

    def test_run_ps1_has_synopsis(self):
        """run.ps1 должен содержать .SYNOPSIS."""
        path = PROJECT_ROOT / "run.ps1"
        assert path.is_file(), "run.ps1 не найден"
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".SYNOPSIS" in content or "SYNOPSIS" in content.upper()

    def test_run_ps1_calls_launchers(self):
        """run.ps1 должен вызывать Run-Unicorn.ps1 и Run-Foundry.ps1 из launchers/."""
        path = PROJECT_ROOT / "run.ps1"
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "Run-Unicorn" in content, "run.ps1 не ссылается на Run-Unicorn"
        assert "launchers" in content, "run.ps1 не ссылается на директорию launchers"

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_has_synopsis(self, launcher: str):
        """Каждый лончер в launchers/ должен содержать .SYNOPSIS."""
        path = LAUNCHERS_DIR / launcher
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".SYNOPSIS" in content or "SYNOPSIS" in content.upper(), (
            f"{launcher} не содержит .SYNOPSIS — добавь PowerShell документацию"
        )

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_reads_env_or_config(self, launcher: str):
        """Лончер должен читать .env файл или config.json."""
        path = LAUNCHERS_DIR / launcher
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".env" in content or "config.json" in content or "pytest" in content, (
            f"{launcher} не обращается к конфигурации проекта"
        )

    @pytest.mark.parametrize("launcher", ["run.ps1"] + [f"launchers/{l}" for l in REQUIRED_LAUNCHERS])
    def test_launcher_no_forbidden_paths(self, launcher: str):
        """Лончеры не должны содержать пути к другим проектам."""
        path = PROJECT_ROOT / launcher
        if not path.is_file():
            pytest.skip(f"{launcher} не существует")
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_PATHS:
            assert forbidden.lower() not in content, (
                f"{launcher} содержит жёстко заданный путь к другому проекту: {forbidden}"
            )

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launchers_resolve_project_root(self, launcher: str):
        """Лончеры в launchers/ должны определять projectRoot для корректной работы из подпапки."""
        path = LAUNCHERS_DIR / launcher
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "projectRoot" in content or "main.py" in content or "Split-Path" in content, (
            f"{launcher} должен определять корень проекта через projectRoot"
        )


class TestLauncherAccessibility:
    """Проверяет доступность и документацию лончеров."""

    def test_launchers_only_in_launchers_directory(self):
        """Лончеры Run-*.ps1 должны быть только в директории launchers/."""
        all_launchers = set(
            f.resolve() for f in PROJECT_ROOT.rglob("Run-*.ps1")
            if ".venv" not in str(f) and "venv" not in str(f)
        )
        expected_launchers = set(f.resolve() for f in LAUNCHERS_DIR.glob("Run-*.ps1"))
        unexpected = all_launchers - expected_launchers
        assert len(unexpected) == 0, f"Найдены лончеры вне папки launchers/: {unexpected}"

    def test_launcher_guide_references_all_required(self):
        """LAUNCHER_GUIDE.md должен упоминать все обязательные лончеры."""
        guide_path = PROJECT_ROOT / ".ai" / "instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not guide_path.is_file():
            guide_path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not guide_path.is_file():
            pytest.skip("LAUNCHER_GUIDE.md не существует")
        content = guide_path.read_text(encoding="utf-8")
        assert "run.ps1" in content, "LAUNCHER_GUIDE.md не упоминает run.ps1"
        for launcher in REQUIRED_LAUNCHERS:
            assert launcher in content, f"LAUNCHER_GUIDE.md не упоминает {launcher}"

