# API Reference

## FastAPI Endpoints

### Authentication

#### POST `/api/auth/login`

Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
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

#### GET `/api/auth/me`

Get current user information.

**Headers:**
```
Authorization: Bearer jwt_token_here
```

### Chat

#### POST `/api/chat`

Send message to AI.

**Request Body:**
```json
{
  "message": "Какой фильм посмотреть?"
}
```

**Response:**
```json
{
  "response": "Рекомендую посмотреть 'Начало' Кристофера Нолана."
}
```

### Control

#### WebSocket `/api/control/ws`

WebSocket connection for player control.

**Connection Parameters:**
- `role`: "player" or "remote"
- `token`: JWT token (optional)
- `room`: Room ID (email or custom)

**Messages:**

From Remote to Player:
```json
{
  "event": "play",
  "file": "/path/to/movie.mkv"
}
{
  "event": "pause"
}
{
  "event": "volume",
  "level": 80
}
```

From Player to Remote:
```json
{
  "event": "status_update",
  "state": "playing",
  "position": 123.45,
  "duration": 7200
}
{
  "event": "playlist_update",
  "files": [...]
}
```

#### GET `/api/control/status`

Get control status for a room.

**Query Parameters:**
- `token`: JWT token (optional)
- `room`: Room ID (default: "default")

### Media Admin

#### POST `/api/media-admin/scan`

Scan media files.

**Request Body:**
```json
{
  "disk": "1",
  "paths": ["E:", "L:"],
  "key": "api_key_name"
}
```

**Response:**
```json
{
  "status": "started",
  "disk": "ДИСК 1"
}
```

#### GET `/api/media-admin/scan/status`

Get scan status.

#### POST `/api/media-admin/audit`

Audit media database.

**Request Body:**
```json
{
  "disk": "1",
  "paths": ["E:"]
}
```

**Response:**
```json
{
  "issues": [...],
  "total": 5,
  "audit_file": "path/to/audit.md"
}
```

#### POST `/api/media-admin/rag/build`

Build RAG index.

**Request Body:**
```json
{
  "key": "api_key_name"
}
```

#### POST `/api/media-admin/rag/search`

Search via RAG.

**Request Body:**
```json
{
  "query": "фильм про войну",
  "top_k": 5,
  "key": "api_key_name"
}
```

### Media

#### GET `/api/media/files`

List all media files.

#### POST `/api/media/by-title`

Find media by title.

**Request Body:**
```json
{
  "title": "Титаник",
  "type": "movie"
}
```

**Response:**
```json
{
  "title": "Титаник",
  "path": "E:\\Films\\Titanic.mkv",
  "type": "movie",
  "year": "1997"
}
```

#### GET `/api/media/by-category`

List media by categories.

### Torrents

#### GET `/api/torrents`

List all torrents.

#### POST `/api/torrents/download`

Download torrent.

**Request Body:**
```json
{
  "url": "magnet:?xt=urn:btih:...",
  "title": "Movie Name",
  "source": "1337x"
}
```

#### POST `/api/torrents/relocate`

Relocate torrent files.

**Request Body:**
```json
{
  "dirs": ["E:", "L:"]
}
```

### Admin

#### GET `/api/admin/system_instruction`
Get system instruction.

#### POST `/api/admin/system_instruction`
Update system instruction.

#### GET `/api/admin/plugin/{plugin_name}/status`
Get plugin status.

#### POST `/api/admin/plugin/{plugin_name}/status`
Update plugin status.

### Keys

#### GET `/api/keys`
List all API keys.

#### GET `/api/keys/{key_name}`
Get key status.

#### POST `/api/keys`
Create new API key.

#### DELETE `/api/keys/{key_name}`
Delete API key.

#### PATCH `/api/keys/{key_name}`
Update API key.

#### POST `/api/keys/{key_name}/reset-quota`
Reset API key quota.

### Logs

#### GET `/api/logs/files`
List log files.

#### GET `/api/logs/read`
Read log file content.

#### DELETE `/api/logs/clear`
Clear logs.

#### POST `/api/logs/analyze`
Analyze logs.

#### GET `/api/logs/reports`
List log reports.

#### GET `/api/logs/report`
Get specific log report.

#### GET `/api/logs/stats`
Get log statistics.

### TTS (Text-to-Speech)

#### GET `/api/tts/stream-text`
Stream text.

#### GET `/api/tts/synthesize`
Synthesize speech.

#### GET `/api/tts/stream-audio`
Stream audio.

#### GET `/api/tts/file/{filename}`
Get TTS audio file.

## Plugins API

### BasePlugin

Base class for all plugins.

```python
from plugins.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    
    async def handle(self, message: str) -> Optional[str]:
        """Handle message, return None to pass to next plugin."""
        if message.startswith("my_command"):
            return "Response"
        return None
    
    async def start(self):
        """Start plugin."""
        pass
    
    async def stop(self):
        """Stop plugin."""
        pass
```

### Available Plugins

#### Media Layer Plugin

```python
# Access via plugins["media_layer"]
```

#### QBittorrent Plugin

```python
# Access via plugins["qbittorrent"]
```

#### Telegram Bot Plugin

```python
# Access via plugins["telegram_bot"]
```

#### RAG Plugin

```python
# Access via plugins["rag"]
```

## Database API

### MediaDatabase

```python
from plugins.media_organizer.core.database import MediaDatabase

# Initialize
db = MediaDatabase("media.db")

# Get records
records = db.export_all()
movies = db.export_movies()
series = db.export_series()

# Get by category
movies_by_cat = db.export_by_category("Боевики")

# Find by title
result = db.find_by_title("Титаник")

# Find duplicates
duplicates = db.find_duplicates()

# Audit
issues = await auditor.audit()
```

## Configuration

### config.json

```json
{
  "host": "0.0.0.0",
  "port": 3000,
  "index_path": "html/index.html",
  "tg_mini_app": {
    "url": "https://your-domain.com/tgmini",
    "name": "ai-assistant",
    "description": "AI Assistant"
  },
  "google_oauth": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "http://localhost:3000/auth/google/callback"
  }
}
```

### search_dirs.json

```json
{
  "dirs": ["E:", "L:", "M:"]
}
```

## Events

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `play` | Remote → Player | Start playback |
| `pause` | Remote → Player | Pause playback |
| `stop` | Remote → Player | Stop playback |
| `volume` | Remote → Player | Set volume (0-100) |
| `seek` | Remote → Player | Seek to position (seconds) |
| `status_update` | Player → Remote | Update status |
| `playlist_update` | Player → Remote | Update playlist |
| `metadata_update` | Player → Remote | Update metadata |

### API Events

| Event | Description |
|-------|-------------|
| `scan_started` | Media scan started |
| `scan_completed` | Media scan completed |
| `audit_completed` | Audit completed |
| `rag_indexed` | RAG index built |

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict (e.g., scan already running) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (e.g., qBittorrent) |

---

[← Architecture](architecture.md) | [Plugins →](plugins.md)