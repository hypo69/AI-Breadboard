# Skills Tab Web Interface

## Overview
Web interface module for managing, inspecting, creating, and packaging AI Agent Skills in AI Breadboard and Gemini CLI environments.

## Features
- **Skill Discovery & Registry**: Lists all discovered skills across `.agents/skills`, `.gemini/skills`, and `skills` directories.
- **Skill Creation**: Interactive wizard for scaffolding standard skill structures (`SKILL.md`, `README.md`, `scripts/`, `references/`, `assets/`).
- **Interactive Inspector & Editor**: Live editor for modifying instructions (`SKILL.md`), developer documentation (`README.md`), and viewing JSON contracts.
- **Packaging Utility**: Compiles skill directories into standard `.skill` ZIP archives.
- **Filtering & Search**: Real-time filtering by keyword and capability flags (scripts, references, packages).

## File Structure
- `index.html`: Main HTML component layout with Cards/Table views and creation/editing modals.
- `main.js`: `SkillsTabManager` class controlling API interactions and UI state.
- `README.md`: Module documentation.
