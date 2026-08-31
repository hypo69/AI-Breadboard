# Документация API проекта ai-assistant

## Общее описание

Проект ai-assistant предоставляет REST API на базе FastAPI для управления медиатекой, AI-ассистентом, торрент-клиентом и системными компонентами. API состоит из 10 роутеров с единой архитектурой и стандартами.

## Базовый URL
```
http://localhost:3000
https://ваш-домен.com
```

## Authentication и Google OAuth

### Google OAuth2 Flow
- `GET /auth/google?next=/` — инициирует процесс аутентификации и синхронизации через Google OAuth2 с запросом прав на доступ к Google Drive, Docs, Calendar, Contacts.
- `GET /auth/google/callback` — обработка callback от Google, обмен авторизационного кода на access/refresh токены, сохранение профиля пользователя в `user_manager` и установка JWT-cookie `auth_token`.
- `GET /auth/google/status` — check подключения и синхронизации Google-аккаунта.

#### ⚠️ Требования к Google Redirect URI (Google Cloud Console):
Во избежание ошибки `400: redirect_uri_mismatch`, в **Google Cloud Console &rarr; Credentials &rarr; OAuth 2.0 Client ID** в list **Authorized redirect URIs** должны быть добавлены все рабочие адреса:
- `https://kino.davidka.net/auth/google/callback` (внешний домен / туннель)
- `http://localhost:8000/auth/google/callback` (локальный порт)
- `http://127.0.0.1:8000/auth/google/callback` (локальный IP)

### Check статуса авторизации
```http
GET /auth/check
```
Returns информацию о текущей сессии:
```json
{
  "authenticated": true,
  "id": 1,
  "email": "user@gmail.com",
  "name": "User Name",
  "picture": "https://...",
  "role": "admin",
  "is_admin": true,
  "has_google": true
}
```

### Выход из системы
```http
POST /auth/logout
```
Очищает cookie `auth_token` и завершает сессию.

## Основные API группы

### 1. Чат AI (`/api/chat`)
**Роутер:** `router_chat.py`

#### WebSocket чат
```
WS /api/chat/ws
```
Двусторонний WebSocket для интерактивного чата с UnifiedChatModel.

#### SSE потоковый чат
```
POST /api/chat
Content-Type: application/json

{
  "message": "текст сообщения",
  "stream": true,
  "model": "gemini-2.0-flash"
}
```

#### Parameters:
- `message` (обязательный): Текст сообщения пользователя
- `stream` (опциональный): Включить потоковый ответ (по умолчанию: false)
- `model` (опциональный): Модель AI (gemini-*, foundry:*, agy-*, ollama:*)
- `tools` (опциональный): List инструментов для Function Calling

### 2. Медиатека (`/api/media`)
**Роутер:** `router_media.py`

#### Поиск медиа по названию
```
POST /api/media/by-title
Content-Type: application/json

{
  "title": "название фильма",
  "type": "movie" // optional: movie, series, season, episode
}
```

#### Потоковая трансляция
```
GET /api/media/stream/{media_id}
Range: bytes=0-1024
```
Returns потоковую трансляцию медиафайла с поддержкой диапазонов байтов.

#### Карточка медиа
```
GET /api/media/card/{media_id}
```
Returns полную карточку медиа с метаданными.

#### Сканирование медиатеки
```
POST /api/media/scan
Content-Type: application/json

{
  "disk": "диск 1",
  "path": "E:",
  "force": false
}
```

### 3. Торренты (`/api/torrents`)
**Роутер:** `router_qbittorrent.py`

#### List торрентов
```
GET /api/torrents/
```
Returns list всех торрентов в qBittorrent.

#### Поиск торрентов
```
POST /api/torrents/search
Content-Type: application/json

{
  "query": "название фильма",
  "category": "movies"
}
```

#### Добавление торрента
```
POST /api/torrents/add
Content-Type: application/json

{
  "url": "magnet:...",
  "category": "movies",
  "tags": ["фильм", "боевик"]
}
```

#### Управление категориями
```
GET /api/torrents/categories
POST /api/torrents/categories
DELETE /api/torrents/categories/{name}
```

### 4. TTS (`/api/tts`)
**Роутер:** `router_tts.py`

#### Синтез речи
```
POST /api/tts/synthesize
Content-Type: application/json

{
  "text": "текст для озвучки",
  "voice": "ru_v3",
  "speed": 1.0
}
```

#### List голосов
```
GET /api/tts/voices
```
Returns list доступных голосов для синтеза.

### 5. Логи (`/api/logs`)
**Роутер:** `router_logs.py`

#### Просмотр логов
```
GET /api/logs/
Query parameters:
  - level: error, warning, info, debug
  - limit: количество записей
  - since: timestamp начала
```

#### Анализ логов
```
GET /api/logs/analyze
```
Анализирует логи и Returns статистику ошибок.

### 6. Ключи API (`/api/keys`)
**Роутер:** `router_keys.py`

#### Status ключей
```
GET /api/keys/status
```
Returns status всех настроенных API ключей.

#### Переключение ключей
```
POST /api/keys/switch
Content-Type: application/json

{
  "provider": "gemini",
  "key_name": "primary"
}
```

### 7. Администрация (`/admin`, `/api/admin`)
**Роутер:** `router_admin.py`

**Защита:** Парольная защита (пароль: `onela`)

#### Административный интерфейс
```
GET /admin
```
HTML интерфейс административной панели.

#### Системные настройки
```
GET /api/admin/settings
POST /api/admin/settings
```

#### Управление пользователями
```
GET /api/admin/users
POST /api/admin/users
PUT /api/admin/users/{id}
DELETE /api/admin/users/{id}
```

#### Мониторинг системы
```
GET /api/admin/monitoring
```
Returns метрики системы и state компонентов.

### 8. Агенты (`/api/agents`)
**Роутер:** `router_agents.py` (новый)

#### List агентов
```
GET /api/agents/
```
Returns list всех настроенных AI агентов.

#### Создание агента
```
POST /api/agents/
Content-Type: application/json

{
  "name": "медиа-аналитик",
  "description": "Агент для анализа медиатеки",
  "config": {
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "plugins": ["rag", "media_organizer"]
  }
}
```

#### Тестирование агента
```
POST /api/agents/{id}/test
Content-Type: application/json

{
  "input": "тестовый запрос",
  "parameters": {}
}
```

#### Генерация промптов
```
POST /api/agents/generate-prompt
Content-Type: application/json

{
  "agent_type": "media_analyzer",
  "requirements": ["анализ", "рекомендации", "структурирование"]
}
```

### 9. WebSocket управление (`/ws/control`)
**Роутер:** `router_control.py`

#### Управление плеером
```
WS /ws/control
```
WebSocket для управления медиаплеером:
- Воспроизведение/пауза
- Перемотка
- Управление громкостью
- Навигация по контенту

### 10. Статические файлы и интерфейсы

#### Пользовательский интерфейс
```
GET /user
```
Основной интерфейс с плеером и чатом.

#### Пульт ДУ
```
GET /rc
```
Голосовой пульт дистанционного управления.

#### Telegram Mini App
```
GET /tgmini
```
Интерфейс для интеграции с Telegram.

#### Телевизионный интерфейс
```
GET /tv
```
Упрощенный интерфейс для телевизоров.

#### TTS тестирование
```
GET /user_tts
```
Интерфейс для тестирования Text-to-Speech.

## Модели данных

### UnifiedChatModel Configuration
```json
{
  "model": "gemini-2.0-flash",
  "api_key": "${GEMINI_API_KEY}",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

### Медиа карточка
```json
{
  "id": 1,
  "title": "Название фильма",
  "title_ru": "Русское название",
  "title_orig": "Original Title",
  "year": 2024,
  "main_category": "Боевики",
  "path": "E:/фильмы/фильм.mkv",
  "media_type": "movie",
  "rating": {
    "imdb": 8.5,
    "tmdb": 8.2
  }
}
```

### Configuration агента
```json
{
  "name": "аналитик медиа",
  "description": "Анализирует медиатеку и предоставляет рекомендации",
  "enabled": true,
  "config": {
    "model": "foundry:qwen3-one",
    "system_prompt": "Ты эксперт по анализу медиаконтента...",
    "plugins": ["rag", "media_organizer"],
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 4096
    }
  }
}
```

## Обработка ошибок

### Стандартные HTTP статусы
- `200 OK`: Успешный запрос
- `201 Created`: Ресурс создан
- `400 Bad Request`: Невалидные данные
- `401 Unauthorized`: Требуется authentication
- `403 Forbidden`: Недостаточно прав
- `404 Not Found`: Ресурс не найден
- `500 Internal Server Error`: Внутренняя Error сервера

### Формат ответа с ошибкой
```json
{
  "error": "описание ошибки",
  "code": "ERROR_CODE",
  "timestamp": "2026-08-24T12:00:00Z"
}
```

## Безопасность

### Защита эндпоинтов
1. Административные функции защищены паролем
2. API ключи хранятся в `.env` файле
3. Сессии управляются через JWT токены
4. Входные данные валидируются через Pydantic

### CORS настройки
```
CORS_ORIGINS = ["http://localhost:3000", "https://ваш-домен.com"]
CORS_CREDENTIALS = true
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
```

## Integration с клиентами

### Python клиент
```python
import requests

BASE_URL = "http://localhost:3000"

def chat_with_ai(message):
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": message, "stream": False}
    )
    return response.json()
```

### JavaScript/TypeScript
```typescript
const API_BASE = 'http://localhost:3000';

async function searchMedia(title: string) {
  const response = await fetch(`${API_BASE}/api/media/by-title`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({title})
  });
  return response.json();
}
```

## Мониторинг и метрики

### Health check
```
GET /health
```
Returns status системы и state компонентов.

### Метрики Prometheus
```
GET /metrics
```
Метрики системы в формате Prometheus.

### OpenAPI документация
```
GET /api/docs
GET /api/redoc
GET /api/openapi.json
```

## Версионирование API

Текущая версия: **v1**
Формат версии в заголовках:
```
Accept: application/json; version=1
```

## Правила разработки новых эндпоинтов

1. Использовать существующие Pydantic модели для валидации
2. Реализовать полную обработку ошибок
3. Добавить документацию через docstrings
4. Интегрировать с системой логирования
5. Тестировать через pytest
6. Обновлять OpenAPI документацию

---

**Последнее update:** 24 августа 2026  
**Версия API:** v1  
**Базовая архитектура:** FastAPI + UnifiedChatModel + Moduleные плагины