# Обновленное описание проекта ai-assistant для AI-модели (август 2026)

## Общее назначение

**ai-assistant** — полноценная AI-платформа для управления медиатекой с расширяемой архитектурой плагинов, поддержкой FastAPI и множеством интерфейсов.

**Основные функции:**
1. 🤖 **AI-ассистент** — интегрированные Google Gemini, Microsoft AI Foundry, AGY SDK и Ollama
2. 🎬 **Умный медиаплеер** — синхронизированный плеер с WebSocket управлением
3. 📡 **Дистанционное управление** — голосовой пульт ДУ с TTS/STT
4. 📱 **Telegram Mini App** — удалённый доступ из Telegram
5. 🧠 **RAG-поиск** — семантический поиск по медиатеке с функцией Function Calling
6. 🧩 **Плагинная архитектура** — 11 Moduleных плагинов для разных задач
7. 📁 **Полный цикл медиа** — от поиска торрентов до автоматической организации
8. 🤖 **Управление агентами** — система настройки и тестирования AI агентов

---

## Обновленная архитектура системы

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
││Unified │           │ Organizer │          │QBittorrent│              │
││Chat    │           └───────────┘          └──────────┘                  │
││Model   │                  │                      │                       │
│└────────┘          ┌──────▼───────┐               │                       │
│    │               │  RAG Index   │               │                       │
│    │               │  (SQLite +   │               │                       │
│    │               │   Embeddings)│               │                       │
│    │               └──────────────┘               │                       │
│    │                      │                      │                       │
│    │              ┌──────▼───────┐               │                       │
│    │              │  Media DB    │               │                       │
│    │              │  (SQLite)    │               │                       │
│    │              └──────────────┘               │                       │
│    │                                             │                       │
│    └─────────────────────────────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Ключевые компоненты 2026

### 1. FastAPI Backend (`core/fastapi/`)
Обновленная маршрутизация с 10 роутерами:

| Module | Описание | Эндпоинты |
|--------|----------|-----------|
| `router_chat.py` | Основной чат AI | `/api/chat` (веб-сокет, SSE) |
| `router_qbittorrent.py` | Управление торрентами | `/api/torrents/`, `/api/torrents/search`, `/api/torrents/add` |
| `router_media.py` | Медиа-управление | `/api/media/`, `/api/media-admin/` (админ) |
| `router_auth.py` | Authentication | `/auth/google`, `/auth/logout`, `/auth/me` |
| `router_control.py` | Веб-сокет управление | WebSocket `/ws/control` |
| `router_tts.py` | Текст в речь | `/api/tts/synthesize`, `/api/tts/voices` |
| `router_logs.py` | Логирование | `/api/logs/`, `/api/logs/analyze` |
| `router_keys.py` | Управление ключами | `/api/keys/`, `/api/keys/status` |
| `router_admin.py` | Админ-панель | `/admin`, `/api/admin/` |
| `router_agents.py` | Управление агентами | `/api/agents/` (новый) |

### 2. AI Модель (`core/ai/`)
Архитектура: UnifiedChatModel с поддержкой 4 провайдеров

| Module | Описание | Префикс |
|--------|----------|---------|
| `unified_chat.py` | `UnifiedChatModel` — единый интерфейс | Роутинг по префиксу |
| `foundry_chat.py` | Клиент Microsoft AI Foundry | `foundry:` |
| `gemini/generative_ai.py` | GoogleGenerativeAI | `gemini-*` (по умолчанию) |
| `agy_chat.py` | AGY SDK (Gemini через прокси) | `agy-*` |
| `ollama_chat.py` | Ollama локальные модели | `ollama:` |
| `model_manager.py` | Менеджер моделей и конфигураций | - |
| `langchain_agent.py` | LangChain Integration | - |

**Правила выбора модели:**
- `foundry:qwen3-one` → Microsoft AI Foundry
- `gemini-2.0-flash` → Google Gemini (по умолчанию)
- `agy-flash` → AGY SDK
- `ollama:llama3.1` → Ollama локально

### 3. Плагины 2026 (`plugins/`)
**11 полных плагинов**:

| Плагин | Триггеры | Назначение | Особенности |
|--------|----------|-----------|-------------|
| `media_organizer` | — (Function Calling) | Управление медиатекой, RAG | Предоставляет Function Calling API |
| `rag` | "фильм", "сериал", "кино", "посоветуй" | Семантический поиск медиа | Integration с RAG, случайная "карусель" |
| `media_layer` | "фильм", "сериал" | Простой медиа-слой | Чтение из БД без сканирования |
| `web_search` | "поищи в интернете", "погугли" | Веб-поиск через Playwright | Асинхронный поиск с AI-анализом |
| `torrent_playwright` | "торрент", "скачать" | Поиск торрентов | Rutracker + NNMClub, AI filtering |
| `movie_search_sources` | "где посмотреть", "плеер" | Поиск источников для просмотра | Каталог streaming-сервисов |
| `qbittorrent` | "добавь торрент", "категории" | Управление qBittorrent | Категории, теги, поиск |
| `telegram_bot` | — (отдельный процесс) | Telegram Mini App | Удалённое управление |
| `user_manager_tool` | `!list_users`, `!user_activity` | Управление пользователями | SQLite users.db |
| `yt_dlp` | "скачай", "youtube", "mp3" | Скачивание видео/аудио | Поддержка yt-dlp |
| `langchain_media` | "лангчейн", "агент" | LangChain медиа-инструменты | Integration с LangChain |


**Loading плагинов:**
```python
# plugins/__init__.py — динамическая Loading всех плагинов
# Отключаемые через DISABLED_PLUGINS в .env
def load_plugins(ai_model) -> dict[str, BasePlugin]
```

**Архитектура плагина:**
```python
class BasePlugin(ABC):
    name: str = 'base'
    enabled: bool = True
    
    async def handle(self, message: str, **kwargs) -> str:
        # Потоковый вывод через yield {"status": "...", "text": "..."}
```

---

## База данных медиатеки 2026

### Таблицы `media.db`:

1. **Основная таблица `media`:** (актуальная структура)
```sql
id, disk_name, path, title, title_ru, title_orig, year, 
main_category, country, genres, directors, cast, 
num_of_seasons, num_episodes_per_season, status, rating, 
awards, plot, atmosphere, why_watch, mood, final_verdict, 
can_stop_at, quote, facts, similar, parent_id, 
episode_scan_skipped, media_type, number, torrent_id, media_size
```

2. **Таблица `media_vector`:** (RAG-поиск)
```sql
id, media_id, embedding
```

3. **Таблица `search_history`:** (история поиска)
```sql
id, query, timestamp, results_count
```

4. **Таблица `users`:** (управление пользователями)
```sql
id, username, email, created_at, last_login, preferences
```

**11 Категорий по умолчанию:**
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
11. 💰 Деньги / Корпорации / Deep State

---

## Новый RAG-поиск (Retrieval-Augmented Generation)

**Обновлённый стек:**
1. **Gemini Embeddings API** — векторное представление
2. **SQLite + FAISS** — хранение и поиск векторов
3. **Function Calling** — Integration с AI-моделями
4. **Streaming статусы** — отображение прогресса в UI

**Процесс RAG-поиска:**
```python
# 1. Векторизация запроса
embedding = await ai_model.embed(query)

# 2. Поиск в FAISS индексе  
results = search_faiss_index(embedding)

# 3. Function Calling в UnifiedChatModel
tools = get_media_tools()  # search_media, get_media_card, get_random_media
response = await ai_model.chat(query, tools=tools)

# 4. Потоковый вывод
yield {"status": "🔍 Поиск в RAG-индексе..."}
yield {"text": "Найдены результаты..."}
```

---

## Технологический стек 2026

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Backend | Python 3.10+, FastAPI, Uvicorn | Python 3.10+ |
| AI | UnifiedChatModel (Gemini + Foundry + AGY + Ollama) | Мультипровайдер |
| Database | SQLite, FAISS | SQLite 3.45+ |
| Frontend | HTML5, CSS3, Vanilla JS | Modern Web APIs |
| Медиа | qBittorrent API, yt-dlp, TMDB API | QBittorrent 4.6+ |
| Поиск | Playwright, DuckDuckGo, Rutracker | Playwright 1.45+ |
| Голос | Silero TTS, Web Speech API | Silero v4 |
| LangChain | LangChain Integration | LangChain 0.1+ |
| Деплой | PowerShell scripts, SSL/TLS | Windows |

---

## Структура проекта (обновленная)

```
ai-assistant/
├── .ai_instructions/           # AI-инструкции (обновлены)
│   ├── knowledge/              # Знания о проекте
│   │   ├── project_overview.md # ← этот файл
│   │   ├── legacy_project_knowledge.md # ← старый обзор
│   │   └── codex/              # Инженерные правила
│   ├── prompts/                # Промпты для моделей
│   │   ├── chat/               # Инструкция чата
│   │   └── media_organizer/    # Инструкция медиатеки
│   └── plans/                  # Дорожная карта
├── plugins/                    # 11 плагинов
│   ├── media_organizer/       # Управление медиатекой (+RAG)
│   ├── rag/                   # RAG-поиск (Function Calling)
│   ├── media_layer/           # Простой медиа-слой
│   ├── web_search/            # Веб-поиск через Playwright
│   ├── torrent_playwright/    # Поиск торрентов
│   ├── movie_search_sources/  # Источники для просмотра
│   ├── qbittorrent/           # Управление qBittorrent
│   ├── telegram_bot/          # Telegram Mini App
│   ├── user_manager_tool/     # Управление пользователями
│   ├── yt_dlp/                # Скачивание видео/аудио
│   ├── langchain_media/       # LangChain медиа-инструменты

├── core/
│   ├── ai/                    # AI модели (UnifiedChatModel)
│   │   ├── unified_chat.py    # UnifiedChatModel
│   │   ├── foundry_chat.py    # Microsoft AI Foundry
│   │   ├── gemini/            # Google Gemini
│   │   ├── agy_chat.py        # AGY SDK
│   │   ├── ollama_chat.py     # Ollama
│   │   ├── model_manager.py   # Менеджер моделей
│   │   └── dev_rag.py         # RAG для разработки
│   ├── fastapi/               # 10 роутеров FastAPI
│   ├── logger/                # Система логирования
│   ├── user_manager/          # Управление пользователями
│   ├── tts/                   # Text-to-Speech (Silero)
│   └── utils/                 # Утилиты (jjson, file)
├── webinterface/              # 6 веб-интерфейсов
│   ├── user/                  # Пользователь (плеер+чат)
│   ├── admin/                 # Админ-панель (пароль: onela)
│   ├── rc/                    # Пульт ДУ (голос+TTS)
│   ├── tgmini/                # Telegram Mini App
│   ├── tv/                    # Телевизионный интерфейс
│   └── user_tts/              # Тестирование TTS
├── main.py                    # Точка входа (FastAPI)
├── requirements.txt           # Зависимости
├── .env                       # Переменные окружения
├── pytest.ini                 # Configuration тестов
├── conftest.py                # Фикстуры pytest
└── mkdocs.yml                 # Документация MkDocs
```

---

## Ключевые файлы конфигурации

| Файл | Описание | Критичность |
|------|----------|-------------|
| `.env` | Переменные окружения (API ключи) | Критично |
| `config.json` | Настройки сервера и плагинов | Критично |
| `core/fastapi/config.json` | Настройки FastAPI | Важно |
| `plugins/media_organizer/config.json` | Настройки медиатеки | Важно |
| `plugins/qbittorrent/config.json` | Настройки qBittorrent | Важно |
| `core/ai/model_manager.py` | Configuration AI моделей | Критично |

**Новые переменные окружения (.env):**
```env
# AI Модели
GEMINI_API_KEY_NAMES=your_api_keys
FOUNDRY_API_KEY=your_foundry_key
FOUNDRY_BASE_URL=http://localhost:8000
AGY_API_KEY=your_agy_key
OLLAMA_BASE_URL=http://localhost:11434

# Плагины
DISABLED_PLUGINS=plugin1,plugin2
```

---

## Examples использования плагинов 2026

1. **RAG-поиск фильма:**
   ```
   "посоветуй фильм про космос"
   → Плагин: rag
   → Процесс: RAG-поиск → Function Calling → AI-рекомендация
   ```

2. **Скачивание видео через yt-dlp:**
   ```
   "скачай https://youtube.com/watch?v=..."
   → Плагин: yt_dlp
   → Процесс: YtDlpClient → прогресс-бар → HTML-карточка результата
   ```

3. **Поиск торрента через Playwright:**
   ```
   "найди торрент фильма Начало"
   → Плагин: torrent_playwright
   → Процесс: Playwright поиск → AI-filtering → HTML-list
   ```

4. **LangChain медиа-анализ:**
   ```
   "анализируй медиатеку с помощью LangChain"
   → Плагин: langchain_media
   → Процесс: LangChain агенты → анализ структуры → рекомендации
   ```

5. **Управление агентами:**
   ```
   "настрой агента для обработки медиа"
   → API: /api/agents/
   → Процесс: создание конфигурации → тестирование → развертывание
   ```

---

## Новые возможности 2026

### 1. **UnifiedChatModel архитектура**
- Единый интерфейс для 4 AI провайдеров
- Автоматическое переключение между Gemini, Foundry, AGY, Ollama
- Централизованное управление конфигурацией

### 2. **Расширенная система плагинов**
- 11 плагинов вместо 10
- Динамическая Loading и управление
- Integration с LangChain
- Плагин для управления плагинами

### 3. **Управление агентами**
- REST API для создания и настройки агентов
- Тестирование и validation конфигураций
- Integration с существующей архитектурой

### 4. **Улучшенный RAG с Function Calling**
- Integration с UnifiedChatModel
- Поддержка потокового вывода
- Автоматическое update индексов

### 5. **Полная Configuration AI моделей**
- Поддержка Foundry, AGY, Ollama
- Централизованное управление ключами
- Настройки через веб-интерфейс

### 6. **Расширенная база данных**
- Дополнительные поля для торрентов
- Управление пользователями
- История поиска и аналитика

---

## Примечания для AI (важные изменения)

1. **UnifiedChatModel** — основной интерфейс для всех AI операций
2. **10 роутеров FastAPI** — добавлен `router_agents.py`
3. **11 плагинов** — добавлены `langchain_media` и улучшена система управления
4. **Configuration через веб-интерфейс** — настройки Foundry, Ollama, AGY
5. **Автоматическое update документации** — через инструменты в `tools/ai/`

---

## Основные изменения с предыдущей версии

| Аспект | Было (2024) | Стало (2026) |
|--------|------------|-------------|
| Роутеры | 9 | 10 (+agents) |
| Плагины | 10 | 11 |
| AI Модели | Gemini + Foundry | UnifiedChatModel (4 провайдера) |
| Configuration | Статическая | Веб-интерфейс + API |
| Управление | Ручное | Агенты + автоматизация |
| База данных | media.db | media.db + users + история |

---

## Быстрый старт 2026

```powershell
# Установка зависимостей
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env: GEMINI_API_KEY_NAMES, FOUNDRY_API_KEY, AGY_API_KEY

# Запуск сервера
python main.py

# Или через PowerShell лончер
.\run.ps1

# Доступные интерфейсы:
# http://localhost:8000/user      - плеер+чат
# http://localhost:8000/rc        - пульт ДУ
# http://localhost:8000/tgmini    - Telegram Mini App
# http://localhost:8000/admin     - админка (пароль: onela)
# http://localhost:8000/api/docs  - OpenAPI документация
```

---

**Последнее update: август 2026**  
*Актуализировано после расширения архитектуры до 11 плагинов, добавления UnifiedChatModel и системы управлен��я агентами.*
