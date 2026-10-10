# 🪟 Windows Window Management Control Plane

## 📋 Обзор архитектуры

Модуль **`apps.windows.sdk.modules.window_control_plane`** представляет собой единый OS-level реестр параметров управления окнами, композицией рабочего стола (DWM), панелью задач, экранным окружением и групповыми политиками для **AI-Breadboard**.

Вместо простых манипуляций над дескрипторами `HWND` (`MoveWindow()`, `ShowWindow()`), модуль реализует **Control Plane системных параметров** Windows 10/11, охватывая **295 системных параметров** в 15 ключевых категориях.

```
FastAPI REST API (/api/v1/window-management/*)
                     │
                     ▼
       WindowManagementControlPlane (manager.py)
   ├── WindowControlPlaneCatalog (295 параметров, catalog.py)
   ├── WindowBackendResolver (resolver.py)
   │     ├── SystemParametersInfoW (Win32 User32)
   │     ├── DWM API (dwmapi.dll)
   │     ├── Display Configuration API & GDI32
   │     ├── Windows Registry (HKCU / HKLM)
   │     └── Group Policy GPO / Policy CSP
   └── WindowsSystemRestoreManager (Точки восстановления и Snapshots)
```

---

## 🗂️ 15 Системных Категорий (295 параметров)

| № | Категория | Диапазон | Элементов | Основной механизм | Описание |
|---|---|---|---|---|---|
| **1** | `focus_activation` | 1–15 | 15 | Win32 SPI / User32 | Фокус за курсором (X-Mouse), таймауты переднего плана, блокировка перехвата фокуса |
| **2** | `animations_visual_effects` | 16–35 | 20 | Win32 SPI / Desktop | Анимации окон, меню, списков, теней, перетаскивания и сглаживания шрифтов ClearType |
| **3** | `window_geometry_metrics` | 36–55 | 20 | Win32 SPI / NonClient | Высота заголовков, рамки окон, размеры меню, полос прокрутки, сетка значков |
| **4** | `window_arrangement_snap` | 56–75 | 20 | Explorer / Shell / Win11 | Snap Windows, Snap Assist, Snap Layouts (Win+Z), Snap Groups, мультимониторное прикрепление |
| **5** | `alt_tab_task_switching` | 76–90 | 15 | Policy CSP / Explorer | Фильтрация вкладок браузера Edge (BrowserAltTabBlowout), изоляция по рабочим столам |
| **6** | `virtual_desktops` | 91–102 | 12 | VirtualDesktops / COM | Изоляция панели задач, переключение рабочих столов, анимации и создание пространств |
| **7** | `dwm_window_composition` | 103–122 | 20 | DwmApi (dwmapi.dll) | Mica/Acrylic фоны, скругление углов, темная тема, границы, цвета заголовков, Aero Peek |
| **8** | `taskbar_app_switching` | 123–147 | 25 | Explorer / StuckRects3 | Положение панели задач, выравнивание значков (слева/центр), группировка, виджеты, часы |
| **9** | `mouse_window_behaviour` | 148–168 | 21 | Win32 SPI / Mouse | Скорость указателя, ускорение, параметры двойного щелчка, шлейфы, сонар Ctrl |
| **10** | `keyboard_focus_navigation` | 169–188 | 20 | Win32 SPI / Keyboard | Скорость повтора, мигание каретки, StickyKeys, FilterKeys, ToggleKeys, рамка фокуса |
| **11** | `accessibility_presentation` | 189–208 | 20 | Win32 Accessibility | Высокая контрастность, экранная лупа Magnifier, толщина курсора, SoundSentry |
| **12** | `display_multi_monitor` | 209–235 | 27 | DisplayConfig / DEVMODE | Топология экранов (Extend/Clone), ориентация (Альбомная/Книжная), разрешение, HDR, DPI |
| **13** | `desktop_explorer` | 236–255 | 20 | Explorer / Desktop | Значки рабочего стола, автовыравнивание, скрытые файлы, обои рабочего стола, темы |
| **14** | `theme_window_metrics` | 256–275 | 20 | Win32 SysColors / Metrics | Цвета активных и неактивных заголовков, фон окон, текст меню, системные шрифты |
| **15** | `shell_policy_controls` | 276–295 | 20 | Group Policy (GPO/CSP) | Блокировка панели задач, запрет персонализации, скрытие трея, блокировка оболочки (Kiosk) |

**ИТОГО:** **295 параметров**

---

## 🛡️ Безопасность и SafeOps

- **Машиночитаемая спецификация:** Каждый параметр содержит тип значения, единицу измерения, диапазон `min`/`max` и список допустимых значений.
- **Предварительный просмотр (Dry-Run Preview):** Эндпоинт `POST /settings/{id}/preview` валидирует значение и возвращает оценку рисков без внесения изменений.
- **Интеграция с точками восстановления Windows:** При изменении параметров с риском `medium`, `high`, `critical` или требующих прав администратора автоматически вызывается `WindowsSystemRestoreManager.create_restore_point()`.
- **Мгновенный откат (Rollback):** Возможность вернуть любое измененное значение по `change_id` через `POST /rollback/{change_id}`.

---

## 🚀 REST API Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/v1/window-management/summary` | Сводная статистика по 295 параметрам, бэкендам и рискам |
| `GET` | `/api/v1/window-management/categories` | Список 15 категорий с перечнем входящих параметров |
| `GET` | `/api/v1/window-management/catalog` | Полнотекстовый поиск и фильтрация параметров |
| `GET` | `/api/v1/window-management/settings/{id}` | Метаданные параметра и текущее живое значение |
| `GET` | `/api/v1/window-management/categories/{id}/live` | Пакетное чтение живых значений всей категории |
| `POST` | `/api/v1/window-management/settings/{id}/preview` | Dry-run симуляция изменения параметра |
| `POST` | `/api/v1/window-management/settings/{id}/apply` | Безопасное применение изменения параметра |
| `POST` | `/api/v1/window-management/batch-apply` | Пакетное применение группы параметров |
| `GET` | `/api/v1/window-management/history` | Журнал аудита примененных изменений |
| `POST` | `/api/v1/window-management/rollback/{id}` | Откат изменения к предыдущему значению |

---

## 💡 Примеры использования в Python

```python
from apps.windows.sdk.modules.window_control_plane import get_window_control_plane
from apps.windows.sdk.modules.window_control_plane.models import SettingApplyRequest

plane = get_window_control_plane()

# 1. Получение информации и живого значения параметра
timeout_val = plane.get_live_value("window.focus.foreground_lock_timeout")
print(f"Foreground Lock Timeout: {timeout_val.value} {timeout_val.unit}")

# 2. Сухой прогон (Dry-Run Preview)
preview = plane.preview_setting("window.taskbar.alignment", 0)  # 0 = Left, 1 = Center
print(preview.safety_summary)

# 3. Безопасное применение
result = plane.apply_setting(
    "window.taskbar.alignment",
    SettingApplyRequest(value=1, custom_comment="Центрирование панели задач Windows 11")
)
print(f"Результат: {result.status}, Точка восстановления: {result.restore_point_id}")
```
