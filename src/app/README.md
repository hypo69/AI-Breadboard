# src/app — Application Layer

FastAPI application builder and core services for AI-Breadboard.

## Structure

```
src/app/
├── __init__.py          # Application factory (create_app, register_routers)
├── state.py             # AppState dataclass (shared services)
├── middleware.py        # HTTP middleware (metrics, auth helpers)
├── cors.py              # CORS configuration builder
├── metrics.py           # Prometheus-compatible metrics collector
├── ws_hub.py            # WebSocket hub for real-time communication
├── config_api.py        # AI provider configuration endpoints
├── versioning.py        # Version check and update logic
├── server_config.py     # Server startup utilities
├── routers/             # API routers (auto-discovered)
├── pages/               # UI page handlers
└── tests/               # Application tests
```

## Core Components

### Application Factory

[`__init__.py`](./__init__.py) provides the main factory pattern:

```python
from src.app import create_app, register_routers, AppState

app = create_app()
state = AppState()
app.state.app_state = state
register_routers(app, state)
```

### AppState

[`state.py`](./state.py) holds shared services in `app.state`:

- `chat_model`, `narrator_model` — UnifiedChatModel instances
- `ws_hub` — WebSocket hub
- `metrics` — Prometheus-compatible metrics collector
- `plugin_registry`, `plugins` — Plugin system
- `started_at` — Server start timestamp

### WebSocket Hub

[`ws_hub.py`](./ws_hub.py) manages real-time connections:

- Channels: `chat`, `stream`, `voice`, `metrics`, `admin`, `events`
- Automatic heartbeat and disconnect detection
- Broadcast and per-user messaging

### Metrics

[`metrics.py`](./metrics.py) collects HTTP and WebSocket metrics:

- Request latency and status counts
- WebSocket connection count
- Prometheus text output at `/health/metrics`

### Middleware

[`middleware.py`](./middleware.py) provides:

- `metrics_middleware` — records latency and status
- `auto_login_local_user` — localhost auth helper
- Request utilities: `is_localhost`, `get_request_hostname`, `is_authenticated_user`

### CORS

[`cors.py`](./cors.py) builds CORS config from `config.json`:

- Auto-includes localhost/loopback
- Supports `server.cors.allow_origins`, `server.client_url`, `server.user_domain`
- Origin regex for LAN addresses

### Configuration API

[`config_api.py`](./config_api.py) exposes endpoints:

- `/api/foundry/config` — Foundry provider settings
- `/api/ollama/config` — Ollama provider settings
- `/api/agy/config` — Antigravity provider settings
- `/api/onnx/config` — ONNX provider settings
- `/api/onnx/providers` — Available execution providers

### Versioning

[`versioning.py`](./versioning.py) handles updates:

- Local version from `setup.cfg`
- Remote version from GitHub API (releases/tags)
- Auto-update prompt and `git pull --ff-only`

### Server Config

[`server_config.py`](./server_config.py) provides `run_server(app)`:

- Reads SSL config from `config.json` or env vars
- Auto-generates mkcert certs if missing
- Uvicorn startup with reload support

## Usage

```python
# main.py
from src.app import create_app, register_routers, AppState

app = create_app()
state = AppState()
app.state.app_state = state
register_routers(app, state)

if __name__ == "__main__":
    from src.app.server_config import run_server
    run_server(app)
```

Access from routes:

```python
from fastapi import Request

async def handler(request: Request):
    chat_model = request.app.state.chat_model
    ws_hub = request.app.state.ws_hub
    metrics = request.app.state.metrics
```
