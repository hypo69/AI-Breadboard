# 📜 Windows System Log Center

Микросервис и интерактивный терминальный интерфейс для обнаружения, мониторинга, AI-диагностики и RAG-поиска по системным журналам Windows (Event Log).

---

## 🏛️ Архитектура

- **FastAPI Router**: Предоставляет REST и SSE/WebSocket API для просмотра и фильтрации журналов (`/api/v1/system_logs`).
- **Log Intelligence Pipeline**: Обработка, агрегация и корреляция системных событий и ошибок.
- **TUI Dashboard**: Консольный мониторинг в реальном времени.

---

## 🚀 Запуск

```powershell
# Запуск через специализированный launcher
.\launchers\Run-SystemLogViewer.ps1

# Прямой запуск через Python
python -m apps.system_log_viewer --mode server --port 8108
```
