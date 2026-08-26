# `webinterface/instructions_tab` — System Instructions & Prompts Manager

## Purpose
Visual interface for managing, editing, and versioning system prompts and role descriptions used by AI models and agents.

---

## Features
- **Active Prompt Editor**: Edit active instructions (`system_instruction.md`, `narrator_style.md`).
- **Version History**: Review, diff, and restore historical prompt revisions (`vN_YYYY-MM-DD.md`).
- **Semantic Prompt Matching**: Preview which rule chunks are retrieved by `RulesRAG` during runtime.

---

## Files
- `index.html`: Prompt editor layout.
- `main.js`: Save, rollback, and versioning dispatcher.
