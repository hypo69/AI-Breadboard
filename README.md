# AI-Breadboard

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/aibreadboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**AI-Breadboard** — модульная платформа для исследования, прототипирования и сравнения языковых моделей искусственного интеллекта. Название отсылает к «макетной плате» (breadboard) в электронике: разные модели подключаются как сменные компоненты через единую шину, без переписывания кода.

Сделана для разработчиков, которые хотят экспериментировать с современными AI-моделями, строить агентов, автоматизировать задачи и создавать собственные инструменты — без глубокого погружения во внутреннее устройство каждого провайдера.

---

## Содержание

- [Назначение](#назначение)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
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

- **Исследование моделей** — сравнивайте ответы Gemini, GPT-4, Ollama, DeepSeek и других в одном интерфейсе
- **Прототипирование агентов** — создавайте ReAct-агентов с инструментами без написания инфраструктурного кода
- **Автоматизация** — подключайте навыки (Skills) и плагины (Plugins) для автоматизации рутинных задач
- **Личная база знаний** — индексируйте документы, почту, Telegram-каналы и ищите по ним через RAG
- **Интеграция с внешними сервисами** — Google Workspace, Telegram, IFTTT, qBittorrent и другие

---

## Возможности

### 🤖 AI-провайдеры

Все модели доступны через единый интерфейс `UnifiedChatModel` с маршрутизацией по префиксу:

| Провайдер | Префикс | Тип |
|---|---|---|
| Google Gemini SDK | `gemini-*` | ☁️ Облако |
| Gemini CLI | `gemini_cli:<model>` | ☁️ Облако / CLI |
| Antigravity AGY | `agy-<model>` | ☁️ Облако |
| OpenAI / GPT-4 | `openai:<model>` | ☁️ Облако |
| DeepSeek | `deepseek:<model>` | ☁️ Облако |
| Groq | `groq:<model>` | ☁️ Облако |
| Microsoft AI Foundry | `foundry:<model>` | 🌐 Локальный сервер |
| Ollama | `ollama:<model>` | 🌐 Локальный сервер |
| LM Studio | `lmstudio:<model>` | 🌐 Локальный сервер |
| Windows AI (NPU/DirectML) | `windows_ai:<model>` | 💾 Локальный инференс |
| ONNX / Olive | `onnx:<model>` | 💾 Локальный инференс |
| Hugging Face Transformers | `hf:<model>` | 💾 Локальный инференс |

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

**Инфраструктура и разработка:** `project-installer`, `cert-installer`, `system-updater`, `file-saver`, `pdf-exporter`, `tdd-doc-gen`, `doc-generator`, `skill-factory`

**Данные и хранилища:** `rag-search-manager`, `rag-cleaner`, `db-inspector`, `storage-controller`, `storage-tool`, `smart-deletion-duplicates`

**Интеграции:** `google-workspace`, `gdrive-organizer`, `invoice-extractor`, `ifttt-controller`, `torrent-controller`

**Медиа и контент:** `media-card-builder`, `media-data-collector`, `media-manager`

**Бизнес и информация:** `employee-offboarding-monitor`, `news-reader`, `travel-agent`, `log-analyzer`, `web-chat-cli`

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

### 📱 Микро-приложения (Apps)

Автономные веб-сервисы на отдельных портах:

| Приложение | Порт | Назначение |
|---|---|---|
| `windows_sysadmin` | 8100 | Управление службами Windows, Event Log, PowerShell |
| `network_terminal` | 8101 | Диагностика сети, порты, SSL, трафик |
| `system_inspector` | 8102 | GPU/NPU/CPU телеметрия, AI-ускорители |
| `trading_terminal` | 8103 | Финансовые данные, графики, технический анализ |
| `cloudflared_monitor` | 8104 | Мониторинг Cloudflare туннелей |
| `user_assistant` | 8105 | Персональный ассистент, доступ к навыкам и плагинам |
| `gcloud_monitor` | 8106 | GCP логи, метрики, AI-диагностика первопричин сбоев |

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

```
┌─────────────────────────────────────────────────────┐
│              ИНТЕРФЕЙСЫ ДОСТУПА                     │
│  Веб-UI  │  CLI (assist)  │  REST API  │  WebSocket │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           УРОВЕНЬ ПРИЛОЖЕНИЯ                        │
│  UnifiedChatModel  │  ModelManager  │  Маршрутизация│
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           УРОВЕНЬ СЕРВИСОВ                          │
│  RAG  │  Skills  │  Plugins  │  TTS  │  UserManager │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           ПРОВАЙДЕРЫ                                │
│  Gemini  │  OpenAI  │  Ollama  │  Foundry  │  ONNX  │
└─────────────────────────────────────────────────────┘
```

---

## Требования к системе

### Минимальные (облачные провайдеры)

- **ОС:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **CPU:** Intel Core i5 10-го поколения или эквивалент
- **RAM:** 4 ГБ
- **Диск:** 2 ГБ свободного места
- **Python:** 3.10, 3.11, 3.12 или 3.13
- **Интернет:** требуется для облачных провайдеров
- **API-ключ:** [Google Gemini API Key](https://aistudio.google.com/api-keys) (бесплатный лимит доступен)

### Рекомендуемые (с локальными моделями)

- **RAM:** 16 ГБ+ (для Ollama с большими моделями)
- **Диск:** 50+ ГБ (5–30 ГБ на каждую локальную модель)
- **GPU:** опционально (ускорение через DirectML/CUDA/NPU)

### Программные зависимости

| Компонент | Версия |
|---|---|
| Python | 3.10+ |
| PowerShell | 5.1+ (Windows) или 7+ (рекомендуется) |
| Git | любая актуальная |
| mkcert | для SSL-сертификатов (устанавливается автоматически) |

---

## Установка

### Windows — одна команда

Откройте PowerShell **от имени администратора** и выполните:

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

Скрипт автоматически выполнит все шаги установки.

### Windows — клонирование репозитория

```powershell
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
.\install.ps1
```

### Linux / macOS

```bash
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
bash install.sh
```

### Что делает установщик

Установка состоит из 8 шагов:

1. **Разблокировка файлов** — снятие метки веба (MOTW) с файлов Windows
2. **Виртуальная среда** — создание `venv` с Python 3.10+
3. **Обновление pip** — `pip`, `setuptools`, `wheel` до актуальных версий
4. **Зависимости** — интерактивный выбор набора пакетов:
   ```
   [1] Полная установка (Core + AI + Utils) — РЕКОМЕНДУЕТСЯ
   [2] Только основной сервер
   [3] Core + AI модули
   [4] Полная установка + Тесты и Документация (Dev)
   [5] Пропустить
   ```
5. **SSL-сертификаты** — генерация локальных HTTPS-сертификатов через mkcert
6. **Команда `assist`** — регистрация глобальной CLI-команды в PATH и профиле PowerShell
7. **Проверка** — тест импортов ключевых модулей
8. **Модели** — интерактивный выбор и загрузка локальных моделей (Ollama, Foundry, ONNX)

По умолчанию платформа устанавливается в:
```
%LOCALAPPDATA%\AI Breadboard
```

При запуске установщика можно выбрать другой путь. Выбор сохраняется в переменную окружения `AIBREADBOARD_DIR`.

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
.\install_ssl_cert.ps1

# 5. Конфигурация
cp .env.example .env
# Отредактируйте .env — добавьте API-ключи
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
| `requirements.txt` | Все объединённые |

---

## Настройка

### Секреты и API-ключи — файл `.env`

Скопируйте шаблон и заполните нужные значения:

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

Полный список переменных:

```ini
# --- Google ---
GEMINI_API_KEY=
GEMINI_API_KEY_1=          # дополнительные ключи для пула ротации
GEMINI_API_KEY_2=
AGY_API_KEY=               # Antigravity (опционально)

# --- Облачные провайдеры ---
OPENAI_API_KEY=
HF_TOKEN=                  # Hugging Face (для закрытых моделей)

# --- Локальные провайдеры ---
FOUNDRY_API_KEY=           # только если Foundry требует авторизацию

# --- Безопасность ---
JWT_SECRET=
ADMIN_PASSWORD=

# --- Google OAuth (опционально) ---
ENABLE_OAUTH=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# --- Telegram (опционально) ---
TELEGRAM_BOT_TOKEN=

# --- SMTP (опционально) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# --- Умный дом (опционально) ---
IFTTT_WEBHOOK_KEY=

# --- TTS голос по умолчанию ---
TTS_VOICE=ru-RU-DmitryNeural

# --- Туннели (опционально) ---
CLOUDFLARE_TUNNEL_TOKEN=
NGROCK_AUTOTOKEN=

# --- SSL (опционально, переопределяет config.json) ---
SSL_CERT_FILE=
SSL_KEY_FILE=
```

> Файл `.env` никогда не коммитится в Git. Все публичные настройки (порты, модели, URL) хранятся в `config.json`.

### Публичная конфигурация — файл `config.json`

Содержит несекретные параметры:

- `server` — хост, порт, настройки SSL
- `ai` — провайдеры по умолчанию, списки моделей, параметры Foundry/AGY/Gemini CLI
- `langchain`, `agents` — конфигурация ReAct-агентов и MCP-инструментов

### Пул ключей Gemini

Для обхода лимитов API поддерживается автоматическая ротация ключей. Добавьте несколько ключей в `.env`:

```ini
GEMINI_API_KEY_1=ключ_1
GEMINI_API_KEY_2=ключ_2
GEMINI_API_KEY_3=ключ_3
```

При достижении лимита одного ключа система автоматически переключается на следующий.

### Настройка плагинов

Каждый плагин имеет собственный `config.json` в своей директории и настраивается через Admin UI (`/admin` → вкладка Plugins) без перезапуска сервера.

Пример настройки Telegram-бота:

```json
{
  "token": "ваш_токен_от_BotFather",
  "admin_ids": ["ваш_telegram_id"],
  "notifications_enabled": true,
  "api_base_url": "http://127.0.0.1:8000"
}
```

---

## Запуск

### Основной сервер

```powershell
# Windows (рекомендуется)
.\run.ps1

# Прямой запуск Python
.\venv\Scripts\python.exe main.py
```

`run.ps1` автоматически проверяет доступность порта, запускает Foundry при необходимости и стартует FastAPI с SSL и авто-перезагрузкой.

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

### Запуск микро-приложений

```powershell
.\launchers\Run-Apps.ps1              # все приложения
.\launchers\Run-WindowsAdmin.ps1      # windows_sysadmin (8100)
.\launchers\Run-NetworkTerminal.ps1   # network_terminal (8101)
.\launchers\Run-SystemInspector.ps1   # system_inspector (8102)
.\launchers\Run-TradingTerminal.ps1   # trading_terminal (8103)
.\launchers\Run-CloudflaredMonitor.ps1 # cloudflared_monitor (8104)
```

### Запуск Telegram-бота

```powershell
.\launchers\Run-TelegramBot.ps1 -Action start
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

### PowerShell: «выполнение скриптов отключено»

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

### Порт 8000 занят

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
# или
assist stop
```

### Python не найден

Установите Python 3.10+ с [python.org](https://www.python.org/downloads/), отметив **«Add python.exe to PATH»** при установке.

### Предупреждение SSL в браузере

```powershell
# Добавить сертификат в доверенные корневые центры Windows
certutil -addstore -f "Root" $env:USERPROFILE\.certs\localhost+2.pem
```

Или нажмите «Дополнительно» → «Перейти на localhost (небезопасно)».

### Файлы логов

| Файл | Содержимое |
|---|---|
| `logs/uvicorn_*.log` | Консольный вывод сервера |
| `ai-breadboard/logs/fastapi.log` | Маршрутизация запросов FastAPI |
| `ai-breadboard/logs/info.log` | Системные события |
| `ai-breadboard/logs/errors.log` | Ошибки |
| `ai-breadboard/logs/gemini.log` | Запросы к Gemini API |

```powershell
assist logs 100   # последние 100 строк через CLI
```

---

## Документация

Полная документация на русском языке доступна в `docs/ru/`:

- [Начало работы](docs/ru/manual/getting-started.md)
- [Установка](docs/ru/manual/installation.md)
- [Архитектура системы](docs/ru/architecture/overview.md)
- [Каталог навыков](docs/ru/skills/catalog.md)
- [Каталог плагинов](docs/ru/plugins/catalog.md)
- [Каталог MCP серверов](docs/ru/mcp/catalog.md)
- [Каталог приложений](docs/ru/apps/catalog.md)
- [Создание агентов](docs/ru/guides/creating-agents.md)
- [Разработка плагинов](docs/ru/plugins/development.md)
- [Разработка навыков](docs/ru/skills/development.md)

Онлайн-документация: [Read the Docs](https://readthedocs.org/) (после публикации)

---

## Лицензия

MIT © 2026 hypo69
