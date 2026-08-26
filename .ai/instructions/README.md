# Unified AI Instructions Hub (`.ai/instructions`)

## Purpose
This directory is the single source of truth for general instructions, engineering standards, workflows, architecture references, and roadmap planning across all AI assistants.

Tool-specific agent configuration directories (`.amazonq`, `.kiro`, `.gemini`, `.chatgpt`) link to files here instead of duplicating behavioral rules.

---

## Directory Contents

- **`rules/CODE_RULES.md`**: Mandatory engineering standards and code style rules.
- **`knowledge/media_organizer_workflow.md`**: Media Organizer processing flow and data schemas.
- **`knowledge/torrent_and_media_principles.md`**: Torrent metadata mapping and media management conventions.
- **`knowledge/scripts_tools.md`**: CLI utility reference guide and execution flags.
- **`knowledge/legacy_project_knowledge.md`**: Historical architecture overview and evolutionary context.
- **`knowledge/codex/`**: Comprehensive codebase reference generated during repository audits.
- **`prompts/`**: Production system prompts loaded dynamically into model context.
- **`plans/roadmap.md`**: Active project requirements and future milestone roadmap.
- **`plans/legacy_amazonq_plan.md`**: Archived task completion logs.

---

## Agent Usage Rules
1. All new general instructions must be added exclusively within this directory.
2. Specific IDE assistants should reference these documents directly via relative links.
3. Tool-specific operational configurations (e.g. `.kiro/hooks/`) remain inside their respective directories.
