# 🚀 AI Agent Script Execution Guide (`MODEL_SCRIPT_EXECUTION_GUIDE.md`)

**Purpose:** Provide unambiguous instructions for AI models and pair programming agents on automated tool execution in AI Breadboard.

---

## 📌 Core Principles

1. **Universal Entry Point:** All system tasks and utility operations are invoked via `manage_tools.py`.
2. **Deterministic CLI Groups:** `skills`, `rag`, `knowledge`, `db`, `docs`, and `assist`.
3. **Fail-Fast Verification:** Always verify execution status codes (0 = success).
4. **No Legacy Invocations:** Never execute removed legacy commands (`media scan`, `torrents *`, `db sizes`).

---

## 🎯 Automated Execution Scenarios

### Scenario 1: Skills Inspection & Discovery
**When:** Searching for capabilities or preparing subagents.  
**Commands:**
```powershell
# List all discovered skills
py manage_tools.py skills list

# Search for relevant skills
py manage_tools.py skills search "storage"

# Export portable contract
py manage_tools.py skills export "storage-controller"
```

### Scenario 2: Documentation & Knowledge Updates
**When:** After editing or adding markdown knowledge or code architecture.  
**Commands:**
```powershell
# Validate RAG / knowledge files
py manage_tools.py rag validate

# Rebuild RAG embeddings
py manage_tools.py rag rebuild

# Check RAG index health
py manage_tools.py rag status
```

### Scenario 3: Database Schema Migrations
**When:** After modifying SQLite models or database schemas in `src/db/`.  
**Commands:**
```powershell
# Check pending migrations
py manage_tools.py db status

# Apply pending migrations
py manage_tools.py db migrate
```

### Scenario 4: Service & Provider Diagnostic
**When:** Verifying local AI daemons or testing server availability.  
**Commands:**
```powershell
# Check background daemons and ports
py manage_tools.py assist status

# Check AI provider availability (Gemini, Foundry, ONNX, Ollama, etc.)
py manage_tools.py assist providers
```

---

## 🤖 Direct Launchers (`launchers/`)

For starting specific services:

```powershell
# Launch FastAPI backend
.\launchers\Run-Unicorn.ps1

# Launch local Foundry service
.\launchers\Run-Foundry.ps1 -Action start

# Run unit and integration tests
.\launchers\run_tests.ps1 -Coverage
```

---

## 📝 Best Practices for AI Agents

1. **Log Intent:** State what tool and parameters are being executed before running.
2. **Check Status:** Inspect exit code and console outputs.
3. **No Interactive Prompt Blockers:** Always prefer non-interactive flags where available.

---

**Status:** ✅ Up to date (September 2026)  
**Version:** 3.0
