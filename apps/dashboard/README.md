# 🎛️ Сводная диагностическая панель (Windows Diagnostic Dashboard)

**Пакет:** `apps.dashboard`  
**Назначение:** Единый центр управления всеми специализированными инструментами мониторинга и низкоуровневой диагностики системы Windows.

---

## 🚀 Возможности
- **Сводный обзор системы:** Моментальный статус состояния подсистем (процессы, память, сервисы, сеть, безопасность).
- **Координация модулей:** Интеграция Process Explorer, Performance Monitor, Network Diagnostics, Services Manager, Registry Viewer, Security Analyzer, Hardware Explorer, Baseline Detector и Realtime Monitor.
- **Интерактивный терминал:** Быстрый доступ к каждому инструменту из единого интерактивного CLI.

---

## 💻 Использование через CLI

```powershell
# Запуск панели управления
python -m apps.dashboard
```

Доступные команды:
- `overview` — Вывести сводную сводку состояния системы
- `modules` — Показать список загруженных диагностических модулей
- `status` — Статус готовности панели
- `processes` — Запуск Process Explorer
- `performance` — Запуск Performance Monitor
- `network` — Запуск Network Diagnostics
- `services` — Запуск Services Manager
- `exit` — Выход из приложения
