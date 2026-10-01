# 📦 Windows Software & Package Manager

Модуль инвентаризации, поиска, установки, обновления и удаления пакетов программного обеспечения Windows (`winget.exe`, `msiexec.exe`, реестр Uninstall).

---

## 🚀 Возможности
- Инвентаризация установленных программ с версиями и источниками (WinGet, MS Store, MSI)
- Поиск пакетов в официальных репозиториях Windows Package Manager
- Проверка доступных обновлений ПО
- SafeOps симуляция (Dry-Run) установки и удаления пакетов

---

## 📡 REST API Эндпоинты (`/api/software-manager`)
- `GET /api/software-manager/report` — сводный отчет об установленном ПО и обновлениях
- `GET /api/software-manager/packages` — список установленных пакетов
- `GET /api/software-manager/search?q=git` — поиск пакета в репозитории
- `POST /api/software-manager/actions` — установка, обновление или удаление пакета

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.software_manager

# Поиск пакета
py -m apps.windows.modules.software_manager --json

# Запуск REST сервера
py -m apps.windows.modules.software_manager --mode server --port 8130
```
