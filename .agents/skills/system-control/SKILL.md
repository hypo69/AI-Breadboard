---
name: system-control
description: Windows System Control Center, maintenance, post-install setup and SafeOps parameter management
description_i18n:
  en: Windows System Control Center, maintenance, post-install setup and SafeOps parameter management
  ru: Центр управления системой Windows: регламентное обслуживание, SafeOps параметры и точки восстановления
---

# ⚙️ Навык: Windows System Control Center (Maintenance & SafeOps)

## 🎯 Назначение
Навык `system-control` обеспечивает управление регламентным обслуживанием операционной системы Windows через модуль `apps/windows/sdk/modules/system_control_center`, подсистемы `servicing_integrity`, `boot_recovery`, `startup` и менеджер `SafeSystemParamManager` (`apps/windows/sdk/core/system_param_manager.py`).

---

## 🏗️ Архитектура подсистем обслуживания (`apps/windows/sdk`)

- **`system_control_center`** (`apps/windows/sdk/modules/system_control_center`):
  - Унифицированный диспетчер регламентных операций, проверка готовности хоста.
- **`servicing_integrity`** (`apps/windows/sdk/modules/servicing_integrity`):
  - Проверка и восстановление целостности системных файлов (`sfc /scannow`, `DISM /Online /Cleanup-Image /RestoreHealth`).
  - Анализ логов CBS (`%windir%\Logs\CBS\CBS.log`).
- **`system_param_manager`** (`apps/windows/sdk/core/system_param_manager.py`):
  - SafeOps протокол изменения системных параметров реестра и политик (телеметрия, автообновления, гибернация, сетевые параметры).
  - Автоматическое создание снимков состояния и точек восстановления перед чувствительными правками (`is_sensitive=True`).
- **`system_restore`** (`apps/windows/sdk/core/system_restore.py`):
  - Создание, удаление, листинг и откат к контрольным точкам Windows System Restore.
- **`boot_recovery`** (`apps/windows/sdk/modules/boot_recovery`):
  - Аудит конфигурации BCD (`bcdedit`), статуса WinRE, безопасного режима.
- **`startup`** (`apps/windows/sdk/modules/startup`):
  - Комплексный аудит всех веток автозагрузки (реестр `Run`/`RunOnce`, папки автозапуска, запланированные задачи).

---

## 🚀 Протокол безопасного изменения параметров (SafeOps Protocol)

1. **Анализ чувствительности**: Определение уровня риска (`SAFE`, `CAUTION`, `CRITICAL`) и флага `is_sensitive`.
2. **Предварительный просмотр (Dry-Run)**: Симуляция применения параметров без записи.
3. **Обязательная точка восстановления**: Автоматическое создание точки восстановления Windows перед модификацией.
4. **Применение и валидация**: Применение нового значения через SDK и верификация реестра.
5. **Откат (Rollback)**: При возникновении аномалий — мгновенный откат из журнала истории изменений.

---

## 🐍 Примеры вызова через SDK

```python
from apps.windows.sdk import windows_sdk

# Создание точки восстановления
rp = windows_sdk.core.restore_manager.create_restore_point("Pre-Maintenance Point")

# Проверка и восстановление компонентов Windows
summary = windows_sdk.get_health_summary()
```
