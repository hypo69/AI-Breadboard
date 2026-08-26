# `webinterface/admin` — Administrator Portal

## Purpose
Hosts the primary administrative portal (`/admin`) for system-wide configuration, advanced AI debugging, media library audits, and server monitoring.

---

## Key Views & Features
- **System Overview**: Host environment status, active background tasks, and connected drive health.
- **Model Orchestration**: Live status of Google Gemini, Microsoft AI Foundry, ONNX, and Ollama providers.
- **Database & Index Management**: Direct maintenance operations for `media.db` and FAISS RAG vector indexes.
- **API Key & Quota Monitor**: Real-time status of pooled API keys, rate-limit cooldowns, and round-robin usage.

---

## Assets
- `index.html`: Administrative layout and navigation shell.
- `main.js`: Dashboard orchestration, event listeners, and API bridge.
- `style.css`: Admin theme styling.
