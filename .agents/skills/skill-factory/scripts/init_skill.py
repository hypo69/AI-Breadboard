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


def _contains_cyrillic(text: str) -> bool:
    """Checks if text contains Cyrillic characters."""
    return any("\u0400" <= char <= "\u04FF" for char in text)


def create_skill(
    name: str,
    description: str = "",
    description_en: str = "",
    description_ru: str = "",
    extra_i18n: dict[str, str] | None = None,
) -> Path:
    """Create a new standard skill directory structure in .agents/skills/<name>.

    Args:
        name (str): The name of the new skill in kebab-case.
        description (str): General description (auto-routed to EN or RU).
        description_en (str): Specific English description.
        description_ru (str): Specific Russian description.
        extra_i18n (dict[str, str] | None): Additional language translations.

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

    # Resolve descriptions
    en_desc = description_en.strip()
    ru_desc = description_ru.strip()
    raw_desc = description.strip()

    if not en_desc and not ru_desc and raw_desc:
        if _contains_cyrillic(raw_desc):
            ru_desc = raw_desc
            en_desc = f"Agent skill for {name}."
        else:
            en_desc = raw_desc
            ru_desc = f"Навык агента для {name}."
    elif not en_desc and not ru_desc:
        en_desc = f"Agent skill for {name}."
        ru_desc = f"Навык агента для {name}."
    elif en_desc and not ru_desc:
        ru_desc = f"Навык агента для {name}."
    elif ru_desc and not en_desc:
        en_desc = f"Agent skill for {name}."

    i18n_dict: dict[str, str] = {
        "en": en_desc,
        "ru": ru_desc,
    }
    if extra_i18n:
        for k, v in extra_i18n.items():
            if v and v.strip():
                i18n_dict[k.strip().lower()] = v.strip()

    i18n_lines = "\n".join(f"  {k}: {v}" for k, v in i18n_dict.items())

    skill_md_content = f"""---
name: {name}
description: {en_desc}
description_i18n:
{i18n_lines}
---

# {name.replace('-', ' ').title()} Skill

## 🎯 Purpose
{en_desc}

## 🚀 Usage & Protocol
Describe how AI agents should execute this skill and what triggers its activation.

## ⚙️ Directory Structure
- `SKILL.md`: Main instructions and frontmatter contract with multilingual i18n metadata.
- `README.md`: English documentation for developers.
- `scripts/`: Executable helper tools.
- `references/`: Reference documentation and guidelines.
- `assets/`: Static data, examples, and assets.
"""

    readme_content = f"""# {name.replace('-', ' ').title()}

## Overview
{en_desc}

## Localization (i18n)
- **English**: {en_desc}
- **Russian**: {ru_desc}

## Location
`.agents/skills/{name}/`
"""

    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
    (skill_dir / "README.md").write_text(readme_content, encoding="utf-8")

    print(f"✅ Successfully created skill '{name}' at:\n   {skill_dir}")
    return skill_dir


def main() -> int:
    """CLI entry point for skill initialization."""
    parser = argparse.ArgumentParser(description="Create a new AI Breadboard agent skill with multilingual support.")
    parser.add_argument("name", help="Name of the skill in kebab-case (e.g. data-analyzer)")
    parser.add_argument("--description", "-d", default="", help="General description of the skill")
    parser.add_argument("--description-en", "-en", default="", help="English description (canonical)")
    parser.add_argument("--description-ru", "-ru", default="", help="Russian description")
    args = parser.parse_args()

    create_skill(
        name=args.name,
        description=args.description,
        description_en=args.description_en,
        description_ru=args.description_ru,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
