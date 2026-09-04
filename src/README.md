# `core` Module — System Core Architecture

## Purpose
The `core` directory hosts backend service components and subsystems powering the `ai-breadboard` / `AI Breadboard` application:

- **AI Model Orchestration** (`core.ai`): Unified multi-provider model switches, Gemini SDK pooling, Microsoft AI Foundry, ONNX, Hugging Face, AGY, Ollama, and LangChain agents.
- **FastAPI Routing & WebSockets** (`core.fastapi`): Modular API routers, streaming endpoints, authentication, and WebSocket gateways.
- **RAG Subsystem** (`core.rag`): Domain-agnostic RAG-First request routing, semantic rule matching, and knowledge retrieval.
- **External Clients** (`core.clients`): Specialized API clients for Foundry, Ollama, and messaging platforms.
- **Logging Subsystem** (`core.logger`): Singleton structured logging with colored console outputs, rotating files, and JSON formats.
- **Secrets Management** (`core.secrets`): Key rotation, quota cooldown tracking, and multi-source credential loading.
- **Skills Framework** (`core.skills`): Discovery, registration, and contract validation for AI agent skills.
- **Speech Synthesis (TTS)** (`core.tts`): Multi-engine text-to-speech abstractions (Edge-TTS, gTTS, Silero).
- **User Management** (`core.user_manager`): User profile CRUD, preferences, and session storage backed by SQLite.
- **Utilities & Converters** (`core.utils`): Format converters, file helpers, resilient JSON parsing, SemVer checks, and media processors.

---

## Architecture Principles

1. **Explicit Dependencies:** No hidden global state; dependencies are explicitly injected or exposed through singleton accessors (`get_chat_model()`, `get_rag_engine()`, `logger`).
2. **Fail-Fast:** Preconditions are validated early with immediate return or explicit exceptions.
3. **No `None` Default Banning:** In alignment with project rules, class attributes and signatures use concrete empty defaults (`Optional[str] = ''`, `Optional[list] = []`, `Optional[dict] = {}`, `Optional[float] = 0.0`).
4. **Universal Contract:** AI providers conform to standard methods: `ask()`, `chat()`, `stream_chat()`, and `chat_stream()`.
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
| **Plugin System** | 11 extension modules (media, rag, qbittorrent, etc.) |
| **RAG** | Semantic search + Function Calling |
| **Configuration** | `config.json` — everything configurable without code changes |
| **LangChain** | Agent and tools integration |
| **MCP** | Model Context Protocol support |

### Code Standards

- **No `None`** — only empty type values (`0`, `''`, `[]`, `{}`)
- **Early Return** — fail-fast pattern
- **Documentation** — mandatory Docstrings for all public functions
- **Configuration** — everything from JSON/ENV, no hardcoded values

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
from core.ai.unified_chat import UnifiedChatModel
from core.config import gs

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