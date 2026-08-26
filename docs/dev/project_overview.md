# Обзор проекта ai-assistant для разработчиков

## Архитектура системы

ai-assistant — это полноценная AI-платформа для управления медиатекой с расширяемой архитектурой плагинов, поддержкой FastAPI и множеством интерфейсов.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Web Interface Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  User Player │  │ Remote Control│ │  Telegram    │  │  Admin Panel │  │
│  │  (video +    │  │  (voice + TTS)│ │  Mini App    │  │  (tabs)      │  │
│  │   chat)      │  │               │  │               │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │                 │          │
│         └─────────────────┴─────────────────┴─────────────────┘          │
│                           │                                               │
│                  ┌────────▼────────┐                                      │
│                  │   FastAPI Server│                                      │
│                  │   (FastAPI +    │                                      │
│                  │    Websocket)   │                                      │
│                  └────────┬────────┘                                      │
│                           │                                               │
│    ┌──────────────────────┼──────────────────────┐                       │
│    │                      │                      │                       │
│┌───▼────┐           ┌────▼──────┐          ┌───▼────┐                  │
││  AI    │           │  Media    │          │ Torrent│                  │
││Gemini/ │           │ Organizer │          │QBittorrent│              │
││Foundry │           └───────────┘          └──────────┘                  │
│└────────┘                  │                      │                       │
│    │              ┌──────▼───────┐               │                       │
│    │              │  RAG Index   │               │                       │
│    │              │  (SQLite +   │               │                       │
│    │              │   Embeddings)│               │                       │
│    │              └──────────────┘               │                       │
│    │                      │                      │                       │
│    │              ┌──────▼───────┐               │                       │
│    │              │  Media DB    │               │                       │
│    │              │  (SQLite)    │               │                       │
│    │              └──────────────┘               │                       │
│    │                                             │                       │
│    └─────────────────────────────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────────┘
```

## Основные компоненты

### 1. FastAPI Backend (`core/fastapi/`)

| Модуль | Описание | Эндпоинты |
|--------|----------|-----------|
| `router_chat.py` | Основной чат AI | `/api/chat` (веб-сокет, SSE) |
| `router_qbittorrent.py` | Управление торрентами | `/api/torrents/`, `/api/torrents/search`, `/api/torrents/add` |
| `router_media.py` | Медиа-управление | `/api/media/`, `/api/media-admin/` (админ) |
| `router_auth.py` | Аутентификация | `/auth/google`, `/auth/logout`, `/auth/me` |
| `router_control.py` | Веб-сокет управление | WebSocket `/ws/control` |
| `router_tts.py` | Текст в речь | `/api/tts/synthesize`, `/api/tts/voices` |
| `router_logs.py` | Логирование | `/api/logs/`, `/api/logs/analyze` |
| `router_keys.py` | Управление ключами | `/api/keys/`, `/api/keys/status` |
| `router_admin.py` | Админ-панель | `/admin`, `/api/admin/` |

### 2. AI Модель (`core/ai/`)

Двойная архитектура: Google Gemini + Microsoft AI Foundry

| Модуль | Описание | Особенности |
|--------|----------|-------------|
| `unified_chat.py` | `UnifiedChatModel` — единый интерфейс | Авто-переключение между Gemini и Foundry |
| `foundry_chat.py` | Клиент Foundry | Локальный qwen3-0.6b-generic-cpu |
| `gemini/generative_ai.py` | GoogleGenerativeAI | Поддержка новых моделей Gemini 2.0 |
| `gemini/rag.py` | GeminiRAG | Векторный поиск через embeddings |

### 3. Плагины (`plugins/`)

**10 полных плагинов:**

| Плагин | Триггеры | Назначение | Особенности |
|--------|----------|-----------|-------------|
| `media_organizer` | — (Function Calling) | Управление медиатекой, RAG | Предоставляет Function Calling API |
| `rag` | "фильм", "сериал", "кино", "посоветуй" | Семантический поиск медиа | Интеграция с RAG, случайная "карусель" |
| `media_layer` | "фильм", "сериал" | Простой медиа-слой | Чтение из БД без сканирования |
| `web_search` | "поищи в интернете", "погугли" | Веб-поиск через Playwright | Асинхронный поиск с AI-анализом |
| `torrent_playwright` | "торрент", "скачать" | Поиск торрентов | Rutracker + NNMClub, AI фильтрация |
| `movie_search_sources` | "где посмотреть", "плеер" | Поиск источников для просмотра | Каталог streaming-сервисов |
| `qbittorrent` | "добавь торрент", "категории" | Управление qBittorrent | Категории, теги, поиск |
| `telegram_bot` | — (отдельный процесс) | Telegram Mini App | Удалённое управление |
| `user_manager_tool` | `!list_users`, `!user_activity` | Управление пользователями | SQLite users.db |
| `yt_dlp` | "скачай", "youtube", "mp3" | Скачивание видео/аудио | Поддержка yt-dlp |

**Загрузка плагинов:**
```python
# plugins/__init__.py — динамическая загрузка всех плагинов
# Отключаемые через DISABLED_PLUGINS в .env
def load_plugins(ai_model) -> dict[str, BasePlugin]
```

## База данных медиатеки

### Таблицы `media.db`:

1. **Основная таблица `media`:**
```sql
id, disk_name, path, title, title_ru, title_orig, year, 
main_category, country, genres, directors, cast, 
num_of_seasons, num_episodes_per_season, status, rating, 
awards, plot, atmosphere, why_watch, mood, final_verdict, 
can_stop_at, quote, facts, similar, parent_id, 
episode_scan_skipped, media_type, number
```

2. **Таблица `media_vector`:**
```sql
id, media_id, embedding
```

3. **Таблица `search_history`:**
```sql
id, query, timestamp, results_count
```

**10 Категорий по умолчанию:**
1. 🎬 Боевики
2. 😱 Триллеры  
3. 🚀 Приключения
4. 😢 Драмы
5. 👪 Семейные
6. 🏰 Исторические/Костюмированные
7. 🔍 Расследования
8. 🕵️ Шпионы
9. 🎭 Мюзиклы
10. 📹 Документальные

## Технологический стек

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Backend | Python 3.10+, FastAPI, Uvicorn | Python 3.10+ |
| AI | Google Gemini 2.0, Microsoft AI Foundry | Gemini 2.0-flash |
| Database | SQLite, FAISS | SQLite 3.45+ |
| Frontend | HTML5, CSS3, Vanilla JS | Modern Web APIs |
| Медиа | qBittorrent API, yt-dlp, TMDB API | QBittorrent 4.6+ |
| Поиск | Playwright, DuckDuckGo, Rutracker | Playwright 1.45+ |
| Голос | Silero TTS, Web Speech API | Silero v4 |
| Деплой | PowerShell scripts, SSL/TLS | Windows |

## Быстрый старт для разработки

```bash
# Установка зависимостей (теперь с yt-dlp)
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env:
# - GEMINI_API_KEY_NAMES (имена ключей из gemini_keys.json)
# - TELEGRAM_BOT_TOKEN (если нужен Telegram)
# - USE_FOUNDRY (true/false)

# Запуск сервера для разработки
python main.py

# Тестирование
pytest  # все тесты
pytest tests/test_ai.py  # тесты AI
pytest --cov=src --cov-report=html  # покрытие кода

# Документация
mkdocs serve  # локальная документация
```

## Структура проекта

```
ai-assistant/
├── .ai_instructions/           # AI-инструкции
├── plugins/                    # 10 ПЛАГИНОВ
├── core/                        # Исходный код
├── webinterface/               # 6 веб-интерфейсов
├── main.py                     # Точка входа (FastAPI)
├── requirements.txt            # Зависимости (с yt-dlp)
├── .env                        # Переменные окружения
├── pytest.ini                  # Конфигурация тестов
├── conftest.py                 # Фикстуры pytest
└── mkdocs.yml                  # Документация MkDocs
```

## Конфигурация

### `.env` (основные переменные):
```
# AI
GEMINI_API_KEY_NAMES=имя1,имя2,...
USE_FOUNDRY=false
FOUNDRY_MODEL_ID=qwen3-0.6b-generic-cpu:4

# Аутентификация
TELEGRAM_BOT_TOKEN=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET=...

# Медиа
TMDB_API_KEY=...
TTS_VOICE=ru-RU-DmitryNeural

# Инфраструктура
USE_SSL=true
DISABLED_PLUGINS=plugin1,plugin2
```

## Дополнительные ресурсы

- **Полная документация**: https://hypo69.github.io/ai-assistant/
- **AI инструкции**: `.ai_instructions/knowledge/`
- **Тесты**: `tests/` с фикстурами в `conftest.py`
- **Скрипты управления**: `manage_tools.py`

---
**Последнее обновление: август 2026**  
*Актуализировано после расширения проекта до 10 плагинов и добавления yt_dlp, web_search и других новых компонентов.*
