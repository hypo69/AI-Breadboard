# Real-Time Messenger & Multi-User Meeting Room Module

The `src/fastapi/messenger` package provides an enterprise-grade, real-time messaging, group chat, and WebRTC video/audio conferencing solution with triple backend deployment capabilities (FastAPI native, standalone microservice, and WordPress SSO sync bridge).

---

## 🌟 Key Features

1. **Telegram & WhatsApp Experience:**
   - Real-time instant messaging via WebSockets.
   - Voice audio recording & inline audio player.
   - Image, video, and file attachment handling.
   - Read receipts (`sent`, `delivered`, `read`) and typing indicators.
   - Direct chats (1-on-1), group rooms, channels, and meeting rooms.
2. **WebRTC Multi-User Meeting Rooms:**
   - 1-on-1 audio/video calling.
   - Meeting room signaling (screen sharing, camera toggle, microphone mute).
3. **WordPress Integration & SSO:**
   - HMAC-SHA256 authenticated webhook sync for WordPress users.
   - JWT SSO exchange for seamless 1-click authentication from WordPress.
4. **AI & RAG Bot Integration:**
   - Mention `@ai`, `@breadboard`, or `@bot` in any room to trigger AI responses with RAG context.

---

## 📁 Package Structure

```
src/fastapi/messenger/
├── __init__.py           # Package exports & router factory
├── database.py           # SQLite / PostgreSQL schema & connection pool
├── models.py             # Pydantic data schemas & WebRTC packets
├── router_messenger.py   # REST & WebSocket endpoints
├── sync_bridge.py        # WordPress webhook & SSO token generator
├── ws_manager.py         # WebSocket connection hub & WebRTC signaling
└── README.md             # Documentation
```

---

## 🚀 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `WS` | `/api/messenger/ws/{user_id}` | Real-time WebSocket connection |
| `GET` | `/api/messenger/rooms` | List active user chat rooms |
| `POST` | `/api/messenger/rooms` | Create a new room / direct chat |
| `GET` | `/api/messenger/rooms/{id}/messages` | Fetch paginated message history |
| `POST` | `/api/messenger/rooms/{id}/messages` | Send a message via REST |
| `POST` | `/api/messenger/upload` | Upload media files and voice notes |
| `GET` | `/api/messenger/users/search` | Search user directory |
| `POST` | `/api/messenger/sync/user` | WordPress user sync webhook |
| `POST` | `/api/messenger/sync/sso-token` | WordPress SSO token exchange |
| `GET` | `/api/messenger/admin/stats` | Admin moderation statistics |
