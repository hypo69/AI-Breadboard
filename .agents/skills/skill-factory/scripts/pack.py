# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Skill Packaging Utility
# =============================================================================
# Description:
#   Packages a skill directory from .agents/skills/<skill_name> into a
#   distributable .skill archive in the dist/ folder.
#
# Examples:
#   python pack.py .agents/skills/project-installer
#   python pack.py project-installer
#
# File: .agents/skills/skill-factory/scripts/pack.py
# Project: AI Breadboard
# Package: SkillFactory
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import os
import sys
import zipfile
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = CURRENT_DIR.parents[1]  # .agents/skills/


def package_skill(skill_target: str) -> Path:
    """Package a skill folder into a .skill archive.

    Args:
        skill_target (str): Name of the skill or path to the skill directory.

    Returns:
        Path: Path to the created .skill package.
    """
    target_path = Path(skill_target)
    if not target_path.exists():
        # Try finding in .agents/skills/<skill_target>
        target_path = SKILLS_ROOT / skill_target

    skill_path = target_path.resolve()
    if not skill_path.is_dir():
        raise FileNotFoundError(f"Skill directory not found: {skill_path}")

    output_path = skill_path / "dist"
    output_path.mkdir(parents=True, exist_ok=True)

    skill_name = skill_path.name
    skill_file = output_path / f"{skill_name}.skill"

    print(f"📦 Packaging skill from {skill_path} into {skill_file}...")

    with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(skill_path):
            # Skip build artifacts, dist, git, and python bytecode
            dirs[:] = [d for d in dirs if d not in ["dist", ".git", "__pycache__", ".pytest_cache"]]

            for file in sorted(files):
                file_path = Path(root) / file
                arcname = file_path.relative_to(skill_path)
                zipf.write(file_path, arcname)

    print(f"✅ Skill successfully packaged: {skill_file}")
    return skill_file


def main() -> int:
    """CLI Entry point for pack utility."""
    parser = argparse.ArgumentParser(description="Package an AI Breadboard agent skill.")
    parser.add_argument("skill", help="Name or path to skill folder (e.g. project-installer)")
    args = parser.parse_args()

    try:
        package_skill(args.skill)
        return 0
    except Exception as ex:
        print(f"❌ Failed to package skill: {ex}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
