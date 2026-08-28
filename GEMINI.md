# GEMINI.md

## 📋 General Information
This file is the primary source of project instructions, standards, and architectural conventions for the `aibreadboard` repository.

## 💡 Project Concept and Strategy (AI Breadboard)
- **Purpose:** Interactive "breadboard" for beginners to study, test, and compare various AI models (Google Gemini, Microsoft AI Foundry, OpenAI, local models, etc.).
- **Breadboard Testbench Architecture:** The project provides a transparent testbench (breadboard) where AI models act as interchangeable microchips. Everything runs natively and directly on the host (PowerShell launchers + Python venv), making signal tracing, bus routing, and vector memory fully observable.
- **Minimum Unnecessary Entities (KISS):** Architecture is built without over-engineering, unnecessary abstraction layers, or bulky frameworks.
- **Universal Model Switches via API:** Users send their requests through a unified API (`/api/chat`, `/v1/chat/completions`, web interface). The code uses universal switches and a single interface contract (`UnifiedChatModel`, `get_chat_model()`, methods `chat()`, `ask()`, `stream_chat()`), which allows seamless work with any model types (Gemini, Foundry, Ollama, OpenAI/DeepSeek/Groq, HF/ONNX) without duplicating business logic.
- **Model Behavior via Instructions:** Sufficient and exhaustive descriptions of behavior, roles, and protocols are embedded directly in machine instructions (`.ai/prompts/`, `.ai/instructions/`), rather than hardcoded in the logic.

## ⚙️ Core Workflows
All developments must strictly adhere to the principles described in `.ai_instructions/`:
- **Code Standards:** Described in `rules/CODE_RULES.md`.
- **TDD Documentation:** For all functional changes in `.py` files, use of the `tdd-doc-gen` skill is MANDATORY (see protocol in `rules/CODE_RULES.md`).
- **Documentation:** Described in `rules/DOCS_RULES.md`. (Atomic changes: documentation + code).
- **Launchers and Service Startup:** `.ai_instructions/knowledge/LAUNCHER_GUIDE.md` — single source of rules.
- **AI Tools:** `tools/` — all utility scripts for agents. Described in `tools/README.md`.

## 🏗️ Architectural Requirements
- **Explicit is better than implicit:** Dependency passing must be explicit.
- **Fail-Fast:** Use early returns.
- **Configuration over Hardcode:** No hardcoded parameters; only JSON configurations or environment variables.
- **Configuration Storage:** All non-secret application settings must be stored in `config.json`. Environment variables and `.env` file must be used EXCLUSIVELY for secret data (API keys, tokens, passwords).
- **Ban on `None`:** The `None` keyword and `is None` checks are strictly forbidden. Function parameters and class attributes MUST use concrete default values: `Optional[float] = 0.0`, `Optional[int] = 0`, `Optional[str] = ''`, `Optional[list] = []`, `Optional[dict] = {}`. Constructing signatures like `temperature: Optional[float] = None` is strictly prohibited.
- **Automatic Frontend Versioning (Cache Busting):** When changing static files (JS, CSS), you must update/increment the version parameter (e.g., `?v=YYYYMMDD` or increment) in all HTML/templates that include this file to prevent browser caching.
- **Mandatory Documentation:** Every new directory in the project MUST contain a `README.md` in English describing the module's purpose and how it works.

## 🚀 Launchers and Service Startup

**Rule:** The main launcher `run.ps1` is located in the repository **root** directory, while individual service launchers are located in the `launchers/` directory.

| Launcher | Purpose |
|----------|--------- |
| `run.ps1` | Main launcher (FastAPI + Foundry) |
| `launchers/Run-Unicorn.ps1` | FastAPI server |
| `launchers/Run-Foundry.ps1` | AI Foundry |
| `launchers/Run-LightServer.ps1` | HTTP server |
| `launchers/Run-GeminiCli.ps1` | Google Gemini CLI agent |
| `launchers/Run-Agy.ps1` | Google Antigravity (AGY) agent |
| `launchers/run_tests.ps1` | Test runner |

See more: `.ai_instructions/knowledge/LAUNCHER_GUIDE.md`

## 🛠️ Using Skills
For specific tasks, use available system skills via the `activate_skill` tool:
- `skill-creator` — for creating new skills.
- `antigravity-support` — for Antigravity CLI migration and setup.
- `microsoft-foundry` — for Foundry agent management.

## 📝 Quality Control (Commit Checklist)
Before committing, ensure:
1. File header conforms to the standard.
2. Public functions have Docstrings in `hypo69 docblock` format.
3. Code contains no Cyrillic (for Web/PHP stack).
4. Logging is strictly via `core.logger.logger`.
5. All secrets are moved to `.env`.
6. **Commit Regulations:** Commits are made ONLY after complete verification of a finished debugging/development session. Do not commit every intermediate change. A commit must reflect a logically complete state of working code.