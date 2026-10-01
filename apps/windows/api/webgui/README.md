# Web Interface — AI Breadboard

The `webinterface/` directory contains the frontend user interfaces and administrative dashboards for the AI Breadboard ecosystem, supporting multi-provider AI chat, media streaming, system management, RAG search, and agent orchestration.

---

## Directory Structure

```
webinterface/
├── index.html            # Main web application dashboard
├── admin/                # Full administrative dashboard portal
├── admin_tab/            # Server settings, active connection monitors, system operations
├── plugins_tab/          # Plugin manager and scanner configurator
├── chat/                 # Conversational AI chat with multi-provider selector and streaming
├── users_tab/            # User account and profile management
├── models_tab/           # Model provider switcher, parameter tuning, API key status
├── agents_tab/           # ReAct AI agent workbench and testing harness
├── search_tab/           # RAG and web search interface
├── tts_tab/              # Text-to-speech engine and voice selection
├── instructions_tab/     # System instruction, role, and prompt version manager
├── cosmicplayer/         # Streaming media video player
├── rc/                   # Remote control interface for synchronized playback
├── sources/              # Media and drive source paths manager
├── sources_tab/          # Visual scan and audit manager for media libraries
├── user/                 # User-facing portal (Telegram Mini App compatible)
├── user_tts/             # User-specific voice preferences
├── help/                 # Integrated help and documentation system
├── js/                   # Shared client-side ES Modules (i18n, chatService, theme)
└── locales/              # i18n localization translation JSON bundles (en, ru, es, he)
```

---

## Portals Overview

### 1. User Interface (`/user`)
A streamlined interface designed for desktop and mobile devices (Telegram Mini App compatible).
- **Player Tab**: Video streaming with automatic playback of sequential episodes.
- **Chat Tab**: Context-aware AI assistant with automated `<film>` tag detection for one-click playback.

### 2. Admin Interface (`/admin`)
Comprehensive management suite for administrators:
- **Chat & Prompts**: Direct AI querying, prompt inspection, and model parameters testing.
- **Media & Torrents**: qBittorrent integration, integrity audits, missing file relocations.
- **RAG & Indexing**: Semantic index rebuilding, confidence thresholds, knowledge base inspection.
- **Agents & Tools**: ReAct agent configuration, MCP server routing, and skill management.

---

## Frontend Architecture & Technology Stack

- **Framework**: Bootstrap 5 + Vanilla JavaScript (Modern ES Modules).
- **Internationalization (i18n)**: Multi-language switching (`i18next`) supporting English, Russian, Spanish, and Hebrew.
- **Real-Time Communication**: Server-Sent Events (SSE) and WebSockets for token streaming, log monitors, and remote control.
- **Version Tracking**: Automatic static asset cache-busting queries (`?v=YYYYMMDD`).
