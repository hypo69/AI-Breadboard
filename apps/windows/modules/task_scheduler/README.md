# ⏰ Windows Task Scheduler Manager

Модуль управления, аудита и запуска запланированных заданий Windows Task Scheduler (`schtasks.exe`, COM ITaskService API).

---

## 🚀 Возможности
- Инвентаризация всех заданий в дереве планировщика Windows
- Просмотр времени последнего и следующего запуска, авторов и триггеров
- Запуск, остановка, включение и безопасное удаление заданий
- TUI дашборд и REST API

---

## 📡 REST API Эндпоинты (`/api/task-scheduler`)
- `GET /api/task-scheduler/report` — сводный отчет о заданиях
- `GET /api/task-scheduler/tasks` — список заданий (с фильтрацией `?state=Ready`)
- `POST /api/task-scheduler/actions` — запуск или изменение состояния задания

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.task_scheduler

# Запуск REST сервера
py -m apps.windows.modules.task_scheduler --mode server --port 8124
```
