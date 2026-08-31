# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Skill definition and registry management for AI agents
# Description: Loads, normalizes, and registers skills for various AI agents.
# File: registry.py
# Project: ai-breadboard
# Package: core.skills
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Loads, normalizes, and registers skills for various AI agents."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from header import __root__

_FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
_DEFAULT_SKILL_DIRS = (".gemini/skills", ".agents/skills", ".github/skills", "skills")

def _parse_scalar(value: str) -> Any:
    """Parses simple YAML values without requiring PyYAML dependency."""
    normalized = value.strip()
    if not normalized:
        return ""
    if normalized.startswith("[") or normalized.startswith("{"):
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            return normalized
    if normalized.lower() in ("true", "false"):
        return normalized.lower() == "true"
    if (normalized.startswith('"') and normalized.endswith('"')) or (
        normalized.startswith("'") and normalized.endswith("'")
    ):
        return normalized[1:-1]
    return normalized

def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Returns frontmatter metadata and Markdown without its header."""
    match = _FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text.strip()

    metadata: dict[str, Any] = {}
    for line in match.group("body").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = _parse_scalar(value)
    return metadata, text[match.end():].strip()

def _load_json_manifest(skill_root: Path) -> dict[str, Any]:
    """Loads optional machine contract for the skill."""
    manifest_path = skill_root / "skill.json"
    if not manifest_path.is_file():
        return {}
    try:
        parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}

@dataclass(frozen=True)
class SkillDefinition:
    """Normalized skill description suitable for any provider."""

    name: str
    description: str
    root: Path
    source: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    instructions: str = ""
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_instructions: bool = True) -> dict[str, Any]:
        """Converts skill to portable JSON contract."""
        result: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "root": self.root.as_posix(),
            "source": self.source.as_posix(),
            "metadata": dict(self.metadata),
            "manifest": dict(self.manifest),
        }
        if include_instructions:
            result["instructions"] = self.instructions
        return result

    def prompt(self) -> str:
        """Returns instructions for adding to the model's system prompt."""
        return self.instructions.strip()

class SkillRegistry:
    """Searches for skills in compatible directories and provides unified access API."""

    def __init__(self, project_root: Path = __root__, skill_dirs: Iterable[str] = _DEFAULT_SKILL_DIRS) -> None:
        self.project_root = Path(project_root).resolve()
        self.skill_dirs = tuple(skill_dirs)

    def discover(self) -> list[SkillDefinition]:
        """Finds all directories with SKILL.md and removes duplicates by name."""
        found: dict[str, SkillDefinition] = {}
        for relative_dir in self.skill_dirs:
            skills_root = self.project_root / relative_dir
            if not skills_root.is_dir():
                continue
            for skill_file in sorted(skills_root.glob("*/SKILL.md")):
                definition = self._load(skill_file)
                if definition.name and definition.name not in found:
                    found[definition.name] = definition
        return sorted(found.values(), key=lambda item: item.name)

    def get(self, name: str) -> SkillDefinition:
        """Returns skill by name or raises KeyError if not found."""
        normalized = name.strip().lower()
        for skill in self.discover():
            if skill.name.lower() == normalized:
                return skill
        raise KeyError(f"Skill not found: {name}")

    def search(self, query: str) -> list[SkillDefinition]:
        """Searches for skills by name and description."""
        terms = [term.lower() for term in query.split() if term.strip()]
        if not terms:
            return self.discover()
        return [
            skill for skill in self.discover()
            if all(term in f"{skill.name} {skill.description}".lower() for term in terms)
        ]

    def export_json(self, name: str, include_instructions: bool = True) -> str:
        """Exports skill to JSON for external agent or model."""
        return json.dumps(self.get(name).to_dict(include_instructions), ensure_ascii=False, indent=2)

    @staticmethod
    def _load(skill_file: Path) -> SkillDefinition:
        raw = skill_file.read_text(encoding="utf-8")
        metadata, instructions = _parse_frontmatter(raw)
        manifest = _load_json_manifest(skill_file.parent)
        name = str(manifest.get("name", metadata.get("name", skill_file.parent.name))).strip()
        description = str(manifest.get("description", metadata.get("description", ""))).strip()
        merged_metadata = dict(metadata)
        merged_metadata.update({key: value for key, value in manifest.items() if key not in ("name", "description")})
        return SkillDefinition(
            name=name,
            description=description,
            root=skill_file.parent,
            source=skill_file,
            metadata=merged_metadata,
            instructions=instructions,
            manifest=manifest,
        )