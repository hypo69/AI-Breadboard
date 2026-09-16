# AI-Breadboard Documentation

AI-Breadboard is a local-first AI assistant server with multi-LLM routing, RAG, TTS, Skills, Agents, and a web interface.

## Quick Links

- [Quick Start](quickstart.md)
- [Features](features.md)
- [User Guide](user/getting-started.md)
- [Developer Guide](dev/getting-started.md)
- [API Reference](dev/api-reference.md)

## Architecture

```
main.py → FastAPI (src/app/factory.py)
        → 25+ Routers (src/fastapi/)
        → AI Orchestration (src/ai/orchestration/)
        → RAG Engine (src/rag/)
        → Plugin System (src/plugins/)
```

See [Architecture](dev/architecture.md) for details.
