# 🛠️ Windows System Control Center

Микросервис и интерактивный терминальный интерфейс для администрирования, управления электропитанием, точками восстановления, системными профилями и оптимизацией Windows.

---

## 🏛️ Архитектура

- **FastAPI Router**: Предоставляет REST API для управления системой, выполнения скриптов SafeOps и применения профилей post-install (`/api/system-control`).
- **Safe Executor**: Безопасный запуск действий с симуляцией (dry-run) и расчетом рисков.
- **TUI Dashboard**: Консольный мониторинг состояния системы.

---

## 🚀 Запуск

```powershell
# Запуск через специализированный launcher
.\launchers\Run-SystemControlCenter.ps1

# Прямой запуск через Python
python -m apps.windows.system_control_center --mode server --port 8109
```
