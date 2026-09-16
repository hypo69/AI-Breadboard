# API Reference

## Authentication

All API endpoints require authentication unless accessed from localhost.

- **Cookie**: `auth_token` (JWT, httponly)
- **Bearer token**: `Authorization: Bearer <token>`
- **Localhost auto-login**: Requests from `127.0.0.1` / `192.168.x.x` are automatically authenticated as user ID 1

## Core Endpoints

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | Single-turn chat completion |
| POST | `/api/chat/stream` | Streaming chat completion |
| WS | `/ws/chat` | WebSocket chat |

### Health & Observability

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe — `{"status": "ok", "version": "...", "uptime_seconds": N}` |
| GET | `/health/detailed` | Readiness probe — provider status, DB, RAG |
| GET | `/health/metrics` | Prometheus-compatible metrics (text/plain) |

### WebSocket Hub

| Path | Description |
|---|---|
| `/ws/chat` | Chat messages |
| `/ws/stream` | Streaming AI responses |
| `/ws/metrics` | Live metrics feed |
| `/ws/admin` | Admin events |

**Auth**: Pass JWT as query param `?token=...` or in cookie `auth_token`.

### Admin

| Method | Path | Description |
|---|---|---|
| GET | `/admin/plugins` | List loaded plugins |
| POST | `/admin/plugins/reload/{name}` | Hot-reload a plugin |
| POST | `/admin/plugins/load` | Load a new plugin |
| DELETE | `/admin/plugins/{name}` | Unload a plugin |

## Full Swagger UI

Available at `/docs` (localhost only).
