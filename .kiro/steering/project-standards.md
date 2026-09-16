---
name: Project Standards
description: Overall project guidelines, architecture decisions, and development practices
inclusion: auto
---

# 🚀 Project Standards & Development Guidelines

Central steering document that coordinates all development standards for the AI-Breadboard project.

## Quick Navigation

| Topic | Document |
|-------|----------|
| **Code Quality** | `engineering-standards.md` |
| **Documentation** | `documentation-standards.md` |
| **Full Details** | `.ai/instructions/` |

## Project Overview

**ai-breadboard** is a comprehensive system for:
- AI model integration (Gemini, OpenAI, Groq, Ollama, etc.)
- Document processing and RAG (Retrieval-Augmented Generation)
- Media organization and automation
- Plugin ecosystem with MCP support
- Web administration interface
- Service orchestration

## Architecture Principles

### 1. Modular Design
- Each component has single responsibility
- Modules can be tested and deployed independently
- Clear interfaces between components

### 2. Configuration-Driven
- All settings come from config files or environment
- No hardcoded values (ports, URLs, timeouts, etc.)
- Secrets stored separately from code

### 3. Type Safety
- All functions have type hints
- Runtime type validation
- **None is FORBIDDEN** - use empty defaults instead

### 4. Developer-Friendly
- Clear error messages
- Comprehensive logging
- Well-documented code
- TDD workflow

## Tech Stack

### Backend
- **Python 3.12+** with FastAPI
- **PostgreSQL** for persistent data
- **Redis** for caching and sessions
- **WebSockets** for real-time updates

### Frontend
- **ES2024 JavaScript/TypeScript**
- **Bootstrap 5** for UI components
- **Modular architecture** for maintainability
- **LocalStorage** for client-side persistence

### DevOps
- **PowerShell** scripts for Windows automation
- **Docker** for containerization
- **GitHub Actions** for CI/CD

## Project Structure

```
.
├── .ai/instructions/          ← Unified AI instructions hub
│   ├── rules/                 ← CODE_RULES, DOCS_RULES, REUSE_RULES
│   └── knowledge/             ← Architecture, API docs, guides
├── .kiro/                     ← Kiro IDE configuration
│   ├── steering/              ← Auto-loaded project guidelines
│   └── hooks/                 ← Automation hooks
├── src/
│   ├── app/                   ← FastAPI application core
│   ├── ai/                    ← AI provider integration
│   ├── api/                   ← REST API endpoints
│   └── webinterface/          ← Web UI frontend
├── apps/                      ← Application modules
├── tests/                     ← Test suite
└── docs/ru/                   ← Russian documentation
```

## Development Workflow

### 1. Planning
- Analyze requirements
- Check for existing implementations (REUSE_RULES)
- Design architecture
- Write specification

### 2. Implementation (TDD-doc-gen)
- Write docstring first
- Implement function
- Write tests (70%+ coverage)
- Add comments explaining design

### 3. Quality Assurance
- Run linters and type checkers
- Execute full test suite
- Code review checklist
- Documentation review

### 4. Integration
- Merge to development branch
- Run CI/CD pipeline
- Deploy to staging
- Verify in staging environment

## Key Standards Summary

### Code Standards
- ✅ SRP (Single Responsibility Principle)
- ✅ Type hints on all functions
- ✅ Early returns and fail-fast
- ✅ No global state
- ✅ NO `None` - use empty defaults
- ✅ Configuration, not hardcode
- ✅ Max 3 nesting levels
- ✅ Max 500 lines per function

### Documentation Standards
- ✅ Docstrings for all functions/classes
- ✅ hypo69 docblock format
- ✅ Comments explain WHY, not WHAT
- ✅ README.md for every module
- ✅ Russian language for docs
- ✅ Examples in docstrings
- ✅ File headers in all files

### Testing Standards
- ✅ Minimum 70% code coverage
- ✅ TDD workflow (test-first approach)
- ✅ Clear test names
- ✅ Integration tests for APIs
- ✅ Automated CI/CD

### Git Standards
- ✅ Descriptive commit messages
- ✅ Feature branches for development
- ✅ Pull request with tests passing
- ✅ Code review before merge

## Common Tasks

### Adding a New Feature

1. **Read** existing code and specifications
2. **Plan** your changes
3. **Write** docstring + tests first
4. **Implement** following CODE_RULES
5. **Test** with pytest
6. **Document** in README.md
7. **Commit** with clear message

### Refactoring Existing Code

1. **Analyze** current implementation
2. **Design** better approach
3. **Write** tests for current behavior
4. **Refactor** following standards
5. **Verify** tests still pass
6. **Update** docstrings and comments
7. **Commit** with "Refactor:" prefix

### Creating New Module

1. **Create** directory structure
2. **Add** `__init__.py` and core modules
3. **Write** `README.md` with architecture
4. **Create** `router.py` for FastAPI endpoints
5. **Write** tests in `tests/`
6. **Register** in main application
7. **Add** to admin interface
8. **Document** in project README

### Integrating New Application

Follow the 6-step Application Lifecycle:
1. Logic & TUI in `apps/<app_name>/`
2. FastAPI Router with `/api/v1/<app>` endpoints
3. Server mount in `src/app/__init__.py`
4. Web tab in `src/api/webinterface/<app>_tab/`
5. Admin navigation and panes
6. TDD with pytest and README

## Language Support

### Russian (Default)
- All docstrings
- All comments
- All documentation
- All file headers
- All log messages

### English (Code Identifiers Only)
- Function names: `fetch_user_data()`
- Variable names: `api_response`
- Class names: `UserHandler`
- Constants: `MAX_RETRIES`

## IDE Integration

This project is configured for **Kiro IDE**:

### Steering Files (Auto-loaded)
- `engineering-standards.md` - Applied to all coding tasks
- `documentation-standards.md` - Applied to all documentation
- `project-standards.md` - This file, provides overview

### Hooks (Automation)
- Pre-commit checks
- Post-save linting
- Test execution
- Documentation generation

### MCP Servers (Optional)
- AWS Documentation
- Other specialized tools

## Resources

### Configuration
- `.ai/instructions/rules/CODE_RULES.md` - Full engineering standards
- `.ai/instructions/rules/DOCS_RULES.md` - Documentation requirements
- `.ai/instructions/rules/REUSE_RULES.md` - Code reuse guidelines
- `.ai/instructions/knowledge/` - Architecture and API documentation

### Project Information
- `README.md` - Project overview
- `docs/ru/` - Russian documentation
- `.env.example` - Environment variables template
- `config.json` - Configuration example

## Getting Help

| Question | Answer Location |
|----------|-----------------|
| How do I code? | `engineering-standards.md` + CODE_RULES.md |
| How do I document? | `documentation-standards.md` + DOCS_RULES.md |
| How do I reuse code? | REUSE_RULES.md |
| How is the system designed? | `.ai/instructions/knowledge/project_overview.md` |
| How do I set up? | INSTALLATION_GUIDE.md |
| What are the APIs? | api_documentation.md |
| How do I run services? | LAUNCHER_GUIDE.md |

## Feedback & Updates

These standards evolve with the project. When you encounter issues or have improvements:

1. Note the problem
2. Suggest improvement
3. Update relevant steering file
4. Commit with "Docs: Update standards"

---

**Active development standard: v1.0 (FastAPI Foundry Edition)**  
**Last updated: September 16, 2026**  
**Maintained by: Project Team**
