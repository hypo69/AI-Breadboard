# Служба технической поддержки (Helpdesk)

## Назначение
Полнофункциональное автономное приложение и рабочий терминал службы технической поддержки для AI Breadboard. Поддерживает управление тикетами, приоритизацию, внутренние заметки, WebSocket-чат и аналитику SLA.

## Структура
```
apps/helpdesk/
├── __init__.py           # Экспорт роутера
├── __main__.py           # CLI точка входа
├── config.json           # Конфигурация порта, SLA и категорий
├── router.py             # FastAPI REST & WebSocket endpoints
├── tui.py                # Rich-интерфейс оператора
└── tests/                # Тесты
```

## Запуск

### Интерактивный TUI консоли
```powershell
python -m apps.helpdesk
```

### Запуск микросервиса
```powershell
python -m apps.helpdesk --mode server --port 8110
```

### Статистика
```powershell
python -m apps.helpdesk --stats
python -m apps.helpdesk --list
```

## API

Базовый префикс: `/api/v1/helpdesk` и `/api/helpdesk`

| Эндпоинт | Описание |
|---|---|
| `GET /api/helpdesk/tickets` | Список обращений |
| `POST /api/helpdesk/tickets` | Создание заявки |
| `PATCH /api/helpdesk/tickets/{id}` | Обновление заявки |
| `GET /api/helpdesk/stats` | Сводная статистика |
| `WS /api/helpdesk/ws/{id}` | Real-time уведомления |
