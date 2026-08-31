# Архитектура чата и системы взаимодействия

## Обзор

Проект `ai-assistant` — это AI-платформа для управления медиатекой с расширяемой архитектурой плагинов, поддержкой FastAPI и множеством интерфейсов. Центральным элементом является система чата, основанная на строгой модели плагинов и семантическом поиске (RAG).

---

## Основные компоненты

### 1. Бэкенд архитектура

#### FastAPI сервер (`main.py`)
- Точка входа для всех API запросов
- Initialization `UnifiedChatModel` — единого интерфейса для AI моделей
- Динамическая Loading 10 плагинов через `plugins/__init__.py`
- Connection 9 роутеров: чат, медиа, торренты, управление, TTS, логи, ключи, authentication, админ

#### UnifiedChatModel (`core/ai/unified_chat.py`)
Единый интерфейс для прозрачного роутинга между моделями:

| Префикс | Провайдер | Пример |
|---------|-----------|--------|
| `foundry:` | Microsoft AI Foundry | `foundry:qwen3-one` |
| `gemini-` | Google Gemini (по умолчанию) | `gemini-2.0-flash` |
| `agy-` | AGY SDK | `agy-flash` |
| `ollama:` | Ollama локально | `ollama:llama3.1` |

**Роутинг:**
```python
if name.startswith("foundry:"): → FoundryChatBase
if name.startswith("agy-"): → AgyChatBase  
if name.startswith("ollama:"): → OllamaChatBase
else: → GoogleGenerativeAI (по умолчанию)
```

### 2. Роутер чата (`core/fastapi/router_chat.py`)

#### Endpoints
- `POST /api/chat` — основной чат (SSE streaming)
- `POST /api/chat/code-helper` — чат помощника кода (FAISS RAG)
- `POST /api/chat/save-rag` — ручное сохранение в User RAG

#### Поток обработки сообщения
```
POST /api/chat {message, history, generation_config}
  ↓
Извлечение user_identifier (JWT токен → email или IP)
  ↓
Loading персональных настроек (system_instruction, model, tts)
  ↓
Поиск контекста из User RAG (FAISS + Gemini Embeddings)
  ↓
Добавление профиля предпочтений (get_recommendation_context)
  ↓
Formation финального system_prompt
  ↓
Маршрутизация:
  ├─ Медиа-запрос → rag плагин (_is_media_query)
  └─ Обычный запрос → последовательный опрос плагинов
  ↓
Генерация ответа (двухэтапная):
  ├─ Этап 1: Основной ответ (chat/voice)
  └─ Этап 2: Адаптация для второго канала
  ↓
Индексация в User RAG (fire-and-forget)
  ↓
SSE StreamingResponse: {status}, {text}, {voice}
```

#### Особенности обработки

**Two-tier generation:**
- Два отдельных запроса к AI: один для текста, второй для голоса (TTS)
- Parameters `response_type: 'chat' | 'voice'` в generation_config

**Debug mode:**
- Включается через `generation_config.debug_mode = true`
- Returns сформированный промпт вместо отправки в модель
- Для отладки маршрутизации и контекста

**Context continuity:**
- Автоматическое пропускание старого контекста для коротких команд
- List контрольных слов: "да", "нет", "ок", "включи", "запусти" и др.
- Порог: сообщение < 25 символов и присутствие контрольных слов

**Голосовая гендерная коррекция:**
- Мужской голос (Dmitry, Yaraslaus, Bayan и т.д.) → ответ от женщины (женский род)
- Женский голос (Svetlana, Elena, Kseniya и т.д.) → ответ от мужчины (мужской род)

---

## Система плагинов

### Базовый class (`plugins/plugin.py`)

```python
class BasePlugin(ABC):
    name: str = 'base'
    
    async def handle(self, message: str, **kwargs) -> str:
        # Обработка с перехватом исключений
        
    @abstractmethod
    async def _handle(self, message: str, **kwargs) -> str:
        # Реализация конкретного плагина
```

### Loading плагинов (`plugins/__init__.py`)

```python
def load_plugins(ai_model) -> dict[str, BasePlugin]:
    # Обход поддиректорий plugins/
    # Импорт через importlib.import_module
    # Disconnection через DISABLED_PLUGINS (env, через запятую)
```

### Активные плагины (2026)

| Название | Триггеры | Назначение |
|----------|----------|------------|
| `rag` | "фильм", "сериал", "кино", "посоветуй" | Семантический поиск и рекомендации |
| `media_organizer` | — (Function Calling) | Управление БД и RAG индексами |
| `web_search` | "поищи в интернете", "погугли" | Веб-поиск через Playwright |
| `torrent_playwright` | "торрент", "скачать" | Поиск торрентов (Rutracker, NNMClub) |
| `movie_search_sources` | "где посмотреть", "плеер" | Поиск streaming-источников |
| `qbittorrent` | "добавь торрент", "категории" | Управление qBittorrent |
| `yt_dlp` | "скачай", "youtube", "mp3" | Скачивание видео/аудио |
| `user_manager_tool` | `!list_users`, `!user_activity` | Управление пользователями |
| `telegram_bot` | — (отдельный процесс) | Telegram Mini App |

### Пример плагина (RAG)

```python
class RAGPlugin(BasePlugin):
    name = "rag"
    
    def _is_media_query(self, message: str) -> bool:
        # Check медиа-ключевых слов
        low = message.lower()
        return any(kw in low for kw in _MEDIA_KEYWORDS)
    
    async def _handle(self, message: str, **kwargs):
        if self._is_media_query(message):
            yield {"status": "🔍 Поиск в RAG-индексе..."}
            results_json = search_media(message)
            results_data = json.loads(results_json)
            
            # Если ничего не найдено → поиск в интернете
            if not results or "интернет" in low_message:
                yield {"status": "🌐 Поиск в интернете..."}
                web_context = await web_searcher.search_and_extract(message)
            
            # Генерация ответа
            if is_conversational:
                yield {"status": "🤖 Генерация ответа ИИ..."}
                system_prompt = f"...Результаты поиска:\n{context_str}\n{web_context}"
                answer = await self.ai.chat(message, system_instruction=system_prompt)
                yield {"text": answer}
```

---

## RAG архитектура

### User RAG (`core/ai/gemini/user_query_rag.py`)
- Хранение персональных запросов и ответов
- Индексация через Gemini Embeddings API
- Поиск в FAISS индексе с порогом схожести 0.45

```python
async def index_user_query(user_id, api_key, query, response):
    # Создание эмбеддинга для запроса
    # Сохранение в SQLite + FAISS
    pass

async def search_user_context(user_id, api_key, query, top_k=2, threshold=0.45):
    # Поиск по векторам
    # Возвращение контекста для добавления в system_prompt
```

### Media RAG (`plugins/media_organizer/core/media_rag.py`)
- Векторный поиск по медиатеке (Films/TV shows)
- Использование Gemini Embeddings для семантического поиска
- Function Calling API для AI моделей

```python
# Function Calling инструменты:
- search_media(query, top_k=5) — поиск фильмов/сериалов
- get_media_card(disk_name, title, type) — карточка медиа
- get_random_media() — случайный фильм
- get_rag_status() — status индексации
```


## Веб-интерфейс (Frontend)

### Структура (`webinterface/`)

```
webinterface/
├── user/        # Основной интерфейс (плеер + чат)
├── admin/       # Админ-панель (пароль: onela)
├── rc/          # Пульт ДУ (голос + TTS)
├── tgmini/      # Telegram Mini App
├── tv/          # Телевизионный интерфейс
├── user_tts/    # Тестирование TTS
├── chat/        # Компоненты чата
├── player/      # Компоненты плеера
└── js/          # Общие JS утилиты (i18n, logger)
```

### Главный файл (`webinterface/user/main.js`)

#### Модули:
1. **Auth** — authorization (Google OAuth, email/password)
2. **Torrent** — обработка торрент-ссылок из ответов бота
3. **Player** — воспроизведение медиафайлов
4. **Chat** — отправка сообщений и получение ответов

#### Ключевые функции:

```javascript
// Отправка сообщения
async function sendMessage() {
    const message = input.value.trim();
    addMessage(message, 'user');
    
    const reply = await window.chatService.sendChatMessage(message);
    addMessage(reply, 'assistant');
    window.chatService.speak(reply);
}

// Обработка торрент-ссылок из ответов бота
function checkAndProcessTorrentLinks(text) {
    const links = findTorrentLinks(text);
    for (const link of links) {
        const shouldDownload = confirm(`Добавить торрент?`);
        if (shouldDownload) {
            await handleTorrentLink(link, downloadDir);
        }
    }
}

// Обработка тегов <film>
function checkAndProcessFilmTags(text) {
    const filmMatches = [...text.matchAll(/<film>(.*?)<\/film>/gi)];
    for (const match of filmMatches) {
        const filmTitle = match[1];
        if (confirm(`Запустить: ${filmTitle}?`)) {
            await launchFilm(filmTitle);
        }
    }
}

// Запуск фильма по названию
async function launchFilm(title) {
    const result = await api.fetch('/api/media/by-title', {
        method: 'POST',
        body: JSON.stringify({ title })
    });
    
    if (result.path) {
        playFile(mediaFiles.findIndex(f => f.path === result.path));
    }
}
```

### WebSocket управление (`core/fastapi/router_control.py`)

**Роли:**
- `player` — плеер (воспроизведение)
- `remote` — пульт (управление)

**Комнаты:**
- Идентификатор: email пользователя или `room` параметр
- Хранение состояния: `manager.room_states[room_id]`
- Хранение плейлиста: `manager.room_playlists[room_id]`

---

## Потоковые технологии

### SSE (Server-Sent Events)
- Для потоковой передачи ответов чата
- Формат: `data: {"status": "..."}\n\n` или `data: {"text": "..."}\n\n`
- Поддержка `voice`, `status`, `error` полей

### WebSocket
- Для управления плеером в реальном времени
- Команды: play, pause, next, previous, seek
- Обновления состояния: status_update, playlist_update

---

## Configuration

### `core/fastapi/config.json`
```json
{
  "host": "0.0.0.0",
  "port": 3000,
  "workers": 1
}
```

### `.env` переменные
```
# AI модели
GEMINI_API_KEY_NAMES=gemini_key_1,gemini_key_2
USE_FOUNDRY=false
FOUNDRY_MODEL_ID=qwen3-0.6b-generic-cpu:4
FOUNDRY_BASE_URL=http://localhost:3000

# AGY (Gemini через прокси)
USE_AGY=false

# Ollama локальные модели
USE_OLLAMA=false
OLLAMA_MODEL_ID=llama3.1
OLLAMA_BASE_URL=http://localhost:11434

# Disconnection плагинов
DISABLED_PLUGINS=telegram_bot,yt_dlp

# TTS
TTS_VOICE=ru-RU-DmitryNeural
```

### Доступные модели (API `/api/chat/models`)
```json
{
  "models": {
    "gemini": ["gemini-2.0-flash", "gemini-1.5-flash"],
    "foundry": ["foundry:qwen3-0.6b-generic-cpu:4"],
    "agy": ["agy-flash", "agy-pro"],
    "ollama": ["ollama:llama3.1", "ollama:mistral"]
  }
}
```

**Примечание:** При выборе Foundry модели в UI используется полное имя с префиксом `foundry:`.

---

## Логирование

### Система логов (`core/logger/logger.py`)
- Singleton паттерн для единого экземпляра
- Moduleные лог-файлы: `fastapi.log`, `gemini.log`, `playwright.log`, `yt_dlp.log`
- JSON форматирование в `log.json`
- Цветной консольный вывод

---

## Integration со скриптами

После обработки медиа или внесения изменений в медиатеку автоматически запускаются:

```bash
# Сопоставление категорий торрентов
py manage_tools.py torrents assign

# Привязка торрентов к медиа
py manage_tools.py torrents ids

# Update размеров файлов
py manage_tools.py db sizes

# Аудит медиафайлов
py manage_tools.py audit media
```

---

## Ключевые принципы архитектуры

1. **Единый интерфейс AI** — `UnifiedChatModel` скрывает детали переключения между моделями
2. **Плагинная архитектура** — 10 независимых плагинов с общим интерфейсом `BasePlugin`
3. **Двухуровневая генерация** — chat + voice ответы для разных каналов вывода
4. **User RAG** — персональная векторная база для каждого пользователя
5. **Потоковая обработка** — SSE для чата, WebSocket для управления
6. **Автоматическая индексация** — после успешных ответов сохранение в RAG (fire-and-forget)
7. **Контекстная адаптация** — профиль предпочтений + пользовательский RAG контекст

---

## Check состояния системы

```bash
# List дос��упных моделей
curl http://localhost:3000/api/chat/models

# Status WebSocket комнат
curl http://localhost:3000/api/control/status

# Status активных плееров
curl http://localhost:3000/api/control/active_players

# Ручное сохранение в RAG
curl -X POST http://localhost:3000/api/chat/save-rag \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "chat_text": "...", "voice_text": "..."}'
```

---

## Последние изменения (август 2026)

- Добавлен плагин `yt_dlp` для скачивания видео/аудио
- Расширена архитектура до 10 плагинов
- Обновлена архитектура RAG (FAISS + Function Calling)
- Добавлены новые интерфейсы (tv, user_tts)
- Синхронизация с скриптами управления через `manage_tools.py`