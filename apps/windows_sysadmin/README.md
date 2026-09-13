# 🪟 Windows System Administrator

Интерактивный инструмент для управления Windows-системами, мониторинга пользовательских сессий, управления учетными записями, проверки политики групп и мониторинга событий безопасности.

## 📋 Оглавление
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Использование](#использование)
- [FastAPI endpoints](#fastapi-endpoints)
- [Конфигурация](#конфигурация)

---

## Возможности

- **Мониторинг пользовательских сессий** — просмотр активных пользователей, время входа, IP-адреса, количество процессов
- **События безопасности** — отслеживание событий Windows Event Log (4624, 4688, 4720 и др.)
- **Статус Active Directory** — проверка подключения к домену и статус AD
- **FastAPI REST API** — программный доступ к всей функциональности
- **Интерактивная TUI** — визуализация данных в терминале с Rich

---

## Архитектура

```
apps/windows_sysadmin/
├── src/
│   └── state.py          # Бизнес-логика: SystemAdminState, UserSession, SecurityEvent
├── tui.py                # TUI-рендерер и интерактивный dashboard
├── router.py             # FastAPI endpoints для REST API
├── __main__.py           # Точка входа (CLI + standalone server)
├── __init__.py           # Экспорт пакета
└── config.json           # Конфигурация сервера (порт 8100)
```

**Разделение ответственности:**
- `src/state.py` — чистая бизнес-логика (модели данных, состояние)
- `tui.py` — TUI-рендеринг и взаимодействие с пользователем
- `router.py` — FastAPI HTTP-роутеры и обработчики запросов
- `__main__.py` — CLI-интерфейс и запуск standalone-сервера

---

## Установка

```bash
cd apps/windows_sysadmin
pip install -r ../../requirements.txt
pip install rich  # Для TUI-интерфейса
```

---

## Использование

### Интерактивный dashboard (TUI)

```bash
python -m apps.windows_sysadmin
```

Клавиши управления:
- `Q` — выход
- `U` — отображение пользователей
- `E` — события безопасности
- `A` — информация о AD
- `R` — обновление данных

### FastAPI сервер

```bash
python -m apps.windows_sysadmin --mode server
```

По умолчанию сервер запускается на `http://127.0.0.1:8100`.

Доступные эндпоинты:
- `/api/sysadmin/status` — общий статус
- `/api/sysadmin/users` — список пользователей
- `/api/sysadmin/events` — события безопасности
- `/api/sysadmin/users/{username}` — информация о пользователе
- `/api/sysadmin/ad/status` — статус Active Directory

### CLI-команды

```bash
# Проверка AD
python -m apps.windows_sysadmin --ad-status

# Мониторинг событий
python -m apps.windows_sysadmin --security-events --hours 24

# Аудит пользователей
python -m apps.windows_sysadmin --audit users --domain CORP

# JSON output
python -m apps.windows_sysadmin --json
```

---

## FastAPI endpoints

### `GET /api/sysadmin/status`

```json
{
  "hostname": "WORKSTATION",
  "domain": "WORKGROUP",
  "ad_connected": false,
  "ad_status": "Disconnected",
  "user_count": 2,
  "event_count": 3
}
```

### `GET /api/sysadmin/users`

```json
{
  "users": [
    {
      "username": "Administrator",
      "session_id": 1,
      "status": "Active",
      "login_time": "2024-01-15T10:30:00",
      "ip_address": "127.0.0.1",
      "process_count": 23
    }
  ]
}
```

### `GET /api/sysadmin/events`

```json
{
  "events": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "event_id": 4624,
      "level": "Information",
      "source": "Security",
      "description": "An account was successfully logged on."
    }
  ]
}
```

### `POST /api/sysadmin/users/{username}/disconnect`

Отключение пользователя (требует права администратора).

---

## Конфигурация

Файл `config.json`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8100,
    "use_ssl": false,
    "workers": 1
  },
  "cors": {
    "allow_origins": [],
    "allow_origin_regex": null,
    "allow_credentials": true,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
  }
}
```

### Порт по умолчанию

Каждое приложение запускается на своем порту:
- `windows_sysadmin`: **8100**
- `network_terminal`: **8101**
- `system_inspector`: **8102**

### CLI-переопределение

Параметры можно переопределить через CLI:

```bash
python -m apps.windows_sysadmin --mode server --port 9000 --host 0.0.0.0
```

---

## Развёртывание

### Режим разработки (с авто-перезагрузкой)

```bash
python -m apps.windows_sysadmin --mode server --reload
```

### Продакшн (многопроцессный)

```bash
python -m apps.windows_sysadmin --mode server --workers 4
```

---

## Лицензия

© 2026 hypo69. Все права защищены.
