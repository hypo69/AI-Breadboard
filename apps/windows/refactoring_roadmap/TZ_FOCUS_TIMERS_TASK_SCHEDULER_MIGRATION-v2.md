# Техническое задание: Подсистема управления режимами фокусировки, таймеров и подавления уведомлений на уровне ОС (v2)

## 1. Назначение и Архитектурная Ревизия (Windows API Reality vs Custom Policy Engine)

Данное техническое задание определяет архитектуру и порядок реализации подсистемы автоматического управления режимами фокусировки (**Windows Focus Policy & Notification Suppression Engine**) в составе платформы *«Интеллектуальный центр тонких настроек операционной системы и телеметрии ОС»*.

### 1.1 Архитектурная ревизия и ограничение нативных API Windows

При разработке подсистемы учитываются фундаментальные ограничения и свойства API операционных систем Windows 10 и Windows 11, описанные в материалах исследования:

1. **Ограничение Windows 11 `FocusSessionManager`**: В Windows 11 (Windows App SDK, пространство имен `Microsoft.Windows.System.UserProfile`) присутствует класс `FocusSessionManager`. Однако он является **наблюдателем (Observer)**, а не управляющим контроллером.
   * `FocusSessionManager` позволяет узнать, активен ли штатный сеанс Focus (`is_focus_active`), и подписаться на события начала (`started`) и завершения (`ended`) сеанса.
   * **Публичного Windows API для произвольного программного включения или выключения нативного режима Focus в Windows НЕ существует**.
2. **Необходимость собственного Focus Policy Engine**: Поскольку штатный системный Focus не предоставляет программного переключателя, вся логика перевода ОС в рабочий режим (**Work Mode**), правила фильтрации уведомлений, управление звуком, панелью задач и индикацией реализуются автономным модулем платформы — **`WindowsFocusController`**.
3. **Универсальный фундамент `UserNotificationListener`**: Для контроля перехвата и подавления входящих системных уведомлений в Windows 10 (начиная со сборки 1607) и Windows 11 используется нативный WinRT API `Windows.UI.Notifications.Management.UserNotificationListener`.

| Функция / Задача | API Windows | Windows 10 | Windows 11 | Роль в платформе |
| :--- | :--- | :---: | :---: | :--- |
| **Детекция состояния системного Focus** | `FocusSessionManager` | — | ✅ | Наблюдатель (Observer) событий ОС |
| **Перехват & перечисление уведомлений** | `UserNotificationListener` | ✅ | ✅ | Ядро захвата и фильтрации |
| **Удаление / очистка плашек (Toasts)** | `RemoveNotification()` / `ClearNotifications()` | ✅ | ✅ | Подавление всплывающих окон |
| **Управление профилями и расписанием** | `WindowsFocusController` (собственный) | ✅ | ✅ | Выполнение правил режима работы |
| **Автономные триггеры времени (09:00 / 18:00)** | Windows Task Scheduler (`schtasks`) | ✅ | ✅ | Гарантированный запуск вне зависимости от UI |

---

## 2. Двухуровневая Архитектура WindowsFocusController

Подсистема строится на базе компонента `WindowsFocusController`, поддерживающего гибридную работу в зависимости от версии Windows.

```
                         WindowsFocusController
                                    │
           ┌────────────────────────┴────────────────────────┐
           │                                                 │
   Backend Windows 10                                Backend Windows 11
           │                                                 │
  ┌────────┴────────┐                              ┌─────────┴─────────┐
  │ Notification    │                              │ FocusSession-     │ (Observer)
  │ Listener        │                              │ Manager           │
  └────────┬────────┘                              └─────────┬─────────┘
           │                                                 │
           │                                       ┌─────────┴─────────┐
           │                                       │ Notification      │ (Enforcer)
           │                                       │ Listener          │
           │                                       └─────────┬─────────┘
           └────────────────────────┬────────────────────────┘
                                    │
                                    ▼
                          Focus Policy Engine
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
    Уведомления (Toasts)       Звук и Аудио        Панель задач (Taskbar)
   Suppression & Archive      Mute Notification     Suppress Badges &
    in notifications.db          Audio Signals          Icon Flashing
```

### 2.1 Режимы работы бэкендов
* **Windows 10 Backend**: Полагается на `UserNotificationListener` для перехвата уведомлений, собственную таблицу расписаний и контроллер системных параметров (звук, бэджи панели задач).
* **Windows 11 Backend**: Дополнительно подключает `FocusSessionManager` для синхронизации состояния, если пользователь вручную запустил сессию Focus через штатный интерфейс Windows 11 (Часы/Календарь).

---

## 3. Модуль Уведомлений: UserNotificationListener и Запрошенные Права

### 3.1 Модель разрешений и безопасный доступ
Класс `UserNotificationListener` требует явного подтверждения от пользователя в соответствии с политикой безопасности Windows.

1. **Запрос доступа (`RequestAccessAsync`)**: При первом запуске подсистемы фокусировки или включении правила перехвата платформа вызывает метод запроса прав:
   ```csharp
   UserNotificationListener listener = UserNotificationListener.Current;
   UserNotificationListenerAccessStatus status = await listener.RequestAccessAsync();
   ```
2. **Обработка статусов доступа (`UserNotificationListenerAccessStatus`)**:
   * `Allowed` — доступ предоставлен, запуск перехвата и сохранение уведомлений разрешены.
   * `Denied` / `Unspecified` — доступ отклонен пользователем. Система переходит в ограниченный режим (управление расписанием и звуком без архивации уведомлений) и выводит понятное предупреждение в UI.

### 3.2 Механика перехвата и фильтрации уведомлений
При наступлении активного сеанса фокусировки (например, в 09:00):

1. Подсистема подписывается на событие `NotificationChanged` интерфейса `UserNotificationListener`.
2. При вызове события фоновый процессор считывает входящие уведомления через `GetNotificationsAsync(NotificationKinds.Toast)`.
3. Анализируются метаданные каждого уведомления (`AppInfo.DisplayInfo.Title`, `CreationTime`, `Id`, текстовое содержимое).
4. **Подавление всплывающей плашки**: Платформа вызывает `listener.RemoveNotification(notification.Id)` или `ClearNotifications()`, предотвращая появление отвлекающего Toast-уведомления на экране пользователя.
5. **Сохранение в локальный архив**: Данные пропущенного уведомления записываются в таблицу `suppressed_notifications` базы данных `telemetry.db`.

---

## 4. Сценарий Подавления, Архивации и Финального Итога (Post-Session Summary)

### 4.1 Полный жизненный цикл сессии (на примере профиля "Work Focus")

```
 09:00                      10:12                   14:35                   18:00
   │                          │                       │                       │
   ▼                          ▼                       ▼                       ▼
Старт сессии            Входящий Toast         Входящий Toast          Завершение сессии
WORK FOCUS ON           от MS Teams            от Outlook              WORK FOCUS OFF
   │                          │                       │                       │
   ├── Активация          ├── Перехват через      ├── Перехват через      ├── Отписка от
   │   Policy Engine          Listener                Listener                Listener
   │                          │                       │                       │
   └── Запуск             ├── Удаление плашки     ├── Удаление плашки     └── Генерация ИИ-
       перехвата              с экрана (Remove)       с экрана (Remove)       карточки итога
                              │                       │                       (Summary UI)
                              └── Запись в            └── Запись в
                                  notifications.db        notifications.db
```

### 4.2 Сводная UI-карточка завершения сессии (Post-Session Summary)
В 18:00 при автоматическом или ручном завершении фокусного интервала подсистема формирует сводный отчет:

```
┌─────────────────────────────────────────────────────────────┐
│ 🎯 Рабочий фокус завершён (09:00 — 18:00)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Всего подавлено отвлекающих уведомлений: 7                  │
│                                                             │
│ 📱 Microsoft Teams       4 уведомления                     │
│ ✉️ Outlook               2 уведомления                     │
│ ✉️ Outlook               2 уведомления                     │
│ ⚙️ Системные службы       1 уведомление                     │
│                                                             │
│ [ 👁 Просмотреть все (7) ]   [ 🗑 Очистить архив ]         │
└─────────────────────────────────────────────────────────────┘
```

При нажатии на «Просмотреть все» пользователь получает развернутый список сохраненных сообщений с фиксацией времени поступления, отправителя и текста.

---

## 5. Конфигурация Профилей Фокусировки (JSON Schema)

Каждый режим работы описывается декларативным JSON-профилем (`FocusProfile`), хранящимся в SQLite.

```json
{
  "profile_id": "prof-work-default",
  "name": "Рабочий фокус",
  "schedule": {
    "days": ["mon", "tue", "wed", "thu", "fri", "sun"],
    "start_time": "09:00",
    "end_time": "18:00",
    "auto_start": true
  },
  "notifications": {
    "mode": "suppress_and_store",
    "allow_priority_apps": ["Microsoft.WindowsTerminal"],
    "store_suppressed": true,
    "show_summary_at_end": true
  },
  "taskbar": {
    "suppress_flashing": true,
    "suppress_badges": true
  },
  "audio": {
    "mute_notification_sounds": true
  },
  "display": {
    "suppress_toast_banners": true
  }
}
```

---

## 6. Интеграция с Windows Task Scheduler

Для гарантии того, что старт сессии в 09:00 и завершение в 18:00 сработают даже при закрытом браузере или перезагрузке системы, расписания регистрируются в системном планировщике Windows.

### 6.1 Именование и структура задач
Раздел планировщика: `\TestComputer\FocusTimers\`
* `TC_Focus_Start_<Profile_ID>` — вызывается во время старта (например, `/ST 09:00`).
* `TC_Focus_Stop_<Profile_ID>` — вызывается во время финиша (например, `/ST 18:00`).

Команда запуска:
`python.exe -m apps.windows.core.focus_executor --action start --profile-id prof-work-default`

---

## 7. Схема Базы Данных SQLite (`telemetry.db`)

Таблицы подсистемы хранят конфигурации профилей, архив подавленных уведомлений и историю сессий.

```sql
-- Таблица профилей фокусировки и расписаний
CREATE TABLE IF NOT EXISTS focus_profiles (
    profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_active_profile INTEGER NOT NULL DEFAULT 0,
    schedule_days TEXT NOT NULL,                  -- 'mon,tue,wed,thu,fri,sun'
    start_time TEXT NOT NULL,                     -- '09:00'
    end_time TEXT NOT NULL,                       -- '18:00'
    is_enabled INTEGER NOT NULL DEFAULT 1,
    profile_json TEXT NOT NULL,                   -- Полный JSON профиля
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Таблица архива подавленных уведомлений
CREATE TABLE IF NOT EXISTS suppressed_notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    app_user_model_id TEXT,
    app_display_name TEXT NOT NULL,
    title TEXT,
    message_text TEXT,
    received_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_read INTEGER NOT NULL DEFAULT 0
);

-- Таблица журнала сессий фокусировки
CREATE TABLE IF NOT EXISTS focus_session_logs (
    session_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    event_type TEXT NOT NULL,                     -- 'SESSION_START', 'SESSION_END', 'MANUAL_OVERRIDE'
    triggered_by TEXT NOT NULL,                   -- 'TASK_SCHEDULER', 'UI_MANUAL', 'SERVICE_SYNC'
    suppressed_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    details_json TEXT
);
```

---

## 8. REST API Контракт (FastAPI)

### 8.1 `GET /api/v1/focus/status`
Возвращает текущее состояние `WindowsFocusController` и статистику активного сеанса.

**Пример ответа**:
```json
{
  "is_focus_active": true,
  "active_profile_id": "prof-work-default",
  "active_profile_name": "Рабочий фокус",
  "session_id": "sess-20261006-090000",
  "session_started_at": "2026-10-06T09:00:00Z",
  "scheduled_end_at": "2026-10-06T18:00:00Z",
  "suppressed_notifications_count": 7,
  "listener_access_status": "Allowed"
}
```

### 8.2 `GET /api/v1/focus/suppressed-notifications`
Возвращает список уведомлений, перехваченных и сохраненных за текущую или выбранную сессию.

### 8.3 `POST /api/v1/focus/profiles`
Создание или обновление профиля расписания с автоматической перерегистрацией задач в Task Scheduler.

### 8.4 `POST /api/v1/focus/request-listener-access`
Инициация системного диалога получения прав `UserNotificationListener.RequestAccessAsync()`.
