# 🎯 Kiro Steering Configuration

This directory contains project-wide steering files that are automatically loaded into Kiro IDE sessions.

## What are Steering Files?

Steering files provide **continuous contextual guidance** to AI agents (Kiro IDE) throughout development work. They:

- ✅ Enforce consistent code quality across the project
- ✅ Maintain architectural principles in all changes
- ✅ Reduce context-switching for developers
- ✅ Ensure documentation standards are followed
- ✅ Prevent common code smells and anti-patterns

## Files in This Directory

### 1. **project-standards.md** (Primary)
Main overview document that coordinates all standards:
- Project architecture principles
- Tech stack overview
- Development workflow
- Common tasks and procedures
- Quick navigation to other standards

**When to read:** Start here for project overview and quick reference

### 2. **engineering-standards.md**
Code quality and style standards applied to all code:
- Readability over cleverness
- Single responsibility principle
- Type safety and null-safety
- Configuration over hardcoding
- Language-specific standards (Python, JS, PHP, HTML/CSS)
- DRY principle and code reuse
- Function/file size limits

**When to read:** Before writing or reviewing code

### 3. **documentation-standards.md**
TDD workflow and documentation requirements:
- Three levels of documentation
- TDD-doc-gen workflow (6 steps)
- Docstring format (hypo69 docblock)
- README.md requirements
- Testing standards
- Comment philosophy
- File header format

**When to read:** Before creating functions or modules

## Auto-Loading Behavior

These files are configured with `inclusion: auto`, which means:

1. **Automatic Activation** - Files are analyzed when Kiro starts
2. **Contextual Application** - Applied when their topic matches user intent
3. **No Manual Import** - You don't need to explicitly reference them
4. **Unified Guidance** - All AI agents use the same standards

### How Activation Works

When you start a task, Kiro's system will:
1. Recognize the task type (coding, documentation, refactoring, etc.)
2. Load relevant steering files based on task description
3. Inject guidelines into agent context
4. Apply standards consistently throughout the task

## How to Use

### During Code Development
The `engineering-standards.md` will be automatically active. You'll see:
- Reminders about SRP and code organization
- Type hint requirements
- Null-safety (no `None`) rules
- Configuration best practices
- Language-specific style guides

### During Documentation
The `documentation-standards.md` will be automatically active. You'll see:
- Docstring format requirements
- README.md structure
- TDD workflow guidance
- Testing standards
- File header requirements

### For Project Overview
Reference `project-standards.md` for:
- Architecture decisions
- Project structure
- Tech stack
- Development workflow
- Resource locations

## Key Standards at a Glance

### Code Quality
```
✅ SRP (Single Responsibility)
✅ Type hints required
✅ Early returns (fail-fast)
✅ NO None (use empty defaults)
✅ Config not hardcode
✅ Max 3 nesting levels
✅ Max 500 lines per function
```

### Documentation
```
✅ Docstrings for all functions
✅ hypo69 docblock format
✅ Comments explain WHY
✅ README.md for modules
✅ Russian language
✅ Examples in docstrings
✅ File headers required
```

### Testing
```
✅ 70%+ code coverage
✅ TDD workflow
✅ pytest for testing
✅ Integration tests for APIs
✅ Clear test names
```

## Quick Reference

### I Need to...
| Task | File | Section |
|------|------|---------|
| Write code | engineering-standards.md | Language-Specific Standards |
| Document function | documentation-standards.md | Docstring Format |
| Create module | documentation-standards.md | README.md Requirements |
| Understand architecture | project-standards.md | Architecture Principles |
| Check style guide | engineering-standards.md | Language-Specific Standards |
| Write tests | documentation-standards.md | Testing Requirements |

## Related Documents

All steering files reference the authoritative source documents in `.ai/instructions/`:

- **CODE_RULES.md** - Full engineering standard (v1.0)
- **DOCS_RULES.md** - Complete documentation guide
- **REUSE_RULES.md** - Code reuse and prior art standards
- **project_overview.md** - System architecture details
- **api_documentation.md** - REST API reference

## Maintenance

### Adding New Guidelines
1. Identify the category (code, docs, or architecture)
2. Add to relevant steering file
3. Reference source document in `.ai/instructions/`
4. Update README.md with new section

### Updating Existing Guidelines
1. Update in `.ai/instructions/rules/` first
2. Sync changes to corresponding steering file
3. Keep descriptions concise (steering is for reminders, not full specs)

### Removing Outdated Guidelines
1. Check if any code relies on pattern
2. Migrate code if needed
3. Remove from steering file
4. Update source document

## Version Information

- **Version**: 1.0 (FastAPI Foundry Edition)
- **Alignment**: Synced with CODE_RULES.md v1.0
- **Last Updated**: September 16, 2026
- **Status**: ✅ Production Ready

## How Kiro Uses These Files

When you interact with Kiro IDE:

1. **Session Start** - Steering files are loaded
2. **Your Request** - Kiro analyzes your intent
3. **Context Injection** - Relevant standards are included in context
4. **Task Execution** - Standards are applied throughout
5. **Quality Check** - Output verified against standards

## Example Workflow

```
You: "Add a function to fetch user data from API"
     ↓
Kiro recognizes: Coding task
     ↓
Activates: engineering-standards.md
     ↓
Kiro remembers:
- Type hints required
- Config-driven (no hardcode)
- Docstring needed (hypo69 format)
- Error handling (no None)
     ↓
Creates function with all standards applied
```

## Contact & Feedback

If you notice:
- Conflicting standards → Update relevant file and document the decision
- Unclear guidelines → Add examples to steering file
- Missing standards → Create new section with clear rationale
- Outdated information → Update source in `.ai/instructions/`

---

**These steering files ensure consistent quality across all Kiro-assisted development.**

Start with `project-standards.md` for overview, then use specific files as needed.

**Happy coding! 🚀**
