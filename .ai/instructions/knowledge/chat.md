# Conversational AI Architecture (`chat.md`)

**Project:** `AI-Breadboard`  
**Status:** ✅ Up to date (September 2026)

---

## 1. Unified Interface & Capability Dispatch

The core conversational routing lives under [`src/ai/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/ai) and [`src/ai/providers/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/ai/providers). Rather than calling provider SDKs directly in routers, workloads are dispatched through unified interfaces supporting capability-driven routing (`chat`, `vision`, `ocr`, `embedding`, `code`).

### Provider Fallback & Routing
- **Cloud Providers:** Google Gemini, OpenAI-compatible APIs, HuggingFace Hub, AGY SDK.
- **Local Runtimes:** Microsoft Foundry Local, Windows AI APIs, ONNX Runtime (DirectML / CPU), Ollama.
- **Dynamic Fallback:** Automatically switches to local execution if cloud quotas are exceeded or internet connectivity is unavailable.

---

## 2. Request Handling & Interaction Modes

1. **`chat(...)`:** Standard text generation and multi-turn conversation with system instruction injection.
2. **`ask_with_tools(...)`:** Function calling / tool execution loop integrating discovered skills from [`src/skills/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/skills) and MCP tools from [`src/fastapi/router_mcp.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_mcp.py).
3. **`embed(...)`:** Text vectorization used by [`src/rag/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/rag).

---

## 3. API & Router Integration

- Conversational API requests are handled by [`src/fastapi/router_chat.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_chat.py) and [`src/fastapi/router_openai.py`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/router_openai.py).
- Supported streaming modes: SSE (Server-Sent Events) and Full-Duplex WebSockets (`/api/chat/ws`).

---

**Status:** ✅ Up to date (September 2026)  
**Version:** 3.0