# Модуль плагинов

## Загрузка плагинов

```python
from plugins import load_plugins

plugins = load_plugins(model)
```

## Базовый класс

```python
from plugins.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    
    async def handle(self, message: str) -> Optional[str]:
        return None
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
```

## Доступные плагины

| Плагин | Описание |
|--------|----------|
| `media_layer` | Управление медиа-слоями (субтитры, звук) |
| `media_organizer` | Организация и аудит медиатеки |
| `movie_search_sources` | Каталог источников для просмотра |
| `qbittorrent` | Управление qBittorrent |
| `rag` | RAG поиск по медиатеке |
| `telegram_bot` | Telegram бот для управления |
| `torrent_playwright` | Поиск и скачивание торрентов |
| `user_manager_tool` | Управление пользователями |
| `web_search` | Веб-поиск через Playwright |
| `yt_dlp` | Скачивание видео/аудио через yt-dlp |

## Пример плагина

```python
from __future__ import annotations

from typing import Optional
from plugins.plugin import BasePlugin

class MediaSearchPlugin(BasePlugin):
    name = "media_search"
    
    async def handle(self, message: str) -> Optional[str]:
        if " найди фильм " in message:
            title = message.replace(" найди фильм ", "").strip()
            return f"Нашел фильм: {title}"
        return None

def plugin(ai_model) -> MediaSearchPlugin:
    return MediaSearchPlugin(ai_model)
```

---

[← Меню](../index.md) | [API Reference →](../dev/api-reference.md)