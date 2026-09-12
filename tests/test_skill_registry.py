# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing universal skill registry
# =============================================================================
# Description:
#   Tests for universal skill registry functionality and discovery.
#
# File: test_skill_registry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Tests for universal skill registry."""

from pathlib import Path

from src.skills import SkillRegistry

def _write_skill(root: Path, name: str, description: str, body: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n",
        encoding="utf-8",
    )

def test_registry_discovers_gemini_and_agent_skill_roots(tmp_path: Path) -> None:
    gemini_root = tmp_path / ".gemini" / "skills"
    agents_root = tmp_path / ".agents" / "skills"
    gemini_root.mkdir(parents=True)
    agents_root.mkdir(parents=True)
    _write_skill(gemini_root, "media-manager", "Media library", "Start audit.")
    _write_skill(agents_root, "db-inspector", "SQLite", "Check schema.")

    registry = SkillRegistry(tmp_path)

    assert [skill.name for skill in registry.discover()] == ["db-inspector", "media-manager"]
    assert registry.get("MEDIA-MANAGER").prompt() == "Start audit."

def test_registry_returns_empty_search_and_rejects_unknown_skill(tmp_path: Path) -> None:
    registry = SkillRegistry(tmp_path)

    assert registry.search("") == []
    try:
        registry.get("missing")
    except KeyError as error:
        assert "missing" in str(error), "Error should contain name of missing skill"
    else:
        raise AssertionError("Unknown skill should raise KeyError")

def test_registry_prefers_json_contract_and_exports_portable_json(tmp_path: Path) -> None:
    skills_root = tmp_path / ".gemini" / "skills"
    skills_root.mkdir(parents=True)
    _write_skill(skills_root, "storage", "Markdown description", "Read the Markdown instructions.")
    (skills_root / "storage" / "skill.json").write_text(
        '{"name": "storage", "description": "JSON description", "providers": ["gemini", "ollama"]}',
        encoding="utf-8",
    )

    exported = SkillRegistry(tmp_path).export_json("storage")

    assert '"description": "JSON description"' in exported
    assert '"providers": [' in exported
    assert "Read the Markdown instructions." in exported

def test_registry_multilingual_frontmatter_nested_dict(tmp_path: Path) -> None:
    agents_root = tmp_path / ".agents" / "skills" / "i18n-skill"
    agents_root.mkdir(parents=True)
    (agents_root / "SKILL.md").write_text(
        "---\n"
        "name: i18n-skill\n"
        "description: Default English description\n"
        "description_i18n:\n"
        "  en: English localized description\n"
        "  ru: Русское локализованное описание\n"
        "  es: Descripción localizada en español\n"
        "---\n\n"
        "# I18n Skill\nInstructions here.\n",
        encoding="utf-8",
    )

    registry = SkillRegistry(tmp_path)
    skill = registry.get("i18n-skill")

    assert skill.get_description("ru") == "Русское локализованное описание"
    assert skill.get_description("es") == "Descripción localizada en español"
    assert skill.get_description("en") == "English localized description"
    assert skill.get_description("de") == "English localized description"  # fallback to EN
    assert skill.to_dict(lang="ru")["description"] == "Русское локализованное описание"

    # Search in RU and ES
    assert len(registry.search("Русское")) == 1
    assert len(registry.search("español")) == 1

def test_registry_multilingual_frontmatter_suffixed_keys(tmp_path: Path) -> None:
    agents_root = tmp_path / ".agents" / "skills" / "suffixed-skill"
    agents_root.mkdir(parents=True)
    (agents_root / "SKILL.md").write_text(
        "---\n"
        "name: suffixed-skill\n"
        "description: Canonical description\n"
        "description_ru: Описание на русском\n"
        "description_es: Descripción en español\n"
        "---\n\n"
        "# Suffixed Skill\n",
        encoding="utf-8",
    )

    registry = SkillRegistry(tmp_path)
    skill = registry.get("suffixed-skill")

    assert skill.get_description("ru") == "Описание на русском"
    assert skill.get_description("es") == "Descripción en español"
    assert skill.get_description("en") == "Canonical description"

def test_init_skill_scaffolding_multilingual(tmp_path: Path, monkeypatch) -> None:
    import importlib.util
    init_script_path = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "skill-factory" / "scripts" / "init_skill.py"
    spec = importlib.util.spec_from_file_location("init_skill", init_script_path)
    init_skill_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(init_skill_mod)

    monkeypatch.setattr(init_skill_mod, "SKILLS_ROOT", tmp_path / ".agents" / "skills")

    skill_path = init_skill_mod.create_skill(
        name="custom-skill",
        description_en="English description for custom skill",
        description_ru="Русское описание кастомного навыка",
    )

    registry = SkillRegistry(tmp_path)
    skill = registry.get("custom-skill")

    assert skill.get_description("en") == "English description for custom skill"
    assert skill.get_description("ru") == "Русское описание кастомного навыка"
    assert skill.to_dict(lang="ru")["description"] == "Русское описание кастомного навыка"


