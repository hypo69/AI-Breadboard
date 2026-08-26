# Модуль `core.fastapi` — Маршрутизация HTTP и WebSocket

## Назначение
Пакет предоставляет набор FastAPI APIRouter для обслуживания веб-интерфейсов и API-эндпоинтов. Всего 10 роутеров:

| Роутер | Описание | Префикс |
|--------|----------|---------|
| `router_chat.py` | WebSocket и SSE эндпоинты для интерактивного чата с UnifiedChatModel | `/api/chat` |
| `router_media.py` | API доступа к медиатеке, потоковой трансляции, карточкам тайтлов | `/api/media` |
| `router_qbittorrent.py` | API управления торрент-клиентом (поиск, добавление, статус) | `/api/torrents` |
| `router_auth.py` | Аутентификация через Google OAuth2, локальный вход | `/auth` |
| `router_control.py` | WebSocket шлюз дистанционного управления плеером | `/ws/control` |
| `router_tts.py` | Синтез речи и выбор голосов для озвучки | `/api/tts` |
| `router_logs.py` | Просмотр и анализ журналов событий | `/api/logs` |
| `router_keys.py` | Проверка состояния и переключение API-ключей | `/api/keys` |
| `router_admin.py` | Эндпоинты панели системного администратора | `/admin`, `/api/admin` |
| `router_agents.py` | API управления AI агентами и их конфигурациями | `/api/agents` |

## Архитектура

### Инициализация роутеров
Каждый роутер предоставляет функцию инициализации `init_router()` или `init_<name>_router()`. Основной модуль `__init__.py` экспортирует все функции инициализации для использования в `main.py`.

### Общие принципы
1. **Префиксы API**: Все API эндпоинты используют префикс `/api/`
2. **Аутентификация**: Защищенные эндпоинты проверяют сессию через `router_auth`
3. **Валидация**: Входные данные валидируются через Pydantic модели
4. **Обработка ошибок**: Все исключения обрабатываются с возвратом корректных HTTP статусов
5. **Логирование**: Операции логируются через `core.logger.logger`

### Новый роутер агентов (`router_agents.py`)
Предоставляет REST API для управления AI агентами:
- Создание, чтение, обновление, удаление конфигураций агентов
- Тестирование агентов с различными параметрами
- Генерация промптов и шаблонов для агентов
- Интеграция с UnifiedChatModel и системой плагинов

## Интеграция с UnifiedChatModel
Все AI-запросы обрабатываются через `UnifiedChatModel`, который предоставляет единый интерфейс для:
- Google Gemini
- Microsoft AI Foundry
- AGY SDK
- Ollama локальные модели

Роутер чата автоматически выбирает оптимального провайдера на основе конфигурации и доступности.

## Документация OpenAPI
Автоматически генерируемая документация доступна по адресу:
- `http://localhost:3000/api/docs` — Swagger UI
- `http://localhost:3000/api/redoc` — ReDoc

## Примеры использования

```python
# Инициализация всех роутеров в main.py
from core.fastapi import (
    init_auth_router,
    init_chat_router,
    init_qbt_router,
    init_media_admin_router,
    init_control_router,
    init_tts_router,
    init_logs_router,
    init_keys_router,
    init_admin_router,
    init_agents_router
)

app = FastAPI()

# Подключение роутеров
app.include_router(init_auth_router(), prefix="/auth")
app.include_router(init_chat_router(model, plugins), prefix="/api")
app.include_router(init_qbt_router(), prefix="/api")
# ... остальные роутеры
```

## Правила разработки
1. Новые роутеры должны следовать существующей структуре
2. Все эндпоинты должны быть документированы через Pydantic модели
3. Обработка ошибок должна возвращать информативные сообщения
4. Интеграция с существующими системами (аутентификация, логирование) обязательна