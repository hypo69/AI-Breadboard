# 📜 Windows Event Log Manager

Модуль инспекции, анализа ошибок, экспорта и очистки каналов журналов событий Windows (`wevtutil.exe`, `wecutil.exe`, WevtAPI).

---

## 🚀 Возможности
- Инвентаризация системных и операционных каналов событий (System, Application, Security, Setup)
- Быстрая выборка недавних системных ошибок (Error, Critical)
- Бинарный экспорт каналов в `.evtx` и безопасная очистка журналов
- TUI дашборд и REST API

---

## 📡 REST API Эндпоинты (`/api/event-logs`)
- `GET /api/event-logs/report` — сводный отчет журналов и счетчик ошибок за 24 часа
- `GET /api/event-logs/channels` — список зарегистрированных каналов
- `GET /api/event-logs/errors` — выборка последних зафиксированных ошибок
- `POST /api/event-logs/actions` — экспорт или очистка канала

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.event_logs

# Запуск REST сервера
py -m apps.windows.modules.event_logs --mode server --port 8129
```
