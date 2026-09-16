# 🏗️ Архитектура системы AI Breadboard

**Статус:** ✅ Up to date (сентябрь 2026)  
**Версия:** 3.0  
**Автор:** hypo69  
**Copyright:** © 2026 hypo69

---

## 📋 Содержание
1. [Концепция системы](#1-концепция-системы)
2. [Общая архитектура](#2-общая-архитектура)
3. [Слои и компоненты](#3-слои-и-компоненты)
4. [Файловая структура `src/`](#4-файловая-структура-src)
5. [AI провайдеры](#5-ai-провайдеры)
6. [FastAPI роутеры](#6-fastapi-роутеры)

---

## 1. Концепция системы

**AI Breadboard** — интерактивный, расширяемый developer workbench и runtime для тестирования, бенчмарков и динамической маршрутизации AI workloads между разнообразными локальными и облачными AI провайдерами:

- **Облачные модели:** Google Gemini, OpenAI-совместимые API, HuggingFace Hub, AGY SDK
- **Локальные runtime:** Microsoft Foundry Local, Windows AI APIs (DirectML / NPU), ONNX Runtime, Ollama
- **Агентные возможности:** Model Context Protocol (MCP) сервер, universal Skills Registry, RAG векторный поиск, audio/TTS pipeline

---

## 2. Общая архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Веб-интерфейс (FastAPI Static)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Chat UI    │  │  Admin Tabs  │  │  Skills Tab  │  │    MCP Tab     │  │
│  │ (SSE / WS)   │  │ (Logs/Keys)  │  │ (Registry)   │  │(Tools/Servers) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         └─────────────────┴─────────────────┴──────────────────┘           │
│                                    │                                        │
│                         ┌──────────▼──────────┐                             │
│                         │    FastAPI Server   │                             │
│                         │   (uvicorn main:app)│                             │
│                         └──────────┬──────────┘                             │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐              │
│          │                         │                         │              │
│   ┌──────▼────────┐         ┌──────▼────────┐         ┌──────▼────────┐     │
│   │   AI Routing  │         │  MCP & Skills │         │ Storage & RAG │     │
│   │   Dispatcher  │         │   Registry    │         │ (SQLite/FAISS)│     │
│   └──────┬────────┘         └──────┬────────┘         └──────┬────────┘     │
│          │                         │                         │              │
│   ┌──────┴───────────────────────────────────────────────────┴───────┐      │
│   │                     AI Provider Layer                            │      │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │      │
│   │  │  Gemini  │ │ Foundry  │ │ WindowsAI│ │   ONNX   │             │      │
│   │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤             │      │
│   │  │  Ollama  │ │   AGY    │ │  OpenAI  │ │  HF Hub  │             │      │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │      │
│   └──────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Слои и компоненты

### 3.1 Слой 1: Веб-интерфейс (Presentation Layer)

**Местоположение:** `src/api/webinterface/`

**Компоненты:**
- **Chat UI** — Интерфейс чата (SSE и WebSocket потоки)
- **Admin Dashboard** — Административные вкладки (логи, ключи, конфиг)
- **Skills Registry** — Реестр доступных умений
- **MCP Dashboard** — Управление MCP серверами и инструментами

### 3.2 Слой 2: API & Маршрутизация (Application Layer)

**Местоположение:** `src/fastapi/`

**FastAPI Router'ы:**
- `router_chat.py` — Unified chat endpoint
- `router_mcp.py` — MCP protocol gateway
- `router_rag.py` — RAG поиск и индексирование
- `router_agents.py` — Управление агентами
- `router_admin.py` — Административные функции
- `router_auth.py` — Аутентификация
- ... и ещё 10+ специализированных роутеров

### 3.3 Слой 3: Бизнес-логика (Business Logic Layer)

**Местоположение:** `src/ai/`, `apps/`, плагины

**Компоненты:**
- **UnifiedChatModel** — Единый интерфейс для всех провайдеров
- **AI Provider Clients** — Интеграция с каждым провайдером
- **Skills System** — Registry и execution engine
- **RAG Engine** — Векторный поиск и embeddings
- **Plugin System** — Динамическая загрузка плагинов

### 3.4 Слой 4: Инфраструктура (Infrastructure Layer)

**Местоположение:** `src/`

**Компоненты:**
- **Logger** — Централизованное логирование
- **Config Manager** — Управление конфигурацией
- **Secrets Manager** — Управление API ключами
- **Database Layer** — SQLite, миграции
- **File Storage** — Хранилище пользовательских файлов

---

## 4. Файловая структура `src/`

```
src/
├── __init__.py
│
├── ai/                                  ← AI Routing & Provider Integration
│   ├── __init__.py
│   ├── providers/                       ← 9 провайдеров (gemini, foundry, ollama, и т.д.)
│   │   ├── gemini/                      ← Google Gemini Flash/Pro
│   │   ├── foundry/                     ← Microsoft Foundry Local
│   │   ├── windows_ai/                  ← Windows AI (DirectML / NPU)
│   │   ├── onnx/                        ← ONNX Runtime
│   │   ├── ollama/                      ← Ollama Local Models
│   │   ├── agy/                         ← AGY SDK
│   │   ├── gemini_cli/                  ← Gemini via CLI
│   │   ├── openai/                      ← OpenAI-compatible
│   │   └── huggingface/                 ← HuggingFace Hub
│   ├── unified_chat_model.py            ← Единый интерфейс всех провайдеров
│   └── README.md
│
├── fastapi/                             ← REST API Layer (17+ роутеров)
│   ├── __init__.py
│   ├── router_chat.py                   ← /api/chat endpoints
│   ├── router_mcp.py                    ← /api/mcp endpoints
│   ├── router_rag.py                    ← /api/rag endpoints
│   ├── router_admin.py                  ← /api/admin endpoints
│   ├── router_auth.py                   ← /auth endpoints
│   ├── router_agents.py                 ← /api/agents endpoints
│   ├── router_keys.py                   ← /api/keys endpoints
│   ├── router_logs.py                   ← /api/logs endpoints
│   ├── router_tts.py                    ← /api/tts endpoints
│   ├── helpdesk/                        ← Support ticket coordinator
│   ├── messenger/                       ← Real-time messenger engine
│   ├── webinterface/                    ← Static веб-интерфейс
│   │   ├── admin/                       ← Admin dashboard
│   │   ├── chat_tab/                    ← Chat tab UI
│   │   ├── skills_tab/                  ← Skills registry UI
│   │   └── mcp_tab/                     ← MCP dashboard UI
│   └── README.md
│
├── .skills/                             ← Skills Discovery & Registry
│   ├── __init__.py
│   ├── registry.py                      ← Skills registry engine
│   ├── contracts.py                     ← Skills contracts
│   └── README.md
│
├── rag/                                 ← RAG (Retrieval Augmented Generation)
│   ├── __init__.py
│   ├── indexer.py                       ← Document indexing
│   ├── retriever.py                     ← Vector search
│   ├── embeddings.py                    ← Embedding models
│   └── README.md
│
├── logger/                              ← Centralized Logging
│   ├── __init__.py
│   ├── logger.py                        ← Logger configuration
│   └── README.md
│
├── secrets/                             ← Secret Management
│   ├── __init__.py
│   ├── secrets_manager.py               ← API keys, credentials
│   └── README.md
│
├── tts/                                 ← Text-to-Speech
│   ├── __init__.py
│   ├── edge_tts.py                      ← Edge TTS provider
│   ├── silero.py                        ← Silero provider
│   └── README.md
│
├── user_manager/                        ← User Profile & Auth
│   ├── __init__.py
│   ├── user.py                          ← User model
│   ├── auth.py                          ← Authentication
│   └── README.md
│
├── config.py                            ← Configuration loader
├── version_manager.py                   ← Semantic versioning
└── README.md                            ← Overview
```

---

## 5. AI провайдеры

### 5.1 Архитектура провайдера

Каждый провайдер имеет одинаковую структуру:

```
src/ai/providers/<provider_name>/
├── __init__.py
├── connector.py             ← Connection management
├── models.py                ← Data models (Pydantic)
├── client.py                ← HTTP/API client
├── handlers.py              ← Response handlers
└── README.md
```

### 5.2 Унификация через UnifiedChatModel

Все провайдеры используются через единый интерфейс:

```python
from src.ai import UnifiedChatModel

# Автоматическое переключение между провайдерами
model = UnifiedChatModel(provider='gemini')  # или 'foundry', 'ollama', и т.д.

# Унифицированный интерфейс
response = model.chat("Hello", temperature=0.7)

# Потоковый вывод
for chunk in model.stream_chat("Tell me a story"):
    print(chunk)
```

### 5.3 Поддерживаемые провайдеры

| Провайдер | Тип | Особенности |
|-----------|-----|-----------|
| **Gemini** | Облако | Multimodal, vision, tool calling |
| **Foundry** | Локально | Microsoft AI Foundry, HTTP API |
| **Ollama** | Локально | Open-source models |
| **ONNX** | Локально | Hardware-optimized inference |
| **Windows AI** | Локально | DirectML, NPU support |
| **OpenAI** | Облако | Compatible API |
| **HuggingFace** | Облако | API inference |
| **AGY** | Облако | Custom AGY SDK |

---

## 6. FastAPI роутеры

### 6.1 Структура роутера

```python
# Каждый роутер: src/fastapi/router_<name>.py

from fastapi import APIRouter

router = APIRouter(
    prefix="/api/<endpoint_name>",
    tags=["<endpoint_name>"]
)

@router.get("/status")
async def get_status():
    """Get endpoint status."""
    return {"status": "ok"}

def init_router():
    """Initialize and return router."""
    return router
```

### 6.2 Основные роутеры

| Роутер | Путь | Назначение |
|--------|------|-----------|
| `router_chat.py` | `/api/chat` | Unified chat endpoint |
| `router_mcp.py` | `/api/mcp` | MCP protocol gateway |
| `router_rag.py` | `/api/rag` | RAG search & indexing |
| `router_admin.py` | `/api/admin` | Admin panel & config |
| `router_auth.py` | `/auth` | Authentication (Google OAuth2) |
| `router_agents.py` | `/api/agents` | Subagent dispatch |
| `router_openai.py` | `/v1` | OpenAI-compatible proxy |
| `router_keys.py` | `/api/keys` | API key health monitoring |
| `router_logs.py` | `/api/logs` | Real-time log streaming |
| `router_tts.py` | `/api/tts` | Text-to-speech synthesis |
| `router_audio.py` | `/api/audio` | Audio transcription |
| `router_version.py` | `/api/version` | System version & compatibility |
| `router_user_storage.py` | `/api/storage` | Per-user file storage |
| `router_google_accounts.py` | `/api/google` | Google services sync |
| `router_control.py` | `/ws/control` | WebSocket device control |
| `router_helpdesk.py` | `/api/helpdesk` | Support tickets |
| `router_messenger.py` | `/api/messenger` | Real-time messaging |

### 6.3 Регистрация роутеров

Все роутеры регистрируются в `src/app/__init__.py`:

```python
def register_routers(app: FastAPI, state: dict) -> None:
    """Register all API routers with FastAPI application."""
    
    app.include_router(init_chat_router())
    app.include_router(init_mcp_router())
    app.include_router(init_rag_router())
    # ... и т.д.
```

---

## 📚 Дополнительные ресурсы

- [`API_REFERENCE.md`](API_REFERENCE.md) — Полный список всех endpoints
- [`CHAT_IMPLEMENTATION.md`](CHAT_IMPLEMENTATION.md) — Как работает UnifiedChatModel
- [`PLUGIN_SYSTEM.md`](PLUGIN_SYSTEM.md) — Архитектура плагинов
- [`standards/ENGINEERING.md`](../standards/ENGINEERING.md) — Инженерные стандарты

---

**Последнее обновление:** сентябрь 2026
