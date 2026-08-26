# aibreadboard — Интерактивная макетная плата для языковых моделей ИИ

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**AI Breadboard** — это интерактивный стенд и «макетная плата» для исследования, тестирования и сравнения различных моделей ИИ (Google Gemini, Microsoft AI Foundry, Antigravity AGY, Ollama, OpenAI/DeepSeek, Hugging Face, ONNX) в единой среде с универсальным интерфейсом сокетов.

---

## 🤖 Оркестратор провайдеров (ядро системы)

Центральный компонент — `core/ai/model_manager.py` — управляет жизненным циклом моделей всех провайдеров: опрашивает доступные модели при старте, кэширует их в памяти, автоматически исключает неработающие модели из ротации.

`core/ai/unified_chat.py` — единая точка входа для всех запросов. Маршрутизирует вызовы к нужному провайдеру по префиксу модели.

### Поддерживаемые провайдеры

| Провайдер | Префикс модели | Адаптер | Описание |
|---|---|---|---|
| **Microsoft AI Foundry** | `foundry:<model_id>` | `foundry_chat.py` | Локальный OpenAI-совместимый сервер (`Run-Foundry.ps1`) |
| **Microsoft ONNX (Olive)** | `onnx:<model_id>` | `onnx_chat.py` | Локальный инференс ONNX/Olive с аппаратным ускорением DirectML / CPU / CUDA |
| **Hugging Face** | `hf:<model_id>` | `hf_chat.py` | Локальный инференс моделей через Hugging Face Transformers |
| **OpenAI-совместимые API** | `openai:<model_id>`, `deepseek:<model_id>`, `lmstudio:<model_id>` | `openai_compat_chat.py` | Облачные и локальные сервисы (OpenAI, DeepSeek, Groq, LM Studio) |
| **Google Gemini SDK** | `gemini-*` (без префикса) | `core/ai/gemini/` | Прямой вызов Google GenAI SDK с пулом API-ключей |
| **Google Gemini CLI** | `gemini_cli:<model_id>` | `gemini_cli_chat.py` | Локальный агент через subprocess (`gemini -p ... -m ...`) |
| **Antigravity AGY** | `agy-<model_id>` | `agy_chat.py` | Antigravity SDK поверх Gemini-моделей |
| **Ollama** | `ollama:<model_id>` | `ollama_chat.py` | Локальный Ollama-сервер |

### Как работает маршрутизация

```
Запрос пользователя → UnifiedChatModel._get_active_model(model_name)
    ├── "foundry:qwen2.5-..."  → FoundryChatBase       → http://localhost:54837/v1
    ├── "onnx:qwen2.5-..."     → ONNXChatBase          → Microsoft ONNX Runtime / Olive (DirectML)
    ├── "hf:Qwen/..."          → HFChatBase            → Hugging Face Transformers
    ├── "openai:gpt-4o"        → OpenAICompatChat      → OpenAI / DeepSeek / LM Studio API
    ├── "gemini_cli:gemini-..."→ GeminiCliChatBase     → subprocess gemini CLI
    ├── "agy-gemini-..."       → AgyChatBase           → google.antigravity SDK
    ├── "ollama:llama3.1"      → OllamaChatBase        → http://localhost:11434
    └── "gemini-flash-..."     → GoogleGenerativeAI    → Google GenAI SDK
```

### Управление моделями

`model_manager.get_available_models(provider)` — получить список доступных моделей провайдера (с кэшированием).

`model_manager.actualize_all_models()` — параллельный прогрев кэша всех провайдеров при старте сервера.

`model_manager.add_unsupported_model(provider, model_name)` — автоматически исключить сломанную модель из ротации (сохраняется в `config.json`).

---

## 🚀 Возможности

- 🤖 **Оркестратор провайдеров:** Единый интерфейс для Foundry, Microsoft ONNX (Olive), Hugging Face, OpenAI/DeepSeek, Gemini CLI, AGY, Gemini SDK, Ollama с автоматическим управлением моделями
- 🧠 **Потоковый RAG-поиск:** Векторный поиск по `media.db` с трансляцией шагов через SSE
- 🧩 **Плагины:** Расширяемая система обработчиков и сканеров дисков

---

## 🏗️ Архитектура

```
┌────────────────────────────────────────────────────────────────────────┐
│                             Web Interface                              │
│                       ┌───────────────────────┐                        │
│                       │      Web UI (/)       │                        │
│                       └───────────┬───────────┘                        │
│                                   │                                    │
│                         ┌─────────▼──────────┐                         │
│                         │   FastAPI Server   │                         │
│                         └─────────┬──────────┘                         │
│    ┌──────────────────────────────┴──────────────────────────────┐     │
│    │                                                             │     │
│┌───▼────────────────────────┐                   ┌────────────────▼────┐│
││  AI Orchestrator           │                   │  RAG & Storage      ││
││ • model_manager.py         │                   │ • RAG Search        ││
││ • unified_chat.py          │                   │ • Vector Index      ││
││                            │                   │ • Knowledge Base    ││
││ Providers:                 │                   │ • media.db          ││
││  Foundry / ONNX / HF       │                   └─────────────────────┘│
││  OpenAI / Gemini / AGY     │                                          │
││  Gemini CLI / Ollama       │                                          │
│└────────────────────────────┘                                          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Быстрый старт

### Системные требования

- **ОС:** Windows 10/11, Linux или macOS
- **Python:** 3.10+ (рекомендуется 3.12 / 3.13)
- **API Ключи:** Google Gemini API Key (для Gemini SDK и AGY)
- **Опционально:** Microsoft AI Foundry, Gemini CLI (`npm install -g @google/gemini-cli`)

---

### 📦 Установка

#### Вариант 1. Быстрая установка в одну строку (PowerShell, Рекомендуется)

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

#### Вариант 2. Установка из репозитория через `install.cmd` (Windows)

```cmd
git clone https://github.com/hypo69/AI-Breadboard.git C:\aibreadboard
cd C:\aibreadboard
install.cmd
```

Установщик: интерактивно выбирает язык (RU/EN/ES/HE), предлагает стандартную директорию (`%USERPROFILE%\AppData\Local\AI Breadboard`) или пользовательский путь, регистрирует постоянную переменную `AIBREADBOARD_DIR`, снимает блокировку файлов Windows, создаёт `venv`, устанавливает зависимости, настраивает SSL и регистрирует глобальные команды `assist`.

#### Вариант 3. Ручная установка

```bash
# Windows
py -3.13 -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# Linux / macOS
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

---

### 📁 Структура зависимостей (`req/`)

- `req/requirements-core.txt` — FastAPI, Uvicorn, Pydantic, JWT, aiohttp, httpx
- `req/requirements-ai.txt` — LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, MCP
- `req/requirements-media.txt` — Edge-TTS, gTTS, PyDub
- `req/requirements-utils.txt` — Pandas, Pillow, BeautifulSoup4
- `req/requirements-test.txt` — pytest, pytest-asyncio, coverage
- `req/requirements-docs.txt` — MkDocs, Material theme

---

### ⚙️ Настройка конфигурации

**`config.json`** — несекретные параметры:
- `server` — хост, порт, SSL
- `ai` — модели, параметры Foundry, AGY, Gemini CLI, списки неподдерживаемых моделей
- `langchain`, `agents` — настройки ReAct-агентов и MCP-серверов

**`.env`** — секретные ключи:
```bash
cp .env.example .env
```
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

---

### ▶️ Запуск сервера

```powershell
# Windows (рекомендуется)
./run.ps1
```

`run.ps1` автоматически: освобождает порт, запускает Microsoft AI Foundry при необходимости, стартует FastAPI с SSL и auto-reload.

```bash
# Прямой запуск
.\venv\Scripts\python.exe main.py
```

---

## 🖥️ Веб-интерфейсы

| Интерфейс | URL | Описание |
|---|---|---|
| 🏠 **Главная** | `http://localhost:3000/` | Чат, модели, RAG, агенты, логи |
| 📄 **API Swagger** | `http://localhost:3000/docs` | OpenAPI документация |

---

## 🛠️ Технологический стек

- **Backend:** Python 3.10+, FastAPI, Uvicorn, AsyncIO, SSE
- **AI Orchestrator:** `model_manager.py` + `unified_chat.py` — маршрутизация между Foundry, Gemini CLI, AGY, Gemini SDK, Ollama
- **Поиск и RAG:** SQLite (`media.db`), FAISS, Sentence-Transformers
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Сеть и безопасность:** mkcert SSL

---

## 📄 Лицензия

MIT © 2026 hypo69
