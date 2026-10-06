# 🎛️ Полный каталог Windows 10/11 Desktop, Taskbar, Window & Shell Control Plane
## Машиночитаемый Command Registry, матрица Win32 / COM / Registry / PowerShell / SafeOps & FastAPI Endpoints

---

## 📋 Архитектура Control Plane

Архитектура управления подсистемой Windows Desktop & Taskbar разделена на специализированные функциональные домены:

```
WINDOWS DESKTOP CONTROL PLANE
│
├── 🪟 WINDOWS (Win32 HWND Subsystem)
│    ├── Enumerate (EnumWindows, EnumChildWindows)
│    ├── Properties & Geometry (Rect, ClientRect, Styles, Z-Order, Process)
│    ├── State Control (Activate, Focus, Minimize, Maximize, Restore, Hide, Show)
│    ├── Geometry & Bounds (Move, Resize, MoveResize, TopMost, Snap)
│    └── Lifecycle (Close WM_CLOSE, ForceClose TerminateProcess)
│
├── 📌 TASKBAR (Shell UI & Integration)
│    ├── Discovery & State (FindWindow Shell_TrayWnd, IsResponsive, Monitors)
│    ├── Settings (Alignment, AutoHide, Search, Widgets, Copilot, TaskView, Clock)
│    ├── Policies & GPO (LockTaskbar, NoPinning, NoNotifications, HideTrayItems)
│    └── Appearance & Theme (Accent, Transparency, DarkMode)
│
├── 🚀 SHELL & EXPLORER
│    ├── Explorer Lifecycle (Restart, Start, Kill, WaitReady)
│    ├── Namespaces & Known Folders (ThisPC, RecycleBin, Desktop, Network)
│    └── COM Shell.Application (Verbs, FolderItem, ParseName, Details)
│
├── 📊 TASKBAR API (Официальная интеграция ITaskbarList3)
│    ├── Progress Indicators (SetProgressValue, SetProgressState: Normal/Error/Paused)
│    ├── Overlay Icons & Badges (SetOverlayIcon)
│    ├── Thumbnail Toolbars & Previews (ThumbBarAddButtons, SetThumbnailClip)
│    └── Tabbed Thumbnails (RegisterTab, UnregisterTab, SetTabActive)
│
├── 📋 JUMP LISTS (ICustomDestinationList)
│    ├── Custom Categories & Recent/Frequent
│    └── User Tasks & Quick Actions (ShellLink)
│
├── 🖥️ MULTI-MONITOR & DESKTOP GEOMETRY
│    ├── Display Discovery (EnumDisplayMonitors, GetMonitorInfo, DPI, Scale)
│    └── Cross-Monitor Window Management (MoveToMonitor, Center, MaximizeOnMonitor)
│
├── 🔲 VIRTUAL DESKTOPS (IVirtualDesktopManager)
│    ├── Desktop Discovery & Switching
│    └── Window Desktop Assignment (MoveWindowToDesktop, IsWindowOnCurrent)
│
└── 🎨 DWM (Desktop Window Manager)
     ├── Extended Frame & Cloaked State
     └── Attributes (DarkMode, CornerPreference, BackdropMica/Acrylic)
```

---

## 🛡️ Классификация надежности и уровней выполнения (Execution Classes)

| Класс | Описание | Примеры | Безопасность |
|---|---|---|---|
| **`NATIVE`** | Документированные Win32 API, COM интерфейсы и официальные CSP/GPO политики | `EnumWindows`, `SetWindowPos`, `ITaskbarList3`, `ICustomDestinationList` | 🟢 Safe |
| **`COMPATIBILITY`** | Настройки реестра Windows, PowerShell командлеты, Shell automation | `TaskbarAl`, `SearchboxTaskbarMode`, `SHAppBarMessage`, `Start-Process` | 🟡 Caution |
| **`RESTRICTED`** | Действия, требующие прав администратора (Elevation/UAC) или влияющие на всех пользователей | `POLICY.TASKBAR_LOCK`, `PROCESS.TERMINATE`, `EXPLORER.KILL` | 🟠 Admin / Confirm |
| **`INTERNAL`** | Недокументированные внутренности Explorer, манипуляции с памятью трея | Прямое закрепление ярлыков в обход пользователя, манипуляции чужими иконками Tray | 🔴 Unsupported |

---

## 📑 Полный реестр команд (260 операций)

### 1. Окна — Базовый слой (001–020)
| # | Команда | Операция | Win32 API | COM / Registry | PowerShell | Статус |
|---|---|---|---|---|---|---|
| 001 | `WINDOW.ENUMERATE` | Получить все окна | `EnumWindows` | — | `Get-Process \| ? MainWindowHandle` | 🟢 Safe |
| 002 | `WINDOW.ENUM_CHILDREN` | Дочерние окна | `EnumChildWindows` | — | — | 🟢 Safe |
| 003 | `WINDOW.GET_TITLE` | Заголовок окна | `GetWindowTextW` | — | `(Get-Process).MainWindowTitle` | 🟢 Safe |
| 004 | `WINDOW.GET_CLASS` | Класс окна | `GetClassNameW` | — | — | 🟢 Safe |
| 005 | `WINDOW.GET_PID` | Идентификатор процесса | `GetWindowThreadProcessId` | — | — | 🟢 Safe |
| 006 | `WINDOW.GET_THREAD_ID` | TID потока | `GetWindowThreadProcessId` | — | — | 🟢 Safe |
| 007 | `WINDOW.GET_PROCESS` | Имя процесса | ToolHelp / `OpenProcess` | — | `Get-Process` | 🟢 Safe |
| 008 | `WINDOW.IS_VISIBLE` | Видимость | `IsWindowVisible` | — | — | 🟢 Safe |
| 009 | `WINDOW.IS_ENABLED` | Доступность ввода | `IsWindowEnabled` | — | — | 🟢 Safe |
| 010 | `WINDOW.IS_MINIMIZED` | Свернутое состояние | `IsIconic` | — | — | 🟢 Safe |
| 011 | `WINDOW.IS_MAXIMIZED` | Развернутое состояние | `IsZoomed` | — | — | 🟢 Safe |
| 012 | `WINDOW.IS_VALID` | Проверка валидности HWND | `IsWindow` | — | — | 🟢 Safe |
| 013 | `WINDOW.GET_RECT` | Геометрия окна | `GetWindowRect` | — | — | 🟢 Safe |
| 014 | `WINDOW.GET_CLIENT_RECT` | Клиентская область | `GetClientRect` | — | — | 🟢 Safe |
| 015 | `WINDOW.GET_STYLE` | Стили окна | `GetWindowLongPtrW(GWL_STYLE)` | — | — | 🟢 Safe |
| 016 | `WINDOW.GET_EXSTYLE` | Расширенные стили | `GetWindowLongPtrW(GWL_EXSTYLE)` | — | — | 🟢 Safe |
| 017 | `WINDOW.GET_OWNER` | Окно-владелец | `GetWindow(GW_OWNER)` | — | — | 🟢 Safe |
| 018 | `WINDOW.GET_PARENT` | Родительское окно | `GetParent` | — | — | 🟢 Safe |
| 019 | `WINDOW.GET_ZORDER` | Z-порядок | `GetWindow(GW_HWNDPREV/NEXT)` | — | — | 🟢 Safe |
| 020 | `WINDOW.GET_FOREGROUND` | Окно переднего плана | `GetForegroundWindow` | — | — | 🟢 Safe |

### 2. Управление окнами (021–040)
| # | Команда | Операция | Win32 API | Статус |
|---|---|---|---|---|
| 021 | `WINDOW.ACTIVATE` | Активировать и вывести на передний план | `SetForegroundWindow` / `BringWindowToTop` | 🟢 Safe |
| 022 | `WINDOW.FOCUS` | Передать клавиатурный фокус | `SetFocus` / `AttachThreadInput` | 🟢 Safe |
| 023 | `WINDOW.MINIMIZE` | Свернуть окно | `ShowWindow(SW_MINIMIZE)` | 🟢 Safe |
| 024 | `WINDOW.MAXIMIZE` | Развернуть окно | `ShowWindow(SW_MAXIMIZE)` | 🟢 Safe |
| 025 | `WINDOW.RESTORE` | Восстановить размер окна | `ShowWindow(SW_RESTORE)` | 🟢 Safe |
| 026 | `WINDOW.HIDE` | Скрыть окно с экрана | `ShowWindow(SW_HIDE)` | 🟢 Safe |
| 027 | `WINDOW.SHOW` | Показать скрытое окно | `ShowWindow(SW_SHOW)` | 🟢 Safe |
| 028 | `WINDOW.CLOSE` | Корректно закрыть окно | `PostMessageW(WM_CLOSE)` | 🟢 Safe |
| 029 | `WINDOW.FORCE_CLOSE` | Принудительно закрыть процесс | `TerminateProcess` / `taskkill` | 🟠 Admin / Confirm |
| 030 | `WINDOW.MOVE` | Переместить координаты | `SetWindowPos` / `MoveWindow` | 🟢 Safe |
| 031 | `WINDOW.RESIZE` | Изменить размеры | `SetWindowPos` | 🟢 Safe |
| 032 | `WINDOW.MOVE_RESIZE` | Изменить позицию и размер | `SetWindowPos` | 🟢 Safe |
| 033 | `WINDOW.TOPMOST` | Установить поверх всех окон | `SetWindowPos(HWND_TOPMOST)` | 🟢 Safe |
| 034 | `WINDOW.NOT_TOPMOST` | Снять статус TopMost | `SetWindowPos(HWND_NOTOPMOST)` | 🟢 Safe |
| 035 | `WINDOW.SET_STYLE` | Изменить стиль окна | `SetWindowLongPtrW(GWL_STYLE)` | 🟡 Caution |
| 036 | `WINDOW.SET_EXSTYLE` | Изменить расширенный стиль | `SetWindowLongPtrW(GWL_EXSTYLE)` | 🟡 Caution |
| 037 | `WINDOW.SEND_MESSAGE` | Синхронная отправка WM_* | `SendMessageTimeoutW` | 🟡 Caution |
| 038 | `WINDOW.POST_MESSAGE` | Асинхронная отправка WM_* | `PostMessageW` | 🟡 Caution |
| 039 | `WINDOW.REDRAW` | Принудительная перерисовка | `RedrawWindow` | 🟢 Safe |
| 040 | `WINDOW.INVALIDATE` | Сброс клиентской области | `InvalidateRect` | 🟢 Safe |

### 3. Процессы окон (041–050)
| # | Команда | Операция | Механизм | Статус |
|---|---|---|---|---|
| 041 | `PROCESS.FROM_WINDOW` | Получить PID по HWND | `GetWindowThreadProcessId` | 🟢 Safe |
| 042 | `PROCESS.GET_NAME` | Имя исполняемого файла | `psutil.Process.name` | 🟢 Safe |
| 043 | `PROCESS.GET_PATH` | Полный путь к бинарнику | `QueryFullProcessImageNameW` | 🟢 Safe |
| 044 | `PROCESS.GET_OWNER` | Владелец процесса | Token API / `OpenProcessToken` | 🟢 Safe |
| 045 | `PROCESS.GET_PARENT` | Родительский процесс | `psutil.Process.ppid` | 🟢 Safe |
| 046 | `PROCESS.GET_COMMANDLINE`| Аргументы запуска | WMI / NT Query `ProcessCommandLine` | 🟡 Caution |
| 047 | `PROCESS.GET_START_TIME` | Время старта | `psutil.Process.create_time` | 🟢 Safe |
| 048 | `PROCESS.GET_CPU` | Использование процессора | PDH / `psutil.cpu_percent` | 🟢 Safe |
| 049 | `PROCESS.GET_MEMORY` | Использование RAM | `GetProcessMemoryInfo` | 🟢 Safe |
| 050 | `PROCESS.TERMINATE` | Принудительное завершение | `TerminateProcess` | 🟠 Admin / Confirm |

### 4. Taskbar — Обнаружение и состояние (051–060)
| # | Команда | Операция | Механизм | Статус |
|---|---|---|---|---|
| 051 | `TASKBAR.FIND` | Найти окно панели задач | `FindWindowW("Shell_TrayWnd", NULL)` | 🟢 Safe |
| 052 | `TASKBAR.GET_HWND` | Получить HWND панели | `FindWindowW` | 🟢 Safe |
| 053 | `TASKBAR.GET_RECT` | Координаты и габариты | `GetWindowRect` | 🟢 Safe |
| 054 | `TASKBAR.IS_VISIBLE` | Видимость панели | `IsWindowVisible` | 🟢 Safe |
| 055 | `TASKBAR.GET_STATE` | Состояние панели | `SHAppBarMessage(ABM_GETSTATE)` | 🟡 Caution |
| 056 | `TASKBAR.GET_MONITORS` | Панели на других мониторах | `FindWindowExW("Shell_SecondaryTrayWnd")` | 🟢 Safe |
| 057 | `TASKBAR.GET_VERSION` | Версия оболочки | Explorer `FileVersionInfo` | 🟢 Safe |
| 058 | `TASKBAR.GET_EXPLORER_PID`| PID процесса Explorer | `GetWindowThreadProcessId` | 🟢 Safe |
| 059 | `TASKBAR.IS_RESPONSIVE` | Проверка зависания панели | `SendMessageTimeoutW` (SMTO_ABORTIFHUNG) | 🟢 Safe |
| 060 | `TASKBAR.WAIT_READY` | Ожидание готовности Shell | Цикл проверки HWND + `IsWindow` | 🟢 Safe |

### 5. Настройки Taskbar (061–080)
| # | Команда | Настройка | Механизм | Статус |
|---|---|---|---|---|
| 061 | `TASKBAR.SET_ALIGNMENT` | Выравнивание значков (0=слева, 1=центр) | Registry `TaskbarAl` + `WM_SETTINGCHANGE` | 🟡 Caution |
| 062 | `TASKBAR.GET_ALIGNMENT` | Текущее выравнивание | Registry `TaskbarAl` | 🟢 Safe |
| 063 | `TASKBAR.SET_AUTOHIDE` | Автоскрытие панели | `SHAppBarMessage(ABM_SETSTATE)` + `StuckRects3` | 🟡 Caution |
| 064 | `TASKBAR.GET_AUTOHIDE` | Статус автоскрытия | `SHAppBarMessage(ABM_GETSTATE)` | 🟡 Caution |
| 065 | `TASKBAR.SET_LOCKED` | Блокировка размера/положения | Registry `TaskbarSizeMove` | 🟢 Safe |
| 066 | `TASKBAR.SET_SEARCH` | Режим строки поиска | Registry `SearchboxTaskbarMode` | 🟡 Caution |
| 067 | `TASKBAR.GET_SEARCH` | Статус поиска | Registry `SearchboxTaskbarMode` | 🟡 Caution |
| 068 | `TASKBAR.SET_WIDGETS` | Виджеты на панели | Registry `TaskbarDa` | 🟡 Caution |
| 069 | `TASKBAR.GET_WIDGETS` | Статус виджетов | Registry `TaskbarDa` | 🟡 Caution |
| 070 | `TASKBAR.SET_TASKVIEW` | Кнопка Task View | Registry `ShowTaskViewButton` | 🟡 Caution |
| 071 | `TASKBAR.GET_TASKVIEW` | Статус Task View | Registry `ShowTaskViewButton` | 🟡 Caution |
| 072 | `TASKBAR.SET_CHAT` | Кнопка Chat (Win11) | Registry `TaskbarMn` | 🟡 Caution |
| 073 | `TASKBAR.SET_COPILOT` | Кнопка Copilot | Registry `ShowCopilotButton` | 🟡 Caution |
| 074 | `TASKBAR.SET_CLOCK` | Видимость часов | Policy `HideClock` | 🟢 Safe |
| 075 | `TASKBAR.SET_DATE` | Видимость даты | Shell settings | 🟡 Caution |
| 076 | `TASKBAR.SET_SECONDS` | Секунды в часах | Registry `ShowSecondsInSystemClock` | 🟡 Caution |
| 077 | `TASKBAR.SET_NOTIFICATIONS`| Уведомления | Policy `TaskbarNoNotification` | 🟢 Safe |
| 078 | `TASKBAR.SET_THUMBNAILS` | Предпросмотр миниатюр | Policy `TaskbarNoThumbnail` | 🟢 Safe |
| 079 | `TASKBAR.SET_MULTIMON` | Несколько мониторов | Policy `TaskbarNoMultimon` | 🟢 Safe |
| 080 | `TASKBAR.SET_RESIZE_ALLOWED`| Разрешение resize | Policy `TaskbarNoResize` | 🟢 Safe |

### 6. Политики Taskbar / GPO (081–095)
| # | Команда | Имя GPO политики | Ветка реестра |
|---|---|---|---|
| 081 | `POLICY.TASKBAR_LOCK` | `TaskbarLockAll` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 082 | `POLICY.TASKBAR_NO_RESIZE` | `TaskbarNoResize` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 083 | `POLICY.TASKBAR_NO_REDOCK` | `TaskbarNoRedock` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 084 | `POLICY.TASKBAR_NO_MULTIMON`| `TaskbarNoMultimon` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 085 | `POLICY.TASKBAR_NO_THUMBNAIL`| `TaskbarNoThumbnail`| `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 086 | `POLICY.TASKBAR_NO_PINNING` | `NoPinningToTaskbar` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 087 | `POLICY.NO_JUMPLIST_PINNING`| `NoPinningToDestinations`| `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 088 | `POLICY.NO_NOTIFICATION` | `TaskbarNoNotification` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 089 | `POLICY.NO_SYSTEM_TRAY` | `NoTrayItemsDisplay` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 090 | `POLICY.HIDE_NETWORK` | `HideSCANetwork` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 091 | `POLICY.HIDE_VOLUME` | `HideSCAVolume` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 092 | `POLICY.HIDE_POWER` | `HideSCAPower` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 093 | `POLICY.HIDE_SECURITY` | `HideSCAHealth` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 094 | `POLICY.DISABLE_NOTIFICATION_CENTER`| `DisableNotificationCenter`| `HKCU\Software\Policies\Microsoft\Windows\Explorer` |
| 095 | `POLICY.NO_FEATURE_ADVERTISEMENTS` | `NoBalloonFeatureAdvertisements` | `HKCU\Software\Policies\Microsoft\Windows\Explorer` |

### 7. Explorer & Shell (096–110)
| # | Команда | Операция | Реализация | Статус |
|---|---|---|---|---|
| 096 | `SHELL.GET_EXPLORER` | Найти процесс Explorer | `psutil` / Win32 | 🟢 Safe |
| 097 | `SHELL.RESTART_EXPLORER` | Перезапустить Explorer | `taskkill /f /im explorer.exe & start explorer.exe` | 🟡 Caution |
| 098 | `SHELL.START_EXPLORER` | Запустить Explorer | `subprocess.Popen(["explorer.exe"])` | 🟢 Safe |
| 099 | `SHELL.OPEN_FOLDER` | Открыть каталог в проводнике | `os.startfile(folder_path)` | 🟢 Safe |
| 100 | `SHELL.OPEN_FILE` | Открыть файл приложением по умолчанию | `ShellExecuteW(open)` | 🟢 Safe |
| 101 | `SHELL.OPEN_URI` | Открыть URL / протокол | `ShellExecuteW(open, uri)` | 🟢 Safe |
| 102 | `SHELL.OPEN_CONTROL_PANEL` | Открыть панель управления | `ShellExecuteW("control.exe")` | 🟢 Safe |
| 103 | `SHELL.OPEN_SETTINGS` | Параметры Windows | `ms-settings:` URI | 🟢 Safe |
| 104 | `SHELL.OPEN_RECYCLE_BIN` | Корзина | `shell:RecycleBinFolder` | 🟢 Safe |
| 105 | `SHELL.OPEN_NETWORK` | Сетевое окружение | `shell:NetworkPlacesFolder` | 🟢 Safe |
| 106 | `SHELL.OPEN_DESKTOP` | Папка Рабочий стол | `shell:Desktop` | 🟢 Safe |
| 107 | `SHELL.EXECUTE` | Запуск с UAC (runas) | `ShellExecuteW(runas)` | 🟢 Safe |
| 108 | `SHELL.GET_SPECIAL_FOLDER` | Путь к Known Folder | `SHGetKnownFolderPath` | 🟢 Safe |
| 109 | `SHELL.GET_KNOWN_FOLDERS` | Список всех Known Folders | `IKnownFolderManager` | 🟢 Safe |
| 110 | `SHELL.PARSE_PATH` | Парсинг Shell Display Name | `SHParseDisplayName` | 🟢 Safe |

### 8. Shell COM Objects (111–120)
| # | Команда | COM Интерфейс | Назначение |
|---|---|---|---|
| 111 | `SHELL.COM_APPLICATION` | `Shell.Application` | Корневой объект автоматизации Shell |
| 112 | `SHELL.COM_WINDOWS` | `Shell.Windows` | Перечисление открытых окон проводника и IE |
| 113 | `SHELL.COM_FOLDER` | `Folder` | Работа с объектами каталогов Shell |
| 114 | `SHELL.COM_FOLDER_ITEM` | `FolderItem` | Метаданные файлов и ярлыков |
| 115 | `SHELL.COM_INVOKE_VERB` | `FolderItem.InvokeVerb` | Вызов глаголов контекстного меню |
| 116 | `SHELL.COM_BROWSE` | `BrowseForFolder` | Диалог выбора каталога |
| 117 | `SHELL.COM_NAMESPACE` | `NameSpace` | Доступ к специальным виртуальным папкам |
| 118 | `SHELL.COM_PARSE_NAME` | `ParseName` | Разрешение относительного имени в FolderItem |
| 119 | `SHELL.COM_GET_DETAILS` | `GetDetailsOf` | Расширенные метаданные (битрейт, размеры) |
| 120 | `SHELL.COM_EXTENDED_PROPERTIES`| `ExtendedProperty` | Чтение системных свойств Windows Property System |

### 9. Закрепленные приложения & Layout (121–128)
| # | Команда | Механизм | Статус |
|---|---|---|---|
| 121 | `TASKBAR.GET_PINNED` | Сканирование `%APPDATA%\...\User Pinned\TaskBar` | 🟡 Caution |
| 122 | `TASKBAR.PIN_APP` | Shell COM / Interactive Shell UI | 🔴 Unsupported (Зарезервировано за пользователем) |
| 123 | `TASKBAR.UNPIN_APP` | Удаление `.lnk` / Shell COM | 🔴 Unsupported |
| 124 | `TASKBAR.PIN_STORE_APP` | Policy / Provisioned Layout | 🟡 Caution |
| 125 | `TASKBAR.APPLY_LAYOUT` | Применение XML макета Taskbar Layout (GPO/OEM) | 🟢 Safe / 🟠 Admin |
| 126 | `TASKBAR.EXPORT_LAYOUT` | Экспорт текущей конфигурации | 🟡 Caution |
| 127 | `TASKBAR.IMPORT_LAYOUT` | Импорт группового макета | 🟠 Admin |
| 128 | `TASKBAR.RESET_LAYOUT` | Сброс к профилю по умолчанию | 🟠 Admin |

### 10. Taskbar API — Официальная интеграция (ITaskbarList3) (129–143)
| # | Команда | API метод | Статус |
|---|---|---|---|
| 129 | `TASKBAR.PROGRESS_SET` | `ITaskbarList3::SetProgressValue(hwnd, completed, total)` | 🟢 Safe |
| 130 | `TASKBAR.PROGRESS_STATE` | `ITaskbarList3::SetProgressState(hwnd, flags)` | 🟢 Safe |
| 131 | `TASKBAR.PROGRESS_NONE` | Сброс индикатора (`TBPF_NOPROGRESS`) | 🟢 Safe |
| 132 | `TASKBAR.PROGRESS_INDETERMINATE` | Бесконечный прогресс-бар (`TBPF_INDETERMINATE`) | 🟢 Safe |
| 133 | `TASKBAR.OVERLAY_SET` | Установка иконки-бейджа (`SetOverlayIcon`) | 🟢 Safe |
| 134 | `TASKBAR.OVERLAY_CLEAR` | Очистка бейджа (`SetOverlayIcon(hwnd, NULL)`) | 🟢 Safe |
| 135 | `TASKBAR.THUMBNAIL_BUTTONS` | Добавление кнопок в миниатюру (`ThumbBarAddButtons`) | 🟢 Safe |
| 136 | `TASKBAR.THUMBNAIL_UPDATE` | Обновление кнопок (`ThumbBarUpdateButtons`) | 🟢 Safe |
| 137 | `TASKBAR.THUMBNAIL_DELETE` | Удаление кнопок | 🟢 Safe |
| 138 | `TASKBAR.TAB_REGISTER` | Регистрация вкладки (`RegisterTab`) | 🟢 Safe |
| 139 | `TASKBAR.TAB_UNREGISTER` | Отмена регистрации (`UnregisterTab`) | 🟢 Safe |
| 140 | `TASKBAR.TAB_ACTIVATE` | Активация вкладки (`SetTabActive`) | 🟢 Safe |
| 141 | `TASKBAR.TAB_ORDER` | Изменение порядка вкладок (`SetTabOrder`) | 🟢 Safe |
| 142 | `TASKBAR.THUMBNAIL_PREVIEW` | Область обрезки предпросмотра (`SetThumbnailClip`) | 🟢 Safe |
| 143 | `TASKBAR.BUTTON_CREATED` | Регистрация сообщения `TaskbarButtonCreated` | 🟢 Safe |

### 11. Jump Lists (144–156)
| # | Команда | Интерфейс COM | Статус |
|---|---|---|---|
| 144 | `JUMPLIST.CREATE` | `CoCreateInstance(CLSID_DestinationList)` | 🟢 Safe |
| 145 | `JUMPLIST.BEGIN` | `ICustomDestinationList::BeginList` | 🟢 Safe |
| 146 | `JUMPLIST.APPEND_CATEGORY` | `ICustomDestinationList::AppendCategory` | 🟢 Safe |
| 147 | `JUMPLIST.APPEND_TASKS` | `ICustomDestinationList::AddUserTasks` | 🟢 Safe |
| 148 | `JUMPLIST.APPEND_SEPARATOR` | Добавление разделителя задач | 🟢 Safe |
| 149 | `JUMPLIST.COMMIT` | `ICustomDestinationList::CommitList` | 🟢 Safe |
| 150 | `JUMPLIST.DELETE` | `ICustomDestinationList::DeleteList` | 🟢 Safe |
| 151 | `JUMPLIST.GET_MAX_ITEMS` | `ICustomDestinationList::GetMaxSlots` | 🟢 Safe |
| 152 | `JUMPLIST.ADD_FILE` | Добавление файла (IShellItem) | 🟢 Safe |
| 153 | `JUMPLIST.ADD_URI` | Добавление веб-ссылки | 🟢 Safe |
| 154 | `JUMPLIST.ADD_COMMAND` | Добавление команды приложения (IShellLink) | 🟢 Safe |
| 155 | `JUMPLIST.SET_ICON` | Назначение иконки действия | 🟢 Safe |
| 156 | `JUMPLIST.SET_TITLE` | Назначение заголовка пункта | 🟢 Safe |

### 12. System Tray & Notification Area (157–166)
| # | Команда | Механизм | Статус |
|---|---|---|---|
| 157 | `TRAY.FIND` | Поиск `TrayNotifyWnd` в `Shell_TrayWnd` | 🟡 Caution |
| 158 | `TRAY.ENUM_WINDOWS` | Перечисление окон трея | 🟡 Caution |
| 159 | `TRAY.GET_ICONS` | Считывание чужих иконок трея | 🔴 Unsupported (Explorer internals) |
| 160 | `TRAY.GET_ICON_RECT` | Координаты значка трея | 🔴 Unsupported |
| 161 | `TRAY.CLICK_ICON` | Эмуляция клика по иконке трея | 🔴 Unsupported |
| 162 | `TRAY.RIGHT_CLICK_ICON` | Эмуляция правого клика трея | 🔴 Unsupported |
| 163 | `TRAY.HIDE_ICON` | Скрытие значка в меню стрелки | 🟡 Caution |
| 164 | `TRAY.SHOW_ICON` | Отображение значка на панели трея | 🟡 Caution |
| 165 | `TRAY.RESTART` | Перезапуск области уведомлений | 🟡 Caution |
| 166 | `TRAY.ENUM_NOTIFICATION_WINDOWS`| Окна всплывающих уведомлений | 🔴 Unsupported |

### 13. Notification Area Policies (167–173)
| # | Команда | GPO Политика | Статус |
|---|---|---|---|
| 167 | `TRAY.POLICY.HIDE_VOLUME` | `HideSCAVolume` | 🟢 Safe |
| 168 | `TRAY.POLICY.HIDE_NETWORK` | `HideSCANetwork` | 🟢 Safe |
| 169 | `TRAY.POLICY.HIDE_POWER` | `HideSCAPower` | 🟢 Safe |
| 170 | `TRAY.POLICY.HIDE_SECURITY` | `HideSCAHealth` | 🟢 Safe |
| 171 | `TRAY.POLICY.DISABLE_CENTER` | `DisableNotificationCenter` | 🟢 Safe |
| 172 | `TRAY.POLICY.NO_NOTIFICATION` | `TaskbarNoNotification` | 🟢 Safe |
| 173 | `TRAY.POLICY.NO_PROMOTION` | `NoSystraySystemPromotion` | 🟢 Safe |

### 14. Desktop & Displays (174–184)
| # | Команда | Win32 API | Статус |
|---|---|---|---|
| 174 | `DESKTOP.GET_HWND` | `GetDesktopWindow` | 🟢 Safe |
| 175 | `DESKTOP.GET_WORK_AREA` | `SystemParametersInfo(SPI_GETWORKAREA)` | 🟢 Safe |
| 176 | `DESKTOP.GET_WORK_AREAS` | `GetMonitorInfoW` | 🟢 Safe |
| 177 | `DESKTOP.GET_MONITORS` | `EnumDisplayMonitors` | 🟢 Safe |
| 178 | `DESKTOP.GET_PRIMARY_MONITOR` | `EnumDisplayMonitors` (MONITORINFOF_PRIMARY) | 🟢 Safe |
| 179 | `DESKTOP.GET_MONITOR_FROM_WINDOW`| `MonitorFromWindow(MONITOR_DEFAULTTONEAREST)` | 🟢 Safe |
| 180 | `DESKTOP.GET_MONITOR_FROM_POINT` | `MonitorFromPoint` | 🟢 Safe |
| 181 | `DESKTOP.GET_DPI` | `GetDpiForWindow` | 🟢 Safe |
| 182 | `DESKTOP.GET_SCALE` | `GetScaleFactorForMonitor` | 🟢 Safe |
| 183 | `DESKTOP.GET_RESOLUTION` | `EnumDisplaySettingsW` | 🟢 Safe |
| 184 | `DESKTOP.SET_DISPLAY_MODE` | `SetDisplayConfig` | 🟡 Caution |

### 15. Multi-Monitor (185–194)
| # | Команда | Назначение | Статус |
|---|---|---|---|
| 185 | `MONITOR.ENUMERATE` | Полный список всех мониторов с геометрией | 🟢 Safe |
| 186 | `MONITOR.GET_NAME` | Имя устройства дисплея (`DisplayDeviceName`) | 🟢 Safe |
| 187 | `MONITOR.GET_RECT` | Полный прямоугольник монитора | 🟢 Safe |
| 188 | `MONITOR.GET_WORKAREA` | Рабочая область без панели задач | 🟢 Safe |
| 189 | `MONITOR.GET_PRIMARY` | Проверка основного монитора | 🟢 Safe |
| 190 | `MONITOR.GET_DPI` | DPI экрана | 🟢 Safe |
| 191 | `MONITOR.GET_SCALE` | Коэффициент масштабирования (100%, 125%, 150%) | 🟢 Safe |
| 192 | `MONITOR.SET_PRIMARY` | Назначение главного монитора | 🟡 Caution |
| 193 | `MONITOR.SET_MODE` | Смена разрешения и частоты развертки | 🟡 Caution |
| 194 | `MONITOR.ROTATE` | Поворот ориентации (0°, 90°, 180°, 270°) | 🟡 Caution |

### 16. Перемещение окон между мониторами & Snap (195–204)
| # | Команда | Операция | Статус |
|---|---|---|---|
| 195 | `WINDOW.MOVE_TO_MONITOR` | Перенос окна на указанный монитор | 🟢 Safe |
| 196 | `WINDOW.CENTER_ON_MONITOR`| Центрирование окна на мониторе | 🟢 Safe |
| 197 | `WINDOW.MAXIMIZE_ON_MONITOR`| Разворачивание окна на заданном мониторе | 🟢 Safe |
| 198 | `WINDOW.MOVE_LEFT_MONITOR`| Перемещение на левый монитор | 🟢 Safe |
| 199 | `WINDOW.MOVE_RIGHT_MONITOR`| Перемещение на правый монитор | 🟢 Safe |
| 200 | `WINDOW.SNAP_LEFT` | Привязка к левой половине экрана | 🟡 Caution |
| 201 | `WINDOW.SNAP_RIGHT` | Привязка к правой половине экрана | 🟡 Caution |
| 202 | `WINDOW.SNAP_TOP` | Привязка к верхней половине экрана | 🟡 Caution |
| 203 | `WINDOW.SNAP_BOTTOM` | Привязка к нижней половине экрана | 🟡 Caution |
| 204 | `WINDOW.SNAP_QUARTER` | Привязка к четверти экрана (углу) | 🟡 Caution |

### 17. Virtual Desktops (205–215)
| # | Команда | COM / API | Статус |
|---|---|---|---|
| 205 | `VDESKTOP.ENUMERATE` | `IVirtualDesktopManager` / Registry | 🟡 Caution |
| 206 | `VDESKTOP.GET_CURRENT` | `IVirtualDesktopManagerInternal` | 🟡 Caution |
| 207 | `VDESKTOP.CREATE` | Создание нового виртуального стола | 🟡 Caution |
| 208 | `VDESKTOP.REMOVE` | Удаление стола | 🟡 Caution |
| 209 | `VDESKTOP.SWITCH` | Переключение на выбранный рабочий стол | 🟡 Caution |
| 210 | `VDESKTOP.GET_NAME` | Получение имени стола | 🟡 Caution |
| 211 | `VDESKTOP.SET_NAME` | Переименование стола | 🟡 Caution |
| 212 | `VDESKTOP.GET_WALLPAPER`| Фоновый рисунок стола | 🟡 Caution |
| 213 | `VDESKTOP.SET_WALLPAPER`| Установка обоев рабочего стола | 🟢 Safe |
| 214 | `VDESKTOP.MOVE_WINDOW` | `IVirtualDesktopManager::MoveWindowToDesktop` | 🟡 Caution |
| 215 | `VDESKTOP.IS_ON_CURRENT` | `IVirtualDesktopManager::IsWindowOnCurrentVirtualDesktop` | 🟡 Caution |

### 18. DWM — Desktop Window Manager (216–223)
| # | Команда | DWM API | Назначение |
|---|---|---|---|
| 216 | `DWM.GET_ATTRIBUTES` | `DwmGetWindowAttribute` | Получение системных свойств окна |
| 217 | `DWM.SET_ATTRIBUTES` | `DwmSetWindowAttribute` | Установка параметров рендеринга DWM |
| 218 | `DWM.GET_EXTENDED_FRAME` | `DWMWA_EXTENDED_FRAME_BOUNDS` | Точные физические границы окна с тенями |
| 219 | `DWM.GET_CLOAKED` | `DWMWA_CLOAKED` | Проверка скрытого виртуального состояния |
| 220 | `DWM.GET_BOUNDS` | `DwmGetWindowAttribute` | Границы окна |
| 221 | `DWM.SET_DARK_MODE` | `DWMWA_USE_IMMERSIVE_DARK_MODE` | Включение темной темы в заголовке окна |
| 222 | `DWM.SET_CORNER` | `DWMWA_WINDOW_CORNER_PREFERENCE` | Скругление углов (Round, DoNotRound, Small) |
| 223 | `DWM.SET_BACKDROP` | `DWMWA_SYSTEMBACKDROP_TYPE` | Эффект Mica, Acrylic или Tabbed |

### 19. Taskbar Appearance & Themes (224–232)
| # | Команда | Назначение | Статус |
|---|---|---|---|
| 224 | `TASKBAR.SET_COLOR` | Установка цвета акцента панели задач | 🟡 Caution |
| 225 | `TASKBAR.GET_COLOR` | Чтение цвета темы (`AccentColor`) | 🟡 Caution |
| 226 | `TASKBAR.SET_TRANSPARENCY`| Включение/отключение прозрачности | 🟡 Caution |
| 227 | `TASKBAR.GET_TRANSPARENCY`| Статус прозрачности | 🟡 Caution |
| 228 | `TASKBAR.SET_DARK_MODE` | Включение общесистемной темной темы | 🟡 Caution |
| 229 | `TASKBAR.GET_DARK_MODE` | Проверка статуса темы (`AppsUseLightTheme`) | 🟡 Caution |
| 230 | `TASKBAR.SET_THEME` | Применение темы Windows | 🟡 Caution |
| 231 | `TASKBAR.SET_ACCENT` | Акцентный цвет окна | 🟢 Safe |
| 232 | `TASKBAR.RELOAD_THEME` | Обновление темы рабочего стола | 🟡 Caution |

### 20. Explorer Management (233–242)
| # | Команда | Операция | Статус |
|---|---|---|---|
| 233 | `EXPLORER.GET_PID` | Получение PID процесса `explorer.exe` | 🟢 Safe |
| 234 | `EXPLORER.GET_WINDOWS` | Список открытых папок (`Shell.Windows`) | 🟢 Safe |
| 235 | `EXPLORER.RESTART` | Безопасный перезапуск Explorer | 🟡 Caution |
| 236 | `EXPLORER.KILL` | Принудительное завершение процесса | 🟠 Admin / Confirm |
| 237 | `EXPLORER.START` | Запуск нового экземпляра `explorer.exe` | 🟢 Safe |
| 238 | `EXPLORER.WAIT_READY` | Ожидание инициализации рабочего стола | 🟢 Safe |
| 239 | `EXPLORER.OPEN_HOME` | Открытие Домашней страницы проводника | 🟢 Safe |
| 240 | `EXPLORER.OPEN_QUICK_ACCESS`| Открытие Быстрого доступа | 🟢 Safe |
| 241 | `EXPLORER.OPEN_THIS_PC`| Открытие «Этот компьютер» | 🟢 Safe |
| 242 | `EXPLORER.OPEN_RECYCLE_BIN`| Открытие «Корзины» | 🟢 Safe |

### 21. Keyboard & Input Simulation (243–250)
| # | Команда | Комбинация клавиш | Назначение |
|---|---|---|---|
| 243 | `INPUT.SEND_KEY` | `SendInput` | Эмуляция одиночного нажатия клавиши |
| 244 | `INPUT.SEND_HOTKEY` | `SendInput` | Эмуляция сочетания клавиш |
| 245 | `INPUT.WIN_TAB` | `Win + Tab` | Открытие представления задач (Task View) |
| 246 | `INPUT.WIN_D` | `Win + D` | Свернуть все окна / Показать рабочий стол |
| 247 | `INPUT.WIN_B` | `Win + B` | Перевод фокуса на область системного трея |
| 248 | `INPUT.WIN_T` | `Win + T` | Переход по кнопкам приложений на панели задач |
| 249 | `INPUT.WIN_SHIFT_T` | `Win + Shift + T` | Обратный переход по кнопкам панели |
| 250 | `INPUT.ALT_TAB` | `Alt + Tab` | Переключение между открытыми окнами |

### 22. Accessibility & UI Automation (251–260)
| # | Команда | UI Automation Interface | Назначение |
|---|---|---|---|
| 251 | `UIA.FIND_ELEMENT` | `IUIAutomation::FindFirst` | Поиск элемента интерфейса по имени/ID |
| 252 | `UIA.GET_NAME` | `CurrentName` | Получение текстового имени элемента |
| 253 | `UIA.GET_CONTROL_TYPE`| `CurrentControlType` | Тип элемента (Button, ToolBar, Pane) |
| 254 | `UIA.GET_PATTERN` | `GetCurrentPattern` | Получение паттерна взаимодействия |
| 255 | `UIA.INVOKE` | `IUIAutomationInvokePattern` | Вызов клика/нажатия на элементе |
| 256 | `UIA.SELECTION` | `IUIAutomationSelectionItemPattern`| Выбор элемента в списке |
| 257 | `UIA.TOGGLE` | `IUIAutomationTogglePattern` | Переключение чекбокса/тумблера |
| 258 | `UIA.EXPAND` | `IUIAutomationExpandCollapsePattern`| Разворачивание выпадающего меню |
| 259 | `UIA.SET_VALUE` | `IUIAutomationValuePattern` | Ввод текста в поле |
| 260 | `UIA.GET_BOUNDS` | `CurrentBoundingRectangle` | Экранные координаты элемента UI |

---

## 🚀 FastAPI Интеграция и Endpoints

```text
GET    /api/v1/taskbar                    - Сводный статус панели, габариты и окна
GET    /api/v1/taskbar/settings           - Текущие настройки панели
PUT    /api/v1/taskbar/settings           - Обновление параметров
GET    /api/v1/taskbar/windows            - Список открытых окон
GET    /api/v1/taskbar/windows/{hwnd}     - Детальная информация об окне
POST   /api/v1/taskbar/windows/{hwnd}/*   - Действия: activate, minimize, maximize, restore, move, close
POST   /api/v1/taskbar/windows/batch      - Пакетные действия над окнами
GET    /api/v1/taskbar/apps               - Закрепленные приложения
POST   /api/v1/taskbar/apps/launch        - Запуск приложений (UAC/Runas)
POST   /api/v1/taskbar/ux/progress        - Управление прогрессом ITaskbarList3
POST   /api/v1/taskbar/ux/overlay         - Установка бейджа-оверлея
GET    /api/v1/taskbar/commands           - Каталог всех 260 команд (с фильтрами category/risk/class)
GET    /api/v1/taskbar/commands/{id}      - Детальные метаданные конкретной команды
POST   /api/v1/taskbar/execute            - Универсальный execution engine для команд
```
