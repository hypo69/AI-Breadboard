# ⚙️ Windows Services Control Center

Модуль управления, аудита и мониторинга системных служб Windows (Service Control Manager, `sc.exe`, `net.exe`, Advapi32 SCM API).

---

## 🚀 Возможности
- Инвентаризация всех служб Windows, текущего статуса (RUNNING, STOPPED, PAUSED) и типов запуска
- Проверка учетных записей запуска (LocalSystem, NetworkService, LocalService)
- Запуск, остановка и смена типа автозапуска служб с валидацией SafeOps
- Консольный TUI дашборд и REST API

---

## 📡 REST API Эндпоинты (`/api/services-manager`)
- `GET /api/services-manager/report` — сводный отчет о состоянии служб
- `GET /api/services-manager/list` — список всех служб (с фильтром `?status=RUNNING`)
- `POST /api/services-manager/actions` — запуск, остановка или изменение типа автозапуска

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.services_manager

# Запуск REST сервера
py -m apps.windows.modules.services_manager --mode server --port 8123
```
