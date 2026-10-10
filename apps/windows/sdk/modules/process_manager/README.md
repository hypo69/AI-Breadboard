# ⚡ Windows Process & Memory Manager

Модуль мониторинга, профилирования и безопасного завершения процессов Windows (`tasklist.exe`, `taskkill.exe`, Psapi / Toolhelp32 Win32 API).

---

## 🚀 Возможности
- Получение списка активных процессов, PID, пользователей, потоков, CPU% и потребления RAM
- Топ процессов по утилизации процессора и оперативной памяти
- Завершение процессов по PID или завершение всего дерева процессов
- Поддержка SafeOps режима Dry-Run и обязательного подтверждения

---

## 📡 REST API Эндпоинты (`/api/process-manager`)
- `GET /api/process-manager/report` — сводный отчет о процессах и топах нагрузки
- `GET /api/process-manager/list` — список процессов с фильтрацией по имени
- `POST /api/process-manager/kill` — завершение процесса по PID

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.sdk.modules.process_manager

# Запуск REST сервера
py -m apps.windows.sdk.modules.process_manager --mode server --port 8125
```
