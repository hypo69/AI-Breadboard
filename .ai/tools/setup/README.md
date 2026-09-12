# Codebase Setup & Audit Tools (`.ai/tools/setup`)

## Purpose
Tooling for static codebase analysis, dependency tree verification, and structural refactoring audits.

---

## Tools

| Script | Purpose | Command |
|---|---|---|
| `analyze_dependencies.py` | Analyzes inter-module dependencies and imports across the codebase. | `py .ai/tools/setup/analyze_dependencies.py` |
| `scan_headers.py` | Verifies docblock and file header compliance for Python files. | `py .ai/tools/setup/scan_headers.py` |
| `convert_to_md.py` | Formats media metadata JSON payloads into structured Markdown cards. | `py .ai/tools/setup/convert_to_md.py` |
