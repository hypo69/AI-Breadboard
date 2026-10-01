# 🔄 Windows Boot & Recovery Manager

Модуль управления хранилищем данных конфигурации загрузки (BCD), таймаутом диспетчера загрузки, безопасным режимом и средой аварийного восстановления Windows Recovery Environment (WinRE).

---

## 🚀 Возможности
- Чтение и парсинг всех загрузочных записей BCD
- Управление таймаутом ожидания меню загрузчика
- Проверка и переключение среды восстановления WinRE (`reagentc.exe`)
- Поддержка симуляции SafeOps изменений перед записью в системный BCD

---

## 📡 REST API Эндпоинты (`/api/boot-recovery`)
- `GET /api/boot-recovery/report` — сводка конфигурации BCD и WinRE
- `GET /api/boot-recovery/entries` — список записей загрузчика
- `GET /api/boot-recovery/winre` — статус и путь к образу WinRE
- `POST /api/boot-recovery/actions` — выполнение или симуляция действий (timeout, safemode, winre toggle)

---

## 🖥️ Использование через CLI
```powershell
# Просмотр TUI
py -m apps.windows.modules.boot_recovery

# Запуск REST сервера
py -m apps.windows.modules.boot_recovery --mode server --port 8121
```
