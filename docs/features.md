# Features

## AI Providers

AI-Breadboard supports multiple LLM backends with automatic routing:

| Provider | Prefix | Notes |
|---|---|---|
| Google Gemini | `gemini:` | Default provider |
| Google Gemini CLI | `gemini_cli:` | Local subprocess agent |
| Antigravity AGY | `agy-` | Google experimental |
| Ollama | `ollama:` | Local models |
| LM Studio / Foundry | `foundry:` | Local models |
| HuggingFace | `hf:` | Local transformers |
| ONNX Runtime | `onnx:` | DirectML accelerated |
| OpenAI Compatible | `openai:`, `deepseek:`, `groq:` | Any OpenAI-compat API |

## RAG (Retrieval-Augmented Generation)

- Document ingestion and indexing
- FAISS / ChromaDB vector search
- RAG-First algorithm (direct answer if score ≥ 0.85)
- User workspace RAG

## Skills & Plugins

- Hot-reload plugin system
- Skill registry from `.agents/skills/`
- Telegram Bot integration
- Google Workspace integration

## Observability

- `GET /health` — liveness probe
- `GET /health/detailed` — readiness with provider status
- `GET /health/metrics` — Prometheus-compatible metrics
- `WS /ws/{channel}` — unified WebSocket hub

## TTS

- Edge TTS (Azure Neural Voices)
- gTTS (Google)
- Silero (local)
