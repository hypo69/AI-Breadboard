# Architecture

## Layer Diagram

```
┌─────────────────────────────────────────────┐
│  main.py  (entry point, ~60 lines)          │
│  src/app/factory.py  (Application Factory)  │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  src/app/  (Application Layer)              │
│  ├── lifespan.py    startup/shutdown        │
│  ├── state.py       AppState (app.state)    │
│  ├── cors.py        CORS configuration      │
│  ├── middleware.py  auto-login, helpers     │
│  ├── routes.py      router registration     │
│  ├── metrics.py     MetricsCollector        │
│  └── ws_hub.py      WebSocket hub           │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  src/fastapi/  (HTTP Layer — 25+ routers)   │
│  router_chat, router_auth, router_rag, ...  │
│  router_health.py   /health, /metrics       │
│  router_ws_hub.py   /ws/{channel}           │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  src/ai/  (AI Layer)                        │
│  orchestration/unified_chat.py              │
│  providers/ × 9                             │
│  agents/                                    │
└─────────────────────────────────────────────┘
```

## Key Design Decisions

- **Application Factory**: `create_app()` in `src/app/factory.py` — testable, no global state
- **lifespan**: Replaces deprecated `@app.on_event` — single startup/shutdown context
- **AppState**: All shared services stored in `app.state` — accessible via `request.app.state`
- **UnifiedChatModel**: Prefix-based routing to 9 LLM providers
- **RAG-First**: Score ≥ 0.85 → direct answer; 0.40–0.85 → LLM with context

## Plugin System

Plugins are Python modules in `plugins/` directory. Hot-reload via `watchfiles`. See [Plugins Guide](plugins.md).
