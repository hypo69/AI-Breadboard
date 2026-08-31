# Документация плагинов ai-assistant

## Общее описание

Плагинная архитектура ai-assistant состоит из 11 Moduleных компонентов, каждый из которых расширяет функциональность системы. Все плагины наследуются от `BasePlugin`, поддерживают динамическую загрузку и интеграцию с `UnifiedChatModel`.

## List плагинов

### 1. **media_organizer** — Управление медиатекой 🎬
**Категория:** Медиатека  
**Status:** Обязательный (ядерный)

#### Назначение
Центральный плагин для управления медиатекой:
- Сканирование дисков и файловой структуры
- Разметка метаданных через TMDB и Gemini API
- Управление базой данных SQLite
- RAG-Integration для семантического поиска
- Генерация отчетов и аналитика

#### Configuration
```json
{
  "media_organizer": {
    "enabled": true,
    "config": {
      "db_path": "plugins/media_organizer/data/media.db",
      "tmdb_api_key": "${TMDB_API_KEY}",
      "rag_enabled": true,
      "auto_scan": false,
      "scan_interval_hours": 24,
      "categories": [
        "Боевики", "Триллеры", "Приключения", "Драмы",
        "Семейные", "Исторические", "Расследования", "Шпионы",
        "Мюзиклы", "Документальные"
      ]
    }
  }
}
```

#### API эндпоинты
- `POST /api/media/scan` — Сканирование дисков
- `GET /api/media/card/{id}` — Карточка медиа
- `POST /api/media/by-title` — Поиск по названию
- `GET /api/media/stats` — Статистика медиатеки

#### Integration с AI
- Function Calling: `search_media`, `get_media_card`, `get_random_media`
- Автоматическая классификация через Gemini
- Генерация описаний и метаданных

### 2. **rag** — Семантический поиск медиа 🔍
**Категория:** Поиск  
**Status:** Обязательный (ядерный)

#### Назначение
Семантический поиск по медиатеке с использованием RAG (Retrieval-Augmented Generation):
- Векторизация запросов через Gemini Embeddings
- Поиск в FAISS индексе
- Function Calling для интеграции с AI моделями
- "Карусель" случайных рекомендаций

#### Configuration
```json
{
  "rag": {
    "enabled": true,
    "config": {
      "index_path": "rag/faiss_index",
      "embedding_model": "gemini",
      "top_k": 10,
      "similarity_threshold": 0.7,
      "enable_function_calling": true,
      "cache_enabled": true
    }
  }
}
```

#### Триггеры
- "фильм", "кино", "сериал", "мультфильм"
- "посоветуй", "рекомендация", "что посмотреть"
- "поиск", "найди", "искать"

#### Integration с AI
- Автоматическое определение медиа-запросов
- Function Calling для точного поиска
- Потоковый вывод результатов

### 3. **media_layer** — Облегченный слой доступа 📁
**Категория:** Медиатека  
**Status:** Опциональный

#### Назначение
Упрощенный доступ к базе данных медиатеки:
- Быстрый поиск по названию и категориям
- Filtering по типам, годам, жанрам
- Статистика и аналитика
- Экспорт данных

#### Особенности
- Не требует сканирования дисков
- Работает с существующей БД
- Оптимизирован для быстрых запросов
- Минимальные зависимости

### 4. **web_search** — Веб-поиск через Playwright 🌐
**Категория:** Веб  
**Status:** Опциональный

#### Назначение
Поиск информации в интернете с AI-анализом:
- Асинхронный поиск через Playwright
- Поддержка DuckDuckGo и других поисковых систем
- AI-суммаризация результатов
- Структурированный вывод

#### Configuration
```json
{
  "web_search": {
    "enabled": true,
    "config": {
      "search_engine": "duckduckgo",
      "max_results": 10,
      "timeout_seconds": 30,
      "summarize_enabled": true,
      "sources": ["wikipedia", "imdb", "kinopoisk"]
    }
  }
}
```

#### Триггеры
- "погугли", "поищи в интернете", "найди информацию"
- "кто такой", "что такое", "когда вышел"
- "новости", "статьи", "обзоры"

### 5. **torrent_playwright** — Поиск торрентов 🧲
**Категория:** Торренты  
**Status:** Опциональный

#### Назначение
Поиск и filtering торрентов через браузерную автоматизацию:
- Поддержка Rutracker и NNMClub
- AI-filtering результатов
- Оценка качества раздач
- Integration с qBittorrent

#### Configuration
```json
{
  "torrent_playwright": {
    "enabled": true,
    "config": {
      "trackers": ["rutracker", "nnmclub"],
      "min_seeders": 10,
      "max_results": 20,
      "quality_filter": true,
      "ai_filtering": true
    }
  }
}
```

#### Триггеры
- "торрент", "скачать", "раздача"
- "magnet", "torrent файл"
- "сериал скачать", "фильм скачать"

### 6. **movie_search_sources** — Источники для просмотра 📺
**Категория:** Источники  
**Status:** Опциональный

#### Назначение
Каталог streaming-сервисов и онлайн-кинотеатров:
- Поиск где посмотреть фильм/сериал
- Info о доступности на платформах
- Сравнение цен и подписок
- Рекомендации сервисов

#### Поддерживаемые сервисы
- Netflix, Amazon Prime, Disney+
- Кинопоиск HD, IVI, More.tv
- YouTube, Twitch, VK Video
- Торрент-трекеры (альтернатива)

### 7. **qbittorrent** — Управление qBittorrent ⚡
**Категория:** Торренты  
**Status:** Обязательный (ядерный)

#### Назначение
Полная Integration с торрент-клиентом qBittorrent:
- Управление Loadingми и состоянием
- Категории и теги
- Мониторинг прогресса
- Автоматическая организация

#### Configuration
```json
{
  "qbittorrent": {
    "enabled": true,
    "config": {
      "host": "localhost",
      "port": 8080,
      "username": "${QBT_USER}",
      "password": "${QBT_PASS}",
      "categories": {
        "movies": "Фильмы",
        "series": "Сериалы",
        "music": "Музыка",
        "other": "Другое"
      }
    }
  }
}
```

#### API эндпоинты
- `GET /api/torrents/` — List торрентов
- `POST /api/torrents/add` — Добавление торрента
- `POST /api/torrents/search` — Поиск торрентов
- `GET /api/torrents/categories` — Управление категориями

### 8. **telegram_bot** — Telegram Mini App 🤖
**Категория:** Коммуникация  
**Status:** Опциональный

#### Назначение
Удаленное управление медиатекой через Telegram:
- Telegram Bot API Integration
- Mini App интерфейс
- Уведомления и оповещения
- Управление воспроизведением

#### Configuration
```json
{
  "telegram_bot": {
    "enabled": true,
    "config": {
      "token": "${TELEGRAM_BOT_TOKEN}",
      "webhook_url": "https://ваш-домен.com/telegram",
      "admin_ids": [123456789],
      "notifications_enabled": true
    }
  }
}
```

#### Функции
- Управление плеером через Telegram
- Получение уведомлений о новых медиа
- Быстрый доступ к часто используемым функциям
- Integration с голосовыми командами

### 9. **user_manager_tool** — Управление пользователями 👥
**Категория:** Пользователи  
**Status:** Опциональный

#### Назначение
Управление пользователями и сессиями:
- Регистрация и authentication
- Управление профилями и настройками
- История активности
- Аналитика использования

#### База данных
```sql
-- Таблица users
id, username, email, created_at, last_login, preferences

-- Таблица sessions  
user_id, session_token, created_at, expires_at, user_agent
```

#### Команды чата
- `!list_users` — List пользователей
- `!user_activity` — Активность пользователей
- `!create_user` — Создание пользователя
- `!delete_user` — Удаление пользователя

### 10. **yt_dlp** — Скачивание видео/аудио 📥
**Категория:** Loading  
**Status:** Опциональный

#### Назначение
Скачивание медиаконтента с различных платформ:
- Поддержка YouTube, Vimeo, Twitch и других
- Конвертация форматов (mp4, mp3, etc.)
- Прогресс-бар и уведомления
- Integration с медиатекой

#### Configuration
```json
{
  "yt_dlp": {
    "enabled": true,
    "config": {
      "download_path": "downloads/",
      "default_format": "best",
      "extract_audio": false,
      "audio_format": "mp3",
      "max_duration_minutes": 120
    }
  }
}
```

#### Триггеры
- "скачай", "загрузи", "download"
- "youtube", "видео", "аудио"
- "mp3", "mp4", "конвертировать"

### 11. **langchain_media** — LangChain медиа-инструменты 🧠
**Категория:** AI  
**Status:** Опциональный (новый)

#### Назначение
Integration с LangChain для расширенного AI анализа:
- LangChain агенты для анализа медиа
- Цепочки обработки контента
- Автоматическая категоризация
- Генерация метаданных

#### Configuration
```json
{
  "langchain_media": {
    "enabled": true,
    "config": {
      "llm_provider": "gemini",
      "tools": ["search", "calculator", "web_search"],
      "memory_enabled": true,
      "max_iterations": 10
    }
  }
}
```

#### Триггеры
- "лангчейн", "агент", "цепочка"
- "проанализируй", "классифицируй", "структурируй"
- "создай отчет", "генерация контента"

### 12. **plugin_manager** — Управление плагинами ⚙️
**Категория:** Система  
**Status:** Обязательный (системный)

#### Назначение
Централизованное управление плагинами:
- Включение/выключение плагинов
- Configuration через веб-интерфейс
- Мониторинг состояния
- Update и установка

#### API эндпоинты
- `GET /api/admin/plugins` — List плагинов
- `POST /api/admin/plugins/{name}/toggle` — Включить/выключить
- `GET /api/admin/plugins/{name}/config` — Configuration
- `POST /api/admin/plugins/{name}/config` — Update конфигурации

## Динамическая Loading плагинов

### Процесс загрузки
```python
# plugins/__init__.py
def load_plugins(ai_model) -> dict[str, BasePlugin]:
    plugins = {}
    
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
            continue
        
        # Импорт модуля
        module = importlib.import_module(f'plugins.{plugin_dir.name}')
        
        # Создание экземпляра
        plugin_instance = module.plugin(ai_model)
        
        # Определение статуса
        is_disabled_by_env = plugin_dir.name in disabled_env
        is_enabled_by_cfg = plugins_cfg.get(plugin_instance.name, {}).get('enabled', True)
        
        plugin_instance.enabled = (not is_disabled_by_env) and is_enabled_by_cfg
        plugins[plugin_instance.name] = plugin_instance
    
    return plugins
```

### Конфигурационные источники
1. **config.json** — Основная Configuration
2. **.env** — Переменные окружения (DISABLED_PLUGINS)
3. **Веб-интерфейс** — Динамическое управление
4. **API** — Программное управление

## Integration с UnifiedChatModel

### Function Calling
Каждый плагин может предоставлять инструменты для AI моделей:

```python
class MediaOrganizerPlugin(BasePlugin):
    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_media",
                    "description": "Поиск медиа по названию",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "type": {"type": "string", "enum": ["movie", "series"]},
                            "year": {"type": "integer"},
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                }
            }
        ]
```

### Автоматическое определение плагина
```python
def _is_plugin_query(message: str, plugins: dict) -> Optional[BasePlugin]:
    """Определяет, какой плагин должен обработать запрос"""
    message_lower = message.lower()
    
    for plugin in plugins.values():
        if not plugin.enabled:
            continue
        
        # Check триггеров
        triggers = plugin.get_manifest().get('triggers', [])
        for trigger in triggers:
            if trigger in message_lower:
                return plugin
        
        # Check через AI классификацию
        if plugin.should_handle(message):
            return plugin
    
    return None
```

## Потоковый вывод

### Формат потокового ответа
```python
async def handle(self, message: str, **kwargs):
    # Начало обработки
    yield {"status": "start", "plugin": self.name}
    
    # Промежуточные статусы
    yield {"status": "processing", "progress": 25, "message": "Поиск в БД..."}
    yield {"status": "processing", "progress": 50, "message": "Анализ результатов..."}
    
    # Финальный результат
    yield {
        "status": "complete",
        "progress": 100,
        "text": "Результаты поиска: ...",
        "data": {...},
        "format": "html"  # или "json", "text", "markdown"
    }
    
    # Error
    # yield {"status": "error", "error": "Описание ошибки"}
```

### Поддержка форматов
1. **HTML** — Для веб-интерфейса
2. **JSON** — Для API клиентов
3. **Text** — Для простого текста
4. **Markdown** — Для форматированного текста

## Мониторинг и отладка

### Логирование
```python
from core.logger import logger

logger.info(f"Плагин {self.name}: Начало обработки запроса")
logger.debug(f"Плагин {self.name}: Parameters: {kwargs}")
logger.error(f"Плагин {self.name}: Error обработки", exc_info=True)
```

### Метрики
- Количество запросов к плагину
- Среднее время выполнения
- Количество ошибок
- Status плагина (enabled/disabled)

### Health check
```python
async def health_check(self) -> dict:
    return {
        "name": self.name,
        "enabled": self.enabled,
        "status": "healthy" if self._check_health() else "unhealthy",
        "last_check": datetime.now().isoformat(),
        "dependencies": self._check_dependencies()
    }
```

## Разработка новых плагинов

### Шаги разработки
1. **Создание структуры** — Новая директория в `plugins/`
2. **Реализация BasePlugin** — Наследование и методы
3. **Configuration** — Файл `config.json`
4. **Документация** — `README.md` в директории плагина
5. **Тестирование** — Moduleные и интеграционные тесты
6. **Регистрация** — Манифест и Integration

### Пример нового плагина
```
plugins/new_feature/
├── __init__.py          # plugin() фабрика
├── plugin.py           # Основной class
├── config.json         # Configuration
├── README.md          # Документация
├── requirements.txt    # Зависимости
└── tests/             # Тесты
    ├── test_plugin.py
    └── __init__.py
```

### Тестирование
```python
# tests/test_new_feature.py
import pytest
from plugins.new_feature import NewFeaturePlugin

@pytest.mark.asyncio
async def test_plugin_handle():
    plugin = NewFeaturePlugin(ai_model_mock)
    
    # Тест обработки сообщения
    async for chunk in plugin.handle("тестовый запрос"):
        assert "status" in chunk
        assert "text" in chunk
    
    # Тест манифеста
    manifest = plugin.get_manifest()
    assert manifest["name"] == "new_feature"
    assert manifest["enabled"] == True
```

## Устранение неполадок

### Распространенные проблемы

#### Плагин не загружается
1. Проверить наличие `__init__.py` с функцией `plugin()`
2. Проверить наследование от `BasePlugin`
3. Проверить переменную окружения `DISABLED_PLUGINS`
4. Проверить логи на ошибки импорта

#### Плагин не processes запросы
1. Проверить триггеры в манифесте
2. Проверить method `should_handle()`
3. Проверить что плагин enabled
4. Проверить интеграцию с роутером чата

#### Ошибки в потоковом выводе
1. Использовать `yield` вместо `return`
2. Правильный формат выходных данных
3. Обработка исключений внутри генератора
4. Check интеграции с SSE/WebSocket

#### Проблемы с конфигурацией
1. Проверить `config.json` на валидность JSON
2. Проверить переменные окружения
3. Проверить права доступа к файлам
4. Проверить загрузку конфигурации в коде

## Миграция и обновления

### Update конфигурации
При изменении структуры конфигурации:
1. Сохранить старую конфигурацию
2. Предоставить миграционный скрипт
3. Обновить документацию
4. Протестировать обратную совместимость

### Добавление новых полей в манифест
1. Обновить `BasePlugin.get_manifest()` если нужно
2. Обновить все существующие плагины
3. Обновить веб-интерфейс для отображения новых полей
4. Протестировать обратную совместимость

---

**Последнее update:** 24 августа 2026  
**Всего плагинов:** 12 (5 обязательных, 7 опциональных)  
**Архитектура:** Moduleная, расширяемая, с динамической загрузкой  
**Integration:** UnifiedChatModel, REST API, веб-интерфейсы