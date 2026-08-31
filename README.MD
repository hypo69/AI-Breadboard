# Interactive `Breadboard` for exploring different AI Language Models

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**AI Breadboard** is an interactive testbench and "breadboard" designed for studying, testing, and comparing diverse AI models (Google Gemini, Microsoft AI Foundry, Antigravity AGY, Ollama, OpenAI/DeepSeek, Hugging Face, ONNX) within a unified environment featuring a standardized socket interface.

---

## 🤖 Provider Orchestrator (System Core)

The central component — `core/ai/model_manager.py` — manages the lifecycle of models across all providers: querying available models at startup, caching them in memory, and automatically removing malfunctioning models from rotation.

`core/ai/unified_chat.py` serves as the single unified entry point for all model invocations, routing requests to the appropriate provider adapter based on model name prefix.

### Supported Providers

| Provider | Model Prefix | Adapter | Description |
|---|---|---|---|
| **Microsoft AI Foundry** | `foundry:<model_id>` | `foundry_chat.py` | Local OpenAI-compatible server (`Run-Foundry.ps1`) |
| **Microsoft ONNX (Olive)** | `onnx:<model_id>` | `onnx_chat.py` | Local ONNX/Olive inference with DirectML / CPU / CUDA acceleration |
| **Hugging Face** | `hf:<model_id>` | `hf_chat.py` | Local model inference via Hugging Face Transformers |
| **OpenAI-Compatible APIs** | `openai:<model_id>`, `deepseek:<model_id>`, `lmstudio:<model_id>` | `openai_compat_chat.py` | Cloud & local services (OpenAI, DeepSeek, Groq, LM Studio) |
| **Google Gemini SDK** | `gemini-*` (no prefix) | `core/ai/gemini/` | Direct Google GenAI SDK integration with API key pooling |
| **Google Gemini CLI** | `gemini_cli:<model_id>` | `gemini_cli_chat.py` | Subprocess-based local agent (`gemini -p ... -m ...`) |
| **Antigravity AGY** | `agy-<model_id>` | `agy_chat.py` | Antigravity SDK running on top of Gemini models |
| **Ollama** | `ollama:<model_id>` | `ollama_chat.py` | Local Ollama inference server |

### Request Routing Pipeline

```
User Request → UnifiedChatModel._get_active_model(model_name)
    ├── "foundry:qwen2.5-..."   → FoundryChatBase       → http://localhost:54837/v1
    ├── "onnx:qwen2.5-..."      → ONNXChatBase          → Microsoft ONNX Runtime / Olive (DirectML)
    ├── "hf:Qwen/..."           → HFChatBase            → Hugging Face Transformers
    ├── "openai:gpt-4o"         → OpenAICompatChat      → OpenAI / DeepSeek / LM Studio API
    ├── "gemini_cli:gemini-..." → GeminiCliChatBase     → subprocess gemini CLI
    ├── "agy-gemini-..."        → AgyChatBase           → google.antigravity SDK
    ├── "ollama:llama3.1"       → OllamaChatBase        → http://localhost:11434
    └── "gemini-flash-..."      → GoogleGenerativeAI    → Google GenAI SDK
```

### Model Management Methods

- `model_manager.get_available_models(provider)`: Retrieve list of active models for a provider (cached).
- `model_manager.actualize_all_models()`: Concurrently warms up model caches across all providers at server boot.
- `model_manager.add_unsupported_model(provider, model_name)`: Automatically excludes failing models from rotation (persisted in `config.json`).

---

## 🚀 Key Features

- 🤖 **Provider Orchestrator:** Unified interface for Foundry, ONNX, Hugging Face, OpenAI/DeepSeek, Gemini CLI, AGY, Gemini SDK, and Ollama.
- 🧠 **Streaming RAG Search:** Vector search over `media.db` with Server-Sent Events (SSE) reasoning steps streaming.
- 🧩 **Extensible Plugin System:** Modular drive scanners, metadata processors, and agent tool hooks.
- 🎙️ **Multi-Engine TTS:** Text-to-speech synthesis supporting Edge-TTS, gTTS, and local audio streaming.

---

## 📖 Documentation

### Project Architecture & Startup Guide

- **[English: Detailed Startup Guide](en/code/start-engine.md)** - Complete explanation of `run.ps1` workflow, component responsibilities, and system impact
- **[Русский: Детальное руководство по запуску](ru/code/start-engine.md)** - Подробное описание процесса запуска, ответственности компонентов и влияния на систему

### CLI Commands Reference

- **[English: CLI Commands](en/code/cli-commands.md)** - Complete reference for `assist` command-line interface
- **[Русский: CLI-команды](ru/code/cli-commands.md)** - Полный справочник по интерфейсу командной строки `assist`

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                             Web Interface                              │
│                       ┌───────────────────────┐                        │
│                       │      Web UI (/)       │                        │
│                       └───────────┬───────────┘                        │
│                                   │                                    │
│                         ┌─────────▼──────────┐                         │
│                         │   FastAPI Server   │                         │
│                         └─────────┬──────────┘                         │
│    ┌──────────────────────────────┴──────────────────────────────┐     │
│    │                                                             │     │
│┌───▼────────────────────────┐                   ┌────────────────▼────┐│
││  AI Orchestrator           │                   │  RAG & Storage      ││
││ • model_manager.py         │                   │ • RAG Search        ││
││ • unified_chat.py          │                   │ • Vector Index      ││
││                            │                   │ • Knowledge Base    ││
││ Providers:                 │                   │ • media.db          ││
││  Foundry / ONNX / HF       │                   └─────────────────────┘│
││  OpenAI / Gemini / AGY     │                                          │
││  Gemini CLI / Ollama       │                                          │
│└────────────────────────────┘                                          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart

### Prerequisites

- **OS:** Windows 10/11, Linux, or macOS
- **Python:** 3.10+ (3.12 or 3.13 recommended)
- **API Keys:** Google Gemini API Key (for Gemini SDK & AGY)
- **Optional:** Microsoft AI Foundry, Gemini CLI (`npm install -g @google/gemini-cli`)

---

## 📦 Installation Workflow

### Overview

AI Breadboard provides **three installation methods**:
1. **One-Liner Script** - Automatic installation (recommended for Windows)
2. **Interactive Installer** - Step-by-step guided setup with language selection
3. **Manual Installation** - Full control over every step

All methods create a virtual environment, install dependencies, generate SSL certificates, and register the global `assist` command.

---

### Option 1: One-Liner Script (PowerShell, Recommended on Windows)

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

This command:
- Downloads the installer script from GitHub
- Runs the full automated installation workflow
- Creates `%LOCALAPPDATA%\AI-Breadboard` with `venv`
- Installs all dependencies from `requirements.txt`
- Generates SSL certificates for local HTTPS
- Registers `assist` global command in PowerShell and PATH

**After installation**, run `./run.ps1` to start the server.

---

### Option 2: Interactive Installer (Web-Based GUI)

#### Step-by-Step Process

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/hypo69/AI-Breadboard.git
   cd AI-Breadboard
   ```

2. **Run the installer:**
   ```powershell
   .\install.ps1
   ```

3. **Installation wizard guide:**

   **Step 0: Language Selection**
   - Choose installation interface language: Russian (RU), English (EN), Spanish (ES), or Hebrew (HE)
   - Selection is saved to `config.json` for future sessions

   **Step 1: File Unblocking**
   - Removes Windows "Mark of the Web" (MOTW) from all project files
   - Windows adds MOTW metadata to files downloaded from the internet, marking them as untrusted
   - Without unblocking, PowerShell blocks `.ps1` script execution with error: "running scripts is disabled on this system"
   - Some Python/Node.js features may not work properly

   **Step 2: Virtual Environment Setup**
   - Searches for Python 3.10+ via `py` launcher, `python`, or `python3` commands
   - Skips Windows Store Python stubs
   - Creates clean `venv` directory or uses existing valid environment
   - Python version and path are saved to `config.json`

   **Step 3: Package Upgrades**
   - Upgrades `pip`, `setuptools`, and `wheel` to latest versions
   - Ensures modern tooling for dependency installation

   **Step 4: Dependency Installation**
   ```
   [1] Full installation (Core + AI + Utils) — RECOMMENDED
   [2] Core server only
   [3] Core + AI modules
   [4] Full installation + Tests & Docs (Dev)
   [5] Skip dependency installation
   ```
   - Installs from `requirements-core.txt`, `requirements-ai.txt`, and `requirements-utils.txt`
   - Creates `requirements.txt` with combined dependencies
   - Can be customized for production vs development needs

   **Step 5: SSL Certificate Generation**
   - Checks for `%USERPROFILE%\.certs\localhost+2.pem` and `localhost+2-key.pem`
   - If not found, runs `install_ssl_cert.ps1` to generate local SSL certificates
   - Enables HTTPS access to `http://localhost:3000`

   **Step 6: Global Command Registration**
   - Creates `assist.ps1`, `assist.cmd`, and `assist` (bash) scripts
   - Installs to `%USERPROFILE%\.local\bin\` (or `~/.local/bin/` on Linux/macOS)
   - Adds path to `PATH` environment variable
   - Registers `assist` function in PowerShell profiles (`$PROFILE`)

   **Step 7: Final Verification**
   - Tests imports of core modules: `fastapi`, `uvicorn`, `pydantic`, `aiofiles`, `cryptography`
   - Logs results to console
   - Saves installation status to `config.json`

4. **Completion Message:**
   ```
   ╔═══════════════════════════════════════════════════════════════╗
   ║         УСТАНОВКА ai-breadboard УСПЕШНО ЗАВЕРШЕНА!                 ║
   ║  Запуск сервера:  ./run.ps1                                   ║
   ╚═══════════════════════════════════════════════════════════════╝
   ```

---

### Option 3: Manual Installation

#### Step 1: Clone Repository

```bash
# Windows
git clone https://github.com/hypo69/AI-Breadboard.git C:\aibreadboard
cd C:\aibreadboard

# Linux / macOS
git clone https://github.com/hypo69/AI-Breadboard.git ~/aibreadboard
cd ~/aibreadboard
```

#### Step 2: Create Virtual Environment

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Upgrade Package Tools

```bash
pip install --upgrade pip setuptools wheel
```

#### Step 4: Install Dependencies

```bash
# Full installation (recommended)
pip install -r requirements.txt

# Or select subsets
pip install -r req/requirements-core.txt
pip install -r req/requirements-ai.txt
pip install -r req/requirements-utils.txt
```

#### Step 5: Generate SSL Certificates

```powershell
# Windows
.\install_ssl_cert.ps1

# Or manually with mkcert
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

The certificates will be saved to `%USERPROFILE%\.certs\`.

#### Step 6: Register Global `assist` Command

```powershell
# Windows
.\assist.ps1 install-profile
```

This creates `~\.local\bin\assist.ps1` and registers it in PowerShell profiles.

---

### Dependency Structure (`req/`)

| File | Contents | Use Case |
|---|---|---|
| `requirements-core.txt` | FastAPI, Uvicorn, Pydantic, JWT, aiohttp, httpx | Minimal server functionality |
| `requirements-ai.txt` | LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, MCP | AI/ML features |
| `requirements-utils.txt` | Pandas, Pillow, BeautifulSoup4 | Utility functions |
| `requirements-test.txt` | pytest, pytest-asyncio, coverage | Development testing |
| `requirements-docs.txt` | MkDocs, Material theme | Documentation building |
| `requirements.txt` | Combined all | Full installation |

---

### ⚙️ Configuration

**`config.json`** — Non-sensitive parameters:
- `server` — host, port, SSL settings
- `ai` — model defaults, Foundry/AGY/Gemini CLI parameters, unsupported models lists
- `langchain`, `agents` — ReAct agent configs, MCP tool definitions

**`.env`** — Secret credentials:
```bash
cp .env.example .env
```
```ini
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_super_secret_jwt_key
```

---

## 🎯 Post-Installation Setup

### Global `assist` Command

After installation, the `assist` command is available globally:

| Command | Description |
|---|---|
| `assist start` | Start main server (`run.ps1`) |
| `assist start unicorn` | Start via FastAPI/Uvicorn |
| `assist start light` | Start lightweight server |
| `assist start foundry` | Start local AI Foundry |
| `assist stop` | Stop server and free port 3000 |
| `assist restart` | Quick server restart |
| `assist status` | Check server status and ports |
| `assist providers` | List AI providers and models |
| `assist logs [N]` | View last N log lines (default: 40) |
| `assist config show` | Display current `config.json` |
| `assist config get <key>` | Get config value |
| `assist config set <key> <val>` | Set config value |
| `assist test` | Run pytest suite |

### Model Selection & Download (New in v2.0)

After installation, you can select and download models for local providers:

**Step-by-step:**

1. **Run the interactive installer** (or re-run `install.ps1`):
   ```powershell
   .\install.ps1
   ```

2. **Select local providers models** at step 8:
   - Script fetches available models from Ollama, Foundry, ONNX
   - Choose models to download by number(s) or range (e.g., `1-3`)
   - Models are downloaded via their native commands

3. **Supported local providers:**
   | Provider | Command | Model Prefix |
   |---|---|---|
   | Ollama | `ollama pull` | `ollama:<model_id>` |
   | Foundry | Auto-download | `foundry:<model_id>` |
   | ONNX | Auto-download (Transformers) | `onnx:<model_id>` |
   | HuggingFace | Auto-download (Transformers) | `hf:<model_id>` |

4. **Start the server:**
   ```powershell
   ./run.ps1
   ```

**Example session:**
```
[8/8] Selecting and downloading models for local providers...

Available models for Ollama:
  [1] llama3.1
  [2] qwen2.5-1.5b-instruct-generic-cpu:4
  [3] mistral-small

Select models to download (numbers separated by comma or range 1-3) [Enter = skip]: 1,2

Downloading model Ollama (llama3.1)...
[OK] Model llama3.1 downloaded successfully

Downloading model Foundry (qwen2.5-1.5b-instruct-generic-cpu:4)...
[INFO] Foundry downloads models automatically on first use
[OK] Model qwen2.5-1.5b-instruct-generic-cpu:4 downloaded successfully
```

### Web Interface Access

- **Main Dashboard:** `http://localhost:3000/`
- **API Documentation:** `http://localhost:3000/docs`
- **Redoc Documentation:** `http://localhost:3000/redoc`

---

## 🔍 Troubleshooting

### Execution Policy Error

If PowerShell shows "running scripts is disabled":

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

### Port 3000 Already in Use

```powershell
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use assist
assist stop
```

### Python Not Found

Install Python 3.10+ from [python.org](https://www.python.org/downloads/), ensuring **"Add python.exe to PATH"** is checked during installation.

### SSL Certificate Warning

Browser warns about self-signed certificate:
1. Click "Advanced" → "Proceed to localhost (unsafe)"
2. Or install certificate into Windows Trusted Root CA:
   ```powershell
   certutil -addstore -f "Root" $env:USERPROFILE\.certs\localhost+2.pem
   ```

### Log Files

Check logs in `logs/` directory:
- `fastapi.log` — FastAPI request routing
- `info.log` — System events
- `errors.log` — Error logs
- `uvicorn_*.log` — Server console output

---

### ▶️ Starting the Application

```powershell
# Windows Launcher (Recommended)
./run.ps1
```

`run.ps1` automatically verifies port availability, launches Microsoft AI Foundry if configured, and starts FastAPI with SSL and auto-reload.

```bash
# Direct Execution
.\venv\Scripts\python.exe main.py
```

---

## 🖥️ Web Endpoints

| Interface | URL | Description |
|---|---|---|
| 🏠 **Main Dashboard** | `http://localhost:3000/` | Interactive chat, models, RAG, agents, logs |
| 📄 **API Swagger Docs** | `http://localhost:3000/docs` | Interactive OpenAPI documentation |

---

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, AsyncIO, Server-Sent Events (SSE)
- **AI Orchestrator:** `model_manager.py` + `unified_chat.py` — provider routing across Foundry, Gemini CLI, AGY, Gemini SDK, Ollama, ONNX, Hugging Face
- **Search & RAG:** SQLite (`media.db`), FAISS, Sentence-Transformers
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES Modules, i18next)
- **Network & Security:** mkcert local SSL

---

## 📄 License

MIT © 2026 hypo69
