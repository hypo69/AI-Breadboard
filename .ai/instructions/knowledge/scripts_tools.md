# CLI Tools & Scripts Reference (`scripts_tools.md`)

**Project:** `AI-Breadboard`  
**Entry Point:** [`manage_tools.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/manage_tools.py)  
**Status:** ✅ Up to date (September 2026)

The root directory contains `manage_tools.py` as the universal CLI entry point for project maintenance, skills management, RAG index operations, database migrations, knowledge extraction, and daemon lifecycle controls.

Run all scripts from the activated project virtual environment:
```powershell
# Activate venv in PowerShell
.\venv\Scripts\Activate.ps1
```

---

## 0. Universal CLI: `manage_tools.py`

### Syntax
```powershell
py manage_tools.py <group> [<subcommand>] [arguments...]
```

### Command Groups Overview

| Group | Subcommands / Actions | Description |
|---|---|---|
| `skills` | `list`, `search`, `show`, `export` | Universal AI skills registry discovery, inspection, and portable JSON export |
| `rag` | `rebuild`, `reindex`, `validate`, `status` | RAG vector index building, maintenance, and status inspection |
| `knowledge` | `extract`, `add`, `init` | Knowledge base extraction and ingestion from documentation & chats |
| `db` | `status`, `migrate`, `create` | SQLite database schema migrations (e.g. `users.db`) |
| `docs` | *(subcommands)* | Documentation generation, validation, and updates |
| `assist` | `start`, `stop`, `status`, `providers`, `restart` | Assistant background service and provider lifecycle control |

---

## 1. Skills Registry (`manage_tools.py skills`)

Discovers capabilities and tools defined in `.agents/skills` and `.gemini/skills`, exposing portable JSON contracts for AI agents.

### Commands

```powershell
# List all discovered skills with roles and descriptions
py manage_tools.py skills list

# Search for skills by keyword or capability
py manage_tools.py skills search "storage"
py manage_tools.py skills search "rag"

# Display full Markdown instructions (SKILL.md) for a skill
py manage_tools.py skills show "storage-controller"
py manage_tools.py skills show "rag-cleaner"

# Export a portable JSON skill contract
py manage_tools.py skills export "db-inspector"
py manage_tools.py skills export "db-inspector" --without-instructions
```

---

## 2. RAG Index Management (`manage_tools.py rag`)

Manages vector embeddings and semantic search indexes used by AI Breadboard and local agents.

### Commands

```powershell
# Check current RAG index status, record count, and embedding health
py manage_tools.py rag status

# Full rebuild of the RAG index
py manage_tools.py rag rebuild

# Reindex existing knowledge base files
py manage_tools.py rag reindex

# Validate knowledge base files and formats
py manage_tools.py rag validate
```

---

## 3. Knowledge Base (`manage_tools.py knowledge`)

Extracts, structures, and registers knowledge entries from developer chats, specifications, and project documents.

### Commands

```powershell
# Initialize knowledge registry
py manage_tools.py knowledge init

# Extract knowledge from a chat or markdown file
py manage_tools.py knowledge extract --file chat.md

# Add a new entry to the knowledge base
py manage_tools.py knowledge add --title "ONNX Runtime Integration" --category "ai"
```

---

## 4. Database Migrations (`manage_tools.py db`)

Manages migrations and schema changes for project databases (e.g., `src/db/users.db`).

### Commands

```powershell
# Check current migration status across databases
py manage_tools.py db status

# Apply all pending migrations
py manage_tools.py db migrate

# Create a new SQL migration file
py manage_tools.py db create users "add_mcp_tokens"

# Create a new Python migration script
py manage_tools.py db create users "migrate_user_storage" --py
```

---

## 5. Assistant Daemon & Service Management (`manage_tools.py assist`)

Forwards commands directly to `scripts/dev/assist_cli.py` for managing background daemons, servers, and provider statuses.

### Commands

```powershell
# Check status of running servers, ports, and AI provider availability
py manage_tools.py assist status

# Start FastAPI and local AI runtimes
py manage_tools.py assist start

# Stop active background services
py manage_tools.py assist stop

# List available AI providers and probe status
py manage_tools.py assist providers

# Register assist CLI in PowerShell profile and PATH
py manage_tools.py assist install-profile
```

---

## 6. Developer Utility Scripts (`scripts/dev/`)

Specialized developer tools located under `scripts/dev/`:

| Script | Purpose | Example Usage |
|---|---|---|
| `scan_headers.py` | Validates standard file headers and docstrings across Python files | `py scripts/dev/scan_headers.py` |
| `package_skill.py` | Packages a skill directory into a distributable archive | `py scripts/dev/package_skill.py cert-installer` |
| `generate_coverage_report.py` | Runs pytest and generates detailed code coverage reports | `py scripts/dev/generate_coverage_report.py` |
| `run_tests.py` | Test execution runner with marker filtering | `py scripts/dev/run_tests.py --unit` |
| `update_docs.py` | Updates project documentation indices and tables of content | `py scripts/dev/update_docs.py` |
| `convert_to_md.py` | Converts text/json logs to Markdown reports | `py scripts/dev/convert_to_md.py input.json output.md` |

---

### 7. Operational Guidelines for AI Agents

AI agents should invoke project CLI commands in specific operational scenarios:

### 7.1 Skills Inspection & Verification
When developing, debugging, or routing agent tasks:
* **Check available capabilities:** `py manage_tools.py skills list`
* **Inspect skill instructions:** `py manage_tools.py skills show <skill-name>`
* **Validate contract structure:** `py manage_tools.py skills export <skill-name>`

### 7.2 RAG Index Maintenance
When updating documentation, codebases, or knowledge files:
* **Validate knowledge files:** `py manage_tools.py rag validate`
* **Rebuild semantic embeddings:** `py manage_tools.py rag rebuild`
* **Check RAG index status:** `py manage_tools.py rag status`

### 7.3 Database Migrations
When modifying SQLite schemas (e.g., users, tokens, storage):
* **Inspect migration state:** `py manage_tools.py db status`
* **Apply pending migrations:** `py manage_tools.py db migrate`
* **Generate new migration:** `py manage_tools.py db create <db_name> <migration_name>`

### 7.4 Daemon & Server Health Checks
When verifying system runtime or testing endpoints:
* **Check running processes and AI providers:** `py manage_tools.py assist status`
* **Probe AI provider status:** `py manage_tools.py assist providers`

---

## 8. Directory Structure Context

```
AI-Breadboard/
├── 📄 manage_tools.py        # Universal CLI entry point
├── 📄 main.py                # FastAPI application
├── 📄 run.ps1                # Main interactive/service launcher
├── 📁 launchers/             # Dedicated service launchers (Run-*.ps1)
├── 📁 src/                   # Main source code (ai/, fastapi/, rag/, skills/, logger/, tts/, db/)
│   ├── 📁 ai/providers/      # Modular AI providers (gemini, foundry, agy, ollama, onnx, windows_ai...)
│   ├── 📁 fastapi/           # FastAPI routers and webinterface
│   ├── 📁 skills/            # Universal skills discovery & registry
│   └── 📁 rag/               # RAG vector index & retrieval
├── 📁 plugins/               # Extensible plugins
├── 📁 scripts/dev/           # Developer utility tools
├── 📁 .agents/skills/        # Portable AI skills (SKILL.md)
├── 📁 tests/                 # Pytest test suite
└── 📁 .ai/instructions/      # AI engineering rules & knowledge base
```

---

**Status:** ✅ Up to date  
**Version:** 3.0 (September 2026)