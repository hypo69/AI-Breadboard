# 🛡️ Windows Servicing & Component Integrity

Модуль верификации защищенных системных файлов (Windows Resource Protection, SFC) и обслуживания хранилища компонентов (DISM Component Store, WinSxS).

---

## 🚀 Возможности
- Проверка и восстановление системных файлов (`sfc.exe /scannow`, `/verifyonly`)
- Анализ маркеров повреждения и восстановление Component Store (`DISM.exe /RestoreHealth`)
- Инвентаризация и управление дополнительными компонентами Windows (Optional Features)
- SafeOps симуляция (Dry-Run) тяжелых сервисных операций

---

## 📡 REST API Эндпоинты (`/api/servicing-integrity`)
- `GET /api/servicing-integrity/report` — сводный отчет целостности файлов и DISM
- `GET /api/servicing-integrity/features` — список компонентов Windows
- `POST /api/servicing-integrity/actions` — запуск или симуляция SFC/DISM операций

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.sdk.modules.servicing_integrity

# Запуск REST сервера
py -m apps.windows.sdk.modules.servicing_integrity --mode server --port 8122
```
