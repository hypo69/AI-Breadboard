# Core AI Subsystem (`core/ai`)

## Overview
The `core/ai` package is the central artificial intelligence engine of **AI-Breadboard**, providing capability routing, hardware awareness, and seamless multi-provider abstraction across local and cloud runtimes.

---

## Architecture

```
                               core/ai
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
     orchestration/           providers/                agents/
  (Routing & Discovery) (Dedicated Adapters)     (Autonomous Agents)
          │                       │
          │                       ├── windows_ai/  (Windows AI APIs & Phi Silica)
          │                       ├── foundry/     (Microsoft Foundry Local)
          │                       ├── ollama/      (Ollama Local Daemon)
          │                       ├── onnx/        (Windows ML & DirectML)
          │                       ├── gemini/      (Google Generative AI)
          │                       ├── gemini_cli/  (Gemini CLI utility)
          │                       ├── agy/         (Antigravity Subprocess)
          │                       ├── huggingface/ (Local Transformers)
          │                       └── openai/      (OpenAI-Compatible APIs)
          │
          └── converter/ (GGUF to ONNX model converter)
```

---

## Key Modules
- **`orchestration/`**: Capability registry, hardware probes, discovery engine, routing policies, and `UnifiedChatModel`.
- **`providers/`**: Modular implementations of all local and cloud backends with dedicated `README.md` documentation.
- **`agents/`**: Agentic workflows, MCP tool integration, and prompt management.
- **`converter/`**: Model format converters (e.g., GGUF to ONNX).

---

## Standards
- **Language**: English only for all code, docstrings, comments, logs, and documentation.
- **Error Handling**: Graceful fallback across local and cloud backends without unhandled runtime crashes.
