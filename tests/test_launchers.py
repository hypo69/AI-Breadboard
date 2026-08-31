# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for project launchers (run.ps1 and launchers/Run-*.ps1)
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: test_launchers.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Tests for project launchers (run.ps1 and launchers/Run-*.ps1).

Tests verify that:
- Main launcher run.ps1 is located in project root
- Specialized launchers are located in launchers/ directory
- Scripts follow Run-<ServiceName>.ps1 naming convention
- Contain .SYNOPSIS (valid PowerShell documentation)
- Read .env file and determine project root
- Do not contain hardcoded paths to other projects
- run.ps1 correctly invokes child launchers from launchers/ directory

Documentation: .ai_instructions/knowledge/LAUNCHER_GUIDE.md
"""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAUNCHERS_DIR = PROJECT_ROOT / "launchers"

# Main launcher in root
ROOT_LAUNCHERS = [
    "run.ps1",
]

# Helper scripts in root
ROOT_HELPER_SCRIPTS = [
    "install.ps1",
    "install_ssl_cert.ps1",
]

# Required specialized launchers in launchers/
REQUIRED_LAUNCHERS = [
    "Run-Unicorn.ps1",
    "Run-Foundry.ps1",
    "Run-LightServer.ps1",
    "Run-GeminiCli.ps1",
    "Run-Agy.ps1",
    "run_tests.ps1",
]

# Forbidden paths from other projects
FORBIDDEN_PATHS = [
    "C:\\~mediateka",
    "C:\\mediateka",
    "c:\\~mediateka",
    "c:\\mediateka",
]

class TestLaunchersStructure:
    """Test correct launcher file structure."""

    def test_launchers_dir_exists(self):
        """Launchers directory must exist in project."""
        assert LAUNCHERS_DIR.is_dir(), f"Directory {LAUNCHERS_DIR} not found"

    @pytest.mark.parametrize("launcher", ROOT_LAUNCHERS)
    def test_root_launcher_exists(self, launcher: str):
        """Main launcher must exist in project root."""
        path = PROJECT_ROOT / launcher
        assert path.is_file(), f"Main launcher {launcher} not found in project root"

    @pytest.mark.parametrize("script", ROOT_HELPER_SCRIPTS)
    def test_root_helper_script_exists(self, script: str):
        """Helper installation scripts must exist in project root."""
        path = PROJECT_ROOT / script
        assert path.is_file(), f"Script {script} not found in project root"

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_exists_in_launchers_dir(self, launcher: str):
        """Each specialized launcher must exist in launchers/."""
        path = LAUNCHERS_DIR / launcher
        assert path.is_file(), f"Launcher {launcher} not found in {LAUNCHERS_DIR}"

class TestLauncherNamingConvention:
    """Test launcher naming convention."""

    def test_no_launchers_in_tools_dir(self):
        """Tools directory must not contain Run-*.ps1 files."""
        tools_dir = PROJECT_ROOT / "tools"
        if not tools_dir.exists():
            pytest.skip("tools/ does not exist")
        ps1_in_tools = list(tools_dir.rglob("Run-*.ps1"))
        assert len(ps1_in_tools) == 0, f"Launchers must not be in tools/: {ps1_in_tools}"

    def test_no_service_launchers_in_root(self):
        """Root directory must not contain Run-*.ps1 files (they should be in launchers/)."""
        root_service_launchers = list(PROJECT_ROOT.glob("Run-*.ps1"))
        assert len(root_service_launchers) == 0, (
            f"Service launchers must be in launchers/, found in root: {root_service_launchers}"
        )

    def test_all_ps1_launchers_follow_naming(self):
        """All Run-*.ps1 in launchers/ must follow Run-PascalCase.ps1 convention."""
        launchers = [f for f in LAUNCHERS_DIR.glob("Run-*.ps1")]
        for launcher in launchers:
            name = launcher.stem  # without .ps1
            assert name.startswith("Run-"), f"{launcher.name} does not follow Run-<ServiceName>.ps1 convention"
            service = name[4:]  # remove "Run-"
            assert service[0].isupper(), f"Service name in {launcher.name} must start with uppercase letter"

class TestLauncherContent:
    """Test launcher content and logic correctness."""

    def test_run_ps1_has_synopsis(self):
        """run.ps1 must contain .SYNOPSIS."""
        path = PROJECT_ROOT / "run.ps1"
        assert path.is_file(), "run.ps1 not found"
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".SYNOPSIS" in content or "SYNOPSIS" in content.upper()

    def test_run_ps1_calls_launchers(self):
        """run.ps1 must invoke Run-Unicorn.ps1 and Run-Foundry.ps1 from launchers/."""
        path = PROJECT_ROOT / "run.ps1"
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "Run-Unicorn" in content, "run.ps1 does not reference Run-Unicorn"
        assert "launchers" in content, "run.ps1 does not reference launchers directory"

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_has_synopsis(self, launcher: str):
        """Each launcher in launchers/ must contain .SYNOPSIS."""
        path = LAUNCHERS_DIR / launcher
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".SYNOPSIS" in content or "SYNOPSIS" in content.upper(), (
            f"{launcher} does not contain .SYNOPSIS — add PowerShell documentation"
        )

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launcher_reads_env_or_config(self, launcher: str):
        """Launcher must read .env file or config.json."""
        path = LAUNCHERS_DIR / launcher
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert ".env" in content or "config.json" in content or "pytest" in content, (
            f"{launcher} does not reference project configuration"
        )

    @pytest.mark.parametrize("launcher", ["run.ps1"] + [f"launchers/{l}" for l in REQUIRED_LAUNCHERS])
    def test_launcher_no_forbidden_paths(self, launcher: str):
        """Launchers must not contain paths to other projects."""
        path = PROJECT_ROOT / launcher
        if not path.is_file():
            pytest.skip(f"{launcher} does not exist")
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_PATHS:
            assert forbidden.lower() not in content, (
                f"{launcher} contains hardcoded path to another project: {forbidden}"
            )

    @pytest.mark.parametrize("launcher", REQUIRED_LAUNCHERS)
    def test_launchers_resolve_project_root(self, launcher: str):
        """Launchers in launchers/ must determine projectRoot for correct execution from subdirectory."""
        path = LAUNCHERS_DIR / launcher
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "projectRoot" in content or "main.py" in content or "Split-Path" in content, (
            f"{launcher} must determine project root through projectRoot"
        )

class TestLauncherAccessibility:
    """Test launcher accessibility and documentation."""

    def test_launchers_only_in_launchers_directory(self):
        """Run-*.ps1 launchers must only be in launchers/ directory."""
        all_launchers = set(
            f.resolve() for f in PROJECT_ROOT.rglob("Run-*.ps1")
            if ".venv" not in str(f) and "venv" not in str(f)
        )
        expected_launchers = set(f.resolve() for f in LAUNCHERS_DIR.glob("Run-*.ps1"))
        unexpected = all_launchers - expected_launchers
        assert len(unexpected) == 0, f"Launchers found outside launchers/ directory: {unexpected}"

    def test_launcher_guide_references_all_required(self):
        """LAUNCHER_GUIDE.md must reference all required launchers."""
        guide_path = PROJECT_ROOT / ".ai" / "instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not guide_path.is_file():
            guide_path = PROJECT_ROOT / ".ai_instructions" / "knowledge" / "LAUNCHER_GUIDE.md"
        if not guide_path.is_file():
            pytest.skip("LAUNCHER_GUIDE.md does not exist")
        content = guide_path.read_text(encoding="utf-8")
        assert "run.ps1" in content, "LAUNCHER_GUIDE.md does not reference run.ps1"
        for launcher in REQUIRED_LAUNCHERS:
            assert launcher in content, f"LAUNCHER_GUIDE.md does not reference {launcher}"
