# AI Agent Utilities (`.ai/tools/ai`)

## Purpose
Scripts designed for direct execution by AI coding agents and automated maintenance workers.

---

## Tools

| Script | Purpose | Command |
|---|---|---|
| `rebuild_rag.py` | Rebuilds the rules and core knowledge RAG index. | `py .ai/tools/ai/rebuild_rag.py [--fresh]` |
| `rebuild_dev_rag.py` | Rebuilds the technical vector RAG index over codebase files. | `py .ai/tools/ai/rebuild_dev_rag.py` |
| `search_code.py` | Semantic search over project source code and docstrings. | `py .ai/tools/ai/search_code.py "query"` |
| `inspect_user_rags.py` | Inspects local user RAG SQLite databases and schemas. | `py .ai/tools/ai/inspect_user_rags.py` |
| `package_skill.py` | Packages a skill directory into a `.skill` archive distribution. | `py .ai/tools/ai/package_skill.py <skill_dir> <output_dir>` |
| `update_docs.py` | Checks git-modified Python files for docstrings and compliance. | `py .ai/tools/ai/update_docs.py` |
| `validate_rag_files.py` | Verifies and lists files eligible for RAG indexing. | `py .ai/tools/ai/validate_rag_files.py` |
