# Рефакторинг структуры приложения

## Выполнено: Объединение /app и src/app

### Проблема
Проект имел дублирующуюся структуру приложения:
- `/app` (в корне) — содержал state.py, middleware.py, cors.py, ws_hub.py, metrics.py, routes.py
- `src/app` — содержал альтернативную реализацию с __init__.py, initialization.py, config_api.py

Это создавало путаницу и усложняло поддержку кода.

### Решение
Все модули объединены в единую структуру `src/app/`:

```
src/app/
├── __init__.py          # Фабрика приложения + регистрация роутеров
├── state.py             # AppState dataclass
├── middleware.py        # HTTP middleware (auto_login, metrics)
├── cors.py              # CORS конфигурация
├── metrics.py           # MetricsCollector (Prometheus)
├── ws_hub.py            # WebSocket hub для real-time коммуникации
├── config_api.py        # API конфигурации AI провайдеров
├── versioning.py        # Проверка обновлений
├── server_config.py     # Конфигурация uvicorn сервера
├── routers/             # Дополнительные роутеры (auto-discovery)
└── pages/               # UI страницы
```

### Изменения в API

#### Старый подход (до рефакторинга)
```python
from src.app import create_app, register_pages, register_config_api

app = create_app()  # Роутеры регистрировались внутри
register_pages(app)
register_config_api(app)
```

#### Новый подход (после рефакторинга)
```python
from src.app import (
    create_app,
    register_routers,
    register_pages,
    register_config_api,
    AppState,
    create_metrics,
    WSHub,
)

# 1. Создаём приложение
app = create_app()

# 2. Инициализируем состояние
state = AppState()
state.metrics = create_metrics(started_at=state.started_at)
state.ws_hub = WSHub()

# 3. Сохраняем в app.state
app.state.app_state = state
app.state.metrics = state.metrics
app.state.ws_hub = state.ws_hub

# 4. Инициализируем модели
state.chat_model = UnifiedChatModel()
state.narrator_model = UnifiedChatModel()

# 5. Регистрируем роутеры с инжекцией состояния
register_routers(app, state)
register_pages(app)
register_config_api(app)
```

### Преимущества новой архитектуры

1. **Единая точка истины** — все модули приложения в `src/app/`
2. **Явное управление состоянием** — AppState содержит все сервисы
3. **Инжекция зависимостей** — роутеры получают модели через параметры
4. **Расширяемость** — легко добавлять новые сервисы в AppState
5. **Тестируемость** — можно создавать mock-объекты для AppState

### Изменённые файлы

- `main.py` — обновлён для использования новой структуры
- `src/app/__init__.py` — объединена логика создания приложения
- `src/app/state.py` — новый модуль для AppState
- `src/app/middleware.py` — перенесён из /app
- `src/app/cors.py` — перенесён из /app
- `src/app/metrics.py` — перенесён из /app
- `src/app/ws_hub.py` — перенесён из /app
- `tests/test_fastapi.py` — обновлены импорты

### Удалено

- `/app/` — старая директория полностью удалена

### Доступ к сервисам из роутеров

```python
from fastapi import Request

async def some_handler(request: Request):
    # Доступ к сервисам через app.state
    chat_model = request.app.state.chat_model
    ws_hub = request.app.state.ws_hub
    metrics = request.app.state.metrics
    
    # Или через app_state
    state = request.app.state.app_state
    model = state.chat_model
```

### Middleware

Оба middleware автоматически активируются при создании приложения:

1. **auto_login_local_user** — автоматическая аутентификация для localhost
2. **metrics_middleware** — сбор метрик запросов

### WebSocket Hub

WebSocket hub автоматически запускается при старте приложения:

```python
@app.on_event("startup")
async def startup_event():
    if state.ws_hub:
        await state.ws_hub.start_heartbeat()

@app.on_event("shutdown")
async def shutdown_event():
    if state.ws_hub:
        await state.ws_hub.stop()
```

## Миграция для разработчиков

Если вы импортировали модули из `/app/`:

**Было:**
```python
from app.state import AppState
from app.cors import build_cors_config
from app.middleware import is_localhost
```

**Стало:**
```python
from src.app.state import AppState
from src.app.cors import build_cors_config
from src.app.middleware import is_localhost
```

Или используйте удобные реэкспорты:

```python
from src.app import AppState, build_cors_config
```

## Совместимость

Все существующие роутеры и функциональность сохранены. Изменения касаются только внутренней структуры проекта.
