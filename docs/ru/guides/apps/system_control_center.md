# Центр управления системой (`apps/windows/system_control_center`)

**Статус:** ✅ Активно  
**Язык:** Русский (документация) / Английский (код)  
**Автор:** hypo69  
**Пакет:** `apps.windows.system_control_center`

---

## 📋 Обзор

**Центр управления системой** — микросервис и интерактивный терминальный интерфейс для администрирования Windows: управление электропитанием, точками восстановления, системными профилями и оптимизацией.

---

## 🏛️ Архитектура

- **FastAPI Router**: REST API для управления (`/api/system-control`).
- **Safe Executor**: Безопасный запуск действий (dry-run) и расчет рисков.
- **TUI Dashboard**: Консольный мониторинг.

---

## 🚀 Запуск

```powershell
# Запуск через специализированный launcher
.\launchers\Run-SystemControlCenter.ps1

# Прямой запуск через Python
python -m apps.windows.system_control_center --mode server --port 8109
```
