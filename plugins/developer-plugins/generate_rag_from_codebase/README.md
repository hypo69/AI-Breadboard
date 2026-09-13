# Codebase RAG & Symbol Indexer Plugin (`generate_rag_from_codebase`)

## Overview

The **`generate_rag_from_codebase`** plugin provides an intelligent, codebase-aware indexing and retrieval system for the AI Breadboard project. Unlike generic character-splitting indexers, it performs syntactic and semantic decomposition across distinct project layers:

1. **Python Source Code (AST-Decomposed)**: Extracts modules, classes, and methods preserving docstrings, signatures, class context, sibling methods, and import relations.
2. **Hierarchical Markdown / RST Documentation**: Chunks documentation by heading hierarchies (`#`, `##`, `###`), preserving parent breadcrumbs and document categories (`project_overview`, `changelog`, `documentation`, `prompt`).
3. **Structured Configuration Files**: Safely indexes `pyproject.toml`, requirements, and YAML/JSON configs.
4. **Secret & Sensitive Data Guard**: Automatically excludes patterns defined in `.ragignore` and masks detected API keys, passwords, and tokens.
5. **Dual Index Architecture**:
   - **AST Code Symbol Index**: Ultra-fast exact and prefix symbol search without embedding latency.
   - **Semantic Vector Index**: Cosine-similarity TF-IDF / vector search over rich contextual chunks.

---

## Architecture

```
                    AI-BREADBOARD CODEBASE
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
          Python Code      Markdown Docs    Configs
               │               │               │
          ast_parser       md_parser      ConfigLoader
               │               │               │
               └───────────────┬───────────────┘
                               ▼
                         ignore_filter
                    (Secrets & .ragignore)
                               ▼
                     Enriched Code Chunks
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        Code Symbol Index             Vector Indexer
         (symbols.json)            (TF-IDF / FAISS Index)
                │                             │
                └──────────────┬──────────────┘
                               ▼
                       RAG Query Engine
```

---

## Admin Actions

| Action ID | Description | Parameters |
|---|---|---|
| `rebuild_index` | Scans project files, runs AST/Markdown parsing, and builds indexes | `{}` |
| `search_symbols` | Looks up classes, functions, or methods in the AST Symbol Index | `{"query": "MediaSearchAgent", "exact": false}` |
| `search_code` | Semantic search over indexed code and documentation chunks | `{"query": "How are providers routed?", "top_k": 5}` |
| `get_stats` | Inspects total chunks, symbols, and vocabulary count | `{}` |

---

## Agent LLM Tools

The plugin registers the following tools for function calling:

- `search_codebase_rag(query: str, top_k: int = 5, type_filter: str = None)`: Semantic search over code, docstrings, docs, and configurations.
- `lookup_symbol(symbol: str, exact: bool = False)`: Direct symbol lookup for class and method signatures.

---

## Configuration (`config.json`)

```json
{
  "include_dirs": ["src", "plugins", "integrations", "launchers", "scripts", "install", "docs", "prompts"],
  "include_files": ["README.md", "README.ru.md", "CHANGELOG.md", "pyproject.toml"],
  "ignore_patterns": [
    ".git/**",
    ".venv/**",
    "logs/**",
    "site/**",
    "SANDBOX/**",
    "**/.env*"
  ],
  "index_dir": "data/rag_index/codebase"
}
```

---

## Tests

Execute unit and integration tests:

```powershell
pytest plugins/generate_rag_from_codebase/tests/ -v
```
