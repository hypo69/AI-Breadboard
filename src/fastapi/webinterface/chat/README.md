# `webinterface/chat` — Conversational AI Chat Interface

## Purpose
Core interactive chat module providing real-time streaming conversations with AI models via `UnifiedChatModel` and provider adapters.

---

## Key Features
- **Provider & Model Switcher**: Seamless switching between Gemini, Foundry, AGY, Ollama, ONNX, and OpenAI.
- **ChatGPT-Style Multi-Session History**: Organize conversations into multiple persistent chat sessions with full sidebar history.
- **Auto-Naming (Smart Titling)**: Sessions are automatically named based on the first prompt of the dialog, with support for manual inline renaming.
- **Collapsible Sidebar**: Easy toggle to collapse or expand the session panel for distraction-free chatting.
- **Output Mode Selector**:
  - `text_only` (💬 Только текст): Direct single-stage text generation with zero voice overhead.
  - `text_and_voice` (💬+🔊 Текст и голос): Real-time text streaming in chat plus automated voice narration synthesis (TTS).
  - `voice_only` (🔊 Только голос): Voice-first interaction with automatic playback and spoken narration formatting.
- **RAG-First Integration**: Dynamic knowledge base searching, score thresholding, and optional auto-indexing.
- **SSE Real-Time Streaming**: Incremental token delivery via `text/event-stream` with Markdown rendering.

---

## Files
- `index.html`: Chat container, toolbar controls (RAG toggle, TOP_K, MIN_SCORE, and Output Mode selector), and message feed.
- `main.js`: Streaming SSE client, mode handler, audio speech trigger, and UI message renderer.
- `style.css`: Chat bubbles and responsive layout styling.
