# `core.fastapi` Module — HTTP Routing & WebSocket Subsystem

## Purpose
The `core.fastapi` package hosts the API routers powering the web dashboards, client applications, streaming chat interfaces, and administrative endpoints for the AI Breadboard.

---

## Router Registry

| Router File | Prefix / Route | Purpose |
|---|---|---|
| `router_chat.py` | `/api/chat` | WebSocket and SSE endpoints for conversational AI streaming with `UnifiedChatModel`. |
| `router_media.py` | `/api/media` | Media library queries, video streaming pipelines, title cards, and metadata inspection. |
| `router_qbittorrent.py` | `/api/torrents` | qBittorrent client integration: search, automated downloads, category routing, status. |
| `router_auth.py` | `/auth` | Google OAuth2 and local session authentication handlers. |
| `router_control.py` | `/ws/control` | WebSocket gateway for synchronized media playback remote control. |
| `router_tts.py` | `/api/tts` | Speech synthesis generation, voice listing, and audio stream delivery. |
| `router_logs.py` | `/api/logs` | Real-time system log streaming and historical log file inspection. |
| `router_keys.py` | `/api/keys` | API key status verification, quota inspection, and key rotation management. |
| `router_admin.py` | `/admin`, `/api/admin` | System health checks, disk scanning, database rebuild, and admin operations. |
| `router_agents.py` | `/api/agents` | ReAct agent configuration CRUD, prompt testing, and MCP tool assignment. |

---

## Initialization Pattern

Each router exports an initialization factory function (e.g. `init_chat_router()`, `init_admin_router()`). The central `core/fastapi/__init__.py` exports all factory functions for assembly in `main.py`:

```python
from fastapi import FastAPI
from core.fastapi import (
    init_auth_router,
    init_chat_router,
    init_qbt_router,
    init_media_admin_router,
    init_control_router,
    init_tts_router,
    init_logs_router,
    init_keys_router,
    init_admin_router,
    init_agents_router
)

app = FastAPI(title="AI Breadboard API")

app.include_router(init_auth_router(), prefix="/auth")
app.include_router(init_chat_router(model, plugins), prefix="/api")
app.include_router(init_agents_router(), prefix="/api")
# Additional routers registered in main.py
```

---

## OpenAPI & Swagger Documentation
Interactive API docs are hosted dynamically at:
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/redoc` — ReDoc
