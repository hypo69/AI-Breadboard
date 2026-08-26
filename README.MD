# aibreadboard — Interactive Breadboard for AI Language Models

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

### 📦 Installation

#### Option 1: Quick One-Liner (PowerShell, Recommended on Windows)

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

#### Option 2: Clone & Run `install.cmd` (Windows)

```cmd
git clone https://github.com/hypo69/AI-Breadboard.git C:\aibreadboard
cd C:\aibreadboard
install.cmd
```

The installer interactively selects UI language, sets up `%USERPROFILE%\AppData\Local\AI Breadboard` (or custom path), registers `AIBREADBOARD_DIR`, creates `venv`, installs dependencies, generates SSL certificates via mkcert, and binds the global `assist` command.

#### Option 3: Manual Installation

```bash
# Windows
py -3.13 -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# Linux / macOS
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

---

### 📁 Dependency Structure (`req/`)

- `req/requirements-core.txt` — FastAPI, Uvicorn, Pydantic, JWT, aiohttp, httpx
- `req/requirements-ai.txt` — LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, MCP
- `req/requirements-media.txt` — Edge-TTS, gTTS, PyDub
- `req/requirements-utils.txt` — Pandas, Pillow, BeautifulSoup4
- `req/requirements-test.txt` — pytest, pytest-asyncio, coverage
- `req/requirements-docs.txt` — MkDocs, Material theme

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
```

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
