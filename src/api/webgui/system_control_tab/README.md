# 🛠️ System Control Center Web Interface Tab

**Путь:** `src/api/webgui/system_control_tab/`  
**Статус:** ✅ Активно (Русский стандарт)  
**Автор:** hypo69  

---

## 📋 Обзор

Вкладка **System Control Center (Центр управления системой)** предоставляет административную веб-панель, интегрированную в интерфейс `/tc` и `/apps` AI Breadboard.

---

## 🏛️ Архитектура и подразделы

Вкладка состоит из `index.html` и `main.js`, экспортируя функцию `window.initSystemControlTab()` для переключения вкладок и управления жизненным циклом.

### Подразделы:
1. **📊 1. Monitoring:** Телеметрия хоста в реальном времени, статус Windows Defender, профили брандмауэра, режим UAC и метрики дисковых накопителей.
2. **⚡ 2. Post-Install Wizard:** Пошаговое выполнение контрольных списков настройки (*Windows Post-Install Baseline*, *Security Hardening*, *Developer Workstation*).
3. **🛠️ 3. Maintenance & Recovery:** Безопасная очистка временного кэша, проверка целостности системных файлов (SFC), проверка хранилища компонентов DISM и создание точек восстановления Windows.
4. **📋 4. Activity Log:** Журнал аудита всех операций и выполненных действий (все события и изменения сохраняются в логах).

---

## 🔗 Backend API

Взаимодействует с FastAPI бэкендом по префиксу `/api/system-control`:
- `GET /api/system-control/status`
- `GET /api/system-control/profiles`
- `POST /api/system-control/profiles/apply`
- `POST /api/system-control/maintenance/cleanup`
- `POST /api/system-control/maintenance/sfc`
- `POST /api/system-control/maintenance/dism`
- `GET /api/system-control/restore-points`
- `POST /api/system-control/restore-points`
- `GET /api/system-control/logs`
