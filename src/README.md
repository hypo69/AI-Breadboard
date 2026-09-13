# `src` Module — System Core Architecture

## Purpose
The `src` directory hosts backend service components and subsystems powering the `AI-Breadboard` application:

- **Application Layer** (`src.app`): FastAPI application factory, middleware, state management, WebSocket hub, metrics collection, and CORS configuration
- **AI Model Orchestration** (`src.ai`): Unified multi-provider model switches, Gemini SDK pooling, Microsoft AI Foundry, ONNX, Hugging Face, AGY, Ollama, and LangChain agents
- **API Routing** (`src.api`): Modular API routers for chat, auth, admin, sync, RAG, audio, and specialized services
- **FastAPI Core** (`src.fastapi`): Legacy routing and WebSocket gateways (being refactored into src.api)
- **RAG Subsystem** (`src.rag`): Domain-agnostic RAG-First request routing, semantic rule matching, and knowledge retrieval
- **Database Layer** (`src.db`): SQLite abstractions for users, sessions, and application data
- **Integrations** (`src.integrations`): External service connectors (Google Workspace, IFTTT, messaging platforms)
- **Logging Subsystem** (`src.logger`): Singleton structured logging with colored console outputs, rotating files, and JSON formats
- **Secrets Management** (`src.secrets`): Key rotation, quota cooldown tracking, and multi-source credential loading
- **Skills Framework** (`src.skills`): Discovery, registration, and contract validation for AI agent skills
- **Plugins System** (`src.plugins`): Dynamic plugin loading and lifecycle management
- **Speech Synthesis (TTS)** (`src.tts`): Multi-engine text-to-speech abstractions (Edge-TTS, gTTS, Silero)
- **User Management** (`src.user_manager`): User profile CRUD, preferences, and session storage backed by SQLite
- **Utilities & Converters** (`src.utils`): Format converters, file helpers, resilient JSON parsing, SemVer checks, and media processors
- **Network Management** (`src.network`): Network configuration, port management, and connectivity checks
- **System Tools** (`src.system`): System-level operations, Windows admin tools, and process management

---

## Application Architecture (src.app)

The `src.app` package provides the unified application layer that wires together all subsystems:

### Structure
```
src/app/
├── __init__.py          # Application factory + router registration
├── state.py             # AppState dataclass (models, services, uptime)
├── middleware.py        # HTTP middleware (auto_login, metrics)
├── cors.py              # CORS configuration builder
├── metrics.py           # Prometheus-compatible metrics collector
├── ws_hub.py            # WebSocket connection hub
├── config_api.py        # AI provider configuration endpoints
├── versioning.py        # Version check and update logic
├── server_config.py     # Uvicorn server configuration
├── routers/             # Additional auto-discovered routers
└── pages/               # UI page handlers
```

### Usage
```python
from src.app import (
    create_app,
    register_routers,
    register_pages,
    register_config_api,
    AppState,
    create_metrics,
    WSHub,
)

# Create application
app = create_app()

# Initialize state
state = AppState()
state.metrics = create_metrics()
state.ws_hub = WSHub()

# Initialize models
state.chat_model = UnifiedChatModel()
state.narrator_model = UnifiedChatModel()

# Store in app.state
app.state.app_state = state
app.state.metrics = state.metrics
app.state.ws_hub = state.ws_hub

# Register routers with dependency injection
register_routers(app, state)
register_pages(app)
register_config_api(app)
```

### AppState Components
| Attribute | Type | Purpose |
|-----------|------|---------|
| `chat_model` | `UnifiedChatModel` | Primary AI model for chat interactions |
| `narrator_model` | `UnifiedChatModel` | Secondary model for narration/streaming |
| `ws_hub` | `WSHub` | WebSocket connection manager |
| `metrics` | `MetricsCollector` | Prometheus metrics collection |
| `plugin_registry` | `PluginRegistry` | Dynamic plugin management |
| `started_at` | `float` | Server startup timestamp |
| `uptime_seconds` | `float` | Property: seconds since startup |

---

## Architecture Principles

1. **Explicit Dependencies:** No hidden global state; dependencies are explicitly injected or exposed through singleton accessors (`get_chat_model()`, `get_rag_engine()`, `logger`).
2. **Fail-Fast:** Preconditions are validated early with immediate return or explicit exceptions.
3. **No `None` Default Banning:** In alignment with project rules, class attributes and signatures use concrete empty defaults (`Optional[str] = ''`, `Optional[list] = []`, `Optional[dict] = {}`, `Optional[float] = 0.0`).
4. **Universal Contract:** AI providers conform to standard methods: `ask()`, `chat()`, `stream_chat()`, and `chat_stream()`.
5. **Single Source of Truth:** All application-level services managed through `AppState`, no duplicate implementations.

---

## AI Breadboard — Concept

**Core Idea:** A construction kit platform for connecting and testing AI models in your projects.

### UnifiedChatModel Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedChatModel                         │
│    (Unified interface for all AI providers)                 │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Gemini    │  Foundry    │   Ollama    │   AGY / OpenAI  │
│  (Google)   │ (Microsoft) │  (Local)    │   (Compatible)  │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Provider** | Gemini, Foundry, Ollama, AGY, OpenAI-compatible via unified interface |
| **Plugin System** | 11+ extension modules (media, rag, qbittorrent, etc.) |
| **RAG** | Semantic search + Function Calling |
| **Configuration** | `config.json` — everything configurable without code changes |
| **LangChain** | Agent and tools integration |
| **MCP** | Model Context Protocol support |
| **WebSocket Hub** | Real-time communication channels (chat, voice, metrics, admin) |
| **Metrics** | Prometheus-compatible monitoring |

### Code Standards

- **No `None`** — only empty type values (`0`, `''`, `[]`, `{}`)
- **Early Return** — fail-fast pattern
- **Documentation** — mandatory Docstrings for all public functions
- **Configuration** — everything from JSON/ENV, no hardcoded values
- **Single Implementation** — no duplicate code paths for the same functionality

### Provider Configuration (config.json)

```json
{
  "ai": {
    "use_foundry": true,
    "foundry_model_id": "qwen2.5-1.5b-instruct-generate:4",
    "use_ollama": true,
    "ollama_model_id": "llama3.1",
    "use_gemini_cli": true
  },
  "openai_compat": {
    "providers": {
      "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"]
      },
      "lmstudio": {
        "base_url": "http://localhost:1234/v1",
        "models": []
      }
    }
  }
}
```

### Available AI Providers

| Provider | Type | Configuration Key |
|----------|------|-------------------|
| Google Gemini | Cloud | `use_gemini_cli`, `gemini_cli_model_id` |
| Microsoft Foundry | Local/Cloud | `use_foundry`, `foundry_model_id` |
| Ollama | Local | `use_ollama`, `ollama_model_id` |
| AGY (Antigravity) | Cloud | `use_agy`, `agy_model_id` |
| OpenAI Compatible | Any REST API | `openai_compat.providers.*` |

### Plugin Architecture

All plugins inherit from `BasePlugin` and implement:
- `name: str` — unique plugin identifier
- `enabled: bool` — plugin activation flag
- `async def handle(self, message: str, **kwargs) -> str` — main handler

Plugins are dynamically loaded from `plugins/` directory and can be disabled via `DISABLED_PLUGINS` environment variable.

### RAG System Components

1. **Indexing** — Vector embeddings via Gemini API or ONNX models
2. **Storage** — SQLite + FAISS for vector similarity search
3. **Retrieval** — Semantic rule matching against queries
4. **Generation** — Function Calling via UnifiedChatModel

### Usage Example

```python
from src.ai.unified_chat_model import UnifiedChatModel
from src.config import server_cfg

# Initialize unified model
model = UnifiedChatModel(
    api_key_names=['gemini'],
    system_instruction='You are a helpful assistant.',
    foundry_model_id='qwen2.5-1.5b-instruct-generate:4',
    use_foundry=True
)

# Automatic provider routing based on model_id
model.model_name = 'gemini-3.1-flash-lite'
response = await model.chat('Hello!')

# Switch to local Foundry model
model.model_name = 'foundry:qwen2.5-1.5b-instruct-generate:4'
response = await model.chat('Hello from local model!')
```

---

## Recent Architectural Changes

### Application Layer Consolidation (2024)
- **Eliminated duplicate implementations**: Merged `/app` (root) and `src/app` into single `src/app` structure
- **Unified state management**: Introduced `AppState` dataclass for all shared services
- **Dependency injection**: Routers now receive models via explicit parameters, not globals
- **See**: `APP_REFACTORING_SUMMARY.md` for migration guide