<!-- Updated: 2026-10-01 20:58:00 -->
# AI-Breadboard

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**AI-Breadboard** — модульная платформа для исследования, прототипирования и сравнения языковых моделей искусственного интеллекта. Название отсылает к «макетной плате» (breadboard) в электронике: разные модели подключаются как сменные компоненты через единую шину, без переписывания кода.

> [!IMPORTANT]
> **Философия и главная идея платформы:**  
> *«Если рабочий процесс начинает состоять из слишком большого количества отдельных инструментов, это рано или поздно начинает бесить.»*

Сделана для разработчиков, которые хотят экспериментировать с современными AI-моделями, строить агентов, автоматизировать задачи и создавать собственные инструменты — без глубокого погружения во внутреннее устройство каждого провайдера и без переключения между десятками разрозненных утилит.

---

## Содержание

- [Назначение](#назначение)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Требования к системе](#требования-к-системе)
- [Установка](#установка)
- [Настройка](#настройка)
- [Запуск](#запуск)
- [Интерфейсы доступа](#интерфейсы-доступа)
- [Устранение неполадок](#устранение-неполадок)
- [Документация](#документация)
- [Лицензия](#лицензия)

---

## Назначение

Платформа решает несколько задач одновременно:

- **Исследование моделей** — сравнивайте ответы Gemini, GPT-4, Ollama, DeepSeek, ONNX и других в одном интерфейсе.
- **Прототипирование агентов** — создавайте ReAct-агентов с инструментами без написания инфраструктурного кода.
- **Автоматизация** — подключайте навыки (Skills) и плагины (Plugins) для автоматизации рутинных задач.
- **Личная база знаний** — индексируйте документы, почту, Telegram-каналы и ищите по ним через RAG.
- **Интеграция с внешними сервисами** — Google Workspace, Telegram, IFTTT, qBittorrent и другие.

---

## Возможности

### 🤖 AI-провайдеры

Все модели доступны через единый интерфейс `UnifiedChatModel` с маршрутизацией по префиксу:

| Провайдер | Префикс | Адаптер | Тип | Описание |
|---|---|---|---|---|
| Google Gemini SDK | `gemini:<model>` | `core/ai/gemini/` | ☁️ Облако | Direct Google GenAI SDK с пулингом ключей |
| Gemini CLI | `gemini_cli:<model>` | `gemini_cli_chat.py` | ☁️ Облако / CLI | Локальный CLI-агент для Google Gemini |
| Antigravity AGY | `agy:<model>` | `agy_chat.py` | ☁️ Облако | AGY SDK поверх моделей Gemini |
| OpenAI | `openai:<model>` | `openai_compat_chat.py` | ☁️ Облако | OpenAI Cloud API (gpt-4o, gpt-4-turbo и др.) |
| DeepSeek | `deepseek:<model>` | `openai_compat_chat.py` | ☁️ Облако | DeepSeek Cloud API (deepseek-chat, deepseek-reasoner) |
| Groq | `groq:<model>` | `openai_compat_chat.py` | ☁️ Облако | Высокоскоростной облачный инференс |
| Microsoft AI Foundry | `foundry:<model>` | `foundry_chat.py` | 🌐 Локальный сервер | OpenAI-совместимый сервер на порту 54837 |
| Ollama | `ollama:<model>` | `ollama_chat.py` | 🌐 Локальный сервер | Инференс-сервер на http://localhost:11434 |
| LM Studio | `lmstudio:<model>` | `openai_compat_chat.py` | 🌐 Локальный сервер | OpenAI-совместимый локальный сервер (http://localhost:1234) |
| Windows AI / ONNX | `onnx:<model>` | `onnx_chat.py` | 💾 Локальный инференс | Модели на диске, ускорение DirectML/CPU/CUDA |
| Hugging Face | `hf:<model>` | `hf_chat.py` | 💾 Локальный инференс | Модели на диске через HuggingFace Transformers |

### 🧩 Плагины (Plugins)

Фоновые сервисы и интеграции, управляемые через Admin UI:

| Плагин | Назначение |
|---|---|
| `telegram_bot` | Telegram-бот с голосовыми ответами (TTS), привязкой аккаунтов и Mini App |
| `telegram_channel_rag` | Индексация Telegram-каналов, семантический поиск с прямыми ссылками на сообщения |
| `google_workspace` | Пул OAuth2-аккаунтов Google, Gmail, Drive, Sheets, Docs |
| `gdrive_sync` | Автоматическая синхронизация файлов с Google Диском |
| `user_storage` | Изолированное хранилище документов для каждого пользователя с квотами |
| `rag_cleaner` | Очистка PDF, DOCX, HTML, ZIP, CSV, JSON перед векторной индексацией |
| `generate_rag_from_codebase` | AST-индексатор Python-кода: функции, классы, docstrings |
| `log_analyzer` | Кластеризация ошибок, метрики надёжности, AI-рекомендации |
| `invoice_processor` | Извлечение реквизитов из PDF-счетов и изображений |
| `news_feed` | RSS-агрегатор с семантической фильтрацией и LLM-дайджестами |
| `media_organizer` | Управление медиатекой, сверка с SQLite |
| `ifttt` | Управление умным домом через IFTTT Webhooks |
| `facebook` | Публикация контента и чтение ленты через Graph API |

### 🧠 Навыки (Skills)

27 инструментов для AI-агентов, регистрируемых в `SkillRegistry`:

- **Инфраструктура и разработка:** `project-installer`, `cert-installer`, `system-updater`, `file-saver`, `pdf-exporter`, `tdd-doc-gen`, `doc-generator`, `skill-factory`
- **Данные и хранилища:** `rag-search-manager`, `rag-cleaner`, `db-inspector`, `storage-controller`, `storage-tool`, `smart-deletion-duplicates`
- **Интеграции:** `google-workspace`, `gdrive-organizer`, `invoice-extractor`, `ifttt-controller`, `torrent-controller`
- **Медиа и контент:** `media-card-builder`, `media-data-collector`, `media-manager`
- **Бизнес и информация:** `employee-offboarding-monitor`, `news-reader`, `travel-agent`, `log-analyzer`, `web-chat-cli`

### 🔌 MCP Серверы

8 серверов для подключения Claude, Cursor, Antigravity CLI к возможностям платформы:

- `gemini_search_mcp_server` — RAG-поиск и Google Search Grounding
- `fastapi_mcp_server` — прямой доступ к REST API платформы
- `langchain_mcp_server` — LangChain цепочки и суммаризация документов
- `auto_commits` — генерация git-коммитов по диффу (Conventional Commits)
- `playwright` — headless-браузер для скрапинга и тестирования UI
- `unicorn_mcp_server` — управление жизненным циклом сервера
- `agy_search_mcp_server` — интеграция с Antigravity
- `gemini_cli_search_mcp_server` — компактный CLI-поиск по RAG

### 🖥️ Полноценные приложения и терминальные пространства (`/apps`)

В директории [`/apps`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps) размещены автономные доменные приложения, терминалы и мониторы, работающие на хосте и интегрированные с платформой:

| Приложение | Терминал / Путь | Описание |
|---|---|---|
| **AI Windows Diagnostic Center** | [`apps/windows`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows) | Центр диагностики и администрирования Windows (15 доменных коллекторов OS, железо, драйверы, SafeOps симуляция, WikiLLM база знаний) |
| **Trading Terminal** | [`apps/trading_terminal`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/trading_terminal) | Биржевой терминал (тикеры в реальном времени, стакан цен, позиция, PnL и технический анализ) |
| **Network Terminal** | [`apps/network_terminal`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/network_terminal) | Сетевой терминал (захват пакетов, протокольный анализ, сокеты и детекция аномалий трафика) |
| **Google Cloud Monitor** | [`apps/gcloud_monitor`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/gcloud_monitor) | Монитор наблюдаемости GCP (Cloud Logging, метрики, IAM аудит, AI-диагностика сбоев) |
| **Website Monitor** | [`apps/website_monitor`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/website_monitor) | Мониторинг веб-сайтов (GA4 Data API, Google Search Console, задержки и доступность) |
| **Cloudflare Monitor** | [`apps/cloudflared_monitor`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/cloudflared_monitor) | Мониторинг и диагностика состояния Cloudflare туннелей |
| **User Assistant** | [`apps/user_assistant`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/user_assistant) | Персональный ассистент (интеграция с Gmail, Google Календарем, файлами и агендой) |
| **IT Support & Helpdesk** | [`apps/helpdesk`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/helpdesk) | Система обработки тикетов и поддержке IT-инфраструктуры |
| **Wikipedia Research** | [`apps/wikipedia_research`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/wikipedia_research) | Исследовательский движок факт-чекинга по Wikipedia |
| **Research & Statistics** | [`apps/research_and_statistic`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/research_and_statistic) | Терминал статистических исследований и анализа данных |
| **AI Breadboard Admin** | [`apps/ai_breadboard_admin`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/ai_breadboard_admin) | Центральная панель администрирования платформы |

> [!NOTE]
> Внутри подсистемы [`apps/windows`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows) выстроена глубокая ИТ-архитектура: 15 коллекторов фактов (Clean, Performance, Drivers, Software, Integrity, Storage, Security, EventLog, Processes, Services, Tasks, Network, Update, Baseline, Postinstall), протокол безопасного исполнения SafeOps (Dry-run), подсистема самообучения WikiLLM и аппаратно-системный мониторинг. Подробнее см. в [apps/windows/README.md](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/README.md).

### 🎙️ Обработка звука

- Диаризация собеседников через Gemini multimodal (кто что сказал, временные метки)
- Транскрипция с executive summary, ключевыми темами и action items
- Форматы: mp3, wav, webm, ogg, m4a
- Сохранение результата в RAG-базу знаний
- TTS (синтез речи): Microsoft Edge TTS, Google TTS, Silero (офлайн)

### 📚 RAG и база знаний

- Семантический поиск по документам (PDF, DOCX, MD, TXT, JSON, CSV, код)
- Персональные RAG-коллекции для каждого пользователя
- Синхронизация с Google Docs
- Индексация Telegram-каналов
- Индексация кодовой базы (AST-парсер)
- RAG-First пайплайн: прямой ответ из базы без вызова LLM при высоком совпадении

---

## Архитектура

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              ИНТЕРФЕЙСЫ ДОСТУПА                                  │
├──────────────────────────────────────┬───────────────────────────────────────────┤
│        Веб-интерфейс                 │           CLI-интерфейс                   │
│   ┌─────────────────────────┐        │   ┌──────────────────────────────┐        │
│   │   Веб-UI (/)            │        │   │  assist model ask "msg"      │        │
│   │   • Чат                 │        │   │  • Запросы к моделям         │        │
│   │   • RAG Поиск           │        │   │  • Управление провайдерами   │        │
│   │   • Агенты              │        │   │  • Системные промпты         │        │
│   └────────────┬────────────┘        │   └──────────────┬───────────────┘        │
│                │                     │                  │                        │
│         ┌──────▼──────┐              │           ┌──────▼─────┐                  │
│         │ FastAPI     │              │           │  Python    │                  │
│         │ Server      │              │           │  Scripts   │                  │
│         └──────┬──────┘              │           │ (assist)   │                  │
│                │                     │           └─────┬──────┘                  │
└────────────────┼─────────────────────┴─────────────────┼─────────────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                        ┌────────────▼──────────────────┐
                        │   RAG И ХРАНИЛИЩЕ             │
                        │ • RAG Поиск                   │
                        │ • Векторный индекс            │
                        │ • База знаний (media.db)      │
                        └────────────┬──────────────────┘
                                     │  
                        ┌────────────▼──────────────────┐
                        │       AI ОРКЕСТРАТОР          │
                        │       unified_chat.py         │
                        │       model_manager.py        │
                        └────────────┬──────────────────┘
                                     │
             ┌───────────────────────┼──────────────────────────┐
             │                       │                          │
        ┌────▼──────────┐    ┌───────▼────────┐     ┌───────────▼──────┐
        │ 💾 ЛОКАЛЬНЫЕ  │    │ 🌐 ЛОКАЛЬНЫЕ   │     │ ☁️ ОБЛАЧНЫЕ      │
        │   МОДЕЛИ      │    │  СЕРВЕРЫ        │     │     API         │
        │ • ONNX        │    │ • Foundry       │     │ • Gemini SDK    │
        │ • HuggingFace │    │ • Ollama        │     │ • Gemini CLI    │
        │ • Transformers│    │ • LM Studio     │     │ • OpenAI        │
        │ На диске      │    │ Локально        │     │ • DeepSeek      │
        │ (RAM/VRAM)    │    │ запущенные      │     │ • Groq / AGY    │
        └───────────────┘    └────────────────┘     └──────────────────┘
```

### Конвейер маршрутизации запросов

```text
Запрос пользователя → UnifiedChatModel._get_active_model(model_name)
    ├── "foundry:qwen2.5-..."   → FoundryChatBase       → http://localhost:54837/v1
    ├── "onnx:qwen2.5-..."      → ONNXChatBase          → Microsoft ONNX Runtime / Olive (DirectML)
    ├── "hf:Qwen/..."           → HFChatBase            → Hugging Face Transformers
    ├── "openai:gpt-4o"         → OpenAICompatChat      → OpenAI / DeepSeek / LM Studio API
    ├── "gemini_cli:gemini-..." → GeminiCliChatBase     → подпроцесс gemini CLI
    ├── "agy:gemini-..."        → AgyChatBase           → google.antigravity SDK
    ├── "ollama:llama3.1"       → OllamaChatBase        → http://localhost:11434
    └── "gemini:gemini-..."     → GoogleGenerativeAI    → Google GenAI SDK
```

### Ключевые системные сервисы

1. **Оркестратор моделей (`ModelManager`)** — управляет жизненным циклом моделей: опрашивает провайдеры при запуске, кэширует их в памяти и автоматически исключает из ротации недоступные модели.
2. **WebSocket-хаб (`WSHub`)** — центральный диспетчер real-time соединений. Позволяет серверу мгновенно транслировать потоковые ответы и системные уведомления.
3. **Сборщик метрик (`MetricsCollector`)** — система мониторинга «здоровья» платформы. Предоставляет данные в формате Prometheus (`/health/metrics`).

---

## Технологический стек

- **Backend:** Python 3.10+, FastAPI, Uvicorn, AsyncIO, WebSockets, Server-Sent Events (SSE).
- **AI Оркестратор:** `model_manager.py` + `unified_chat.py` — единая маршрутизация провайдеров (Foundry, Gemini CLI, AGY, Gemini SDK, Ollama, ONNX, Hugging Face).
- **Поиск и RAG:** SQLite (`media.db`), FAISS, Sentence-Transformers, AST-индексатор.
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES Modules, i18next).
- **Безопасность и сеть:** JWT-аутентификация, SSL через mkcert.

---

## Требования к системе

### Минимальные (облачные провайдеры)

- **ОС:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **CPU:** Intel Core i5 10-го поколения или эквивалент
- **RAM:** 4 ГБ
- **Диск:** 2 ГБ свободного места
- **Python:** 3.10, 3.11, 3.12 или 3.13
- **Интернет:** требуется для облачных провайдеров
- **API-ключ:** [Google Gemini API Key](https://aistudio.google.com/api-keys) (доступен бесплатный лимит)

### Рекомендуемые (с локальными моделями)

- **RAM:** 16 ГБ+ (для Ollama и ONNX с большими моделями)
- **Диск:** 50+ ГБ (5–30 ГБ на каждую локальную модель)
- **GPU:** опционально (ускорение через DirectML/CUDA/NPU)

### Программные зависимости

| Компонент | Версия |
|---|---|
| Python | 3.10+ |
| PowerShell | 5.1+ (Windows) или 7+ (рекомендуется) |
| Git | Любая актуальная |
| mkcert | Для SSL-сертификатов (устанавливается автоматически) |

---

## Установка

### Windows — одна команда

Откройте PowerShell **от имени администратора** и выполните:

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

### Клонирование репозитория

```powershell
# Windows:
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
.\install.ps1

# Linux / macOS:
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
bash install.sh
```

### Модульная архитуктура установщика

Процесс установки управляется главным скриптом и узкоспециализированными модулями:

- `install.ps1` / `install.sh` / `install.py` — главные оркестраторы
- `install/Install-I18n.ps1` — мультиязычный интерфейс (RU, EN, ES, HE)
- `install/Install-Directory.ps1` — выбор директории установки (по умолчанию `%LOCALAPPDATA%\AI Breadboard`)
- `install/Install-Venv.ps1` — подготовка виртуальной среды Python
- `install/Install-Deps.ps1` — установка зависимостей
- `install/Install-Certs.ps1` — генерация локальных SSL-сертификатов
- `install/Install-Cli.ps1` — регистрация глобальной команды `assist` в `%USERPROFILE%\.local\bin\`
- `install/Install-Verify.ps1` — проверка целостности и импорта модулей
- `install/Install-Models.ps1` — выбор и загрузка локальных моделей (Ollama, Foundry, ONNX)

### Ручная установка

```bash
# 1. Клонировать
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard

# 2. Виртуальная среда
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# 3. Зависимости
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 4. SSL-сертификаты (Windows)
.\install\Install-SslCertificate.ps1

# 5. Конфигурация
cp .env.example .env
```

### Структура пакетов зависимостей

| Файл | Содержимое |
|---|---|
| `requirements-core.txt` | FastAPI, Uvicorn, Pydantic, JWT, aiohttp, httpx |
| `requirements-ai.txt` | LangChain, Google GenAI, FAISS, MCP |
| `requirements-media.txt` | Обработка изображений, видео, аудио |
| `requirements-utils.txt` | Pandas, Pillow, BeautifulSoup4 |
| `requirements-test.txt` | pytest, pytest-asyncio, coverage |
| `requirements-docs.txt` | MkDocs, Material theme |
| `requirements.txt` | Все объединённые зависимости |

---

## Настройка

### Секреты и API-ключи — файл `.env`

Скопируйте шаблон и заполните необходимые значения:

```bash
cp .env.example .env
```

Минимальная конфигурация для старта:

```ini
# Обязательно — для Gemini SDK и AGY
GEMINI_API_KEY=ваш_ключ_gemini

# Обязательно — для JWT-аутентификации
JWT_SECRET=сгенерируйте_случайную_строку

# Пароль панели администратора
ADMIN_PASSWORD=ваш_пароль
```

Пул ключей Gemini поддерживается из коробки для авто-ротации при превышении лимитов:

```ini
GEMINI_API_KEY_1=ключ_1
GEMINI_API_KEY_2=ключ_2
GEMINI_API_KEY_3=ключ_3
```

### Публичная конфигурация — файл `config.json`

Содержит несекретные системные параметры:

- `server` — хост, порт, настройки SSL
- `ai` — провайдеры по умолчанию, списки моделей, параметры Foundry/AGY/Gemini CLI
- `langchain`, `agents` — конфигурация ReAct-агентов и MCP-инструментов

---

## Запуск

### Основной сервер

```powershell
# Windows (рекомендуется)
.\run.ps1

# Прямой запуск Python
.\venv\Scripts\python.exe main.py
```

### CLI-команда `assist`

После установки команда `assist` доступна глобально:

```powershell
assist start          # запустить сервер
assist stop           # остановить сервер
assist restart        # перезапустить
assist status         # статус сервера и моделей
assist providers      # список провайдеров и их статус
assist models         # список моделей текущего провайдера
assist select provider gemini    # выбрать провайдера
assist select model gemini-2.0-flash  # выбрать модель
assist model ask "Привет, как дела?"  # отправить запрос
assist logs 50        # последние 50 строк логов
assist config show    # показать config.json
assist help           # полный справочник команд
```

### Запуск микро-приложений и бота

```powershell
.\launchers\Run-Apps.ps1              # Все микро-приложения
.\launchers\Run-TelegramBot.ps1 -Action start  # Telegram-бот
```

---

## Интерфейсы доступа

| Интерфейс | URL | Описание |
|---|---|---|
| Главная панель | `http://localhost:8000/` | Чат, RAG, агенты, логи |
| Admin UI | `http://localhost:8000/admin` | Управление плагинами, навыками, пользователями |
| Swagger API | `http://localhost:8000/docs` | Интерактивная документация REST API |
| Redoc | `http://localhost:8000/redoc` | Альтернативная документация API |
| AI Foundry | `http://localhost:54837/` | OpenAI-совместимый локальный API |
| Ollama | `http://localhost:11434/` | Локальный инференс-сервер |

---

## Устранение неполадок

### Ошибка политики выполнения PowerShell

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

### Порт 8000 занят

```powershell
assist stop
# Или вручную:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Python не найден

Установите Python 3.10+ с [python.org](https://www.python.org/downloads/), отметив **«Add python.exe to PATH»**.

### Предупреждение SSL в браузере

```powershell
certutil -addstore -f "Root" $env:USERPROFILE\.certs\localhost+2.pem
```

---

## Документация

Полная документация на русском языке доступна в директории `docs/ru/`:

- [Начало работы](docs/ru/manual/getting-started.md)
- [Установка](docs/ru/manual/installation.md)
- [Архитектура системы](docs/ru/architecture/overview.md)
- [Каталог навыков](docs/ru/skills/catalog.md)
- [Каталог плагинов](docs/ru/plugins/catalog.md)
- [Каталог MCP серверов](docs/ru/mcp/catalog.md)
- [Каталог приложений](docs/ru/apps/catalog.md)

 Онлайн-документация: [GitHub Pages](https://hypo69.github.io/aibreadboard/)

---

## Лицензия

MIT © 2026 hypo69
