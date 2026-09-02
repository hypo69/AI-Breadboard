# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Verification and Structural Integrity Test for AI Breadboard
# =============================================================================
# Description:
#   Automated diagnostic tool that verifies presence and integrity of all
#   required project directories, essential configuration files, Python
#   virtual environment binaries, and core package imports.
#
# Examples:
#   python verify_installation.py
#   python verify_installation.py --json
#   python verify_installation.py --project-root "C:\path\to\AI-Breadboard"
#
# File: .agents/skills/project-installer/scripts/verify_installation.py
# Project: AI Breadboard
# Package: Installation
# Module: Verification
# Class: InstallationVerifier
# Function: main
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import importlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class VerificationResult:
    """Dataclass holding the verification results and status."""
    is_valid: bool = True
    os_name: str = platform.system()
    project_root: str = ""
    missing_directories: List[str] = field(default_factory=list)
    existing_directories: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    existing_files: List[str] = field(default_factory=list)
    venv_status: Dict[str, str] = field(default_factory=dict)
    module_status: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class InstallationVerifier:
    """Validates full structural integrity and runtime readiness of AI Breadboard."""

    REQUIRED_DIRECTORIES: List[str] = [
        "core",
        "scripts",
        "install",
        "launchers",
        "docs",
        "tests",
        "webinterface",
        ".ai",
        ".agents/skills",
        "tmp",
    ]

    REQUIRED_FILES: List[str] = [
        "header.py",
        "config.json",
        "requirements.txt",
        "INSTALL-INSTRUCTION.md",
    ]

    ALTERNATIVE_FILES: List[Tuple[str, str]] = [
        (".env", ".env.example"),
    ]

    CORE_MODULES: List[str] = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "dotenv",
        "cryptography",
        "aiohttp",
        "platformdirs",
    ]

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the InstallationVerifier.

        Args:
            project_root (Optional[Path]): Root directory of the project.
        """
        if project_root:
            self.root: Path = project_root.resolve()
        else:
            # Try finding root by locating header.py or config.json
            current: Path = Path(__file__).resolve().parent
            found_root: Optional[Path] = None
            for parent in [current] + list(current.parents):
                if (parent / "header.py").exists() and (parent / "config.json").exists():
                    found_root = parent
                    break
            self.root = found_root if found_root else Path.cwd().resolve()

    def check_directories(self, result: VerificationResult) -> None:
        """Verify presence of all mandatory directories.

        Args:
            result (VerificationResult): Result object to update.
        """
        for dir_name in self.REQUIRED_DIRECTORIES:
            dir_path: Path = self.root / dir_name
            if dir_path.is_dir():
                result.existing_directories.append(dir_name)
            else:
                result.missing_directories.append(dir_name)
                result.is_valid = False
                result.errors.append(f"Missing required directory: {dir_name}")

    def check_files(self, result: VerificationResult) -> None:
        """Verify presence of all mandatory and configuration files.

        Args:
            result (VerificationResult): Result object to update.
        """
        for file_name in self.REQUIRED_FILES:
            file_path: Path = self.root / file_name
            if file_path.is_file():
                result.existing_files.append(file_name)
            else:
                result.missing_files.append(file_name)
                result.is_valid = False
                result.errors.append(f"Missing required file: {file_name}")

        for primary, fallback in self.ALTERNATIVE_FILES:
            has_primary: bool = (self.root / primary).is_file()
            has_fallback: bool = (self.root / fallback).is_file()
            if has_primary:
                result.existing_files.append(primary)
            elif has_fallback:
                result.existing_files.append(fallback)
                result.warnings.append(
                    f"Optional file {primary} missing, found template {fallback}"
                )
            else:
                result.missing_files.append(primary)
                result.warnings.append(
                    f"Neither {primary} nor {fallback} was found in project root"
                )

    def check_virtual_environment(self, result: VerificationResult) -> Optional[Path]:
        """Check the status and executable path of the virtual environment.

        Args:
            result (VerificationResult): Result object to update.

        Returns:
            Optional[Path]: Path to python executable if valid, None otherwise.
        """
        venv_dir: Path = self.root / "venv"
        is_windows: bool = platform.system() == "Windows"

        if is_windows:
            py_exe: Path = venv_dir / "Scripts" / "python.exe"
            pip_exe: Path = venv_dir / "Scripts" / "pip.exe"
        else:
            py_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"

        if venv_dir.is_dir() and py_exe.is_file():
            result.venv_status["path"] = str(py_exe)
            result.venv_status["pip"] = str(pip_exe) if pip_exe.is_file() else "not_found"
            result.venv_status["status"] = "active"

            # Check Python version from venv
            try:
                proc = subprocess.run(
                    [str(py_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                result.venv_status["version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as ex:
                result.venv_status["version_check_error"] = str(ex)
            return py_exe
        else:
            result.venv_status["path"] = "missing"
            result.venv_status["status"] = "missing"
            result.warnings.append(
                f"Virtual environment missing at {venv_dir}. Run installer to create venv."
            )
            return None

    def check_core_modules(
        self, result: VerificationResult, python_exe: Optional[Path] = None
    ) -> None:
        """Check whether core dependencies can be imported.

        Args:
            result (VerificationResult): Result object to update.
            python_exe (Optional[Path]): Specific python binary to test against.
        """
        if python_exe and python_exe.is_file():
            # Test in external venv subprocess
            for module_name in self.CORE_MODULES:
                try:
                    proc = subprocess.run(
                        [str(python_exe), "-c", f"import {module_name}"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if proc.returncode == 0:
                        result.module_status[module_name] = "ok"
                    else:
                        result.module_status[module_name] = "missing"
                        result.warnings.append(
                            f"Module '{module_name}' failed to import in virtualenv: {proc.stderr.strip()}"
                        )
                except Exception as ex:
                    result.module_status[module_name] = f"error: {ex}"
        else:
            # Test in current Python environment
            for module_name in self.CORE_MODULES:
                try:
                    importlib.import_module(module_name)
                    result.module_status[module_name] = "ok"
                except ImportError:
                    result.module_status[module_name] = "missing"
                    result.warnings.append(
                        f"Module '{module_name}' is not installed in current Python environment"
                    )
                except Exception as ex:
                    result.module_status[module_name] = f"load_error: {type(ex).__name__}"
                    result.warnings.append(
                        f"Module '{module_name}' encountered load issue: {ex}"
                    )

    def verify_all(self) -> VerificationResult:
        """Execute full verification checks across directories, files, venv, and modules.

        Returns:
            VerificationResult: Populated validation result object.
        """
        result: VerificationResult = VerificationResult(
            project_root=str(self.root)
        )

        self.check_directories(result)
        self.check_files(result)
        python_exe: Optional[Path] = self.check_virtual_environment(result)
        self.check_core_modules(result, python_exe)

        return result


def main() -> int:
    """CLI Entry point for verification tool.

    Returns:
        int: Exit code 0 if required components exist, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Verify AI Breadboard installation integrity and directories."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default="",
        help="Path to AI Breadboard project root (default: auto-detected)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON results",
    )
    args = parser.parse_args()

    project_root_path: Optional[Path] = Path(args.project_root) if args.project_root else None
    verifier: InstallationVerifier = InstallationVerifier(project_root_path)
    result: VerificationResult = verifier.verify_all()

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print("=" * 65)
        print("🔍 AI Breadboard Installation Verification")
        print("=" * 65)
        print(f"Project Root: {result.project_root}")
        print(f"Platform:     {result.os_name}")
        print(f"Status:       {'✅ PASSED' if result.is_valid else '❌ FAILED'}")
        print("-" * 65)
        print(f"Directories:  {len(result.existing_directories)} verified, {len(result.missing_directories)} missing")
        print(f"Files:        {len(result.existing_files)} verified, {len(result.missing_files)} missing")
        print(f"Venv:         {result.venv_status.get('status', 'unknown')} ({result.venv_status.get('path', 'N/A')})")

        if result.module_status:
            ok_mods = sum(1 for v in result.module_status.values() if v == "ok")
            print(f"Modules:      {ok_mods}/{len(result.module_status)} imported successfully")

        if result.errors:
            print("\n❌ Errors:")
            for err in result.errors:
                print(f"  • {err}")

        if result.warnings:
            print("\n⚠️ Warnings:")
            for warn in result.warnings:
                print(f"  • {warn}")

        print("=" * 65)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
