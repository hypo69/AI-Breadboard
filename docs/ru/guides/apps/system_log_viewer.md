# Просмотр системных журналов (`apps/system_log_viewer`)

**Статус:** ✅ Активно  
**Язык:** Русский (документация) / Английский (код)  
**Автор:** hypo69  
**Пакет:** `apps.system_log_viewer`

---

## 📋 Обзор

**Просмотр системных журналов** — микросервис и терминальный интерфейс для обнаружения, мониторинга, ИИ-диагностики и RAG-поиска по журналам Windows (Event Log).

---

## 🏛️ Архитектура

- **FastAPI Router**: REST и WebSocket API (`/api/v1/system_logs`).
- **Log Intelligence Pipeline**: Обработка, агрегация и корреляция событий.
- **TUI Dashboard**: Консольный мониторинг в реальном времени.

---

## 🚀 Запуск

```powershell
# Запуск через специализированный launcher
.\launchers\Run-SystemLogViewer.ps1

# Прямой запуск через Python
python -m apps.system_log_viewer --mode server --port 8108
```
