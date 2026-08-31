# Unified AI Instructions Hub (`.ai/instructions`)

## Purpose
This directory is the single source of truth for general instructions, engineering standards, workflows, architecture references, and roadmap planning across all AI assistants.

Tool-specific agent configuration directories (`.amazonq`, `.kiro`, `.gemini`, `.chatgpt`) link to files here instead of duplicating behavioral rules.

---

## Directory Structure

```
.ai/instructions/
├── README.md                    ← You are here
├── rules/
│   ├── CODE_RULES.md            ← Engineering standards and code style
│   └── DOCS_RULES.md            ← Documentation rules, TDD workflow, docstrings
└── knowledge/
    ├── project_overview.md      ← System architecture and components
    ├── legacy_project_knowledge.md ← Historical context (2026)
    ├── LAUNCHER_GUIDE.md        ← Service launchers and scripts
    ├── INSTALLATION_GUIDE.md    ← Installation and setup guide
    ├── scripts_tools.md         ← CLI tools reference (manage_tools.py)
    ├── MODEL_SCRIPT_EXECUTION_GUIDE.md ← AI models script automation rules
    ├── api_documentation.md     ← REST API endpoints reference
    ├── chat.md                  ← Chat implementation and UnifiedChatModel
    ├── UI_DOCUMENTATION_SUMMARY.md ← Web UI components
    ├── UI_INTERFACES.md         ← Frontend architecture
    ├── plugins_documentation.md ← Plugin system overview
    ├── media_organizer_workflow.md ← Media organization logic
    └── codex/                   ← Auto-generated codebase reference
```

---

## Key Documents

### Engineering Standards
- **`rules/CODE_RULES.md`**: Mandatory coding standards, architecture principles, language-specific rules (Python 3.12+, PHP 8.3+, JS ES2024)
- **`rules/DOCS_RULES.md`**: Documentation standards, TDD workflow, docstring format (`hypo69 docblock`), README.md requirements

### Architecture & Design
- **`knowledge/project_overview.md`**: Overall system design, key components, data flow, module relationships
- **`knowledge/legacy_project_knowledge.md`**: Historical context and evolution of the project (August 2026)

### Operational Guides
- **`knowledge/INSTALLATION_GUIDE.md`**: Complete setup and installation procedures for Windows/Linux/macOS
- **`knowledge/LAUNCHER_GUIDE.md`**: PowerShell launchers, service startup, creating new launchers
- **`knowledge/scripts_tools.md`**: Reference for `manage_tools.py` CLI, script groups, and AI auto-execution guidelines
- **`knowledge/MODEL_SCRIPT_EXECUTION_GUIDE.md`**: When and how AI models should automatically run scripts

### Implementation Details
- **`knowledge/api_documentation.md`**: REST API endpoints, authentication, request/response formats
- **`knowledge/chat.md`**: UnifiedChatModel implementation, provider switching, RAG integration
- **`knowledge/plugins_documentation.md`**: Plugin architecture and system
- **`knowledge/media_organizer_workflow.md`**: Media library organization, metadata, storage management
- **`knowledge/UI_DOCUMENTATION_SUMMARY.md`**: Frontend components and interfaces
- **`knowledge/UI_INTERFACES.md`**: Detailed UI/UX documentation

---

## Agent Usage Rules
1. **All new general instructions** must be added exclusively within this directory.
2. **Specific IDE assistants** should reference these documents directly via relative links.
3. **Tool-specific configurations** (e.g. `.kiro/hooks/`, `.gemini/settings.json`) remain inside their respective directories.
4. **Cross-references**: Use relative links from `.md` files for navigation between documents.

---

## Quick Navigation

| Need | Document |
|------|----------|
| How to code? | `rules/CODE_RULES.md` |
| How to document? | `rules/DOCS_RULES.md` |
| How to set up? | `knowledge/INSTALLATION_GUIDE.md` |
| How to run services? | `knowledge/LAUNCHER_GUIDE.md` |
| How to use CLI tools? | `knowledge/scripts_tools.md` |
| How is the system designed? | `knowledge/project_overview.md` |
| What are the API endpoints? | `knowledge/api_documentation.md` |
| How does chat work? | `knowledge/chat.md` |

---

**Last Updated:** August 2026  
**Status:** ✅ Current and actively maintained
