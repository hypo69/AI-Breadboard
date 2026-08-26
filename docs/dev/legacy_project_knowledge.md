# Архитектура проекта ai-assistant (исторический документ)

**⚠️ Этот документ содержит историческую информацию о проекте.**
**Для актуальной информации смотрите `project_overview.md`**

## Точка входа (историческая версия)

`main.py` — FastAPI-сервер с автологином локальных пользователей и 10 плагинами.

### Что делал main.py (старая версия):
- Читал конфиг из `core/fastapi/config.json` → `_cfg` (host: 0.0.0.0, port: 3000)
- Читал `.env`: `GEMINI_API_KEY_NAMES`, `USE_FOUNDRY`, `FOUNDRY_MODEL_ID`
- Читал системную инструкцию из `.ai_instructions/prompts/chat/system_instruction.md`
- Создавал `UnifiedChatModel` (Gemini + Foundry)
- Загружал 10 плагинов через `load_plugins(model)`
- Подключал 9 роутеров FastAPI
- Автологин для localhost → user_id=1 через JWT cookie
- Поддерживал SSL сертификаты из `~/.certs/`
- При старте: сканирование дисков, запуск анализатора логов, предзагрузка Silero TTS

## Конфигурация (историческая)

### `.env` (старые переменные):
```
# AI
GEMINI_API_KEY_NAMES=имя1,имя2,...
USE_FOUNDRY=false
FOUNDRY_MODEL_ID=qwen3-0.6b-generic-cpu:4
FOUNDRY_BASE_URL=http://localhost:3000

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

### `core/fastapi/config.json` (старый):
```json
{
  "host": "0.0.0.0",
  "port": 3000,
  "workers": 4
}
```

### Структура API ключей Gemini (`core/secrets/gemini_keys.json`):
```json
{
  "ключ_имя": {
    "api_key": "<API_KEY>",
    "status": "active",
    "last_run": "2026-08-04T12:00:00Z",
    "exhausted_at": null
  }
}
```

## Модуль AI (историческая структура)

### `core/ai/unified_chat.py` — `UnifiedChatModel`
**Унифицированный интерфейс для AI моделей:**

- **Поддерживал**: Google Gemini и Microsoft AI Foundry
- **Автоматическое переключение**: при ошибках Gemini → Foundry
- **Управление ключами**: ротация Gemini API ключей
- **Методы**:
  - `chat(message, system_instruction, model_name)` — основной чат
  - `ask(prompt)` — простой запрос без истории
  - `ask_with_tools(prompt, tools)` — с Function Calling
  - `embed(text)` — векторизация через Gemini Embeddings

### `core/ai/foundry_chat.py` — `FoundryChatModel`
**Клиент для Microsoft AI Foundry:**

- **Локальная модель**: qwen3-0.6b-generic-cpu:4
- **HTTP API**: интеграция через Foundry Base URL
- **Fallback**: использовался при недоступности Gemini

### `core/ai/gemini/generative_ai.py` — `GoogleGenerativeAI` (старая версия)
**Поддержка старых моделей Gemini:**

- **Модели**: gemini-2.0-flash-exp, gemini-2.0-pro-exp
- **Streaming**: поддержка потокового вывода
- **Function Calling**: интеграция с инструментами плагинов
- **Retry-логика**: улучшенная обработка квот и ошибок

## Структура путей (историческая)

```
ai-assistant/
├── main.py                          # Точка входа FastAPI
├── header.py                        # Определял __root__ проекта
├── .env                             # Переменные окружения
├── .ai_instructions/                # Инструкции для AI
│   ├── knowledge/                   # Знания о проекте
│   ├── prompts/                     # Промпты для моделей
│   └── plans/                       # Дорожная карта
├── core/
│   ├── ai/                          # AI модели
│   │   ├── unified_chat.py          # UnifiedChatModel
│   │   ├── foundry_chat.py          # Microsoft AI Foundry
│   │   ├── gemini/generative_ai.py  # GoogleGenerativeAI
│   │   ├── gemini/rag.py            # GeminiRAG
│   │   └── dev_rag.py               # RAG для разработки
│   ├── fastapi/                     # 9 роутеров
│   │   ├── router_chat.py           # Чат с плагинами
│   │   ├── router_qbittorrent.py    # Управление торрентами
│   │   ├── router_media.py          # Медиа-управление
│   │   ├── router_auth.py           # Google OAuth + JWT
│   │   ├── router_control.py        # Веб-сокет управление
│   │   ├── router_tts.py            # Text-to-Speech
│   │   ├── router_logs.py           # Логирование
│   │   ├── router_keys.py           # Управление ключами
│   │   └── router_admin.py          # Админ-панель
│   ├── logger/                      # Система логирования
│   ├── user_manager/                # Управление пользователями
│   ├── tts/                         # Text-to-Speech (Silero)
│   └── utils/                       # Утилиты
├── plugins/                         # 10 ПЛАГИНОВ
│   ├── __init__.py                  # load_plugins()
│   ├── plugin.py                    # BasePlugin ABC
│   ├── media_organizer/             # Управление медиатекой
│   ├── rag/                         # RAG-поиск
│   ├── media_layer/                 # Простой медиа-слой
│   ├── web_search/                  # Веб-поиск
│   ├── torrent_playwright/          # Поиск торрентов
│   ├── movie_search_sources/        # Источники для просмотра
│   ├── qbittorrent/                 # Управление qBittorrent
│   ├── telegram_bot/                # Telegram Mini App
│   ├── user_manager_tool/           # Управление пользователями
│   └── yt_dlp/                      # Скачивание видео/аудио
├── webinterface/                    # 6 веб-интерфейсов
│   ├── user/                        # Пользовательский интерфейс
│   ├── admin/                       # Админка (пароль: onela)
│   ├── rc/                          # Пульт ДУ (голос+TTS)
│   ├── tgmini/                      # Telegram Mini App
│   ├── tv/                          # Телевизионный интерфейс
│   └── user_tts/                    # Тестирование TTS
├── logs/                            # Логи приложения
├── tests/                           # Тесты Pytest
└── docs/                            # Документация MkDocs
```

## Система плагинов (историческая)

### Базовый класс `BasePlugin` (`plugins/plugin.py`)
**Старая архитектура:**
```python
class BasePlugin(ABC):
    name: str = 'base'
    
    def can_handle(self, message: str) -> bool:
        # Определял, может ли плагин обработать сообщение
        return True
    
    async def handle(self, message: str, **kwargs) -> str:
        # Основной метод обработки с перехватом исключений
        # Поддерживал async generator для потокового вывода
    
    @abstractmethod
    async def _handle(self, message: str, **kwargs) -> str:
        # Реализация в каждом плагине
        # Мог возвращать async generator
```

### `load_plugins(model)` (`plugins/__init__.py`)
**Старые функции:**
- **Динамическая загрузка** всех 10 плагинов
- **Отключение плагинов**: через `DISABLED_PLUGINS` в `.env`
- **Логирование ошибок**: при загрузке проблемных плагинов
- **Возвращал**: `dict[str, BasePlugin]` {имя: экземпляр}

## Плагины (исторический список)

### 1. `rag` (`plugins/rag/__init__.py`)
**RAG-поиск по медиатеке с Function Calling:**

- **Триггеры**: "фильм", "сериал", "кино", "посоветуй", "рекомендуй"
- **Функции**:
  - Семантический поиск через RAG
  - "Карусель" случайных фильмов
  - Интеграция с веб-поиском (Playwright)
  - Озвучка результатов TTS
- **Особенности**: Streaming статусы, AI-анализ результатов

### 2. `web_search` (`plugins/web_search/__init__.py`)
**Веб-поиск через Playwright:**

- **Триггеры**: "поищи в интернете", "найди в интернете", "погугли"
- **Технология**: Playwright (Headless Chrome)
- **Интеграция**: с AI для анализа результатов
- **Потоковый вывод**: статусы поиска → AI анализ → ответ

### 3. `torrent_playwright` (`plugins/torrent_playwright/__init__.py`)
**Поиск торрентов через Playwright:**

- **Триггеры**: "торрент", "скачать", "tracker", "раздач"
- **Трекеры**: Rutracker, NNMClub
- **AI фильтрация**: Gemini для отбора лучших раздач
- **HTML карточки**: интерактивные кнопки загрузки в qBittorrent

### 4. `movie_search_sources` (`plugins/movie_search_sources/movie_search_sources.py`)
**Каталог источников для просмотра:**

- **Триггеры**: "где посмотреть", "плеер", "iframe", "стриминг"
- **Категории**:
  - Metadata APIs (TMDB, OMDb, IMDb)
  - Streaming агрегаторы (JustWatch, Reelgood)
  - Iframe плееры (VidSrc, 2Embed)
  - Прямые сайты (Rezka, Kinogo, Seasonvar)
- **Особенности**: Streaming уведомления о поиске в каждом источнике

### 5. `user_manager_tool` (`plugins/user_manager_tool/plugin.py`)
**Управление пользователями:**

- **Триггеры**: `!list_users`, `!user_activity`
- **База данных**: `users.db` (SQLite)
- **Функции**: список пользователей, активность, роли
- **Интеграция**: с JWT аутентификацией

### 7. `yt_dlp` (`plugins/yt_dlp/`) 
**Скачивание видео/аудио через yt-dlp:**

- **Триггеры**: "скачай", "скачать", "youtube", "mp3", "аудио"
- **Функции**:
  - Скачивание видео (лучшее качество)
  - Конвертация в аудио (mp3)
  - Поиск на YouTube
  - Информация о видео без скачивания
- **Прогресс**: Streaming статусы загрузки
- **HTML карточки**: результаты с обложками, метаданными

## База данных медиатеки (историческая)

### Таблицы в `media.db`:

1. **Основная таблица `media`** (старая версия):
```sql
CREATE TABLE media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disk_name TEXT NOT NULL,
    path TEXT NOT NULL,
    title TEXT,
    title_ru TEXT,
    title_orig TEXT,
    year INTEGER,
    main_category TEXT,
    country TEXT,
    genres TEXT,           -- JSON массив
    directors TEXT,        -- JSON массив
    cast TEXT,             -- JSON массив
    num_of_seasons INTEGER,
    num_episodes_per_season TEXT,  -- JSON массив
    status TEXT,
    rating TEXT,           -- JSON объект {imdb: 8.5, kinopoisk: 8.7}
    awards TEXT,           -- JSON массив
    plot TEXT,
    atmosphere TEXT,
    why_watch TEXT,
    mood TEXT,
    final_verdict TEXT,
    can_stop_at TEXT,
    quote TEXT,
    facts TEXT,            -- JSON массив
    similar TEXT,          -- JSON массив
    parent_id INTEGER DEFAULT 0,
    episode_scan_skipped INTEGER DEFAULT 0,
    media_type TEXT,       -- 'movie', 'series', 'season', 'episode'
    number INTEGER
);
```

2. **Таблица `media_vector`** для RAG:
```sql
CREATE TABLE media_vector (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
```

3. **Таблица `search_history`**:
```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    results_count INTEGER
);
```

## Управление пользователями (историческое)

### База данных `users.db` (`core/user_manager/`):
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    picture TEXT,
    role TEXT DEFAULT 'user',
    is_admin BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Класс `UserManager`:
- **Управление пользователями**: CRUD операции
- **JWT токены**: генерация и верификация
- **Активность**: логирование действий пользователей
- **Автологин**: для localhost (user_id=1)

## Веб-интерфейсы (исторические)

### 6 специализирован��ых интерфейсов:

| Интерфейс | URL | Описание | Особенности |
|-----------|-----|----------|-------------|
| **User Player** | `/user` | Основной плеер + чат | RAG-поиск, AI чат, синхронизация плееров |
| **Remote Control** | `/rc` | Пульт ДУ + голос | TTS/STT, упрощённое управление, голосовые команды |
| **Telegram Mini App** | `/tgmini` | Telegram Web App | Оптимизирован для мобильных, удалённый доступ |
| **Admin Panel** | `/admin` | Административный контроль | Полный контроль медиатеки, логи, ключи |
| **TV Interface** | `/tv` | Телевизионный интерфейс | Упрощённый для больших экранов, пульт ДУ |
| **TTS Test** | `/user_tts` | Тестирование TTS | Эксперименты с голосовым с��нтезом |

## Изменения с предыдущей версии (2024 → 2026)

| Аспект | 2024 | 2026 |
|--------|------|------|
| **AI модели** | Только Gemini | Gemini + Foundry |
| **Плагины** | 5 | 10 (+5 новых) |
| **RAG поиск** | Простой | FAISS + Function Calling |
| **Веб-поиск** | Нет | Playwright + AI анализ |
| **Торренты** | qBittorrent API | + Playwright поиск |
| **Скачивание видео** | Нет | yt-dlp плагин |
| **Пользователи** | Нет | JWT + база данных |
| **Голосовой интерфейс** | Базовая TTS | Silero + Web Speech API |
| **Тестирование** | Минимальное | Pytest + покрытие |
| **Документация** | README | MkDocs + GitHub Pages |

---

**⚠️ Этот документ сохранен для исторической справки.**
**Для актуальной информации используйте `project_overview.md`.**