# Google Cloud Monitor

Инструмент для мониторинга облачной инфраструктуры Google Cloud Platform (GCP).

---

## 🎯 Назначение

`gcloud_monitor` — это микроприложение для наблюдения и администрирования ресурсов GCP. Позволяет:
- Мониторить логи (Cloud Logging).
- Отслеживать метрики (Cloud Monitoring).
- Проводить аудит безопасности (Cloud Audit Logs).
- Анализировать ошибки (Error Reporting).

---

## 🚀 Основные возможности

- Интерактивный терминальный интерфейс (TUI) для мониторинга.
- Сбор логов в реальном времени с поддержкой фильтрации.
- Визуализация метрик и событий.
- Диагностика причин неисправностей (AI-assisted).

---

## 💻 Запуск

### TUI-дашборд
```powershell
python -m apps.gcloud_monitor
```

### Сервер API
```powershell
python -m apps.gcloud_monitor --mode server --port 8105
```
