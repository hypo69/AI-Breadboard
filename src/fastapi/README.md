# `src.fastapi` Package — HTTP Routing, WebSocket Subsystem & Uvicorn Runtime

## 📋 Overview

The `src.fastapi` package forms the central API and web gateway for **AI-Breadboard**. Built on **FastAPI** and served via **Uvicorn**, it provides modular HTTP endpoints, streaming Server-Sent Events (SSE), real-time WebSockets, multi-provider LLM routing, role-based access control (RBAC), and administrative management.

---

## 🏗️ Architecture & Router Registry

The application mounts 15+ specialized routers exported from `src.fastapi`:

| Router Module | Prefix / Path | Purpose & Capabilities | Security / Access |
|---|---|---|---|
| `router_auth.py` | `/auth` | Google OAuth2, Email/Password, Telegram Widget auth, JWT session management, user settings. | Public & Authenticated |
| `router_admin.py` | `/admin`, `/api/admin`, `/api/skills`, `/api/plugins` | System prompt versioning (`chat`, `narrator`), plugin registry, RAG settings, user administration. | Admin (`require_admin_user`, cookie verification) |
| `router_chat.py` | `/api/chat` | AI chat streaming (SSE), WebSocket dialogue pipeline, history management, memory integration. | Authenticated / Local |
| `router_openai.py` | `/v1` | OpenAI-compatible `/v1/chat/completions` and `/v1/models` API for IDEs and external tools. | Bearer Token / Local |
| `router_mcp.py` | `/api/admin/mcp`, `/api/user/mcp` | Model Context Protocol (MCP) server management and tool aggregation. | Admin & Authenticated |
| `router_agents.py` | `/api/agents` | ReAct subagents registry, execution pipeline, task monitoring. | Authenticated / Local |
| `router_rag.py` | `/api/rag` | Vector search, semantic document queries, FAISS re-indexing, RAG diagnostics. | Authenticated / Local |
| `router_keys.py` | `/api/keys` | Multi-key quota monitoring, key masking, automated rotation, daily exhaustion reset. | Admin (`require_admin_user`) |
| `router_logs.py` | `/api/logs` | Real-time WebSocket log streaming, log file queries, log analyzer integration. | Admin / Authenticated |
| `router_control.py` | `/api/control`, `/ws/control` | WebSocket remote control pairing rooms, media player state synchronization. | Authenticated / Local |
| `router_tts.py` | `/api/tts` | Text-to-speech synthesis (Edge-TTS, Silero), voice discovery. | Authenticated / Local |
| `router_audio.py` | `/api/audio` | Audio transcription, hardware audio device enumeration. | Authenticated / Local |
| `router_google_accounts.py` | `/api/google/accounts` | Multi-account Google OAuth tokens (Drive, Docs, Gmail, Calendar, Contacts). | Authenticated / Local |
| `router_user_storage.py` | `/api/user/storage` | User sandboxed storage files, upload/delete pipelines. | Authenticated / Local |
| `router_version.py` | `/api/version` | Version checks, Git commit hash reporting, automated updates. | Public / Local |

---

## 🚀 Uvicorn (Unicorn) Launch Ecosystem

The server can be launched through multiple interfaces tailored for development and production:

### 1. PowerShell Launcher (`launchers/Run-Unicorn.ps1`)
Features:
- **Port Conflict Resolution:** Automatically detects occupied ports via `Get-NetTCPConnection` and terminates stale processes before binding.
- **Dynamic SSL/TLS:** Checks `server.use_ssl` and auto-loads certificates from `~/.certs/localhost+2.pem`.
- **Autoreload vs Workers:** Automatically switches between `--reload --reload-dir` (single process dev mode) and `--workers N` (multi-process production mode).
- **Background Watcher:** Launches a background thread waiting for TCP socket readiness to open the browser at `/admin`.

```powershell
.\launchers\Run-Unicorn.ps1 -Host 0.0.0.0 -Port 8000
```

### 2. Cross-Platform Launcher (`launchers/run_unicorn.py`)
Cross-platform Python wrapper supporting Windows, Linux, and macOS with virtual environment detection and automated port management.

```bash
python launchers/run_unicorn.py --host 0.0.0.0 --port 8000
```

### 3. Direct Host Launch (`main.py`)
Direct entry point with custom Windows Proactor EventLoop connection noise suppression (`WinError 10054/10053` handler).

---

## 🔐 Permissions & Access Control (RBAC)

### Access Control Layers
1. **Localhost & Subnet Auto-Authentication (`auto_login_local_user` middleware):**
   - Requests from `127.0.0.1`, `localhost`, and private local networks (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`) automatically receive a JWT cookie mapped to default administrator `user_id=1`.
2. **Admin Password Cookie (`admin_password_verified`):**
   - Form POST to `/admin` validates against `ADMIN_PASSWORD` in `.env` and sets an `HttpOnly` cookie for administrative UI access.
3. **JWT Bearer Token / Cookie Auth:**
   - Standard HS256 JWT tokens with 24-hour expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`). Handled via `get_current_user_data(request)` and `require_admin_user(request)`.
4. **Multi-Platform Identity:**
   - **Google OAuth2:** PKCE-like state validation with offline refresh token handling.
   - **Telegram Widget / WebApp:** Validated via HMAC-SHA256 signature using `TELEGRAM_BOT_TOKEN`.
   - **Email / Password:** Salted password hashing with email verification codes.

---

## 🛡️ Security Mechanisms & Hardening

- **CORS Protection:** Configured with strict origin regex permitting only localhost, private subnets (RFC 1918), and explicitly configured `user_domain` / `cors_origins`.
- **OpenAPI / Swagger Isolation:** `/docs`, `/redoc`, and `/openapi.json` are disabled in public schema (`include_in_schema=False`) and strictly return HTTP 404 for external/public domain requests.
- **CSRF & State Validation:** OAuth authorization flows generate cryptographically secure 32-byte state tokens with 10-minute expiry stored server-side and matched against `HttpOnly` cookies.
- **Open Redirect Defense:** Target redirect query parameters (`next`) are validated strictly against relative path prefixes (`/`).
- **Path Traversal Prevention:** Admin instruction activation sanitizes filenames using `Path(filename).name` before reading or copying from `versions/`.
- **Secrets vs Config Separation:** Public runtime parameters reside in `config.json`; secret keys, passwords, and tokens reside strictly in `.env`.
