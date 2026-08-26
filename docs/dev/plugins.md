# Плагины

Плагины позволяют расширять функциональность проекта без изменения основного кода.

## Базовый класс

```python
from plugins.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    
    async def handle(self, message: str) -> Optional[str]:
        """Handle message. Return None to pass to next plugin."""
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

## Доступные плагины

### 1. Media Layer

**Описание:** Управление медиа-слоями (субтитры, звуковые дорожки)

**Использование:**
```python
# В чате
"Включи субтитры"
"Переключи звук"
```

**Конфигурация:**
```json
{
  "subtitles": {
    "enabled": true,
    "size": 24,
    "color": "#FFFFFF"
  }
}
```

### 2. Media Organizer

**Описание:** Организация и аудит медиатеки

**Основные функции:**
- Сканирование дисков
- Классификация через AI
- Обнаружение дубликатов
- Регулярный аудит

**Использование:**
```python
from plugins.media_organizer.core.media_organizer import MediaScanner, MediaAuditor

scanner = MediaScanner()
scanner.scan_paths([Path("E:"), Path("L:")])

auditor = MediaAuditor(db, gemini=model)
issues = await auditor.audit()
```

### 3. QBittorrent

**Описание:** Управление qBittorrent

**Использование:**
```python
from plugins.qbittorrent.qbittorrent import QBittorrentClient

client = QBittorrentClient(
    host="localhost",
    port=8080,
    username="admin",
    password="adminadmin"
)

torrents = client.torrents()
client.add_torrent_by_url("magnet:?xt=urn:btih:...")
```

**API Endpoints:**
- `GET /api/torrents` — список торрентов
- `POST /api/torrents/download` — скачивание
- `POST /api/torrents/relocate` — перемещение
- `POST /api/torrents/assign-categories` — назначение категорий

### 4. RAG

**Описание:** RAG (Retrieval-Augmented Generation) поиск

**Использование:**
```python
from plugins.media_organizer.media_rag import build_media_rag, rag_search_tool

# Построение индекса
rag = build_media_rag(api_key="key_name")

# Поиск
results = rag_search_tool("фильм про войну", top_k=5)
```

### 5. Telegram Bot

**Описание:** Telegram-бот для управления

**Использование:**
```python
from plugins.telegram_bot.telegram_bot import TelegramBot

bot = TelegramBot(token="your_token")
await bot.start()

# Обработка сообщений
@bot.on_message
async def handle_message(message):
    await bot.send_message(message.chat.id, "Hello!")
```

**Команды:**
- `/start` — запуск
- `/help` — справка
- `/status` — статус плеера

### 6. Torrent Playwright

**Описание:** Поиск и скачивание торрентов через Playwright

**Использование:**
```python
from plugins.torrent_playwright.playwright_searcher import PlaywrightTorrentSearcher

searcher = PlaywrightTorrentSearcher()
file_content = await searcher.download_torrent_file("1337x", "https://example.com")
```

## Создание собственного плагина

### 1. Создайте директорию

```
plugins/my_plugin/
├── __init__.py
├── plugin.py
└── README.md
```

### 2. Создайте файл plugin.py

```python
from __future__ import annotations

from typing import Optional
from plugins.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    description = "My custom plugin"
    
    def __init__(self, ai_model):
        self.ai_model = ai_model
        self.config = {}
    
    async def handle(self, message: str) -> Optional[str]:
        """Handle message from chat."""
        if message.startswith("my_command"):
            return "Response to my_command"
        return None
    
    async def start(self):
        """Start plugin."""
        print("Plugin started")
    
    async def stop(self):
        """Stop plugin."""
        print("Plugin stopped")
    
    async def setup(self) -> bool:
        """Setup plugin."""
        return True
    
    async def teardown(self):
        """Cleanup plugin."""
        pass

def plugin(ai_model) -> MyPlugin:
    """Factory function to create plugin instance."""
    return MyPlugin(ai_model)
```

### 3. Загрузка плагина

Плагин будет автоматически загружен при запуске, если он находится в `plugins/` директории.

## Конфигурация плагинов

Плагины могут иметь собственную конфигурацию:

```python
class MyPlugin(BasePlugin):
    name = "my_plugin"
    
    def __init__(self, ai_model, config_path: Path = None):
        self.config_path = config_path or Path(__file__).parent / "config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.config_path.exists():
            import json
            return json.loads(self.config_path.read_text())
        return {}
```

## Порядок загрузки

Плагины загружаются в следующем порядке:

1. `media_layer`
2. `media_organizer`
3. `qbittorrent`
4. `rag`
5. `telegram_bot`
6. `torrent_playwright`

## Обработка сообщений

Плагины обрабатывают сообщения последовательно:

```python
for plugin in plugins.values():
    response = await plugin.handle(request.message)
    if response:
        return {'response': response}  # Плагин обработал сообщение
# Сообщение не обработано, передаётся в AI
```

---

[← API Reference](api-reference.md) | [Development →](development.md)