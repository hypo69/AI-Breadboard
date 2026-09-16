# Helpdesk Support Desk (`apps/helpdesk`)

**Статус:** ✅ Активен  
**Порт по умолчанию:** `8110`  
**Префикс API:** `/api/v1/helpdesk` и `/api/helpdesk`  
**База данных:** `data/helpdesk.db`  

---

## 📋 Описание

`apps.helpdesk` — полнофункциональное автономное приложение и рабочий терминал службы технической поддержки для AI Breadboard.
Поддерживает управление жизненным циклом обращений (тикеты), приоритизацию, внутренние служебные заметки оператора, живой WebSocket-чат и аналитику SLA.

---

## 🏛️ Архитектура

```
apps/helpdesk/
├── __init__.py           # Экспорт роутера
├── __main__.py           # CLI точка входа (TUI, server, stats, list)
├── config.json           # Конфигурация порта, SLA и категорий
├── router.py             # FastAPI REST & WebSocket endpoints (/api/v1/helpdesk)
├── tui.py                # Rich-интерфейс оператора
├── README.md             # Документация приложения
└── tests/
    ├── __init__.py
    └── test_helpdesk_app.py # Модульные тесты
```

---

## 🚀 Запуск и использование

### 1. Интерактивный TUI консоли
```powershell
python -m apps.helpdesk
```

### 2. Запуск выделенного микросервиса
```powershell
# Запуск через PowerShell лончер
.\launchers\Run-Helpdesk.ps1

# Или через CLI
python -m apps.helpdesk --mode server --port 8110
```

### 3. Просмотр статистики и списка тикетов
```powershell
python -m apps.helpdesk --stats
python -m apps.helpdesk --list
python -m apps.helpdesk --stats --json
```

---

## 📡 API Endpoints

- `GET /api/helpdesk/tickets` — получение списка обращений с фильтрацией
- `POST /api/helpdesk/tickets` — создание новой заявки
- `GET /api/helpdesk/tickets/{id}` — получение переписки по обращению
- `POST /api/helpdesk/tickets/{id}/messages` — отправка ответа или внутренней заметки
- `PATCH /api/helpdesk/tickets/{id}` — изменение статуса, приоритета или ответственного
- `GET /api/helpdesk/stats` — сводная статистика для дашборда
- `WS /api/helpdesk/ws/{client_id}` — WebSocket для real-time уведомлений
