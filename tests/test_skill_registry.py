# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Тесты универсального реестра навыков."""
#
# File: test_skill_registry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты универсального реестра навыков."""

from pathlib import Path

from core.skills import SkillRegistry

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
    _write_skill(gemini_root, "media-manager", "Медиатека", "Запускай аудит.")
    _write_skill(agents_root, "db-inspector", "SQLite", "Проверяй схему.")

    registry = SkillRegistry(tmp_path)

    assert [skill.name for skill in registry.discover()] == ["db-inspector", "media-manager"]
    assert registry.get("MEDIA-MANAGER").prompt() == "Запускай аудит."

def test_registry_returns_empty_search_and_rejects_unknown_skill(tmp_path: Path) -> None:
    registry = SkillRegistry(tmp_path)

    assert registry.search("") == []
    try:
        registry.get("missing")
    except KeyError as error:
        assert "missing" in str(error), "Error должна содержать имя отсутствующего навыка"
    else:
        raise AssertionError("Неизвестный навык должен приводить к KeyError")

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