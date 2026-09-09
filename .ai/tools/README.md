# Project Utility Tools (`.ai/tools`)

## Purpose
Internal developer and agent utility scripts for code inspection, dependency analysis, and developer RAG maintenance.

> [!NOTE]
> Main application launchers (`run.ps1`, `Run-*.ps1`) reside in the project root directory.

---

## Tool Categories
- **[`ai/`](ai/)**: RAG index rebuilders (`rebuild_rag.py`, `rebuild_dev_rag.py`), skill packager (`package_skill.py`), code search (`search_code.py`), and documentation validator (`update_docs.py`).
- **[`setup/`](setup/)**: Dependency tree analysis (`analyze_dependencies.py`), header scanner (`scan_headers.py`), and Markdown converter (`convert_to_md.py`).
