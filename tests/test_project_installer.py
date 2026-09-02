# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing Project Installer Skill and Verification Suite
# =============================================================================
# Description:
#   Comprehensive unit and integration tests for AI Breadboard Project Installer
#   skill, verification logic, directory structure checks, and CLI runners.
#
# File: tests/test_project_installer.py
# Project: AI Breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = PROJECT_ROOT / ".agents" / "skills" / "project-installer"
VERIFIER_SCRIPT = SKILL_DIR / "scripts" / "verify_installation.py"

# Import InstallationVerifier dynamically
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from verify_installation import InstallationVerifier, VerificationResult


class TestProjectInstallerSkillStructure:
    """Test the structure and completeness of the project-installer skill."""

    def test_skill_directory_exists(self):
        """Check that .agents/skills/project-installer directory exists."""
        assert SKILL_DIR.is_dir(), f"Skill directory not found at {SKILL_DIR}"

    def test_skill_md_exists_and_valid(self):
        """Check that SKILL.md exists and contains required frontmatter and instructions."""
        skill_md = SKILL_DIR / "SKILL.md"
        assert skill_md.is_file(), "SKILL.md is missing from project-installer"

        content = skill_md.read_text(encoding="utf-8")
        assert "name: project-installer" in content, "SKILL.md missing name frontmatter"
        assert "gemini-3.1-flash-lite" in content, "SKILL.md missing gemini-3.1-flash-lite model reference"
        assert "INSTALL-INSTRUCTION.md" in content, "SKILL.md missing INSTALL-INSTRUCTION.md reference"
        assert "verify_installation.py" in content, "SKILL.md missing verification script reference"

    def test_install_instruction_md_in_skill(self):
        """Check that INSTALL-INSTRUCTION.md exists inside the skill directory."""
        instr_file = SKILL_DIR / "INSTALL-INSTRUCTION.md"
        assert instr_file.is_file(), "INSTALL-INSTRUCTION.md missing in skill directory"
        content = instr_file.read_text(encoding="utf-8")
        assert "install.ps1" in content, "Missing Windows install.ps1 reference in instruction"
        assert "install.sh" in content, "Missing Linux/macOS install.sh reference in instruction"
        assert len(content) > 300, "INSTALL-INSTRUCTION.md is too short"

    def test_install_instruction_md_in_root(self):
        """Check that INSTALL-INSTRUCTION.md exists in the project root."""
        root_instr = PROJECT_ROOT / "INSTALL-INSTRUCTION.md"
        assert root_instr.is_file(), "INSTALL-INSTRUCTION.md missing in project root"
        content = root_instr.read_text(encoding="utf-8")
        assert "AI Breadboard" in content, "Root INSTALL-INSTRUCTION.md missing project header"

    def test_launchers_exist(self):
        """Check that Gemini CLI runner scripts exist in the skill."""
        ps1_launcher = SKILL_DIR / "scripts" / "run_installer_gemini.ps1"
        sh_launcher = SKILL_DIR / "scripts" / "run_installer_gemini.sh"
        assert ps1_launcher.is_file(), "run_installer_gemini.ps1 is missing"
        assert sh_launcher.is_file(), "run_installer_gemini.sh is missing"

        ps1_content = ps1_launcher.read_text(encoding="utf-8")
        assert "gemini-3.1-flash-lite" in ps1_content, "PowerShell launcher missing model parameter"


class TestInstallationVerifier:
    """Test the InstallationVerifier class and verification checks."""

    @pytest.fixture
    def verifier(self):
        """Fixture returning an InstallationVerifier initialized with PROJECT_ROOT."""
        return InstallationVerifier(PROJECT_ROOT)

    def test_check_directories(self, verifier):
        """Verify that all required directories exist in the project."""
        result = VerificationResult(project_root=str(PROJECT_ROOT))
        verifier.check_directories(result)

        assert len(result.missing_directories) == 0, (
            f"Missing required directories: {result.missing_directories}"
        )
        assert "core" in result.existing_directories
        assert "scripts" in result.existing_directories
        assert "launchers" in result.existing_directories
        assert "install" in result.existing_directories

    def test_check_files(self, verifier):
        """Verify that required files are detected properly."""
        result = VerificationResult(project_root=str(PROJECT_ROOT))
        verifier.check_files(result)

        assert "header.py" in result.existing_files
        assert "config.json" in result.existing_files
        assert "requirements.txt" in result.existing_files
        assert "INSTALL-INSTRUCTION.md" in result.existing_files

    def test_verify_all_passes(self, verifier):
        """Verify that full verification passes on the repository."""
        result = verifier.verify_all()
        assert result.is_valid is True, f"Full verification failed with errors: {result.errors}"
        assert len(result.missing_directories) == 0
        assert len(result.missing_files) == 0


class TestVerificationCli:
    """Test execution of verify_installation.py as a CLI utility."""

    def test_cli_json_output(self):
        """Verify that running with --json flag outputs valid parseable JSON."""
        cmd = [sys.executable, str(VERIFIER_SCRIPT), "--project-root", str(PROJECT_ROOT), "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        assert proc.returncode == 0, f"Script failed with code {proc.returncode}: {proc.stderr}"
        data = json.loads(proc.stdout)
        assert data.get("is_valid") is True
        assert len(data.get("missing_directories", [])) == 0
        assert len(data.get("missing_files", [])) == 0

    def test_cli_human_readable_output(self):
        """Verify standard CLI formatting contains header and summary."""
        cmd = [sys.executable, str(VERIFIER_SCRIPT), "--project-root", str(PROJECT_ROOT)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        assert proc.returncode == 0, f"Script failed: {proc.stderr}"
        assert "AI Breadboard Installation Verification" in proc.stdout
        assert "PASSED" in proc.stdout
