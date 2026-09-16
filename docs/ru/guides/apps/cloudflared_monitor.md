# Монитор Cloudflare Tunnel (Cloudflared Monitor)

## Назначение
Мониторинг и управление Cloudflare Tunnel (`cloudflared`). Обеспечивает наблюдение за процессом демона, потоковую передачу и парсинг логов (`logs/cloudflared.log`), проверку задержки общедоступных конечных точек и эвристическую диагностику состояния.

## Структура
```
apps/cloudflared_monitor/
├── __init__.py                # Инициализация и экспорт
├── __main__.py                # CLI (дашборд, сервер, диагностика)
├── config.json                # Конфигурация (порты, эндпоинты)
├── router.py                  # API эндпоинты
├── tui.py                     # Дашборд TUI
└── src/                       # Логика супервизора
```

## Запуск

### Интерактивный TUI
```powershell
python -m apps.cloudflared_monitor
```

### Автономный API сервер
```powershell
python -m apps.cloudflared_monitor --mode server --port 8104
```

### CLI инструменты
- `--status` — Проверка статуса
- `--health` — Диагностика состояния
- `--logs` — Просмотр последних логов
- `--restart` — Перезапуск

## API

Базовый префикс: `/api/cloudflared`

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/status` | Статус процесса, токена, эндпоинта |
| `GET` | `/logs` | Парсинг логов с фильтрацией |
| `GET` | `/metrics` | Метрики (CPU, RAM, сеть) |
| `GET` | `/diagnostic` | Диагностика состояния и аномалий |
| `POST` | `/test-endpoint` | HTTP probe для публичной URL |
| `POST` | `/start`/`/stop`/`/restart` | Управление демоном |
