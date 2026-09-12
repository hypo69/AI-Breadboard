# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Skill definition and registry management for AI agents
# Description: Loads, normalizes, and registers skills for various AI agents.
# File: registry.py
# Project: ai-breadboard
# Package: src.skills
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
_DEFAULT_SKILL_DIRS = (".agents/skills", ".github/skills", "skills", ".gemini/skills")

def _get_home_dir() -> Path | None:
    """Safely retrieves user home directory across platforms."""
    try:
        return Path.home()
    except Exception:
        import os
        user_profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        if user_profile:
            return Path(user_profile)
        return None

def _get_default_global_dirs() -> tuple[Path, ...]:
    """Returns accessible global user skill directories."""
    home = _get_home_dir()
    if not home:
        return ()
    return (home / ".agents" / "skills", home / ".gemini" / "skills")

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
    body_lines = match.group("body").splitlines()
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent == 0:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if not val:
                # Check for indented dictionary block
                sub_dict: dict[str, Any] = {}
                i += 1
                while i < len(body_lines):
                    sub_line = body_lines[i]
                    if not sub_line.strip() or sub_line.lstrip().startswith("#"):
                        i += 1
                        continue
                    sub_indent = len(sub_line) - len(sub_line.lstrip())
                    if sub_indent <= indent:
                        break
                    if ":" in sub_line:
                        s_key, s_val = sub_line.split(":", 1)
                        sub_dict[s_key.strip()] = _parse_scalar(s_val)
                    i += 1
                metadata[key] = sub_dict
                continue
            else:
                metadata[key] = _parse_scalar(val)
        i += 1
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
    descriptions_i18n: dict[str, str] = field(default_factory=dict)

    def get_description(self, lang: str = "en") -> str:
        """Returns skill description in requested language with fallback to EN/base."""
        if not lang:
            return self.description
        lang_key = lang.strip().lower().split("-")[0].split("_")[0]
        if lang_key in self.descriptions_i18n and self.descriptions_i18n[lang_key]:
            return self.descriptions_i18n[lang_key]
        if "en" in self.descriptions_i18n and self.descriptions_i18n["en"]:
            return self.descriptions_i18n["en"]
        return self.description

    def to_dict(self, include_instructions: bool = True, lang: str | None = None) -> dict[str, Any]:
        """Converts skill to portable JSON contract."""
        resolved_desc = self.get_description(lang) if lang else self.description
        result: dict[str, Any] = {
            "name": self.name,
            "description": resolved_desc,
            "descriptions_i18n": dict(self.descriptions_i18n),
            "root": self.root.as_posix(),
            "source": self.source.as_posix(),
            "metadata": dict(self.metadata),
            "manifest": dict(self.manifest),
        }
        if include_instructions:
            result["instructions"] = self.instructions
        return result

    def prompt(self, lang: str | None = None) -> str:
        """Returns instructions for adding to the model's system prompt."""
        return self.instructions.strip()

class SkillRegistry:
    """Searches for skills in compatible directories and provides unified access API."""

    def __init__(
        self,
        project_root: Path = __root__,
        skill_dirs: Iterable[str] = _DEFAULT_SKILL_DIRS,
        include_global: bool | None = None,
        global_dirs: Iterable[Path] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.skill_dirs = tuple(skill_dirs)
        if include_global is None:
            self.include_global = (self.project_root == Path(__root__).resolve())
        else:
            self.include_global = include_global
        resolved_global = global_dirs if global_dirs is not None else _get_default_global_dirs()
        self.global_dirs = tuple(Path(d).resolve() for d in resolved_global)

    def discover(self, lang: str | None = None) -> list[SkillDefinition]:
        """Finds all directories with SKILL.md and removes duplicates by name."""
        found: dict[str, SkillDefinition] = {}
        # 1. Project-level skill directories
        for relative_dir in self.skill_dirs:
            skills_root = self.project_root / relative_dir
            if not skills_root.is_dir():
                continue
            for skill_file in sorted(skills_root.glob("*/SKILL.md")):
                definition = self._load(skill_file)
                if definition.name and definition.name not in found:
                    found[definition.name] = definition

        # 2. Global user skill directories (if enabled)
        if self.include_global:
            for g_dir in self.global_dirs:
                if not g_dir.is_dir():
                    continue
                for skill_file in sorted(g_dir.glob("*/SKILL.md")):
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

    def search(self, query: str, lang: str | None = None) -> list[SkillDefinition]:
        """Searches for skills by name and description across all languages."""
        terms = [term.lower() for term in query.split() if term.strip()]
        if not terms:
            return self.discover(lang=lang)
        results = []
        for skill in self.discover(lang=lang):
            all_text = f"{skill.name} {skill.description} " + " ".join(skill.descriptions_i18n.values())
            if all(term in all_text.lower() for term in terms):
                results.append(skill)
        return results

    def export_json(self, name: str, include_instructions: bool = True, lang: str | None = None) -> str:
        """Exports skill to JSON for external agent or model."""
        return json.dumps(self.get(name).to_dict(include_instructions, lang=lang), ensure_ascii=False, indent=2)

    @staticmethod
    def _load(skill_file: Path) -> SkillDefinition:
        raw = skill_file.read_text(encoding="utf-8")
        metadata, instructions = _parse_frontmatter(raw)
        manifest = _load_json_manifest(skill_file.parent)
        name = str(manifest.get("name", metadata.get("name", skill_file.parent.name))).strip()

        i18n_descriptions: dict[str, str] = {}

        # 1. From manifest i18n
        manifest_i18n = manifest.get("i18n", {})
        if isinstance(manifest_i18n, dict):
            for lang_key, item in manifest_i18n.items():
                if isinstance(item, dict) and "description" in item:
                    i18n_descriptions[str(lang_key).lower()] = str(item["description"]).strip()
                elif isinstance(item, str):
                    i18n_descriptions[str(lang_key).lower()] = item.strip()

        # 2. From metadata frontmatter i18n
        for i18n_key in ("description_i18n", "descriptions_i18n", "i18n"):
            front_i18n = metadata.get(i18n_key)
            if isinstance(front_i18n, dict):
                for lang_key, text_val in front_i18n.items():
                    if isinstance(text_val, dict) and "description" in text_val:
                        i18n_descriptions[str(lang_key).lower()] = str(text_val["description"]).strip()
                    elif isinstance(text_val, str):
                        i18n_descriptions[str(lang_key).lower()] = text_val.strip()

        # 3. From suffixed keys in frontmatter (e.g. description_ru, description_en)
        for k, v in metadata.items():
            if k.startswith("description_") and len(k) > len("description_"):
                suffix = k[len("description_"):].lower()
                if suffix not in ("i18n",) and isinstance(v, str):
                    i18n_descriptions[suffix] = v.strip()

        # Base canonical description
        base_desc = str(manifest.get("description", metadata.get("description", ""))).strip()
        if not base_desc and "en" in i18n_descriptions:
            base_desc = i18n_descriptions["en"]
        elif not base_desc and i18n_descriptions:
            base_desc = next(iter(i18n_descriptions.values()))

        if base_desc and "en" not in i18n_descriptions:
            i18n_descriptions["en"] = base_desc

        merged_metadata = dict(metadata)
        merged_metadata.update({key: value for key, value in manifest.items() if key not in ("name", "description")})
        return SkillDefinition(
            name=name,
            description=base_desc,
            root=skill_file.parent,
            source=skill_file,
            metadata=merged_metadata,
            instructions=instructions,
            manifest=manifest,
            descriptions_i18n=i18n_descriptions,
        )