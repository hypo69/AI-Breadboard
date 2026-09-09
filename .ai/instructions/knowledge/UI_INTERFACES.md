# Web Interfaces & UI Architecture (`UI_INTERFACES.md`)

**Project:** `AI-Breadboard`  
**Location:** [`src/fastapi/webinterface/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/src/fastapi/webinterface)  
**Status:** ✅ Up to date (September 2026)

The web interface is organized as a modular frontend built with modern ES Modules, vanilla JavaScript, and CSS Flex/Grid. The administrative panel dynamically loads dedicated tab components from `src/fastapi/webinterface/*_tab/`.

---

## 🎯 Primary Interfaces

### 1. `/user` — Conversational AI & Multimedia Workspace
**Path:** `src/fastapi/webinterface/user/`  
**Features:**
- Interactive AI chat with SSE streaming and WebSocket support
- RAG semantic search and capability-based routing
- Integrated media player (CosmicPlayer)
- Speech-to-Text (STT) and voice control

### 2. `/admin` — Modular Administration Dashboard
**Path:** `src/fastapi/webinterface/admin/`  
**Features:**
- Unified administrative container dynamically mounting modular tab controllers:
  - **`models_tab`:** AI Provider configuration (Gemini, Foundry, ONNX, Ollama, Windows AI, OpenAI)
  - **`skills_tab`:** Universal skills registry, tool tester, and JSON contract inspector
  - **`mcp_tab`:** Model Context Protocol servers and live tool status
  - **`rag_tab`:** Vector index status, search playground, and rebuild triggers
  - **`agents_tab`:** Subagent memory, execution quotas, and scheduling
  - **`google_accounts_tab`:** Google OAuth credentials and synchronization status
  - **`plugins_tab`:** Extensible plugin activation and runtime options
  - **`search_tab`:** Codebase and document search
  - **`sources_tab`:** Connected drives and data source explorer
  - **`tts_tab` & `voice_tab`:** Text-to-speech and voice input configuration
  - **`users_tab`:** User management and access tokens
  - **`instructions_tab`:** System prompt loader and rules viewer

### 3. `/rc` — Voice & Remote Control
**Path:** `src/fastapi/webinterface/rc/`  
**Features:**
- Voice-activated command listener (Web Speech API)
- Real-time player and assistant control via `/ws/control`

### 4. `/user_tts` — Text-to-Speech Studio
**Path:** `src/fastapi/webinterface/user_tts/`  
**Features:**
- Speech synthesis playground across Edge-TTS and Silero neural voices
- Rate, pitch, and SSML tuning

---

## 📁 Webinterface Layout

```
src/fastapi/webinterface/
├── index.html                  # Landing page
├── admin/                      # Admin shell and layout
├── user/                       # User chat and multimedia interface
├── rc/                         # Remote voice control
├── user_tts/                   # Dedicated TTS studio
├── admin_tab/                  # System administration settings
├── agents_tab/                 # Subagent configuration tab
├── google_accounts_tab/        # Google OAuth sync tab
├── instructions_tab/           # Instructions & prompts tab
├── mcp_tab/                    # MCP servers & tools tab
├── models_tab/                 # AI model routing tab
├── plugins_tab/                # Plugin manager tab
├── rag_tab/                    # RAG vector index tab
├── search_tab/                 # Code/media search tab
├── skills_tab/                 # AI skills registry tab
├── sources_tab/                # Data sources tab
├── tts_tab/ & voice_tab/       # Audio & speech tabs
├── users_tab/                  # User accounts tab
├── js/ & css/                  # Shared utility libraries and styles
└── locales/                    # Multilingual localization bundles
```

---

**Status:** ✅ Up to date (September 2026)  
**Version:** 3.0