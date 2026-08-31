# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Валидация и проверка установщиков AI Breadboard
# =============================================================================
# Description:
#   Утилита для проверки логики установщиков, валидации конфигурации
#   и тестирования кроссплатформенной совместимости.
#
# Examples:
#   python validate_installers.py
#   python validate_installers.py --check-python
#   python validate_installers.py --check-bash
#
# File: validate_installers.py
# Project: AI Breadboard
# Package: Installation
# Module: Validation
# Class: InstallerValidator
# Function: validate_all
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class InstallerValidator:
    """Валидатор логики установщиков."""

    def __init__(self, install_dir: Path):
        """Initialization валидатора.

        Args:
            install_dir (Path): Директория install/.
        """
        self.install_dir: Path = install_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_python_installer(self) -> bool:
        """Проверка логики Python установщика.

        Returns:
            bool: Успешность проверки.

        Examples:
            >>> validator = InstallerValidator(Path("install"))
            >>> success = validator.validate_python_installer()
            >>> print(success)
        """
        print("[1/3] Validating Python installer...")

        python_file: Path = self.install_dir / "install.py"

        if not python_file.exists():
            self.errors.append("install.py not found")
            return False

        content: str = python_file.read_text(encoding="utf-8")

        # Проверка наличия класса Installer
        if "class Installer:" not in content:
            self.errors.append("Installer class not found in install.py")
            return False

        # Проверка наличия методов
        required_methods: List[str] = [
            "find_python",
            "create_venv",
            "upgrade_pip",
            "install_dependencies",
            "verify_environment",
            "run"
        ]

        for method in required_methods:
            if f"def {method}(" not in content:
                self.errors.append(f"Method {method} not found in Installer class")
                return False

        # Проверка мультиязычности
        languages: List[str] = ["ru", "en", "es", "he"]
        for lang in languages:
            if f'"{lang}":' not in content:
                self.warnings.append(f"Language {lang} not found in I18N")

        # Проверка отсутствия None
        if " = None" in content or ": None" in content:
            self.warnings.append("Found 'None' assignments in install.py (violates CODE_RULES)")

        print("✓ Python installer validation passed")
        return True

    def validate_bash_installer(self) -> bool:
        """Проверка логики Bash установщика.

        Returns:
            bool: Успешность проверки.

        Examples:
            >>> validator = InstallerValidator(Path("install"))
            >>> success = validator.validate_bash_installer()
            >>> print(success)
        """
        print("[2/3] Validating Bash installer...")

        bash_file: Path = self.install_dir / "install.sh"

        if not bash_file.exists():
            self.errors.append("install.sh not found")
            return False

        content: str = bash_file.read_text(encoding="utf-8")

        # Проверка shebang
        if not content.startswith("#!/bin/bash"):
            self.errors.append("Bash installer missing shebang")
            return False

        # Проверка наличия функций
        required_functions: List[str] = [
            "select_language",
            "find_python",
            "create_venv",
            "upgrade_pip",
            "install_dependencies",
            "verify_environment",
            "main"
        ]

        for func in required_functions:
            if f"{func}()" not in content:
                self.errors.append(f"Function {func} not found in install.sh")
                return False

        # Проверка мультиязычности
        languages: List[str] = ["MESSAGES_RU", "MESSAGES_EN", "MESSAGES_ES"]
        for lang in languages:
            if f"declare -A {lang}" not in content:
                self.warnings.append(f"Language {lang} not found in install.sh")

        print("✓ Bash installer validation passed")
        return True

    def validate_config_json(self) -> bool:
        """Проверка конфигурации install.json.

        Returns:
            bool: Успешность проверки.

        Examples:
            >>> validator = InstallerValidator(Path("install"))
            >>> success = validator.validate_config_json()
            >>> print(success)
        """
        print("[3/3] Validating install.json...")

        config_file: Path = self.install_dir / "install.json"

        if not config_file.exists():
            self.errors.append("install.json not found")
            return False

        try:
            config: Dict = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            self.errors.append(f"Invalid JSON in install.json: {ex}")
            return False

        # Проверка обязательных полей
        required_fields: List[str] = [
            "defaults",
            "paths",
            "env_vars",
            "verify",
            "supported_languages"
        ]

        for field in required_fields:
            if field not in config:
                self.errors.append(f"Missing required field in config: {field}")
                return False

        # Проверка поддерживаемых языков
        supported_langs: List[str] = config.get("supported_languages", [])
        expected_langs: List[str] = ["ru", "en", "es", "he"]

        for lang in expected_langs:
            if lang not in supported_langs:
                self.warnings.append(f"Language {lang} not in supported_languages")

        # Проверка Python версий
        python_versions: List[str] = config.get("defaults", {}).get(
            "python_preferred_versions", []
        )
        if not python_versions:
            self.warnings.append("No Python versions specified in config")

        print("✓ Configuration validation passed")
        return True

    def validate_consistency(self) -> bool:
        """Проверка консистентности между установщиками.

        Returns:
            bool: Успешность проверки.

        Examples:
            >>> validator = InstallerValidator(Path("install"))
            >>> success = validator.validate_consistency()
            >>> print(success)
        """
        print("\nValidating consistency between installers...")

        python_file: Path = self.install_dir / "install.py"
        bash_file: Path = self.install_dir / "install.sh"

        if not python_file.exists() or not bash_file.exists():
            return False

        python_content: str = python_file.read_text(encoding="utf-8")
        bash_content: str = bash_file.read_text(encoding="utf-8")

        # Проверка одинакового количества шагов
        python_steps: int = len(re.findall(r"step_\d+", python_content))
        bash_steps: int = len(re.findall(r"step_\d+", bash_content))

        if python_steps != bash_steps:
            self.warnings.append(
                f"Step count mismatch: Python={python_steps}, Bash={bash_steps}"
            )

        # Проверка одинаковых профилей установки
        python_profiles: List[str] = re.findall(r'"([1-5])":', python_content)
        bash_profiles: List[str] = re.findall(r'case "\$profile" in\s+(\d)', bash_content)

        if set(python_profiles) != set(bash_profiles):
            self.warnings.append("Installation profiles mismatch between installers")

        print("✓ Consistency validation passed")
        return True

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Полная валидация всех установщиков.

        Returns:
            Tuple[bool, List[str], List[str]]: (успех, ошибки, предупреждения).

        Examples:
            >>> validator = InstallerValidator(Path("install"))
            >>> success, errors, warnings = validator.validate_all()
            >>> print(f"Success: {success}, Errors: {len(errors)}, Warnings: {len(warnings)}")
        """
        print("=" * 60)
        print("AI Breadboard Installer Validation")
        print("=" * 60)
        print()

        results: List[bool] = [
            self.validate_python_installer(),
            self.validate_bash_installer(),
            self.validate_config_json(),
            self.validate_consistency()
        ]

        print()
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        success: bool = all(results) and not self.errors

        if success:
            print("\n✅ All validations passed!")
        else:
            print("\n❌ Validation failed!")

        print("=" * 60)

        return success, self.errors, self.warnings


def main() -> int:
    """Главная функция валидатора.

    Returns:
        int: Код выхода (0 — успех, 1 — ошибка).

    Examples:
        >>> exit_code = main()
        >>> sys.exit(exit_code)
    """
    install_dir: Path = Path(__file__).parent

    validator: InstallerValidator = InstallerValidator(install_dir)
    success, errors, warnings = validator.validate_all()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
