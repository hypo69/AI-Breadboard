# API модуль

## FastAPI Endpoints

### Основные endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/chat` | POST | Чат с AI |
| `/api/control/ws` | WS | WebSocket управление |
| `/api/media/*` | GET/POST | Управление медиатекой |
| `/api/torrents/*` | GET/POST | Управление торрентами |

### Специализированные endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/auth/login` | POST | Аутентификация |
| `/api/auth/me` | GET | Информация о пользователе |
| `/api/media-admin/*` | GET/POST | Админ управление |

## WebSocket

### Подключение

```javascript
const ws = new WebSocket(
  `ws://localhost:3000/api/control/ws?role=remote&room=${room_id}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Формат сообщений

```json
{
  "event": "play|pause|stop|volume|seek",
  "file": "/path/to/file",
  "level": 80,
  "position": 123.45
}
```

---

[← Меню](../index.md) | [Media Organizer →](media-organizer.md)