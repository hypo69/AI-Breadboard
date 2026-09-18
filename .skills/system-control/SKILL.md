---
name: system-control
description: Windows System Control Center, maintenance and setup
description_i18n:
  en: Windows System Control Center, maintenance and setup
  ru: Центр управления системой Windows, обслуживание и настройка
---

# Навык: System Control

## 🎯 Назначение
Навык `system-control` обеспечивает взаимодействие с центром управления системой (`apps/system_control_center`) и модулем `SafeSystemParamManager`. Предназначен для выполнения задач по настройке после установки, создания контрольных точек восстановления (Windows Restore Points), безопасного изменения системных параметров с автоматическим созданием точек восстановления перед модификацией чувствительных настроек, обслуживания (DISM/SFC) и управления безопасностью.

## 🚀 Протокол безопасного изменения параметров (SafeOps Protocol)
1. **Анализ чувствительности**: Перед изменением любого системного параметра агент определяет уровень риска (`SAFE`, `CAUTION`, `CRITICAL`) и признак `is_sensitive`.
2. **Предварительный просмотр (Dry-Run)**: Запрос симуляции (`preview_change` или `py manage_tools.py sys-param preview <id> <val>`) для оценки последствий.
3. **Обязательная точка восстановления**: При модификации любого чувствительного параметра (`is_sensitive=True` или риск `CAUTION`/`CRITICAL`) система в обязательном порядке автоматически создает новую точку восстановления Windows (`Checkpoint-Computer` / WMI `SystemRestore`) и сохраняет снимок состояния до применения изменений.
4. **Применение и валидация**: Применение нового значения через API или CLI и проверка успешности записи.
5. **Откат (Rollback)**: При сбое или по запросу пользователя выполняется откат к сохраненному в журнале значению или вызов восстановления системы.

## 🛠️ Основные команды и API
- `py manage_tools.py sys-param list` — Просмотр каталога параметров с флагами чувствительности и рисками.
- `py manage_tools.py sys-param preview <param_id> <value>` — Симуляция изменения параметра (Dry-Run).
- `py manage_tools.py sys-param set <param_id> <value>` — Безопасное изменение параметра с автоматической точкой восстановления.
- `py manage_tools.py sys-param restore-points` — Список существующих точек восстановления Windows.
- `py manage_tools.py sys-param create-rp "<description>"` — Ручное создание точки восстановления.
- `py manage_tools.py sys-param history` — Журнал изменений параметров и привязанных точек восстановления.
- `py manage_tools.py sys-param rollback <change_id>` — Откат выполненного изменения.

## 🌐 API эндпоинты
- `GET /api/system-control/params`
- `POST /api/system-control/params/preview`
- `POST /api/system-control/params/apply`
- `GET /api/system-control/params/history`
- `POST /api/system-control/params/rollback`
- `GET /api/system-control/restore-points`
- `POST /api/system-control/restore-points`

## ⚠️ Важное замечание
Все операции с критическими параметрами системы Windows требуют повышенных привилегий (Run as Administrator).

