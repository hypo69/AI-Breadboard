# `webinterface/chat` — Conversational AI Chat Interface

## Purpose
Core interactive chat module providing real-time streaming conversations with AI models via `UnifiedChatModel`.

---

## Key Features
- **Provider & Model Switcher**: Seamless switching between Gemini, Foundry, AGY, Ollama, ONNX, and OpenAI.
- **SSE & WebSocket Streaming**: Low-latency token-by-token response rendering with markdown syntax highlighting.
- **Tool & Action Tags**: Automatic extraction and rendering of custom UI cards (e.g. `<film>` media tags, links).
- **Chat History & Context**: Session-based memory management and dynamic prompt attachment.

---

## Files
- `index.html`: Chat container and message feed markup.
- `main.js`: Streaming SSE client, markdown renderer, and prompt dispatcher.
- `style.css`: Chat bubbles and responsive layout styling.
