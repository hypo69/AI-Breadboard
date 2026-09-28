---
name: dlq
description: Dead Letter Queue (DLQ) manager and interactive TUI dashboard for monitoring, retrying, and purging failed tasks or API errors.
description_i18n:
  en: Dead Letter Queue (DLQ) manager and interactive TUI dashboard for monitoring, retrying, and purging failed tasks or API errors.
  ru: Управление тупиковой очередью (DLQ) и интерактивный TUI дашборд для мониторинга, повтора и очистки сбойных задач ИИ.
---

# 🚨 DLQ (Dead Letter Queue) Skill

Этот навык обеспечивает перехват, хранение, интерактивный просмотр и обработку ошибочных вызовов, необработанных задач субагентов и таймаутов сетевых запросов.

---

## 🎯 Когда активировать навык

Используйте этот навык, если пользователь запрашивает:
- Просмотр сбойных сообщений или ошибочных запросов (`покажи dlq`, `что упало в очередь`, `проверь невыполненные задачи`).
- Интерактивный TUI мониторинг (`запусти tui dlq`, `покажи консольный дашборд ошибок`, `tui dlq`).
- Добавление сбоя в очередь, изменение статуса или повтор обработки задачи из DLQ.

---

## 🚀 Протокол использования

### 1. Интерактивный TUI Дашборд
Для запуска визуального интерфейса в консоли:

```powershell
py .agents/skills/dlq/scripts/tui.py
```

Или однократный рендеринг дашборда:
```powershell
py .agents/skills/dlq/scripts/tui.py --once
```

---

### 2. CLI Менеджер управления

#### Добавить запись в DLQ:
```powershell
py .agents/skills/dlq/scripts/manager.py push --source "gemini-cli" --error "Timeout connecting to provider" --payload '{"attempt": 1}'
```

#### Просмотр списка сбойных записей:
```powershell
py .agents/skills/dlq/scripts/manager.py list
```

#### Просмотр в формате JSON:
```powershell
py .agents/skills/dlq/scripts/manager.py list --json
```

#### Повторная попытка (Retry):
```powershell
py .agents/skills/dlq/scripts/manager.py retry --id 1
```

#### Очистить решенные или все записи:
```powershell
py .agents/skills/dlq/scripts/manager.py purge --status RESOLVED
```

---

## 🛠️ Программная интеграция из Python

```python
from .agents.skills.dlq.scripts.storage import DLQStorage

storage = DLQStorage()

# Сохранить ошибку
msg_id = storage.push(
    source="my-subagent",
    error_message="HTTP 503 Service Unavailable",
    payload={"url": "https://api.example.com/v1"}
)

# Получить список нерешенных ошибок
pending = storage.list_all(status="PENDING")
```

---

## 📊 Статусная модель
- `PENDING`: Ошибка зарегистрирована, ожидает анализа.
- `RETRYING`: Задача находится в процессе повторного выполнения.
- `RESOLVED`: Задача успешно обработана.
- `FAILED`: Фатальная ошибка, повторная обработка невозможна.
