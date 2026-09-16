# 🔌 API Reference: FastAPI endpoints

**Статус:** ✅ Reference (основная информация)  
**Версия:** 3.0  
**Последнее обновление:** сентябрь 2026

---

## 📋 Содержание
1. [Обзор всех роутеров](#1-обзор-всех-роутеров)
2. [Примеры использования](#2-примеры-использования)
3. [Аутентификация](#3-аутентификация)
4. [Обработка ошибок](#4-обработка-ошибок)

---

## 1. Обзор всех роутеров

### Core Endpoints

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET/POST** | `/api/chat` | Unified chat endpoint | `router_chat.py` |
| **WS** | `/api/chat/ws` | WebSocket chat stream | `router_chat.py` |
| **GET** | `/api/chat/stream` | Server-Sent Events stream | `router_chat.py` |

### MCP & Tools

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/mcp/servers` | List MCP servers | `router_mcp.py` |
| **GET** | `/api/mcp/tools` | List available tools | `router_mcp.py` |
| **POST** | `/api/mcp/call` | Execute tool | `router_mcp.py` |

### RAG Operations

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **POST** | `/api/rag/search` | Vector search | `router_rag.py` |
| **POST** | `/api/rag/rebuild` | Rebuild indices | `router_rag.py` |
| **GET** | `/api/rag/status` | RAG system status | `router_rag.py` |

### Administration

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/admin/config` | Get system config | `router_admin.py` |
| **POST** | `/api/admin/config` | Update config | `router_admin.py` |
| **GET** | `/api/admin/stats` | System statistics | `router_admin.py` |

### Authentication

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/auth/google` | Google OAuth2 login | `router_auth.py` |
| **GET** | `/auth/callback` | OAuth2 callback | `router_auth.py` |
| **GET** | `/auth/check` | Check auth status | `router_auth.py` |
| **POST** | `/auth/logout` | Logout | `router_auth.py` |

### AI Agents

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/agents/list` | List subagents | `router_agents.py` |
| **POST** | `/api/agents/invoke` | Invoke subagent | `router_agents.py` |

### Keys & Monitoring

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/keys/status` | API key health | `router_keys.py` |
| **POST** | `/api/keys/rotate` | Rotate keys | `router_keys.py` |

### Logs & Diagnostics

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **WS** | `/api/logs/stream` | Real-time logs | `router_logs.py` |
| **POST** | `/api/logs/analyze` | Analyze logs | `router_logs.py` |

### Audio & TTS

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **POST** | `/api/tts/synthesize` | Text-to-speech | `router_tts.py` |
| **GET** | `/api/tts/voices` | Available voices | `router_tts.py` |
| **POST** | `/api/audio/transcribe` | Audio transcription | `router_audio.py` |

### Storage & Files

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/storage/files` | List user files | `router_user_storage.py` |
| **POST** | `/api/storage/upload` | Upload file | `router_user_storage.py` |
| **GET** | `/api/storage/quota` | Get quota | `router_user_storage.py` |

### System Info

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/version` | Get system version | `router_version.py` |
| **GET** | `/api/version/check` | Check for updates | `router_version.py` |

### OpenAI-Compatible

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **POST** | `/v1/chat/completions` | OpenAI-compatible chat | `router_openai.py` |
| **GET** | `/v1/models` | List models | `router_openai.py` |

### Helpdesk & Messaging

| Метод | Path | Описание | Module |
|-------|------|---------|--------|
| **GET** | `/api/helpdesk/tickets` | List support tickets | `router_helpdesk.py` |
| **POST** | `/api/helpdesk/tickets` | Create ticket | `router_helpdesk.py` |
| **WS** | `/api/helpdesk/ws/{id}` | Ticket WebSocket | `router_helpdesk.py` |
| **GET** | `/api/messenger/rooms` | List chat rooms | `router_messenger.py` |
| **WS** | `/api/messenger/ws/{id}` | Messenger WebSocket | `router_messenger.py` |

---

## 2. Примеры использования

### Chat API

```python
import requests

# Simple chat
response = requests.post('http://localhost:8000/api/chat', json={
    'message': 'Hello, world!',
    'model': 'gemini',
    'temperature': 0.7
})
print(response.json())
```

### RAG Search

```python
response = requests.post('http://localhost:8000/api/rag/search', json={
    'query': 'How to install the system?',
    'limit': 5
})
results = response.json()['results']
```

### MCP Tool Call

```python
response = requests.post('http://localhost:8000/api/mcp/call', json={
    'server': 'tool-server',
    'tool': 'fetch_data',
    'arguments': {'url': 'https://example.com'}
})
```

### TTS Synthesis

```python
response = requests.post('http://localhost:8000/api/tts/synthesize', json={
    'text': 'Hello world',
    'voice': 'en-US-AriaNeural',
    'rate': 1.0
})
audio_content = response.content  # Binary audio data
```

---

## 3. Аутентификация

### Google OAuth2 Flow

```
1. Перенаправить на /auth/google
2. Пользователь авторизуется через Google
3. Callback на /auth/callback?code=...
4. Получить JWT токен
5. Использовать токен в Authorization header:
   Authorization: Bearer <token>
```

### Check Auth Status

```python
response = requests.get('http://localhost:8000/auth/check')
if response.json()['authenticated']:
    print("Пользователь авторизован")
```

---

## 4. Обработка ошибок

### HTTP Status Codes

| Code | Описание |
|------|---------|
| 200 | OK — успешный ответ |
| 201 | Created — ресурс создан |
| 400 | Bad Request — ошибка в запросе |
| 401 | Unauthorized — требуется авторизация |
| 403 | Forbidden — доступ запрещён |
| 404 | Not Found — ресурс не найден |
| 500 | Internal Server Error — ошибка сервера |

### Error Response Format

```json
{
  "status": "error",
  "code": 400,
  "message": "Invalid parameter: model not supported",
  "details": {
    "parameter": "model",
    "allowed": ["gemini", "foundry", "ollama"]
  }
}
```

---

## 📚 Дополнительно

Для полного списка параметров каждого endpoint'а, смотрите:
- Документацию провайдера в `src/ai/providers/`
- Docstrings в `src/fastapi/router_*.py`
- Swagger UI: `http://localhost:8000/docs`

**Последнее обновление:** сентябрь 2026
