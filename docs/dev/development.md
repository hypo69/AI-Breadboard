# Разработка

## Настройка окружения

### 1. Клонирование репозитория

```bash
git clone https://github.com/hypo69/ai-assistant.git
cd ai-assistant
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Установка плагинов Playwright

```bash
cd .mcp/playwright
npm install
npx playwright install-deps
npx playwright install
cd ../../..
```

## Структура проекта

```
core/
├── ai/                    # AI модули
│   ├── __init__.py
│   └── gemini/           # Google Gemini интеграция
│       ├── __init__.py
│       └── gemini.py
├── fastapi/              # FastAPI приложение
│   ├── __init__.py
│   ├── config.json       # Конфигурация
│   ├── router_auth.py    # Аутентификация
│   ├── router_chat.py    # Чат с AI
│   ├── router_control.py # WebSocket управление
│   ├── router_media.py   # Управление медиатекой
│   └── router_qbittorrent.py
├── logger/               # Логирование
│   ├── __init__.py
│   ├── logger.py
│   └── README.MD
├── media_granularity.py  # Управление медиа-таймингами
├── secrets/              # Управление секретами
│   ├── __init__.py
│   └── api_key_state.py
├── user_manager/         # Управление пользователями
│   ├── __init__.py
│   └── user_manager.py
└── utils/                # Утилиты
    ├── file.py
    ├── date_time.py
    ├── jjson.py
    ├── smtp.py
    └── ...
```

## Работа с базой данных

### Создание миграций

```python
from plugins.media_organizer.core.database import MediaDatabase

db = MediaDatabase("media.db")

# Создание таблиц
db.create_tables()

# Экспорт данных
records = db.export_all()
```

### Работа с TMDB

```python
from plugins.media_organizer.core.media_organizer import TMDBClient

tmdb = TMDBClient("your_api_key")

# Получение информации о фильме
movie = tmdb.get_movie("tt0109830")

# Поиск
results = tmdb.search_movie("Matrix")
```

## Работа с API ключами

```python
from core.secrets.api_key_state import load_api_keys, update_last_run

# Загрузка ключей
api_keys, key_names, key_states = load_api_keys()

# Обновление статуса использования
update_last_run("key_name")
```

## Тестирование

### Unit тесты

```bash
pip install pytest pytest-asyncio

pytest tests/ -v
```

### Тесты API

```bash
# Запуск сервера
python main.py

# Запуск тестов
pytest tests/api/ -v
```

### Тесты плагинов

```bash
pytest tests/plugins/ -v
```

## CI/CD

### GitHub Actions

Конфигурация в `.github/workflows/`:

- `docs.yml` — сборка и деплой документации

### Локальная сборка документации

```bash
# Установка mkdocs
pip install mkdocs mkdocs-material mkdocstrings

# Сборка
mkdocs build

# Локальный сервер
mkdocs serve
```

## Логирование

```python
from core.logger import logger

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

### Уровни логирования

| Уровень | Описание |
|---------|----------|
| DEBUG | Отладочная информация |
| INFO | Информационные сообщения |
| WARNING | Предупреждения |
| ERROR | Ошибки |
| CRITICAL | Критические ошибки |

## Отладка

### VS Code launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: main.py",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

### Chrome DevTools

1. Откройте `chrome://inspect`
2. Найдите ваше приложение
3. Откройте DevTools

## Продакшен деплоймент

См. [Deployment](deployment.md) для подробной информации.

---

[← Plugins](plugins.md) | [Deployment →](deployment.md)