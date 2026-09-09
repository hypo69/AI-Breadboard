# Project Overview: AI Breadboard

**Project:** `AI-Breadboard`  
**Status:** ✅ Up to date (September 2026)  
**Version:** 3.0

---

## 💡 System Concept

**AI Breadboard** is an interactive, extensible developer workbench and runtime designed for testing, benchmarking, and dynamically routing AI workloads across diverse local and cloud AI providers:
- **Cloud Models:** Google Gemini, OpenAI-compatible APIs, HuggingFace Hub, AGY SDK.
- **Local Runtimes:** Microsoft Foundry Local, Windows AI APIs (DirectML / NPU), ONNX Runtime, Ollama.
- **Agentic Capabilities:** Model Context Protocol (MCP) server, universal Skills Registry, RAG vector retrieval, and audio/TTS pipelines.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Web Interface Layer (FastAPI Static)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Chat UI    │  │  Admin Tabs  │  │  Skills Tab  │  │    MCP Tab     │  │
│  │ (SSE / WS)   │  │ (Logs/Keys)  │  │ (Registry)   │  │(Tools/Servers) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         └─────────────────┴─────────────────┴──────────────────┘           │
│                                    │                                        │
│                         ┌──────────▼──────────┐                             │
│                         │    FastAPI Server   │                             │
│                         │   (uvicorn main:app)│                             │
│                         └──────────┬──────────┘                             │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐              │
│          │                         │                         │              │
│   ┌──────▼────────┐         ┌──────▼────────┐         ┌──────▼────────┐     │
│   │   AI Routing  │         │  MCP & Skills │         │ Storage & RAG │     │
│   │   Dispatcher  │         │   Registry    │         │ (SQLite/FAISS)│     │
│   └──────┬────────┘         └──────┬────────┘         └──────┬────────┘     │
│          │                         │                         │              │
│   ┌──────┴───────────────────────────────────────────────────┴───────┐      │
│   │                     AI Provider Layer                            │      │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │      │
│   │  │  Gemini  │ │ Foundry  │ │ WindowsAI│ │   ONNX   │             │      │
│   │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤             │      │
│   │  │  Ollama  │ │   AGY    │ │  OpenAI  │ │  HF Hub  │             │      │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │      │
│   └──────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Codebase Layout (`src/`)

All functional code resides under [`src/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src):

| Directory | Module Purpose |
|---|---|
| [`src/ai/providers/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/ai/providers) | 9 modular provider packages (`gemini`, `foundry`, `windows_ai`, `onnx`, `ollama`, `agy`, `gemini_cli`, `openai`, `huggingface`) |
| [`src/fastapi/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi) | 15 API routers and static webinterface |
| [`src/skills/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/skills) | Universal skills discovery, registry, and contract exporter |
| [`src/rag/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/rag) | RAG indexing, embeddings, and vector retrieval |
| [`src/logger/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/logger) | Centralized, cross-platform logging system |
| [`src/secrets/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/secrets) | Secure API key state and secret loaders |
| [`src/tts/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/tts) | Text-to-speech synthesis (Edge TTS, Silero) |
| [`src/user_manager/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/user_manager) | User profile, authentication, and token management |
| [`src/version_manager.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/version_manager.py) | Semantic versioning and changelog tracking |

---

## 🌐 FastAPI Routers Specification

The backend exposes 15 dedicated routers under `src/fastapi/`:

| Router | Path Prefix | Key Endpoints | Description |
|---|---|---|---|
| `router_chat.py` | `/api/chat` | `/api/chat`, `/api/chat/ws`, `/api/chat/stream` | Unified conversational routing and streaming |
| `router_openai.py` | `/v1` | `/v1/chat/completions`, `/v1/models` | OpenAI-compatible proxy interface |
| `router_mcp.py` | `/api/mcp` | `/api/mcp/servers`, `/api/mcp/tools`, `/api/mcp/call` | Model Context Protocol gateway |
| `router_rag.py` | `/api/rag` | `/api/rag/search`, `/api/rag/rebuild`, `/api/rag/status` | Semantic vector search and RAG operations |
| `router_agents.py` | `/api/agents` | `/api/agents/list`, `/api/agents/invoke` | Subagent dispatch and execution monitoring |
| `router_admin.py` | `/admin`, `/api/admin` | `/api/admin/config`, `/api/admin/stats` | Administrative control panel and configuration |
| `router_auth.py` | `/auth` | `/auth/google`, `/auth/callback`, `/auth/check`, `/auth/logout` | Authentication and Google OAuth2 integration |
| `router_control.py` | `/ws/control` | `/ws/control` | Real-time WebSocket device control |
| `router_google_accounts.py` | `/api/google` | `/api/google/accounts`, `/api/google/sync` | Multi-account Google services management |
| `router_keys.py` | `/api/keys` | `/api/keys/status`, `/api/keys/rotate` | API key health and quota monitoring |
| `router_logs.py` | `/api/logs` | `/api/logs/stream`, `/api/logs/analyze` | Real-time log streaming and diagnostic analysis |
| `router_tts.py` | `/api/tts` | `/api/tts/synthesize`, `/api/tts/voices` | Text-to-speech audio synthesis |
| `router_audio.py` | `/api/audio` | `/api/audio/transcribe`, `/api/audio/devices` | Audio capture and transcription |
| `router_user_storage.py` | `/api/storage` | `/api/storage/files`, `/api/storage/quota` | Per-user sandboxed storage |
| `router_version.py` | `/api/version` | `/api/version`, `/api/version/check` | System version and component compatibility |

---

## 🤖 AI Providers Reference (`src/ai/providers/`)

1. **`gemini`:** Google Gemini Flash/Pro models with multimodal vision and tool calling.
2. **`foundry`:** Microsoft Foundry Local integration for local ONNX/DirectML LLMs.
3. **`windows_ai`:** Native Windows App SDK / Copilot+ PC AI features and NPU offloading.
4. **`onnx`:** Direct execution of quantized models via ONNX Runtime (DirectML / CPU / CUDA).
5. **`ollama`:** Local daemon integration for open-weights models (Llama 3, Qwen, Mistral).
6. **`agy`:** Google Antigravity SDK proxy.
7. **`openai`:** OpenAI API and generic OpenAI-compatible cloud/local endpoints.
8. **`huggingface`:** Inference client for HuggingFace models.
9. **`gemini_cli`:** Google Gemini CLI agent wrapper.

---

## 🧩 Plugins (`plugins/`)

Modular extensions located in [`plugins/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/plugins):
- `rag_cleaner`: Document sanitizer for parsing PDF, DOCX, ZIP, HTML into clean RAG chunks.
- `generate_rag_from_codebase`: Automated RAG index generator from source code files.
- `log_analyzer`: Intelligent log clustering and error diagnosis.
- `telegram_bot`: Telegram notifications and remote interaction.
- `media_organizer`: Media indexing and metadata categorization.
- `facebook`: Facebook graph integration adapter.

---

### 🛠️ Management & Launch

- **Universal CLI:** `py manage_tools.py <skills|rag|knowledge|db|docs|assist>`
- **Main Launcher:** `.\run.ps1`
- **FastAPI Launcher:** `.\launchers\Run-Unicorn.ps1`
- **Tests:** `.\launchers\run_tests.ps1`

---

## 🔗 Related Knowledge & Standards

- [`GEMINI.md`](../../../GEMINI.md) — Master project overview and engineering principles
- [`scripts_tools.md`](scripts_tools.md) — Universal CLI and scripts reference
- [`MODEL_SCRIPT_EXECUTION_GUIDE.md`](MODEL_SCRIPT_EXECUTION_GUIDE.md) — AI agent script execution guide
- [`api_documentation.md`](api_documentation.md) — Full REST and WebSocket API specification
- [`UI_INTERFACES.md`](UI_INTERFACES.md) — Web interfaces, tabs, and component layout
- [`LAUNCHER_GUIDE.md`](LAUNCHER_GUIDE.md) — Launchers and background service management
- [`.ai/instructions/rules/CODE_RULES.md`](../rules/CODE_RULES.md) — Code quality and architecture standards
- [`.ai/instructions/rules/DOCS_RULES.md`](../rules/DOCS_RULES.md) — Documentation and TDD rules

---

**Status:** ✅ Up to date (September 2026)  
**Version:** 3.0  
**Author:** hypo69
