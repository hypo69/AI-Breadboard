# Обновленная архитектура проекта ai-assistant (август 2026)

## Точка входа - обновленная

`main.py` — FastAPI-сервер с автологином локальных пользователей и 10 плагинами.

### Что делает main.py в 2026:
- Reads конфиг из `core/fastapi/config.json` → `_cfg` (host: 0.0.0.0, port: 3000)
- Reads `.env`: `GEMINI_API_KEY_NAMES`, `USE_FOUNDRY`, `FOUNDRY_MODEL_ID`
- Reads системную инструкцию из `.ai_instructions/prompts/chat/system_instruction.md`
- Creates `UnifiedChatModel` (Gemini + Foundry)
- Loads 10 плагинов через `load_plugins(model)`
- Подключает 9 роутеров FastAPI
- Автологин для localhost → user_id=1 через JWT cookie
- Поддерживает SSL сертификаты из `~/.certs/`
- При старте: сканирование дисков, запуск анализатора логов, предLoading Silero TTS

---

## Configuration 2026

### `.env` (основные переменные):
```
# AI
GEMINI_API_KEY_NAMES=имя1,имя2,...
USE_FOUNDRY=false
FOUNDRY_MODEL_ID=qwen3-0.6b-generic-cpu:4
FOUNDRY_BASE_URL=http://localhost:3000

# Authentication
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

### `core/fastapi/config.json`:
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

---

## Обновленная структура модуля AI

### `core/ai/unified_chat.py` — `UnifiedChatModel`
**Унифицированный интерфейс для AI моделей:**

- **Поддерживает**: Google Gemini и Microsoft AI Foundry
- **Автоматическое переключение**: при Errorх Gemini → Foundry
- **Управление ключами**: ротация Gemini API ключей
- **Методы**:
  - `chat(message, system_instruction, model_name)` — основной чат
  - `ask(prompt)` — простой запрос без истории
  - `ask_with_tools(prompt, tools)` — с Function Calling
  - `embed(text)` — векторизация через Gemini Embeddings

### `core/ai/foundry_chat.py` — `FoundryChatModel`
**Клиент для Microsoft AI Foundry:**

- **Локальная модель**: qwen3-0.6b-generic-cpu:4
- **HTTP API**: Integration через Foundry Base URL
- **Fallback**: используется при недоступности Gemini

### `core/ai/gemini/generative_ai.py` — `GoogleGenerativeAI` (обновленный)
**Поддержка новых моделей Gemini 2.0:**

- **Модели**: gemini-2.0-flash-exp, gemini-2.0-pro-exp
- **Streaming**: поддержка потокового вывода
- **Function Calling**: Integration с инструментами плагинов
- **Retry-логика**: улучшенная обработка квот и ошибок

---

## Расширенная структура путей 2026

```
ai-assistant/
├── main.py                          # Точка входа FastAPI
├── header.py                        # Определяет __root__ проекта
├── .env                             # Переменные окружения
├── .ai_instructions/                # Инструкции для AI
│   ├── knowledge/                   # Знания о проекте
│   ├── prompts/                     # Промпты для моделей
│   └── plans/                       # Дорожная карта
├── core/
│   ├── ai/                          # AI модели
│   │   ├── unified_chat.py          # UnifiedChatModel ← НОВЫЙ
│   │   ├── foundry_chat.py          # Microsoft AI Foundry
│   │   ├── gemini/generative_ai.py  # GoogleGenerativeAI
│   │   ├── gemini/rag.py            # GeminiRAG
│   │   └── dev_rag.py               # RAG для разработки
│   ├── fastapi/                     # 9 роутеров
│   │   ├── router_chat.py           # Чат с плагинами
│   │   ├── router_qbittorrent.py    # Управление торрентами
│   │   ├── router_media.py          # Медиа-управление
│   │   ├── router_auth.py           # Google OAuth + JWT
│   │   ├── router_control.py        # Веб-сокет управление ← НОВЫЙ
│   │   ├── router_tts.py            # Text-to-Speech
│   │   ├── router_logs.py           # Логирование
│   │   ├── router_keys.py           # Управление ключами
│   │   └── router_admin.py          # Админ-панель
│   ├── logger/                      # Система логирования
│   ├── user_manager/                # Управление пользователями
│   ├── tts/                         # Text-to-Speech (Silero)
│   └── utils/                       # Утилиты
├── plugins/                         # 10 ПЛАГИНОВ
│   ├── __init__.py                  # load_plugins() ← обновлен
│   ├── plugin.py                    # BasePlugin ABC
│   ├── media_organizer/             # Управление медиатекой
│   ├── rag/                         # RAG-поиск ← НОВЫЙ
│   ├── media_layer/                 # Простой медиа-слой
│   ├── web_search/                  # Веб-поиск ← НОВЫЙ
│   ├── torrent_playwright/          # Поиск торрентов ← НОВЫЙ
│   ├── movie_search_sources/        # Источники для просмотра ← НОВЫЙ
│   ├── qbittorrent/                 # Управление qBittorrent
│   ├── telegram_bot/                # Telegram Mini App
│   ├── user_manager_tool/           # Управление пользователями ← НОВЫЙ
│   └── yt_dlp/                      # Скачивание видео/аудио ← НОВЫЙ
├── webinterface/                    # 6 веб-интерфейсов
│   ├── user/                        # Пользовательский интерфейс
│   ├── admin/                       # Админка (пароль: onela)
│   ├── rc/                          # Пульт ДУ (голос+TTS)
│   ├── tgmini/                      # Telegram Mini App
│   ├── tv/                          # Телевизионный интерфейс ← НОВЫЙ
│   └── user_tts/                    # Тестирование TTS ← НОВЫЙ
├── logs/                            # Логи приложения
├── tests/                           # Тесты Pytest
└── docs/                            # Документация MkDocs
```

---

## Обновленная система плагинов

### Базовый class `BasePlugin` (`plugins/plugin.py`)
**Улучшенная архитектура:**
```python
class BasePlugin(ABC):
    name: str = 'base'
    
    def can_handle(self, message: str) -> bool:
        # Определяет, может ли плагин обработать сообщение
        return True
    
    async def handle(self, message: str, **kwargs) -> str:
        # Основной method обработки с перехватом исключений
        # Поддерживает async generator для потокового вывода
    
    @abstractmethod
    async def _handle(self, message: str, **kwargs) -> str:
        # Реализация в каждом плагине
        # Может возвращать async generator
```

### `load_plugins(model)` (`plugins/__init__.py`)
**Улучшения 2026:**
- **Динамическая Loading** всех 10 плагинов
- **Disconnection плагинов**: через `DISABLED_PLUGINS` в `.env`
- **Логирование ошибок**: при загрузке проблемных плагинов
- **Returns**: `dict[str, BasePlugin]` {имя: экземпляр}

---

## Новые плагины (добавлены с 2024)

### 1. `rag` (`plugins/rag/__init__.py`)
**RAG-поиск по медиатеке с Function Calling:**

- **Триггеры**: "фильм", "сериал", "кино", "посоветуй", "рекомендуй"
- **Функции**:
  - Семантический поиск через RAG
  - "Карусель" случайных фильмов
  - Integration с веб-поиском (Playwright)
  - Озвучка результатов TTS
- **Особенности**: Streaming статусы, AI-анализ результатов

### 2. `web_search` (`plugins/web_search/__init__.py`)
**Веб-поиск через Playwright:**

- **Триггеры**: "поищи в интернете", "найди в интернете", "погугли"
- **Технология**: Playwright (Headless Chrome)
- **Integration**: с AI для анализа результатов
- **Потоковый вывод**: статусы поиска → AI анализ → ответ

### 3. `torrent_playwright` (`plugins/torrent_playwright/__init__.py`)
**Поиск торрентов через Playwright:**

- **Триггеры**: "торрент", "скачать", "tracker", "раздач"
- **Трекеры**: Rutracker, NNMClub
- **AI filtering**: Gemini для отбора лучших раздач
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
- **Функции**: list пользователей, активность, роли
- **Integration**: с JWT аутентификацией

### 7. `yt_dlp` (`plugins/yt_dlp/`) ← **САМЫЙ НОВЫЙ**
**Скачивание видео/аудио через yt-dlp:**

- **Триггеры**: "скачай", "скачать", "youtube", "mp3", "аудио"
- **Функции**:
  - Скачивание видео (лучшее качество)
  - Конвертация в аудио (mp3)
  - Поиск на YouTube
  - Info о видео без скачивания
- **Прогресс**: Streaming статусы загрузки
- **HTML карточки**: результаты с обложками, метаданными

---

## Обновленная база данных медиатеки

### Таблицы в `media.db`:

1. **Основная таблица `media`** (улучшена):
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

2. **Новая таблица `media_vector`** для RAG:
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

---

## Управление пользователями 2026

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

### Class `UserManager`:
- **Управление пользователями**: CRUD операции
- **JWT токены**: генерация и верификация
- **Активность**: логирование действий пользователей
- **Автологин**: для localhost (user_id=1)

---

## Веб-интерфейсы 2026

### 6 специализированных интерфейсов:

| Интерфейс | URL | Описание | Особенности |
|-----------|-----|----------|-------------|
| **User Player** | `/user` | Основной плеер + чат | RAG-поиск, AI чат, синхронизация плееров |
| **Remote Control** | `/rc` | Пульт ДУ + голос | TTS/STT, упрощённое управление, голосовые команды |
| **Telegram Mini App** | `/tgmini` | Telegram Web App | Оптимизирован для мобильных, удалённый доступ |
| **Admin Panel** | `/admin` | Административный контроль | Полный контроль медиатеки, логи, ключи |
| **TV Interface** | `/tv` | Телевизионный интерфейс | Упрощённый для больших экранов, пульт ДУ |
| **TTS Test** | `/user_tts` | Тестирование TTS | Эксперименты с голосовым синтезом |

---

## Тестирование и документация

### 1. **Pytest** (`tests/`):
- **Configuration**: `pytest.ini`, `conftest.py`
- **Фикстуры**: `mock_ai_model`, `mock_db`, `mock_qbt_client`
- **Маркеры**: `unit`, `integration`, `slow`, `database`, `api`, `asyncio`
- **Покрытие**: `--cov=src --cov=plugins --cov-report=term-missing`

### 2. **MkDocs документация** (`docs/`):
- **Configuration**: `mkdocs.yml`
- **Навигация**: 6 разделов (Пользователь, Разработчик, Модули, Интеграции, QA, Troubleshooting)
- **Тема**: Material Design
- **Деплой**: GitHub Pages (https://hypo69.github.io/ai-assistant/)

### 3. **AI инструкции** (`.ai_instructions/`):
- **Промпты**: `prompts/chat/`, `prompts/media_organizer/`
- **Знания**: `knowledge/` (этот файл)
- **Правила**: `rules/CODE_RULES.md`
- **Планы**: `plans/roadmap.md`

---

## API ключи и безопасность

### Управление Gemini API ключами:
1. **Хранение**: `core/secrets/gemini_keys.json` (в .gitignore)
2. **Имена ключей**: в `.env` как `GEMINI_API_KEY_NAMES=имя1,имя2,...`
3. **Статусы**: `active`, `regional restriction`, `exhausted_at`
4. **Ротация**: автоматическая при квотах/Errorх

### JWT authentication:
- **Секрет**: `JWT_SECRET` в `.env`
- **Токены**: 30 дней для автологина localhost
- **Cookies**: `auth_token`, `admin_password_verified`
- **Верификация**: в middleware FastAPI

### SSL/TLS:
- **Сертификаты**: `~/.certs/localhost+2.pem`, `~/.certs/localhost+2-key.pem`
- **Configuration**: `USE_SSL=true` в `.env`
- **Запуск**: автоматическое определение наличия сертификатов

---

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

## Быстрый старт (обновленный)

```bash
# Клонирование и установка
git clone https://github.com/hypo69/ai-assistant.git
cd ai-assistant

# Установка зависимостей (теперь с yt-dlp)
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Редактируем .env:
# - GEMINI_API_KEY_NAMES (имена ключей из gemini_keys.json)
# - TELEGRAM_BOT_TOKEN (если нужен Telegram)
# - USE_FOUNDRY (true/false)

# Создание сертификатов SSL (опционально)
# mkdir ~/.certs
# mkcert localhost

# Запуск сервера
python main.py

# Тестирование
pytest  # все тесты
pytest tests/test_ai.py  # тесты AI
pytest --cov=src --cov-report=html  # покрытие кода

# Документация
mkdocs serve  # локальная документация
```

---

## Основные команды для AI

1. **Для разработки:**
   ```
   "покажи архитектуру проекта" → описание из этого файла
   "какие плагины есть" → list 10 плагинов
   "как работает RAG" → описание RAG-поиска
   ```

2. **Для пользователей:**
   ```
   "посоветуй фильм" → RAG плагин
   "скачай видео" → yt_dlp плагин
   "найди в интернете" → web_search плагин
   "где посмотреть" → movie_search_sources плагин
   ```

3. **Для администраторов:**
   ```
   "!list_users" → user_manager_tool плагин
   "ревизия медиатеки" → media_organizer плагин
   "категории торрентов" → qbittorrent плагин
   ```

---

**Последнее update: август 2026**  
*Актуализировано после расширения проекта до 10 плагинов и добавления yt_dlp, web_search, movie_search_sources и других новых компонентов.*
