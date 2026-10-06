# Техническое задание: Подсистема персонализации, тем оформления Windows и управления курсором (Personalization Control Plane)

## 1. Назначение и архитектурная изолированность

Настоящее техническое задание определяет структуру, системные интерфейсы и порядок реализации автономной подсистемы управления персонализацией, внешним видом и параметрами интерфейса Windows (**Personalization & Visual Control Plane**).

Подсистема выделена в строго изолированный функциональный домен, независящий от сервисов фокуса внимания, таймеров и мониторинга процессов. Основная задача подсистемы — обеспечение точного аудита системных визуальных настроек, считывание и принудительное изменение параметров курсора мыши, тем оформления, фоновых изображений и акцентных цветов с параллельным фиксированием транзакций в базе данных `telemetry.db`.

### Ключевые архитектурные принципы

* **Изолированность домена (Domain Separation)**: Изменения интерфейса и параметров мыши/тем выполняются специализированным модулем `PersonalizationManager` и не затрагивают правила блокировки уведомлений или расписания Task Scheduler.
* **Принцип Data-First from SQLite**: Веб-интерфейс панели управления (`/tc#tab-personalization`) опрашивает актуальный срез визуальных параметров напрямую из локальной базы данных `telemetry.db`, получая время отклика менее 5 мс.
* **Транзакционный аудит и откатоустойчивость**: Любая операция смены цвета курсора, размера указателя или системной темы сопровождается фиксацией снимка «до/после» в журнале изменений и созданием контрольной точки восстановления при модификации критических ключей реестра.

---

## 2. Компоненты управления внешним видом и системные API

Управление параметрами персонализации осуществляется через прямые вызовы системных Win32 API (`user32.dll`, `shell32.dll`), манипуляции с ветками системного реестра Windows и работу с Desktop Window Manager (DWM).

### 2.1 Модуль управления курсором и указателем мыши (`CursorSettings`)

Модуль отвечает за считывание и модификацию настроек манипулятора «мышь» и визуального представления указателя.

| Параметр | Системный механизм / Ветка реестра | Диапазон значений / Формат |
| :--- | :--- | :--- |
| **Размер курсора** | `HKCU\Software\Microsoft\Accessibility` -> `CursorSize` | Целое число от `1` до `128` пикселей |
| **Цветовая схема курсора** | `HKCU\Software\Microsoft\Accessibility` -> `CursorType` | `white` (белый), `black` (черный), `inverted` (инверсный), `custom` (пользовательский) |
| **Пользовательский цвет** | `HKCU\Software\Microsoft\Accessibility` -> `CursorColor` | Цвет в формате COLORREF / HEX (например, `#FFCC00`) |
| **Тень под указателем** | `HKCU\Control Panel\Desktop` -> `UserPreferencesMask` | `0` (отключена), `1` (включена) |
| **Шлейф курсора (Trails)** | `SystemParametersInfoW(SPI_SETMOUSETRAILS)` | `0` (отключен) или `2..7` (длина шлейфа) |
| **Скорость движения** | `SystemParametersInfoW(SPI_SETMOUSESPEED)` | Целое число от `1` до `20` (по умолчанию `10`) |
| **Скрытие при наборе** | `SystemParametersInfoW(SPI_SETMOUSETRAILS)` / Desktop Registry | `0` (показывать), `1` (скрывать курсор при вводе с клавиатуры) |
| **Подсветка при Ctrl** | `HKCU\Control Panel\Desktop` -> `MouseTrails` / Accessibility | `0` (выключено), `1` (показывать концентрические круги при нажатии Ctrl) |

### 2.2 Модуль тем оформления и акцентных цветов (`WindowsThemeInfo`)

Обеспечивает инвентаризацию и переключение системных тем, а также управление цветовым оформлением Desktop Window Manager (DWM).

* **Инвентаризация системных и пользовательских тем**:
  * Сканирование дисковых каталогов `%WINDIR%\Resources\Themes` (системные темы) и `%LOCALAPPDATA%\Microsoft\Windows\Themes` (пользовательские темы `.theme`).
  * Парсинг конфигурационных `.theme` файлов для извлечения метаданных (имя темы, путь к фоновому рисунку, цветовая палитра).
* **Управление режимами Light / Dark Mode**:
  * `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize` -> `AppsUseLightTheme` (`0` — тёмный режим приложений, `1` — светлый).
  * `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize` -> `SystemUsesLightTheme` (`0` — тёмная системная панель и Пуск, `1` — светлая).
* **Акцентный цвет DWM (Accent Color)**:
  * Чтение и установка ключа `HKCU\Software\Microsoft\Windows\DWM` -> `AccentColor` (32-битное RGBA/HEX значение).
  * Включение отображения акцентного цвета на заголовках окон и границах (`ColorPrevalence`).

### 2.3 Модуль обоев и экрана блокировки (`WallpaperSettings`)

Управляет фоновыми изображениями всех подключенных мониторов и экраном блокировки.

* **Типы фонового покрытия**:
  * `picture` — статическое изображение (JPEG, PNG, BMP).
  * `solid_color` — сплошной цвет заливки.
  * `slideshow` — циклическая смена изображений из выбранной директории.
  * `spotlight` — динамические обои службы Windows Spotlight.
* **Режимы масштабирования (`fit_mode`)**:
  * Применение режима через `SystemParametersInfoW(SPI_SETDESKWALLPAPER)` и ветку `HKCU\Control Panel\Desktop` -> `WallpaperStyle` / `TileWallpaper`:
    * `Fill` (Style 10) — заполнение с обрезкой.
    * `Fit` (Style 6) — вписывание без обрезки.
    * `Stretch` (Style 2) — растягивание по осям.
    * `Tile` (Style 0, Tile 1) — замощение плиткой.
    * `Center` (Style 0, Tile 0) — выравнивание по центру.
    * `Span` (Style 22) — растягивание единого панорамного изображения на несколько мониторов.
* **ИИ-модуль AI Spotlight**:
  * Интерактивный фоновый разбор текущего изображения с генерацией контекстных справок о географии, архитектуре и истории изображенного объекта.

### 2.4 Управление панелью задач и окнами (`Window Control Plane`)

* **Параметры панели задач**:
  * Выравнивание иконок в Windows 11 (`TaskbarAl`: `0` — слева, `1` — по центру) через `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced`.
  * Автоматическое скрытие панели задач (`TaskbarSizeMove`).
* **Параметры DWM**:
  * Управление эффектами размытия и прозрачности (Mica / Acrylic), эффектами Snap Layouts и анимацией сворачивания окон.

---

## 3. Схема хранения в SQLite (`telemetry.db`) и журнал аудита

Все срезы конфигураций и истории изменений записываются в базы данных SQLite.

```sql
-- Снимок текущей конфигурации персонализации
CREATE TABLE IF NOT EXISTS personalization_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cursor_size INTEGER NOT NULL DEFAULT 32,
    cursor_type TEXT NOT NULL DEFAULT 'white',
    cursor_color_hex TEXT,
    cursor_shadow_enabled INTEGER NOT NULL DEFAULT 1,
    cursor_trails_length INTEGER NOT NULL DEFAULT 0,
    cursor_speed INTEGER NOT NULL DEFAULT 10,
    apps_use_light_theme INTEGER NOT NULL DEFAULT 0,
    system_use_light_theme INTEGER NOT NULL DEFAULT 0,
    dwm_accent_color_hex TEXT NOT NULL DEFAULT '#0078D4',
    wallpaper_path TEXT,
    wallpaper_fit_mode TEXT NOT NULL DEFAULT 'Fill',
    taskbar_alignment TEXT NOT NULL DEFAULT 'center',
    captured_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Журнал транзакций и изменений персонализации
CREATE TABLE IF NOT EXISTS personalization_change_history (
    change_id TEXT PRIMARY KEY,
    parameter_group TEXT NOT NULL,          -- 'CURSOR', 'THEME', 'WALLPAPER', 'TASKBAR'
    parameter_name TEXT NOT NULL,           -- 'cursor_size', 'apps_use_light_theme', etc.
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL DEFAULT 'USER_UI', -- 'USER_UI', 'AI_AGENT', 'REST_API'
    restore_point_created INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 4. Контракт REST API (FastAPI)

Базовый префикс роутера: `/api/v1/windows/personalization`

### 4.1 `GET /api/v1/windows/personalization/state`
Возвращает свежий срез всех параметров персонализации из таблицы `personalization_snapshots`.

**Пример ответа**:
```json
{
  "cursor": {
    "size": 48,
    "type": "custom",
    "color_hex": "#FFCC00",
    "shadow_enabled": true,
    "trails_length": 0,
    "speed": 12,
    "hide_while_typing": true
  },
  "theme": {
    "active_theme_name": "Windows Dark",
    "apps_use_light_theme": false,
    "system_use_light_theme": false,
    "accent_color_hex": "#38BDF8"
  },
  "wallpaper": {
    "current_path": "C:\\Windows\\Web\\Wallpaper\\Windows\\img19.jpg",
    "fit_mode": "Fill",
    "source_type": "picture"
  },
  "taskbar": {
    "alignment": "center",
    "auto_hide": false
  },
  "last_updated": "2026-10-06T11:15:00Z"
}
```

### 4.2 `POST /api/v1/windows/personalization/cursor`
Применяет новые параметры указателя мыши и синхронизирует изменения с реестром и `SystemParametersInfoW`.

**Тело запроса**:
```json
{
  "size": 48,
  "type": "custom",
  "color_hex": "#FFCC00",
  "shadow_enabled": true,
  "trails_length": 0,
  "speed": 12
}
```

### 4.3 `POST /api/v1/windows/personalization/theme`
Переключает темы оформления или режим Dark/Light.

### 4.4 `GET /api/v1/windows/personalization/history`
Возвращает историю изменений из таблицы `personalization_change_history`.

---

## 5. Гарантии безопасности и откатоустойчивость (SafeOps)

1. **Валидация диапазонов**: Перед записью в реестр значения параметров курсора жестко проверяются на допустимые границы (`cursor_size`: 1..128, `cursor_speed`: 1..20).
2. **Безопасное обновление DWM**: При смене акцентного цвета выполняется радиовещательное уведомление окон через `SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, ...)` для предотвращения зависания проводника Explorer.
3. **Резервное копирование ветки реестра**: Модуль `SafeSystemParamManager` автоматически сохраняет бэкап редактируемых веток реестра в каталог экспорта перед применением групповых изменений.
