# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Skill Initializer Utility
# =============================================================================
# Description:
#   Scaffolds a new standard AI Breadboard agent skill directory in
#   .agents/skills/<skill_name> with SKILL.md, README.md, scripts/, references/,
#   and assets/ folders.
#
# Examples:
#   python init_skill.py my-awesome-skill --description "Description of skill"
#
# File: .agents/skills/skill-factory/scripts/init_skill.py
# Project: AI Breadboard
# Package: SkillFactory
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
import sys
from pathlib import Path

# Find project root
CURRENT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = CURRENT_DIR.parents[1]  # .agents/skills/
PROJECT_ROOT = CURRENT_DIR.parents[2]  # project root


def create_skill(name: str, description: str = "") -> Path:
    """Create a new standard skill directory structure in .agents/skills/<name>.

    Args:
        name (str): The name of the new skill in kebab-case.
        description (str): Short description of the skill.

    Returns:
        Path: The path to the created skill directory.
    """
    skill_dir = SKILLS_ROOT / name
    if skill_dir.exists():
        print(f"⚠️ Skill directory already exists: {skill_dir}")
        return skill_dir

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "assets").mkdir(exist_ok=True)

    skill_md_content = f"""---
name: {name}
description: {description or f"Agent skill for {name}."}
---

# {name.replace('-', ' ').title()} Skill

## 🎯 Purpose
{description or f"Provides capabilities for {name}."}

## 🚀 Usage & Protocol
Describe how AI agents should execute this skill and what triggers its activation.

## ⚙️ Directory Structure
- `SKILL.md`: Main instructions and frontmatter contract.
- `README.md`: English documentation for developers.
- `scripts/`: Executable helper tools.
- `references/`: Reference documentation and guidelines.
- `assets/`: Static data, examples, and assets.
"""

    readme_content = f"""# {name.replace('-', ' ').title()}

## Overview
{description or f"Skill module for {name}."}

## Location
`.agents/skills/{name}/`
"""

    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
    (skill_dir / "README.md").write_text(readme_content, encoding="utf-8")

    print(f"✅ Successfully created skill '{name}' at:\n   {skill_dir}")
    return skill_dir


def main() -> int:
    """CLI entry point for skill initialization."""
    parser = argparse.ArgumentParser(description="Create a new AI Breadboard agent skill.")
    parser.add_argument("name", help="Name of the skill in kebab-case (e.g. data-analyzer)")
    parser.add_argument("--description", "-d", default="", help="Description of the skill")
    args = parser.parse_args()

    create_skill(args.name, args.description)
    return 0


if __name__ == "__main__":
    sys.exit(main())
