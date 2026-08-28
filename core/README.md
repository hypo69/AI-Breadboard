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
