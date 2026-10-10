# 📈 Windows Performance & Tracing Manager

Модуль сбора счетчиков производительности в реальном времени (`typeperf.exe`, PDH API) и управления сборщиками данных трассировки событий ETW (`logman.exe`).

---

## 🚀 Возможности
- Моментальный замер счетчиков CPU%, памяти, длины очередей диска и сетевой активности
- Управление сессиями и сборщиками данных Data Collector Sets (start, stop, query)
- TUI интерфейс и REST API

---

## 📡 REST API Эндпоинты (`/api/performance-tracing`)
- `GET /api/performance-tracing/report` — сводный отчет производительности
- `GET /api/performance-tracing/counters` — моментальные значения счетчиков
- `GET /api/performance-tracing/collectors` — список сборщиков данных ETW
- `POST /api/performance-tracing/collectors/actions` — запуск или остановка сборщика

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.sdk.modules.performance_tracing

# Запуск REST сервера
py -m apps.windows.sdk.modules.performance_tracing --mode server --port 8128
```
