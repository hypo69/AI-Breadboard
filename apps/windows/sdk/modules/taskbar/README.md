# 📌 Windows Taskbar & Window Management Module

## 📋 Обзор модуля

Модуль **`apps.windows.sdk.modules.taskbar`** реализует многоуровневое управление панелью задач Windows 10/11 и окнами рабочего стола для платформы **AI-Breadboard**.

```
FastAPI REST API (/api/v1/taskbar/*)
        │
        ▼
TaskbarController (manager.py)
   ├── SettingsManager (Registry: Advanced / StuckRects3, Shell AppBar API)
   ├── WindowManager   (Win32 User32: EnumWindows, ShowWindow, MoveWindow, WM_CLOSE)
   └── AppManager      (Shell32, PowerShell, User Pinned shortcuts, UAC Runas)
```

---

## 🎛️ Архитектурные уровни и возможности

| Домен | Технология | Возможности |
|---|---|---|
| **Настройки панели** | Registry / Shell API | Выравнивание значков (слева/центр), поиск, виджеты, Copilot, Task View, автоскрытие, бейджи, группировка |
| **Управление окнами** | Win32 User32 / DWM | Перечисление открытых окон (`EnumWindows`), активация, сворачивание, разворачивание, перемещение, закрытие (`WM_CLOSE`), пакетные действия |
| **Закрепление и запуск** | Shell / COM / PS | Список закрепленных приложений (`User Pinned\TaskBar`), запуск приложений с аргументами / UAC, закрепление и открепление |

---

## 🚀 FastAPI Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/v1/taskbar` | Сводный отчет о состоянии панели задач и открытых окон |
| `GET` | `/api/v1/taskbar/settings` | Получение текущих параметров панели задач |
| `PUT` | `/api/v1/taskbar/settings` | Обновление настроек панели задач |
| `GET` | `/api/v1/taskbar/windows` | Список окон верхнего уровня рабочего стола |
| `GET` | `/api/v1/taskbar/windows/{hwnd}` | Детальная информация об окне по дескриптору HWND |
| `POST` | `/api/v1/taskbar/windows/{hwnd}/activate` | Активация и вывод окна на передний план |
| `POST` | `/api/v1/taskbar/windows/{hwnd}/minimize` | Сворачивание окна |
| `POST` | `/api/v1/taskbar/windows/{hwnd}/maximize` | Разворачивание окна |
| `POST` | `/api/v1/taskbar/windows/{hwnd}/restore` | Восстановление окна |
| `POST` | `/api/v1/taskbar/windows/{hwnd}/move` | Перемещение и масштабирование окна |
| `DELETE` | `/api/v1/taskbar/windows/{hwnd}` | Корректное закрытие окна |
| `POST` | `/api/v1/taskbar/windows/batch` | Пакетные действия (`minimize_all`, `restore_all`, `minimize_all_except`, `close_by_process`) |
| `GET` | `/api/v1/taskbar/apps` | Список закрепленных приложений |
| `POST` | `/api/v1/taskbar/apps/launch` | Запуск приложения (включая режим администратора) |
| `POST` | `/api/v1/taskbar/apps/pin` | Закрепление приложения на панели |
| `DELETE` | `/api/v1/taskbar/apps/pin` | Открепление приложения от панели |

---

## 💡 Примеры использования в Python

```python
from apps.windows.sdk.modules.taskbar import TaskbarController
from apps.windows.sdk.modules.taskbar.core.models import TaskbarSettingsUpdate, WindowBatchActionRequest

controller = TaskbarController()

# 1. Получить сводный статус
summary = controller.get_summary()
print(f"Открыто окон: {summary.windows_count}, Панель: {summary.taskbar_rect}")

# 2. Найти и активировать окно
edge_windows = controller.list_windows(process_filter="msedge")
if edge_windows:
    controller.activate_window(edge_windows[0].hwnd)

# 3. Свернуть все окна, кроме целевого
controller.execute_batch_window_action(WindowBatchActionRequest(
    action="minimize_all_except",
    target_hwnd=edge_windows[0].hwnd if edge_windows else None
))

# 4. Обновить настройки панели (выравнивание по центру)
controller.update_settings(TaskbarSettingsUpdate(alignment=1, auto_hide=False))
```
