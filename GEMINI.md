# GEMINI.md

## 📋 Master Overview

This file serves as the **primary instruction index** for the project. It links to all project documents, architectural principles, and engineering standards.

> [!IMPORTANT]
> **Language Standard**: All documentation, code, docstrings, code comments, tests, and commit messages **MUST** be written strictly in **English**.

---

## 🚀 Quick Start

### Initial Setup
```powershell
.\install.ps1          # Project and venv installation
.\run.ps1              # Run application server (FastAPI + AI backends)
```

### Documentation and Tools
- **Installation Guide:** [`.ai/instructions/knowledge/INSTALLATION_GUIDE.md`](.ai/instructions/knowledge/INSTALLATION_GUIDE.md)
- **Launcher Guide:** [`.ai/instructions/knowledge/LAUNCHER_GUIDE.md`](.ai/instructions/knowledge/LAUNCHER_GUIDE.md)
- **CLI Tools Reference:** [`.ai/instructions/knowledge/scripts_tools.md`](.ai/instructions/knowledge/scripts_tools.md)

---

## 💡 Project Concept (AI Breadboard)

**Purpose:** An interactive "breadboard" for testing, benchmarking, and seamlessly routing between diverse AI providers and runtimes (Windows AI APIs, Microsoft Foundry Local, Windows ML / ONNX Runtime, Ollama, Google Gemini, OpenAI-compatible APIs, and HuggingFace).

**Key Architectural Pillars:**
- **Capability-Driven Routing:** Workloads are dispatched based on capability requirements (`chat`, `vision`, `ocr`, `embedding`, `code`) and policy constraints (`local_only`, `privacy_strict`, `performance_first`, `cloud_fallback`).
- **Dynamic Discovery & Hardware Awareness:** Automatically probes CPU, GPU (CUDA, DirectML), NPU (QNN, DirectML), Windows AI Component availability, and local daemon ports without crashing on unsupported hardware.
- **Provider Modularization:** Each provider resides in its own package under `core/ai/providers/` with dedicated logic and an English `README.md`.
- **Zero-Hardcode Configuration:** Model behaviors and routing rules are declared in JSON configuration and policy files.
- **Direct Host Execution:** Everything runs natively on the Windows host with full observability.

---

## 📚 Development Standards

All development **MUST** adhere to instructions located in `.ai/instructions/`:

### 1. **Engineering Standards**
📄 [`.ai/instructions/rules/CODE_RULES.md`](.ai/instructions/rules/CODE_RULES.md)

Key requirements:
- Architecture principles: Explicit DI, Fail-Fast, DRY, Single Responsibility
- Language standards: Python 3.12+ (strictly English code, docstrings, and comments)
- Prohibition of undocumented `None` returns
- Standardized logging via `core.logger.logger`
- Strict separation of configuration (`config.json`) and secrets (`.env`)

### 2. **Documentation & TDD**
📄 [`.ai/instructions/rules/DOCS_RULES.md`](.ai/instructions/rules/DOCS_RULES.md)

Key requirements:
- Mandatory TDD workflow for all Python changes
- Standardized docstring structure (`hypo69 docblock` in English)
- English `README.md` in every directory and provider package

### 3. **Architectural Documentation**
📄 [`.ai/instructions/knowledge/project_overview.md`](.ai/instructions/knowledge/project_overview.md)

- Comprehensive system architecture and capability dispatch diagrams
- Runtime layers: Windows AI, Foundry Local, ONNX/DirectML, Ollama, Gemini

---

## 🛠️ Common Commands

### Service Launch
```powershell
# Unified launcher (everything)
.\run.ps1

# FastAPI server only
.\launchers\Run-Unicorn.ps1

# Status check
assist status
```

### Script Execution via `manage_tools.py`
```powershell
# Universal CLI
py manage_tools.py <group> <command> [arguments]

# Examples
py manage_tools.py media scan --disk "disk 2"
py manage_tools.py torrents assign
py manage_tools.py check db
```

### Testing
```powershell
.\launchers\run_tests.ps1         # Full test suite execution
pytest tests/ --cov                # Pytest with coverage reporting
```

---

## ⚙️ Core Architectural Principles

| Principle | Description | Reference |
|---|---|---|
| **Explicit DI** | Pass dependencies explicitly; avoid hidden globals | CODE_RULES.md § 3.3 |
| **Fail-Fast** | Early return on invalid inputs or failed preconditions | CODE_RULES.md § 3.4 |
| **Config > Hardcode** | System parameters loaded from configuration | CODE_RULES.md § 3.5 |
| **No None Ambiguity** | Explicit types and robust fallback handling | CODE_RULES.md § 3.6 |
| **DRY** | No code duplication across provider adapters | CODE_RULES.md § 4.2 |
| **English Only** | Code, docstrings, comments, and docs in English | CODE_RULES.md § 5.1 |
| **300-Line Limit** | Maximum 300 lines of functional code per function | CODE_RULES.md § 4.4 |
| **Documentation** | English Docstrings + README.md per directory | DOCS_RULES.md § 3-4 |

---

## 🔐 Configuration & Secrets

### Configuration (`config.json`)
Public system settings stored in root configuration:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1
  },
  "ai": {
    "use_foundry": true,
    "foundry_base_url": "http://localhost:54837",
    "use_ollama": true,
    "ollama_base_url": "http://localhost:11434",
    "use_windows_ai": false
  }
}
```

### Secrets (`.env`)
Private credentials, tokens, and keys:
```env
GEMINI_API_KEY_1=AIzaSy...
JWT_SECRET=secret_value
TELEGRAM_BOT_TOKEN=...
```

Rule: **Never commit `.env`!** Use `.env.example` as a template.

---

## ✅ Pre-Commit Checklist

Before every commit, verify:

- [ ] File header follows the required standard (see CODE_RULES.md § 6)
- [ ] All code, docstrings, comments, and logs are in **English**
- [ ] All public functions and classes have `hypo69 docblock` docstrings
- [ ] Logging is executed via `core.logger.logger` (no raw `print` calls)
- [ ] All credentials and secrets are managed via `.env`
- [ ] Commit represents a **logically complete, verified state** of working code
- [ ] Tests pass: `pytest tests/ --cov`
- [ ] New directories contain an English `README.md`

---

**Status:** ✅ Active (English Standard)  
**Version:** 3.0  
**Author:** hypo69