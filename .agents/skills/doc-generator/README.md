# Document Generator Skill (AI-Breadboard)

Automated documentation generation, validation, and synchronization toolkit.

## Overview
This skill provides complete tooling and protocols for maintaining accurate, up-to-date documentation across AI-Breadboard.

## Capabilities
- **API Documentation Generation:** Parses Python docstrings across core modules via AST and produces structured Markdown documentation in docs/ru/api/ and docs/en/api/.
- **Scripts Catalog Synchronization:** Categorizes scripts across scripts/ and root, generating structured index summaries (SCRIPTS_SUMMARY.md).
- **Docstrings & Links Validation:** Verifies docstring presence on modified files and checks internal link integrity.

## Usage
Execute via universal CLI:
`powershell
# Full batch generation (API docs + scripts catalog)
python manage_tools.py docs generate

# Validate docstrings on modified files
python manage_tools.py docs update
`

## Structure
- SKILL.md: Main skill definition with multilingual (n, 
u, s, he) metadata and agent protocols.
- README.md: English documentation for the skill package.
