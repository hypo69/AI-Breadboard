# `core.skills` Module — Universal Skills Registry

## Overview
The `core.skills` package provides a unified registry for discovering, inspecting, and managing skills across AI models, agents, and IDE tools.

---

## How It Works

1. `SkillRegistry` automatically scans skill directories in:
   - `.gemini/skills/`
   - `.agents/skills/`
   - `.github/skills/`
   - `skills/`
2. Each valid skill folder must contain a `SKILL.md` file with YAML frontmatter.
3. An optional `skill.json` file defines the machine contract: providers, capabilities, parameters, and tool interfaces.
4. The registry loads skill metadata and instructions into memory safely. Execution of skill scripts remains an explicit, isolated operation.

---

## Module Files

- `registry.py`: `SkillDefinition` data model, discovery engine, search filters, and JSON serialization.
- `__init__.py`: Public package exports and singleton accessors.

---

## Usage

```python
from core.skills import get_skill_registry

registry = get_skill_registry()
all_skills = registry.list_skills()

# Find skill by capability or name
skill = registry.get_skill("file-saver")
if skill:
    print(f"Loaded skill: {skill.name} - {skill.description}")
```
