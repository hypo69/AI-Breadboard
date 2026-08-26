# Архитектура проекта

## Общая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  User Player │  │ Remote Control│ │  Telegram    │          │
│  │   (HTML/CSS) │  │   (Voice)    │  │   Mini App   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                   │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │   FastAPI HTTP  │                            │
│                  │   WebSocket API │                            │
│                  └────────┬────────┘                            │
└────────────────────────────────┼────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼──────┐       ┌────────▼────────┐       ┌────────▼────────┐
│   AI Layer   │       │   Media Layer   │       │  Torrent Layer  │
│  (Gemini AI) │       │  (Organizer)    │       │ (QBittorrent)   │
│              │       │                 │       │                 │
│  - Chat      │       │  - Database     │       │  - qBittorrent  │
│  - Embeddings│       │  - Scanning     │       │  - Playwright   │
│  - RAG       │       │  - TMDB API     │       │                 │
│              │       │  - Classification│      │                 │
└──────────────┘       └─────────────────┘       └─────────────────┘
        │                        │                        │
        │                        │                        │
┌───────▼──────┐       ┌────────▼────────┐       ┌────────▼────────┐
│   Storage    │       │   Plugins       │       │  Utilities      │
│   Layer      │       │   Layer         │       │   Layer         │
│              │       │                 │       │                 │
│  - SQLite    │       │  - Media Layer  │       │  - File Utils   │
│  - JSON      │       │  - QBittorrent  │       │  - Date/Time    │
│  - File Sys  │       │  - RAG          │       │  - SMTP         │
│              │       │  - Telegram Bot │       │  - CSV/XLS      │
└──────────────┘       └─────────────────┘       └─────────────────┘
```

## Слои приложения

### 1. Frontend Layer

#### Компоненты

- **User Player** — основной плеер для воспроизведения
- **Remote Control** — пульт с голосовым управлением
- **Telegram Mini App** — интеграция с Telegram

#### Технологии

- HTML5, CSS3, JavaScript (Vanilla)
- WebSocket для синхронизации
- Speech API для голосового ввода
- Web Audio API для аудио

### 2. Backend Layer (FastAPI)

#### Слой HTTP API

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/chat` | POST | Чат с AI |
| `/api/control/ws` | WS | WebSocket для управления |
| `/api/media/*` | REST | Управление медиатекой |
| `/api/torrents/*` | REST | Управление торрентами |

#### Слой WebSocket

| Канал | Описание |
|-------|----------|
| `/api/control/ws` | Управление плеером в реальном времени |
| /api/chat | Чат с сервером |

### 3. AI Layer

#### Google Gemini

```python
from core.ai import GoogleGenerativeAI

model = GoogleGenerativeAI(
    api_key_names=["key1", "key2"],
    system_instruction="You are a helpful assistant."
)
```

#### Возможности

- **Chat** — генерация текстов
- **Embeddings** — создание векторных представлений
- **RAG** — поиск по векторной базе данных

### 4. Media Layer

#### База данных

```python
from plugins.media_organizer.core.database import MediaDatabase

db = MediaDatabase("media.db")
```

#### Таблицы

- **media** — записи медиафайлов
- **categories** — категории жанров
- **metadata** — метаданные (TMDB)
- **plugins** — плагины

#### Модули

- **MediaScanner** — сканирование файловой системы
- **MediaAuditor** — аудит базы данных
- **TMDBClient** — интеграция с TMDB API

### 5. Plugin Layer

#### Базовый класс

```python
from plugins.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    
    async def handle(self, message: str) -> Optional[str]:
        # Обработка сообщения
        return None
```

#### Доступные плагины

| Плагин | Описание |
|--------|----------|
| `media_layer` | Управление субтитрами |
| `media_organizer` | Организация медиатеки |
| `qbittorrent` | Управление qBittorrent |
| `rag` | RAG поиск |
| `telegram_bot` | Telegram бот |
| `torrent_playwright` | Поиск торрентов |

### 6. Storage Layer

#### Базы данных

- **SQLite** — основная БД (media.db)
- **JSON** — конфигурация и кэш

#### Файловая система

```
plugins/media_organizer/
├── media.db              # SQLite база данных
├── reports/              # Отчёты
├── scan_cache/           # Кэш сканирования
└── search_dirs.json      # Список директорий
```

## Модули FastAPI

### router_auth.py

Аутентификация и JWT токены.

```python
from core.fastapi.router_auth import verify_jwt_token

token_data = verify_jwt_token(token)
```

### router_chat.py

Чат с AI моделью.

```python
from core.fastapi.router_chat import init_router

app.include_router(init_router(model, plugins))
```

### router_control.py

WebSocket управление плеером.

```python
from core.fastapi.router_control import manager

await manager.broadcast_to_role(room_id, "player", data)
```

### router_media.py

REST API для медиатеки.

```python
from core.fastapi.router_media import init_router

app.include_router(init_router(prefix='/api/media-admin'))
```

### router_qbittorrent.py

Управление qBittorrent.

```python
from core.fastapi.router_qbittorrent import init_router

app.include_router(init_router())
```

## Поток данных

### 1. Запуск плеера

```
User → Frontend → WebSocket → Backend → Player
```

### 2. Чат

```
User → Chat Input → FastAPI → AI Model → Response → Frontend
```

### 3. Поиск медиа и логика ответов чата

Подробный алгоритм диспетчеризации запросов, фильтрации RAG и внешнего поиска описан в [Архитектуре ответов чата и RAG](chat_and_rag_logic.md).

```
User Query → Media Intent Check → Local Search (media.db + FAISS) → Direct Play / Local Context LLM / Web Search Fallback → Narrator TTS
```

### 4. Сканирование медиатеки

```
Scheduler → Scanner → TMDB API → Database → RAG Index
```

## Безопасность

### Аутентификация

- JWT токены для API
- Session cookies для web interface
- CORS middleware

### Авторизация

- Проверка токенов в каждом запросе
- Роли пользователей (admin, user)

### Шифрование

- HTTPS для продакшена
- Шифрование API ключей
- Секреты через `.env`

---

[← Начало работы](getting-started.md) | [API Reference →](api-reference.md)