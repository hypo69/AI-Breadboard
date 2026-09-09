# FastAPI REST & WebSocket API Documentation (`api_documentation.md`)

**Project:** `AI-Breadboard`  
**Backend:** FastAPI / Uvicorn  
**Base URL:** `http://localhost:8000` (or configured HTTPS domain)  
**Status:** ✅ Up to date (September 2026)

The AI Breadboard API provides 15 modular routers under [`src/fastapi/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi) for conversational AI, multi-provider routing, Model Context Protocol (MCP), RAG search, skills dispatch, user storage, authentication, audio/TTS, and system administration.

---

## 🔐 Authentication & Session Management (`/auth`)

**Router:** [`src/fastapi/router_auth.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_auth.py)

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/auth/google` | Initiates Google OAuth2 login flow (`?next=/`) |
| `GET` | `/auth/callback` | OAuth2 callback, token exchange, and JWT cookie set |
| `GET` | `/auth/check` | Returns current session and user profile information |
| `POST` | `/auth/logout` | Clears `auth_token` cookie and terminates session |

---

## 💬 Conversational AI & Streaming (`/api/chat`)

**Router:** [`src/fastapi/router_chat.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_chat.py)

### Endpoints

- **`POST /api/chat`** — Send chat prompt with optional streaming (SSE) and capability routing.
  ```json
  {
    "message": "Explain how ONNX DirectML execution works.",
    "model": "gemini-2.0-flash",
    "stream": true,
    "tools": ["storage-controller", "rag-search-manager"]
  }
  ```
- **`WS /api/chat/ws`** — Full-duplex WebSocket stream for real-time token streaming and function call roundtrips.
- **`GET /api/chat/history`** — Retrieve chat history for the active session.
- **`DELETE /api/chat/sessions/{session_id}`** — Clear specific chat session context.

---

## 🔌 OpenAI-Compatible API (`/v1`)

**Router:** [`src/fastapi/router_openai.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_openai.py)

Enables any standard OpenAI client (e.g. OpenAI SDK, LangChain, Cursor, Continue) to connect directly to AI Breadboard.

### Endpoints

- **`POST /v1/chat/completions`** — Standard OpenAI chat completions endpoint (supports streaming SSE).
- **`GET /v1/models`** — List all available models discovered across providers (Gemini, Foundry, Ollama, ONNX, Windows AI).

---

## 🧩 Model Context Protocol (MCP) (`/api/mcp`)

**Router:** [`src/fastapi/router_mcp.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_mcp.py)

### Endpoints

- **`GET /api/mcp/servers`** — List configured and active MCP servers.
- **`POST /api/mcp/servers`** — Register or update an external MCP server connection.
- **`GET /api/mcp/tools`** — List all MCP tools aggregated from registered servers.
- **`POST /api/mcp/call`** — Execute a specific MCP tool call.

---

## 🧠 Semantic Search & RAG (`/api/rag`)

**Router:** [`src/fastapi/router_rag.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_rag.py)

### Endpoints

- **`POST /api/rag/search`** — Perform semantic vector search over knowledge chunks.
  ```json
  {
    "query": "How are skills discovered?",
    "top_k": 5,
    "threshold": 0.65
  }
  ```
- **`POST /api/rag/rebuild`** — Trigger background vector index re-embedding and FAISS index build.
- **`GET /api/rag/status`** — Get index health, record counts, and embedding model state.

---

## 🤖 Subagent Management (`/api/agents`)

**Router:** [`src/fastapi/router_agents.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_agents.py)

### Endpoints

- **`GET /api/agents`** — List active agent configurations, memory quotas, and execution history.
- **`POST /api/agents/invoke`** — Invoke an agent execution pipeline.
- **`GET /api/agents/status/{task_id}`** — Query progress of a background subagent task.

---

## 🔑 API Keys & Provider Health (`/api/keys`)

**Router:** [`src/fastapi/router_keys.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_keys.py)

### Endpoints

- **`GET /api/keys/status`** — Check status, quota health, and error rates of configured provider keys.
- **`POST /api/keys/rotate`** — Force immediate rotation of active Gemini or external API keys.

---

## 📊 Logging & Diagnostics (`/api/logs`)

**Router:** [`src/fastapi/router_logs.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_logs.py)

### Endpoints

- **`GET /api/logs`** — Query system and access logs with filtering by level, component, and date range.
- **`WS /api/logs/ws`** — Live WebSocket stream of system logs.
- **`POST /api/logs/analyze`** — Run AI-powered log diagnostic and error clustering.

---

## 🔊 Audio & Text-to-Speech (`/api/tts`, `/api/audio`)

**Routers:** [`src/fastapi/router_tts.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_tts.py), [`src/fastapi/router_audio.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_audio.py)

### Endpoints

- **`POST /api/tts/synthesize`** — Synthesize text into audio stream (Edge-TTS / Silero).
- **`GET /api/tts/voices`** — List available TTS voices and locales.
- **`POST /api/audio/transcribe`** — Transcribe audio input into text.
- **`GET /api/audio/devices`** — Probe host audio input and output devices.

---

## 📁 User Storage & Google Accounts (`/api/storage`, `/api/google`)

**Routers:** [`src/fastapi/router_user_storage.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_user_storage.py), [`src/fastapi/router_google_accounts.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_google_accounts.py)

### Endpoints

- **`GET /api/storage/files`** — List user sandboxed files and storage quota utilization.
- **`POST /api/storage/upload`** — Upload document or asset for processing / RAG ingestion.
- **`DELETE /api/storage/files/{file_id}`** — Delete user file.
- **`GET /api/google/accounts`** — List connected Google accounts and synced service scopes.
- **`POST /api/google/sync`** — Trigger synchronization of Google Drive / Docs metadata.

---

## ⚙️ Administration & Versioning (`/api/admin`, `/api/version`, `/ws/control`)

**Routers:** [`src/fastapi/router_admin.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_admin.py), [`src/fastapi/router_version.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_version.py), [`src/fastapi/router_control.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_control.py)

### Endpoints

- **`GET /api/admin/config`** — Read public `config.json` configuration.
- **`POST /api/admin/config`** — Update configuration parameters.
- **`GET /api/version`** — Returns current system version, git commit hash, and component versions.
- **`GET /api/version/check`** — Check for updates against remote repository.
- **`WS /ws/control`** — Real-time device and remote control WebSocket connection.