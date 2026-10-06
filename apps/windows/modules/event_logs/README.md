# 📜 Windows Event Log Manager & Log Intelligence

Модуль инспекции, анализа ошибок, экспорта, очистки каналов журналов событий Windows (`WevtAPI`, `wevtutil.exe`) и интеграции аналитического ядра **Log Intelligence** (`apps/windows/log_intelligence`).

---

## 🚀 Возможности
- Инвентаризация системных и операционных каналов событий (System, Application, Security, Setup)
- Быстрая выборка недавних системных ошибок (Error, Critical)
- **Log Intelligence (EDA ➔ Decision Gate ➔ Adaptive RAG)**:
  - Вычисление коэффициента избыточности ($R_{dup}$) и индекса здоровья ($SHI$)
  - Выявление аномалий и частотных всплесков (Rate Spikes)
  - Двуязычный семантический и ключевой поиск по адаптивному RAG-индексу логов
- Бинарный экспорт каналов в `.evtx` и безопасная очистка журналов
- Веб-интерфейс, TUI дашборд и REST API

---

## 📡 REST API Эндпоинты (`/api/event-logs`)
- `GET /api/event-logs/report` — сводный отчет журналов и счетчик ошибок за 24 часа
- `GET /api/event-logs/channels` — список зарегистрированных каналов
- `GET /api/event-logs/events` — выборка нормализованных событий из канала
- `GET /api/event-logs/errors` — выборка последних зафиксированных ошибок
- `GET /api/event-logs/intelligence/profile` — запуск EDA профилирования и Decision Gate
- `POST /api/event-logs/intelligence/search` — гибридный поиск по адаптивной базе знаний RAG
- `GET /api/event-logs/intelligence/audit` — полный статистический аудит канала
- `POST /api/event-logs/actions` — экспорт или очистка канала

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.event_logs

# Запуск REST сервера
py -m apps.windows.modules.event_logs --mode server --port 8129
```
