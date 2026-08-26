# Руководство по API тестированию

## Обзор API

Проект использует FastAPI для создания REST API и WebSocket для real-time коммуникации.

### API Слои

```
Frontend → FastAPI (HTTP/WebSocket) → Plugins → AI/DB
```

## API Endpoints

### 1. Chat API (`/api/chat`)

**POST** `/api/chat` - Отправка сообщения

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Какой фильм посмотреть?",
    "history": []
  }'
```

**Response (200):**
```json
{
  "status": "Проверка плагинов...",
  "text": "Рекомендую посмотреть 'Начало' Кристофера Нолана."
}
```

**Тест-кейсы:**
- TC-API-CHAT-001: Валидное сообщение
- TC-API-CHAT-002: Пустое сообщение
- TC-API-CHAT-003: Слишком длинное сообщение
- TC-API-CHAT-004: Продолжение диалога с историей

### 2. Media API (`/api/media`)

**GET** `/api/media/files` - Список медиафайлов

```bash
curl -X GET http://localhost:3000/api/media/files
```

**Response (200):**
```json
[
  {
    "name": "Test Movie",
    "path": "E:/Movies/Test Movie.mkv",
    "type": "movie",
    "year": 2024
  }
]
```

**POST** `/api/media/by-title` - Поиск по названию

```bash
curl -X POST http://localhost:3000/api/media/by-title \
  -H "Content-Type: application/json" \
  -d '{"title": "Титаник", "type": "movie"}'
```

**Response (200):**
```json
{
  "title": "Титаник",
  "path": "E:\\Films\\Titanic.mkv",
  "type": "movie",
  "year": "1997"
}
```

**Тест-кейсы:**
- TC-API-MEDIA-001: Поиск существующего файла
- TC-API-MEDIA-002: Поиск несуществующего файла
- TC-API-MEDIA-003: Поиск по частичному названию
- TC-API-MEDIA-004: Фильтрация по типу

### 3. Torrent API (`/api/torrents`)

**GET** `/api/torrents` - Список торрентов

```bash
curl -X GET http://localhost:3000/api/torrents
```

**Response (200):**
```json
[
  {
    "hash": "abc123",
    "name": "Test Torrent",
    "state": "Downloading",
    "progress": 45.0,
    "size": 1073741824
  }
]
```

**POST** `/api/torrents/download` - Скачивание торрента

```bash
curl -X POST http://localhost:3000/api/torrents/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "magnet:?xt=urn:btih:test",
    "title": "Test",
    "source": "1337x"
  }'
```

**Тест-кейсы:**
- TC-API-TORR-001: Скачивание magnet ссылки
- TC-API-TORR-002: Скачивание .torrent файла
- TC-API-TORR-003: Невалидная ссылка
- TC-API-TORR-004: qBittorrent недоступен

### 4. Auth API (`/api/auth`)

**POST** `/api/auth/login` - Вход

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Response (200):**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user": {
    "email": "user@example.com",
    "role": "user"
  }
}
```

**GET** `/api/auth/me` - Текущий пользователь

```bash
curl -X GET http://localhost:3000/api/auth/me \
  -H "Authorization: Bearer jwt_token_here"
```

**Тест-кейсы:**
- TC-API-AUTH-001: Успешный вход
- TC-API-AUTH-002: Неверный пароль
- TC-API-AUTH-003: Невалидный токен
- TC-API-AUTH-004: Получение профиля

### 5. Control API (`/api/control`)

**WebSocket** `/api/control/ws` - Real-time управление

**Тест-кейсы:**
- TC-API-CTRL-001: Подключение к WebSocket
- TC-API-CTRL-002: Отправка команды play
- TC-API-CTRL-003: Отправка команды pause
- TC-API-CTRL-004: Получение статуса

### 6. TTS API (`/api/tts`)

**Тест-кейсы:**
- TC-API-TTS-001: Синтез речи edge-tts
- TC-API-TTS-002: Синтез речи gtts
- TC-API-TTS-003: Синтез речи silero

## Инструменты для API тестирования

### 1. curl (командная строка)

```bash
# Тест эндпоинта
curl -X GET http://localhost:3000/api/media/files

# С заголовками
curl -X GET http://localhost:3000/api/media/files \
  -H "Authorization: Bearer token"

# POST запрос
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### 2. httpie

```bash
# Установка
pip install httpie

# GET запрос
http GET http://localhost:3000/api/media/files

# POST запрос
http POST http://localhost:3000/api/chat \
  message="Hello" \
  history:='[]'
```

### 3. Postman

Импортируйте коллекцию из `tests/postman_collection.json`

### 4. Python requests

```python
import requests

# GET запрос
response = requests.get('http://localhost:3000/api/media/files')
print(response.json())

# POST запрос
response = requests.post(
    'http://localhost:3000/api/chat',
    json={'message': 'Hello', 'history': []}
)
print(response.json())
```

## Автоматизированное API тестирование

### pytest + httpx

```python
# tests/test_integration_api.py
def test_get_media_files():
    response = client.get('/api/media/files')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Запуск API тестов

```bash
# Все API тесты
pytest tests/test_integration_api.py

# Конкретный API тест
pytest tests/test_integration_api.py::TestMediaAPI::test_get_media_files

# С детальным выводом
pytest tests/test_integration_api.py -v
```

## Ошибки API

| Код | Описание | Решение |
|-----|----------|---------|
| 400 | Bad Request | Проверьте входные данные |
| 401 | Unauthorized | Проверьте JWT токен |
| 403 | Forbidden | Проверьте права пользователя |
| 404 | Not Found | Проверьте путь |
| 500 | Internal Server Error | Проверьте логи сервера |
| 503 | Service Unavailable | Проверьте qBittorrent |

---

[← Чеклист QA](qa-checklist.md) | [Интеграционное тестирование →](integration-testing.md)