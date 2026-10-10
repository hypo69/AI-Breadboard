# 🎯 Focus Policy Engine (`apps/windows/modules/focus_policy`)

**Status:** ✅ Active · **Author:** hypo69

Автономный контроллер режимов фокусировки (ТЗ `refactoring_roadmap/TZ_FOCUS_TIMERS_TASK_SCHEDULER_MIGRATION-v2.md`).
Системный Focus Windows 11 (`FocusSessionManager`) — только наблюдатель, поэтому логика режима работы реализована здесь.

| Компонент | Назначение |
|---|---|
| `controller.py` | `WindowsFocusController`: профили, сессии, подавление/архив уведомлений, итог сессии |
| `scheduler.py` | `FocusTaskRegistrar`: задачи `\TestComputer\FocusTimers\TC_Focus_Start_<id>` / `TC_Focus_Stop_<id>` через `schtasks` |
| `listener.py` | Адаптер WinRT `UserNotificationListener` (нужен пакет `winrt-Windows.UI.Notifications.Management`; без него и без прав — режим без архивации) |
| `../../core/focus_executor.py` | Точка входа Task Scheduler: `python -m apps.windows.sdk.core.focus_executor --action start --profile-id <id>` |

Таблицы `telemetry.db`: `focus_profiles`, `suppressed_notifications`, `focus_session_logs`. Состояние активной сессии хранится в БД.

## REST API (`/api/v1/focus`)

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/status` | Состояние контроллера и активной сессии |
| `GET` | `/suppressed-notifications` | Архив подавленных уведомлений |
| `POST` | `/profiles` | Создать/обновить профиль и перерегистрировать задачи |
| `POST` | `/request-listener-access` | Запросить права `UserNotificationListener` |

> Перехват выполняется вызовом `WindowsFocusController.poll_notifications()` (подписка на `NotificationChanged` не реализована).
> Звук (`audio.mute_notification_sounds`) пока не применяется — в проекте нет реализации.
